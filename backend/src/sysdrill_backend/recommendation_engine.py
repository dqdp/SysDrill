import copy
import threading
from datetime import datetime, timezone
from typing import Any

from sysdrill_backend.executable_learning_unit_materializer import supported_materialization_pairs

_ACTION_PAIR_ORDER = {
    ("Study", "LearnNew"): 0,
    ("Study", "Reinforce"): 1,
    ("Study", "SpacedReview"): 2,
    ("Practice", "Reinforce"): 3,
    ("Practice", "Remediate"): 4,
}


class RecommendationEngineError(ValueError):
    pass


class NoRecommendationCandidatesError(RecommendationEngineError):
    pass


class RecommendationDecisionNotFoundError(RecommendationEngineError):
    pass


def _strictness_profile(mode: str) -> str:
    if mode == "Study":
        return "supportive"
    if mode == "Practice":
        return "standard"
    return "strict"


def _action_pattern(action: dict[str, Any]) -> tuple[str, str, str]:
    return (
        action["mode"],
        action["session_intent"],
        action["target_id"],
    )


class RecommendationEngine:
    def __init__(self, runtime: Any):
        self._runtime = runtime
        self._decisions: dict[str, dict[str, Any]] = {}
        self._decision_counter = 0
        self._state_lock = threading.RLock()

    def next_recommendation(self, user_id: str) -> dict[str, Any]:
        with self._state_lock:
            candidate_records = self._candidate_records()
            if not candidate_records:
                raise NoRecommendationCandidatesError("no recommendation candidates are available")

            decision_context = self._choose_action(user_id, candidate_records)
            decision_id = self._next_decision_id()
            occurred_at = self._utc_now_iso()
            decision_record = {
                "decision_id": decision_id,
                "user_id": user_id,
                "policy_version": "bootstrap.recommendation.v1",
                "decision_mode": "rule_based",
                "candidate_actions": [
                    copy.deepcopy(record["action"])
                    for record in decision_context["candidate_records"]
                ],
                "chosen_action": copy.deepcopy(decision_context["chosen_action"]),
                "supporting_signals": list(decision_context["supporting_signals"]),
                "blocking_signals": list(decision_context["blocking_signals"]),
                "rationale": decision_context["rationale"],
                "alternatives_summary": decision_context["alternatives_summary"],
                "generated_at": occurred_at,
                "shown_at": occurred_at,
                "accepted_at": None,
                "accepted_session_id": None,
                "completed_at": None,
                "completed_session_id": None,
            }
            self._decisions[decision_id] = decision_record
            return self._public_decision(decision_record)

    def get_decision(self, decision_id: str) -> dict[str, Any]:
        with self._state_lock:
            decision = self._decisions.get(decision_id)
            if decision is None:
                raise RecommendationDecisionNotFoundError(
                    "unknown decision_id: {0}".format(decision_id)
                )
            return copy.deepcopy(decision)

    def mark_accepted(self, decision_id: str, session_id: str) -> None:
        with self._state_lock:
            decision = self._require_decision(decision_id)
            decision["accepted_at"] = self._utc_now_iso()
            decision["accepted_session_id"] = session_id

    def mark_completed(self, decision_id: str, session_id: str) -> None:
        with self._state_lock:
            decision = self._require_decision(decision_id)
            decision["completed_at"] = self._utc_now_iso()
            decision["completed_session_id"] = session_id

    def _public_decision(self, decision: dict[str, Any]) -> dict[str, Any]:
        return {
            "decision_id": decision["decision_id"],
            "policy_version": decision["policy_version"],
            "decision_mode": decision["decision_mode"],
            "candidate_actions": copy.deepcopy(decision["candidate_actions"]),
            "chosen_action": copy.deepcopy(decision["chosen_action"]),
            "supporting_signals": list(decision["supporting_signals"]),
            "blocking_signals": list(decision["blocking_signals"]),
            "rationale": decision["rationale"],
            "alternatives_summary": decision["alternatives_summary"],
        }

    def _candidate_records(self) -> list[dict[str, Any]]:
        records = []
        for mode, session_intent in supported_materialization_pairs():
            pair_order = _ACTION_PAIR_ORDER[(mode, session_intent)]
            launch_options = self._runtime.list_manual_launch_options(
                mode=mode,
                session_intent=session_intent,
            )
            for option in launch_options:
                target_id = option.get("content_id")
                if not isinstance(target_id, str) or not target_id:
                    continue
                records.append(
                    {
                        "action": {
                            "mode": mode,
                            "session_intent": session_intent,
                            "target_type": "concept",
                            "target_id": target_id,
                            "difficulty_profile": option["effective_difficulty"],
                            "strictness_profile": _strictness_profile(mode),
                            "session_size": "single_unit",
                            "delivery_profile": "text_first",
                        },
                        "target_title": (
                            option.get("display_title")
                            or option.get("topic_slug")
                            or option["content_id"]
                        ),
                        "pair_order": pair_order,
                    }
                )
        records.sort(key=lambda record: (record["action"]["target_id"], record["pair_order"]))
        return records

    def _choose_action(
        self,
        user_id: str,
        candidate_records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        latest_outcomes = {}
        for outcome in self._runtime.list_user_reviewed_outcomes(user_id):
            latest_outcomes[outcome["content_id"]] = outcome

        learn_new_targets = {
            record["action"]["target_id"]
            for record in candidate_records
            if (
                record["action"]["mode"] == "Study"
                and record["action"]["session_intent"] == "LearnNew"
            )
        }
        filtered_records = [
            record
            for record in candidate_records
            if not (
                record["action"]["mode"] == "Practice"
                and record["action"]["target_id"] not in latest_outcomes
                and record["action"]["target_id"] in learn_new_targets
            )
        ]

        blocking_signals = []
        recent_patterns = self._recent_accepted_patterns(user_id)
        if len(recent_patterns) >= 2 and recent_patterns[-1] == recent_patterns[-2]:
            repeated_pattern = recent_patterns[-1]
            anti_loop_filtered = [
                record
                for record in filtered_records
                if _action_pattern(record["action"]) != repeated_pattern
            ]
            if anti_loop_filtered:
                filtered_records = anti_loop_filtered
                blocking_signals.append("anti_loop_guardrail")

        if not filtered_records:
            raise NoRecommendationCandidatesError("no recommendation candidates are available")

        weak_targets = []
        middling_targets = []
        unseen_targets = sorted(
            {
                record["action"]["target_id"]
                for record in filtered_records
                if (
                    record["action"]["mode"] == "Study"
                    and record["action"]["session_intent"] == "LearnNew"
                    and record["action"]["target_id"] not in latest_outcomes
                )
            }
        )
        seen_targets = []

        for target_id in sorted({record["action"]["target_id"] for record in filtered_records}):
            outcome = latest_outcomes.get(target_id)
            if outcome is None:
                continue

            seen_targets.append(target_id)
            weighted_score = outcome["weighted_score"]
            missing_dimension_count = len(outcome["missing_dimensions"])
            if weighted_score < 0.55 or missing_dimension_count >= 2:
                weak_targets.append(target_id)
            elif weighted_score < 0.8 or missing_dimension_count >= 1:
                middling_targets.append(target_id)

        if weak_targets:
            target_id = weak_targets[0]
            chosen_record = self._first_matching_record(
                filtered_records,
                target_id=target_id,
                mode="Practice",
                session_intent="Remediate",
            )
            return self._decision_payload(
                candidate_records=filtered_records,
                chosen_record=chosen_record,
                supporting_signals=[
                    "weak_reviewed_outcome",
                    "bounded_remediation_priority",
                ],
                blocking_signals=blocking_signals,
                rationale=(
                    "Choose Practice / Remediate on '{0}' because the latest reviewed "
                    "outcome is weak and the next step should be bounded remediation."
                ).format(chosen_record["target_title"]),
                alternatives_summary=(
                    "Study actions remain available, but bounded remediation is ranked "
                    "higher than exploration after a weak reviewed attempt."
                ),
            )

        if middling_targets:
            target_id = middling_targets[0]
            chosen_record = self._first_matching_record(
                filtered_records,
                target_id=target_id,
                mode="Practice",
                session_intent="Reinforce",
            )
            return self._decision_payload(
                candidate_records=filtered_records,
                chosen_record=chosen_record,
                supporting_signals=[
                    "partially_stable_reviewed_outcome",
                    "bounded_reinforcement_priority",
                ],
                blocking_signals=blocking_signals,
                rationale=(
                    "Choose Practice / Reinforce on '{0}' because the latest reviewed "
                    "outcome is promising but still needs reinforcement."
                ).format(chosen_record["target_title"]),
                alternatives_summary=(
                    "Study actions remain available, but the current recommendation "
                    "prefers one tighter reinforcement pass first."
                ),
            )

        if unseen_targets:
            target_id = unseen_targets[0]
            chosen_record = self._first_matching_record(
                filtered_records,
                target_id=target_id,
                mode="Study",
                session_intent="LearnNew",
            )
            return self._decision_payload(
                candidate_records=filtered_records,
                chosen_record=chosen_record,
                supporting_signals=[
                    "no_prior_reviewed_attempt_for_target",
                    "bootstrap_exploration_bias",
                ],
                blocking_signals=blocking_signals,
                rationale=(
                    "Start with a supportive Study / LearnNew unit on '{0}' because "
                    "there is no reviewed evidence for this concept yet."
                ).format(chosen_record["target_title"]),
                alternatives_summary=(
                    "Practice actions remain available but are downranked until there "
                    "is reviewed evidence for this concept."
                ),
            )

        if seen_targets:
            target_id = seen_targets[0]
            chosen_record = self._first_matching_record(
                filtered_records,
                target_id=target_id,
                mode="Study",
                session_intent="SpacedReview",
            )
            return self._decision_payload(
                candidate_records=filtered_records,
                chosen_record=chosen_record,
                supporting_signals=[
                    "reviewed_success_without_unseen_targets",
                    "bounded_spaced_review_fallback",
                ],
                blocking_signals=blocking_signals,
                rationale=(
                    "Use Study / SpacedReview on '{0}' because reviewed performance "
                    "is currently stable and there are no unseen concepts left."
                ).format(chosen_record["target_title"]),
                alternatives_summary=(
                    "Practice actions stay available, but the current placeholder "
                    "policy falls back to bounded review after stable recent outcomes."
                ),
            )

        raise NoRecommendationCandidatesError("no recommendation candidates are available")

    def _decision_payload(
        self,
        candidate_records: list[dict[str, Any]],
        chosen_record: dict[str, Any],
        supporting_signals: list[str],
        blocking_signals: list[str],
        rationale: str,
        alternatives_summary: str,
    ) -> dict[str, Any]:
        chosen_action = copy.deepcopy(chosen_record["action"])
        chosen_action["rationale"] = rationale
        return {
            "candidate_records": candidate_records,
            "chosen_action": chosen_action,
            "supporting_signals": supporting_signals,
            "blocking_signals": blocking_signals,
            "rationale": rationale,
            "alternatives_summary": alternatives_summary,
        }

    def _first_matching_record(
        self,
        records: list[dict[str, Any]],
        target_id: str,
        mode: str,
        session_intent: str,
    ) -> dict[str, Any]:
        for record in records:
            action = record["action"]
            if (
                action["target_id"] == target_id
                and action["mode"] == mode
                and action["session_intent"] == session_intent
            ):
                return record
        raise NoRecommendationCandidatesError(
            "no recommendation candidates are available for target '{0}'".format(target_id)
        )

    def _recent_accepted_patterns(self, user_id: str) -> list[tuple[str, str, str]]:
        accepted_records = [
            decision
            for decision in self._decisions.values()
            if decision["user_id"] == user_id and decision["accepted_at"] is not None
        ]
        accepted_records.sort(key=lambda decision: decision["decision_id"])
        return [_action_pattern(decision["chosen_action"]) for decision in accepted_records]

    def _require_decision(self, decision_id: str) -> dict[str, Any]:
        decision = self._decisions.get(decision_id)
        if decision is None:
            raise RecommendationDecisionNotFoundError(
                "unknown decision_id: {0}".format(decision_id)
            )
        return decision

    def _next_decision_id(self) -> str:
        self._decision_counter += 1
        return "rec.{0:04d}".format(self._decision_counter)

    def _utc_now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()
