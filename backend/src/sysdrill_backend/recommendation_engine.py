import copy
import threading
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from sysdrill_backend.executable_learning_unit_materializer import supported_materialization_pairs
from sysdrill_backend.learner_projection import LearnerProjector

_ACTION_PAIR_ORDER = {
    ("Study", "LearnNew"): 0,
    ("Study", "Reinforce"): 1,
    ("Study", "SpacedReview"): 2,
    ("Practice", "Reinforce"): 3,
    ("Practice", "Remediate"): 4,
    ("MockInterview", "ReadinessCheck"): 5,
}


class RecommendationEngineError(ValueError):
    pass


class NoRecommendationCandidatesError(RecommendationEngineError):
    pass


class RecommendationDecisionNotFoundError(RecommendationEngineError):
    pass


class RecommendationDecisionLifecycleError(RecommendationEngineError):
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
    def __init__(self, runtime: Any, learner_projector: Any | None = None):
        self._runtime = runtime
        self._learner_projector = (
            LearnerProjector() if learner_projector is None else learner_projector
        )
        self._decisions: dict[str, dict[str, Any]] = {}
        self._decision_counter = 0
        self._state_lock = threading.RLock()

    def next_recommendation(self, user_id: str) -> dict[str, Any]:
        with self._state_lock:
            candidate_records = self._candidate_records()
            if not candidate_records:
                raise NoRecommendationCandidatesError("no recommendation candidates are available")

            recommendation_context = self._recommendation_context(user_id, candidate_records)
            decision_context = self._choose_action(recommendation_context)
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
            self._record_acceptance(decision, session_id)

    def accept_session(
        self,
        decision_id: str,
        session_starter: Callable[[], dict[str, Any]],
    ) -> dict[str, Any]:
        with self._state_lock:
            decision = self._require_decision(decision_id)
            self._ensure_decision_not_accepted(decision)
            session = session_starter()
            session_id = session.get("session_id")
            if not isinstance(session_id, str) or not session_id:
                raise RecommendationDecisionLifecycleError(
                    "accepted session must include a non-empty session_id"
                )
            self._record_acceptance(decision, session_id)
            return session

    def accept_session_or_replay(
        self,
        decision_id: str,
        session_starter: Callable[[], dict[str, Any]],
        accepted_session_loader: Callable[[str], dict[str, Any]],
    ) -> dict[str, Any]:
        with self._state_lock:
            decision = self._require_decision(decision_id)
            accepted_session_id = decision.get("accepted_session_id")
            if isinstance(accepted_session_id, str) and accepted_session_id:
                try:
                    session = accepted_session_loader(accepted_session_id)
                except Exception as exc:  # pragma: no cover - normalized into lifecycle error
                    raise RecommendationDecisionLifecycleError(
                        "accepted session is not available for replay"
                    ) from exc
                session_id = session.get("session_id")
                if not isinstance(session_id, str) or session_id != accepted_session_id:
                    raise RecommendationDecisionLifecycleError(
                        "accepted session is not available for replay"
                    )
                return session

            session = session_starter()
            session_id = session.get("session_id")
            if not isinstance(session_id, str) or not session_id:
                raise RecommendationDecisionLifecycleError(
                    "accepted session must include a non-empty session_id"
                )
            self._record_acceptance(decision, session_id)
            return session

    def mark_completed(self, decision_id: str, session_id: str) -> None:
        with self._state_lock:
            decision = self._require_decision(decision_id)
            accepted_session_id = decision.get("accepted_session_id")
            if not isinstance(accepted_session_id, str) or not accepted_session_id:
                raise RecommendationDecisionLifecycleError(
                    "decision must be accepted before it can be completed"
                )
            if accepted_session_id != session_id:
                raise RecommendationDecisionLifecycleError(
                    "decision can only complete for its accepted session"
                )
            if decision.get("completed_at") is not None:
                raise RecommendationDecisionLifecycleError("decision is already completed")
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
            pair_order = _ACTION_PAIR_ORDER.get((mode, session_intent))
            if pair_order is None:
                continue
            launch_options = self._runtime.list_manual_launch_options(
                mode=mode,
                session_intent=session_intent,
            )
            for option in launch_options:
                target_id = option.get("content_id")
                if not isinstance(target_id, str) or not target_id:
                    continue
                action_target_type = "concept"
                if (mode, session_intent) == ("MockInterview", "ReadinessCheck"):
                    target_id = _scenario_family_from_content_id(target_id)
                    action_target_type = "scenario_family"
                records.append(
                    {
                        "action": {
                            "mode": mode,
                            "session_intent": session_intent,
                            "target_type": action_target_type,
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
        recommendation_context: dict[str, Any],
    ) -> dict[str, Any]:
        candidate_records = recommendation_context["candidate_records"]
        concept_state = recommendation_context["concept_state"]
        subskill_state = recommendation_context["subskill_state"]
        latest_outcomes = recommendation_context["latest_outcomes"]
        recent_patterns = recommendation_context["recent_accepted_patterns"]
        trajectory_state = recommendation_context["trajectory_state"]
        recent_mock_feedback = recommendation_context["recent_mock_feedback"]
        scenario_bound_concept_ids = recommendation_context["scenario_bound_concept_ids"]
        seen_targets = set(concept_state)

        learn_new_targets = {
            record["action"]["target_id"]
            for record in candidate_records
            if (
                record["action"]["mode"] == "Study"
                and record["action"]["session_intent"] == "LearnNew"
            )
        }
        unlocked_bound_targets = {
            target_id for target_id in seen_targets if target_id in scenario_bound_concept_ids
        }

        filtered_records = []
        for record in candidate_records:
            action = record["action"]
            target_id = action["target_id"]
            if (
                action["target_type"] == "concept"
                and target_id in scenario_bound_concept_ids
                and target_id not in unlocked_bound_targets
            ):
                continue
            if (
                action["mode"] == "Practice"
                and target_id not in seen_targets
                and target_id in learn_new_targets
            ):
                continue
            filtered_records.append(record)

        blocking_signals = []
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

        mock_record = self._eligible_mock_record(
            filtered_records=filtered_records,
            concept_state=concept_state,
            trajectory_state=trajectory_state,
        )
        if recent_mock_feedback is not None:
            filtered_records = [
                record
                for record in filtered_records
                if (
                    record["action"]["mode"] != "MockInterview"
                    or record["action"]["session_intent"] != "ReadinessCheck"
                )
            ]
            mock_record = None
            blocking_signals.append(recent_mock_feedback["signal"])
        if mock_record is None:
            filtered_records = [
                record
                for record in filtered_records
                if (
                    record["action"]["mode"] != "MockInterview"
                    or record["action"]["session_intent"] != "ReadinessCheck"
                )
            ]
            if not filtered_records:
                raise NoRecommendationCandidatesError("no recommendation candidates are available")

        weak_targets = []
        reinforce_targets = []
        review_due_targets = []
        unseen_targets = sorted(
            {
                record["action"]["target_id"]
                for record in filtered_records
                if (
                    record["action"]["mode"] == "Study"
                    and record["action"]["session_intent"] == "LearnNew"
                    and record["action"]["target_id"] not in seen_targets
                )
            }
        )
        seen_targets = []
        supported_subskill_gap = _supported_subskill_gap(subskill_state)

        for target_id in sorted({record["action"]["target_id"] for record in filtered_records}):
            concept_summary = concept_state.get(target_id)
            if not isinstance(concept_summary, dict):
                continue

            seen_targets.append(target_id)
            if _is_confirmed_weak(concept_summary):
                weak_targets.append(target_id)
                continue
            if _is_review_due_target(concept_summary):
                review_due_targets.append(target_id)
                continue
            if _is_reinforcement_target(
                concept_summary,
                latest_outcomes.get(target_id),
                supported_subskill_gap,
            ):
                reinforce_targets.append(target_id)

        if weak_targets:
            target_id = self._first_target_by_priority(
                targets=weak_targets,
                concept_state=concept_state,
                metric="proficiency_estimate",
                reverse=False,
            )
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
                    "learner state shows confirmed weakness and the next step should "
                    "be bounded remediation."
                ).format(chosen_record["target_title"]),
                alternatives_summary=(
                    "Study actions remain available, but bounded remediation is ranked "
                    "higher than exploration after confirmed weak evidence."
                ),
            )

        if review_due_targets:
            target_id = self._first_target_by_priority(
                targets=review_due_targets,
                concept_state=concept_state,
                metric="review_due_risk",
                reverse=True,
            )
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
                    "review_due_risk_is_high",
                    "maintenance_review_priority",
                ],
                blocking_signals=blocking_signals,
                rationale=(
                    "Use Study / SpacedReview on '{0}' because learner state shows "
                    "maintenance review is currently due."
                ).format(chosen_record["target_title"]),
                alternatives_summary=(
                    "Exploration and practice remain available, but due maintenance is "
                    "currently ranked higher than progression."
                ),
            )

        if reinforce_targets:
            target_id = self._first_target_by_priority(
                targets=reinforce_targets,
                concept_state=concept_state,
                metric="proficiency_estimate",
                reverse=False,
            )
            chosen_record = self._first_matching_record(
                filtered_records,
                target_id=target_id,
                mode="Practice",
                session_intent="Reinforce",
            )
            supporting_signals = [
                "partially_stable_reviewed_outcome",
                "bounded_reinforcement_priority",
            ]
            if supported_subskill_gap:
                supporting_signals[0] = "supported_subskill_gap"
            return self._decision_payload(
                candidate_records=filtered_records,
                chosen_record=chosen_record,
                supporting_signals=supporting_signals,
                blocking_signals=blocking_signals,
                rationale=(
                    "Choose Practice / Reinforce on '{0}' because learner state shows "
                    "the concept is promising but still needs reinforcement."
                ).format(chosen_record["target_title"]),
                alternatives_summary=(
                    "Study actions remain available, but the current recommendation "
                    "prefers one tighter reinforcement pass first."
                ),
            )

        if mock_record is not None:
            return self._decision_payload(
                candidate_records=filtered_records,
                chosen_record=mock_record,
                supporting_signals=[
                    "mock_readiness_threshold_met",
                    "bounded_readiness_check_unlocked",
                ],
                blocking_signals=blocking_signals,
                rationale=(
                    "Use MockInterview / ReadinessCheck on '{0}' because readiness "
                    "signals are strong enough for a bounded mock pass."
                ).format(mock_record["target_title"]),
                alternatives_summary=(
                    "Study and practice remain available, but the current learner "
                    "trajectory is ready for one bounded readiness check."
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

    def _recommendation_context(
        self,
        user_id: str,
        candidate_records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        learner_profile = self._learner_projector.build_profile(self._runtime, user_id)
        concept_state = learner_profile.get("concept_state", {})
        if not isinstance(concept_state, dict):
            concept_state = {}
        subskill_state = learner_profile.get("subskill_state", {})
        if not isinstance(subskill_state, dict):
            subskill_state = {}
        trajectory_state = learner_profile.get("trajectory_state", {})
        if not isinstance(trajectory_state, dict):
            trajectory_state = {}

        latest_outcomes = {}
        for outcome in self._runtime.list_user_reviewed_outcomes(user_id):
            latest_outcomes[outcome["content_id"]] = outcome

        review_due_targets = sorted(
            [
                target_id
                for target_id, summary in concept_state.items()
                if isinstance(summary, dict) and _is_review_due_target(summary)
            ]
        )
        return {
            "concept_state": concept_state,
            "subskill_state": subskill_state,
            "trajectory_state": trajectory_state,
            "latest_outcomes": latest_outcomes,
            "review_due_targets": review_due_targets,
            "candidate_records": candidate_records,
            "scenario_bound_concept_ids": self._scenario_bound_concept_ids(),
            "recent_accepted_patterns": self._recent_accepted_patterns(user_id),
            "recent_mock_feedback": self._recent_mock_feedback(user_id),
            "policy_version": "bootstrap.recommendation.v1",
        }

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

    def _first_target_by_priority(
        self,
        targets: list[str],
        concept_state: dict[str, dict[str, Any]],
        metric: str,
        reverse: bool,
    ) -> str:
        ordered_targets = sorted(
            targets,
            key=lambda target_id: (
                concept_state.get(target_id, {}).get(metric, 0.0),
                target_id,
            ),
            reverse=reverse,
        )
        return ordered_targets[0]

    def _recent_accepted_patterns(self, user_id: str) -> list[tuple[str, str, str]]:
        accepted_records = [
            decision
            for decision in self._decisions.values()
            if decision["user_id"] == user_id and decision["accepted_at"] is not None
        ]
        accepted_records.sort(
            key=lambda decision: (
                _timestamp_sort_key(decision.get("accepted_at")),
                decision.get("decision_id", ""),
            )
        )
        return [_action_pattern(decision["chosen_action"]) for decision in accepted_records]

    def _require_decision(self, decision_id: str) -> dict[str, Any]:
        decision = self._decisions.get(decision_id)
        if decision is None:
            raise RecommendationDecisionNotFoundError(
                "unknown decision_id: {0}".format(decision_id)
            )
        return decision

    def _eligible_mock_record(
        self,
        filtered_records: list[dict[str, Any]],
        concept_state: dict[str, dict[str, Any]],
        trajectory_state: dict[str, Any],
    ) -> dict[str, Any] | None:
        mock_records = [
            record
            for record in filtered_records
            if (
                record["action"]["mode"] == "MockInterview"
                and record["action"]["session_intent"] == "ReadinessCheck"
            )
        ]
        if not mock_records:
            return None
        if _metric(trajectory_state, "mock_readiness_estimate") < 0.30:
            return None
        if _metric(trajectory_state, "mock_readiness_confidence") < 0.20:
            return None
        if _metric(trajectory_state, "recent_abandonment_signal") >= 0.25:
            return None
        if _average_hint_dependency_signal(concept_state) >= 0.20:
            return None
        return mock_records[0]

    def _scenario_bound_concept_ids(self) -> set[str]:
        bound_concept_ids: set[str] = set()
        for option in self._runtime.list_manual_launch_options(
            mode="MockInterview",
            session_intent="ReadinessCheck",
        ):
            option_bound_concepts = option.get("bound_concept_ids", [])
            if not isinstance(option_bound_concepts, list):
                continue
            for target_id in option_bound_concepts:
                if isinstance(target_id, str) and target_id:
                    bound_concept_ids.add(target_id)
        return bound_concept_ids

    def _recent_mock_feedback(self, user_id: str) -> dict[str, Any] | None:
        latest_session_id = None
        latest_session_at: tuple[int, str] | None = None
        latest_mock_session_id = None
        latest_mock_session_at: tuple[int, str] | None = None
        latest_mock_state = None

        for session in self._runtime.list_user_sessions(user_id):
            session_id = session.get("session_id")
            if not isinstance(session_id, str) or not session_id:
                continue
            session_at = _latest_event_timestamp(self._runtime.list_session_events(session_id))
            session_sort_key = _timestamp_sort_key(session_at)
            if latest_session_at is not None and session_sort_key <= latest_session_at:
                continue
            latest_session_at = session_sort_key
            latest_session_id = session_id

        for session in self._runtime.list_user_sessions(user_id):
            if (
                session.get("mode") != "MockInterview"
                or session.get("session_intent") != "ReadinessCheck"
            ):
                continue
            if session.get("state") not in {"review_presented", "completed", "abandoned"}:
                continue
            session_id = session.get("session_id")
            if not isinstance(session_id, str) or not session_id:
                continue
            session_at = _latest_event_timestamp(self._runtime.list_session_events(session_id))
            session_sort_key = _timestamp_sort_key(session_at)
            if latest_mock_session_at is not None and session_sort_key <= latest_mock_session_at:
                continue
            latest_mock_session_at = session_sort_key
            latest_mock_session_id = session_id
            latest_mock_state = session.get("state")

        if latest_mock_session_id is None or latest_mock_session_id != latest_session_id:
            return None
        if latest_mock_state == "abandoned":
            return {"signal": "recent_mock_abandonment"}
        return {"signal": "recent_mock_attempt"}

    def _next_decision_id(self) -> str:
        self._decision_counter += 1
        return "rec.{0:04d}".format(self._decision_counter)

    def _utc_now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _record_acceptance(self, decision: dict[str, Any], session_id: str) -> None:
        self._ensure_decision_not_accepted(decision)
        decision["accepted_at"] = self._utc_now_iso()
        decision["accepted_session_id"] = session_id

    def _ensure_decision_not_accepted(self, decision: dict[str, Any]) -> None:
        if decision.get("accepted_at") is not None:
            raise RecommendationDecisionLifecycleError("decision is already accepted")


def _is_confirmed_weak(concept_summary: dict[str, Any]) -> bool:
    proficiency = _metric(concept_summary, "proficiency_estimate")
    confidence = _metric(concept_summary, "confidence")
    review_due_risk = _metric(concept_summary, "review_due_risk")
    return confidence >= 0.25 and (
        proficiency <= 0.45 or (proficiency <= 0.55 and review_due_risk >= 0.75)
    )


def _is_review_due_target(concept_summary: dict[str, Any]) -> bool:
    review_due_risk = _metric(concept_summary, "review_due_risk")
    confidence = _metric(concept_summary, "confidence")
    return review_due_risk >= 0.55 and confidence >= 0.25


def _is_reinforcement_target(
    concept_summary: dict[str, Any],
    latest_outcome: dict[str, Any] | None,
    supported_subskill_gap: bool,
) -> bool:
    proficiency = _metric(concept_summary, "proficiency_estimate")
    confidence = _metric(concept_summary, "confidence")
    if proficiency >= 0.55 and supported_subskill_gap and confidence >= 0.25:
        return True
    if 0.45 <= proficiency < 0.78 and confidence >= 0.25:
        return True
    if not isinstance(latest_outcome, dict):
        return False
    weighted_score = latest_outcome.get("weighted_score", 0.0)
    missing_dimension_count = len(latest_outcome.get("missing_dimensions", []))
    return weighted_score < 0.8 or missing_dimension_count >= 1


def _supported_subskill_gap(subskill_state: dict[str, dict[str, Any]]) -> bool:
    for subskill_id in ("tradeoff_reasoning", "communication_clarity"):
        summary = subskill_state.get(subskill_id)
        if not isinstance(summary, dict):
            continue
        if (
            _metric(summary, "proficiency_estimate") <= 0.45
            and _metric(summary, "confidence") >= 0.25
        ):
            return True
    return False


def _metric(summary: dict[str, Any], key: str) -> float:
    value = summary.get(key, 0.0)
    if not isinstance(value, (int, float)):
        return 0.0
    return float(value)


def _timestamp_sort_key(value: Any) -> tuple[int, str]:
    if not isinstance(value, str) or not value:
        return (1, "")

    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return (1, "")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return (0, parsed.astimezone(timezone.utc).isoformat())


def _latest_event_timestamp(events: list[dict[str, Any]]) -> str | None:
    latest_value = None
    latest_key = None
    for event in events:
        if not isinstance(event, dict):
            continue
        occurred_at = event.get("occurred_at")
        sort_key = _timestamp_sort_key(occurred_at)
        if sort_key[0] != 0:
            continue
        if latest_key is None or sort_key > latest_key:
            latest_key = sort_key
            latest_value = occurred_at
    return latest_value


def _average_hint_dependency_signal(concept_state: dict[str, dict[str, Any]]) -> float:
    hint_signals = [
        _metric(summary, "hint_dependency_signal")
        for summary in concept_state.values()
        if isinstance(summary, dict)
    ]
    if not hint_signals:
        return 0.0
    return sum(hint_signals) / len(hint_signals)


def _scenario_family_from_content_id(content_id: str) -> str:
    tokens = content_id.split(".")
    if len(tokens) < 3 or tokens[0] != "scenario":
        raise RecommendationEngineError(
            "mock recommendation content_id is not a scenario id: {0}".format(content_id)
        )
    return tokens[1].replace("-", "_")
