import copy
import threading
from datetime import datetime, timezone
from typing import Any

from sysdrill_backend.executable_learning_unit_materializer import (
    materialize_executable_learning_units,
    supported_materialization_pairs,
)
from sysdrill_backend.rule_first_evaluator import (
    RuleFirstEvaluationError,
    evaluate_concept_recall,
)


class SessionRuntimeError(ValueError):
    pass


class SessionNotFoundError(SessionRuntimeError):
    pass


class UnitNotFoundError(SessionRuntimeError):
    pass


class UnitModeIntentMismatchError(SessionRuntimeError):
    pass


class SessionRuntimeInvalidStateError(SessionRuntimeError):
    pass


def _is_draft_field(payload: Any) -> bool:
    return (
        isinstance(payload, dict)
        and "value" in payload
        and "provenance" in payload
        and "review_required" in payload
    )


def _unwrap_payload(payload: Any) -> Any:
    if _is_draft_field(payload):
        return _unwrap_payload(payload["value"])
    if isinstance(payload, dict):
        return {key: _unwrap_payload(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [_unwrap_payload(value) for value in payload]
    return payload


class SessionRuntime:
    def __init__(
        self,
        catalog: dict[str, dict[str, Any]],
        evaluator: Any | None = None,
    ):
        self._catalog = catalog
        self._sessions: dict[str, dict[str, Any]] = {}
        self._events: list[dict[str, Any]] = []
        self._session_counter = 0
        self._event_counter = 0
        self._state_lock = threading.RLock()
        self._units_by_mode_intent: dict[tuple[str, str], dict[str, dict[str, Any]]] = {}
        self._unit_owner_by_id: dict[str, tuple[str, str]] = {}
        self._content_metadata_by_id = self._build_content_metadata_by_id(catalog)
        self._evaluator = evaluate_concept_recall if evaluator is None else evaluator

        with self._state_lock:
            for mode, session_intent in supported_materialization_pairs():
                units = materialize_executable_learning_units(
                    catalog,
                    mode=mode,
                    session_intent=session_intent,
                )
                indexed_units = {unit["id"]: copy.deepcopy(unit) for unit in units}
                self._units_by_mode_intent[(mode, session_intent)] = indexed_units
                for unit_id in indexed_units:
                    self._unit_owner_by_id[unit_id] = (mode, session_intent)

    def start_manual_session(
        self,
        user_id: str,
        mode: str,
        session_intent: str,
        unit_id: str,
        source: str = "web",
    ) -> dict[str, Any]:
        with self._state_lock:
            unit = self._resolve_unit(mode, session_intent, unit_id)
            return self._start_session(
                user_id=user_id,
                mode=mode,
                session_intent=session_intent,
                unit=unit,
                source=source,
            )

    def start_session_from_recommendation(
        self,
        user_id: str,
        decision_id: str,
        action: dict[str, Any],
        source: str = "web",
    ) -> dict[str, Any]:
        with self._state_lock:
            unit = self._resolve_recommendation_action(action)
            return self._start_session(
                user_id=user_id,
                mode=action["mode"],
                session_intent=action["session_intent"],
                unit=unit,
                source=source,
                recommendation_context={
                    "decision_id": decision_id,
                    "action": copy.deepcopy(action),
                },
            )

    def _start_session(
        self,
        user_id: str,
        mode: str,
        session_intent: str,
        unit: dict[str, Any],
        source: str,
        recommendation_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        unit_id = unit["id"]
        session_id = self._next_session_id()
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "mode": mode,
            "session_intent": session_intent,
            "strictness_profile": self._strictness_profile(mode),
            "source": source,
            "trace_id": "trace.{0}".format(session_id),
            "state": "planned",
            "planned_unit_ids": [unit_id],
            "current_unit_id": unit_id,
            "current_unit": copy.deepcopy(unit),
            "event_ids": [],
            "last_evaluation_request": None,
            "last_evaluation_result": None,
            "last_review_report": None,
            "recommendation_decision_id": (
                recommendation_context["decision_id"] if recommendation_context else None
            ),
        }
        self._sessions[session_id] = session

        if recommendation_context is not None:
            action = recommendation_context["action"]
            self._emit_event(
                session,
                "recommendation_accepted",
                {
                    "decision_id": recommendation_context["decision_id"],
                    "recommended_mode": action["mode"],
                    "recommended_intent": action["session_intent"],
                    "target_type": action["target_type"],
                    "target_id": action["target_id"],
                    "difficulty_profile": action["difficulty_profile"],
                    "strictness_profile": action["strictness_profile"],
                    "session_size": action["session_size"],
                    "delivery_profile": action["delivery_profile"],
                },
            )

        self._emit_event(
            session,
            "session_planned",
            {
                "planned_unit_ids": [unit_id],
                "current_unit_id": unit_id,
            },
        )
        session["state"] = "started"
        self._emit_event(
            session,
            "session_started",
            {
                "current_unit_id": unit_id,
                "strictness_profile": session["strictness_profile"],
            },
        )
        session["state"] = "unit_presented"
        self._emit_event(
            session,
            "unit_presented",
            {
                "unit_id": unit_id,
                "visible_prompt": unit["visible_prompt"],
            },
        )
        session["state"] = "awaiting_answer"

        return self.get_session(session_id)

    def get_session(self, session_id: str) -> dict[str, Any]:
        with self._state_lock:
            session = self._require_session(session_id)
            return self._snapshot_session(session)

    def list_session_events(self, session_id: str) -> list[dict[str, Any]]:
        with self._state_lock:
            self._require_session(session_id)
            return [
                copy.deepcopy(event) for event in self._events if event["session_id"] == session_id
            ]

    def list_user_sessions(self, user_id: str) -> list[dict[str, Any]]:
        with self._state_lock:
            sessions = []
            for session in self._sessions.values():
                if session["user_id"] != user_id:
                    continue
                # Projection must consume runtime-owned read seams, not mutable internals.
                snapshot = self._snapshot_session(session)
                snapshot["source"] = session["source"]
                sessions.append(snapshot)

            sessions.sort(key=lambda payload: payload["session_id"])
            return copy.deepcopy(sessions)

    def list_manual_launch_options(
        self,
        mode: str,
        session_intent: str,
    ) -> list[dict[str, Any]]:
        with self._state_lock:
            units = self._units_by_mode_intent.get((mode, session_intent))
            if units is None:
                raise UnitModeIntentMismatchError(
                    "unsupported runtime mode/session_intent combination: {0}/{1}".format(
                        mode,
                        session_intent,
                    )
                )

            launch_options = []
            for unit in units.values():
                content_ids = unit.get("source_content_ids", [])
                content_id = content_ids[0] if content_ids else None
                content_metadata = self._content_metadata_by_id.get(content_id, {})
                launch_options.append(
                    {
                        "unit_id": unit["id"],
                        "content_id": content_id,
                        "topic_slug": content_metadata.get("topic_slug"),
                        "display_title": content_metadata.get("display_title"),
                        "visible_prompt": unit["visible_prompt"],
                        "effective_difficulty": unit["effective_difficulty"],
                    }
                )

            return copy.deepcopy(launch_options)

    def list_user_reviewed_outcomes(self, user_id: str) -> list[dict[str, Any]]:
        with self._state_lock:
            outcomes = []
            for session in self._sessions.values():
                if session["user_id"] != user_id:
                    continue
                evaluation_result = session.get("last_evaluation_result")
                if not isinstance(evaluation_result, dict):
                    continue
                content_ids = session["current_unit"].get("source_content_ids", [])
                content_id = content_ids[0] if content_ids else None
                if not isinstance(content_id, str) or not content_id:
                    continue
                outcomes.append(
                    {
                        "session_id": session["session_id"],
                        "content_id": content_id,
                        "mode": session["mode"],
                        "session_intent": session["session_intent"],
                        "weighted_score": evaluation_result["weighted_score"],
                        "missing_dimensions": list(evaluation_result.get("missing_dimensions", [])),
                        "recommendation_decision_id": session.get("recommendation_decision_id"),
                    }
                )

            outcomes.sort(key=lambda outcome: outcome["session_id"])
            return copy.deepcopy(outcomes)

    def submit_answer(
        self,
        session_id: str,
        transcript: str,
        response_modality: str,
        submission_kind: str,
        response_latency_ms: int | None = None,
    ) -> dict[str, Any]:
        with self._state_lock:
            session = self._require_session(session_id)
            if session["state"] != "awaiting_answer":
                raise SessionRuntimeInvalidStateError(
                    "cannot submit answer when session state is '{0}'".format(session["state"])
                )
            self._validate_submission_kind(session, submission_kind)

            session["state"] = "submitted"
            self._emit_event(
                session,
                "answer_submitted",
                {
                    "response_modality": response_modality,
                    "char_count": len(transcript),
                    "response_latency_ms": response_latency_ms,
                    "submission_kind": submission_kind,
                    "used_prior_hints": False,
                    "follow_up_context": False,
                },
            )

            evaluation_request = {
                "session_id": session_id,
                "session_mode": session["mode"],
                "session_intent": session["session_intent"],
                "executable_unit_id": session["current_unit_id"],
                "unit_family": self._unit_family(session["current_unit"]),
                "binding_id": session["current_unit"]["evaluation_binding_id"],
                "transcript_text": transcript,
                "hint_usage_summary": {
                    "hint_count": 0,
                    "used_prior_hints": False,
                },
                "answer_reveal_flag": False,
                "timing_summary": {
                    "response_latency_ms": response_latency_ms,
                },
                "completion_status": "submitted",
                "strictness_profile": session["strictness_profile"],
            }
            session["last_evaluation_request"] = copy.deepcopy(evaluation_request)
            session["state"] = "evaluation_pending"

            return {
                "session": self.get_session(session_id),
                "submitted_unit_id": session["current_unit_id"],
                "evaluation_request": evaluation_request,
            }

    def evaluate_pending_session(self, session_id: str) -> dict[str, Any]:
        with self._state_lock:
            session = self._require_session(session_id)
            if session["state"] != "evaluation_pending":
                raise SessionRuntimeInvalidStateError(
                    "cannot attach evaluation when session state is '{0}'".format(session["state"])
                )
            evaluation_request = session.get("last_evaluation_request")
            if not isinstance(evaluation_request, dict):
                raise SessionRuntimeError("no evaluation_request is available for this session")

            try:
                evaluation_bundle = self._evaluator(copy.deepcopy(evaluation_request))
            except RuleFirstEvaluationError as exc:
                raise SessionRuntimeError(str(exc)) from exc

            evaluation_result = evaluation_bundle.get("evaluation_result")
            review_report = evaluation_bundle.get("review_report")
            if not isinstance(evaluation_result, dict) or not isinstance(review_report, dict):
                raise SessionRuntimeError("evaluator returned an invalid evaluation bundle")

            session["last_evaluation_result"] = copy.deepcopy(evaluation_result)
            session["state"] = "evaluated"
            self._emit_event(
                session,
                "evaluation_attached",
                {
                    "evaluation_id": evaluation_result["evaluation_id"],
                    "weighted_score": evaluation_result["weighted_score"],
                    "overall_confidence": evaluation_result["overall_confidence"],
                    "missing_dimensions": list(evaluation_result["missing_dimensions"]),
                },
            )

            session["last_review_report"] = copy.deepcopy(review_report)
            session["state"] = "review_presented"
            self._emit_event(
                session,
                "review_presented",
                {
                    "evaluation_id": evaluation_result["evaluation_id"],
                    "strength_count": len(review_report.get("strengths", [])),
                    "missed_dimension_count": len(review_report.get("missed_dimensions", [])),
                },
            )
            if isinstance(session.get("recommendation_decision_id"), str):
                self._emit_event(
                    session,
                    "recommendation_completed",
                    {
                        "decision_id": session["recommendation_decision_id"],
                        "completion_state": "review_presented",
                    },
                )

            return {
                "session": self.get_session(session_id),
                "evaluation_result": copy.deepcopy(evaluation_result),
                "review_report": copy.deepcopy(review_report),
            }

    def get_review(self, session_id: str) -> dict[str, Any]:
        with self._state_lock:
            session = self._require_session(session_id)
            evaluation_result = session.get("last_evaluation_result")
            review_report = session.get("last_review_report")
            if not isinstance(evaluation_result, dict) or not isinstance(review_report, dict):
                raise SessionRuntimeInvalidStateError(
                    "review is not available when session state is '{0}'".format(session["state"])
                )
            return {
                "session": self.get_session(session_id),
                "evaluation_result": copy.deepcopy(evaluation_result),
                "review_report": copy.deepcopy(review_report),
            }

    def _resolve_unit(self, mode: str, session_intent: str, unit_id: str) -> dict[str, Any]:
        units = self._units_by_mode_intent.get((mode, session_intent))
        if units is None:
            raise UnitModeIntentMismatchError(
                "unsupported runtime mode/session_intent combination: {0}/{1}".format(
                    mode,
                    session_intent,
                )
            )

        unit = units.get(unit_id)
        if unit is not None:
            return copy.deepcopy(unit)

        owning_pair = self._unit_owner_by_id.get(unit_id)
        if owning_pair is not None:
            raise UnitModeIntentMismatchError(
                "unit_id '{0}' is not available for mode '{1}' and session_intent '{2}'".format(
                    unit_id,
                    mode,
                    session_intent,
                )
            )

        raise UnitNotFoundError("unknown unit_id: {0}".format(unit_id))

    def _resolve_recommendation_action(self, action: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(action, dict):
            raise SessionRuntimeError("recommendation action must be an object")

        target_type = action.get("target_type")
        if target_type != "concept":
            raise SessionRuntimeError(
                "unsupported recommendation action target_type: {0}".format(target_type)
            )

        mode = action.get("mode")
        session_intent = action.get("session_intent")
        target_id = action.get("target_id")
        difficulty_profile = action.get("difficulty_profile")
        strictness_profile = action.get("strictness_profile")
        session_size = action.get("session_size")
        delivery_profile = action.get("delivery_profile")

        if not all(
            isinstance(value, str) and value
            for value in (
                mode,
                session_intent,
                target_id,
                difficulty_profile,
                strictness_profile,
                session_size,
                delivery_profile,
            )
        ):
            raise SessionRuntimeError("recommendation action contains invalid fields")

        units = self._units_by_mode_intent.get((mode, session_intent))
        if units is None:
            raise UnitModeIntentMismatchError(
                "unsupported runtime mode/session_intent combination: {0}/{1}".format(
                    mode,
                    session_intent,
                )
            )

        matching_units = [
            unit for unit in units.values() if target_id in unit.get("source_content_ids", [])
        ]
        if not matching_units:
            raise SessionRuntimeError(
                "recommendation action target_id '{0}' is not currently resolvable".format(
                    target_id
                )
            )
        if len(matching_units) > 1:
            raise SessionRuntimeError(
                "recommendation action target_id '{0}' resolves ambiguously".format(target_id)
            )

        unit = matching_units[0]
        if difficulty_profile != unit.get("effective_difficulty"):
            raise SessionRuntimeError(
                (
                    "recommendation action difficulty_profile '{0}' does not match resolved unit"
                ).format(difficulty_profile)
            )
        expected_strictness_profile = self._strictness_profile(mode)
        if strictness_profile != expected_strictness_profile:
            raise SessionRuntimeError(
                (
                    "recommendation action strictness_profile '{0}' does not match resolved unit"
                ).format(strictness_profile)
            )
        if session_size != "single_unit":
            raise SessionRuntimeError(
                "recommendation action session_size '{0}' is unsupported".format(session_size)
            )
        if delivery_profile != "text_first":
            raise SessionRuntimeError(
                "recommendation action delivery_profile '{0}' is unsupported".format(
                    delivery_profile
                )
            )

        return copy.deepcopy(unit)

    def _require_session(self, session_id: str) -> dict[str, Any]:
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError("unknown session_id: {0}".format(session_id))
        return session

    def _validate_submission_kind(self, session: dict[str, Any], submission_kind: str) -> None:
        completion_rules = session["current_unit"].get("completion_rules")
        if not isinstance(completion_rules, dict):
            raise SessionRuntimeError("current unit completion_rules are missing")

        expected_submission_kind = completion_rules.get("submission_kind")
        if not isinstance(expected_submission_kind, str) or not expected_submission_kind:
            raise SessionRuntimeError("current unit completion_rules.submission_kind is invalid")
        if submission_kind != expected_submission_kind:
            raise SessionRuntimeError(
                "submission_kind '{0}' does not match current unit completion rule '{1}'".format(
                    submission_kind,
                    expected_submission_kind,
                )
            )

    def _emit_event(
        self,
        session: dict[str, Any],
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        event_id = self._next_event_id()
        content_ids = session["current_unit"].get("source_content_ids", [])
        event = {
            "event_id": event_id,
            "event_type": event_type,
            "user_id": session["user_id"],
            "session_id": session["session_id"],
            "mode": session["mode"],
            "session_intent": session["session_intent"],
            "content_id": content_ids[0] if content_ids else None,
            "occurred_at": self._utc_now_iso(),
            "payload": payload,
            "source": session["source"],
            "trace_id": session["trace_id"],
        }
        self._events.append(event)
        session["event_ids"].append(event_id)

    def _snapshot_session(self, session: dict[str, Any]) -> dict[str, Any]:
        return {
            "session_id": session["session_id"],
            "user_id": session["user_id"],
            "mode": session["mode"],
            "session_intent": session["session_intent"],
            "strictness_profile": session["strictness_profile"],
            "state": session["state"],
            "planned_unit_ids": list(session["planned_unit_ids"]),
            "current_unit": copy.deepcopy(session["current_unit"]),
            "event_ids": list(session["event_ids"]),
            "last_evaluation_result": copy.deepcopy(session["last_evaluation_result"]),
            "last_review_report": copy.deepcopy(session["last_review_report"]),
            "recommendation_decision_id": session.get("recommendation_decision_id"),
        }

    def _unit_family(self, unit: dict[str, Any]) -> str:
        unit_id = unit.get("id")
        if isinstance(unit_id, str) and unit_id.startswith("elu.concept_recall."):
            return "concept_recall"
        raise SessionRuntimeError("unable to derive unit_family for unit_id: {0}".format(unit_id))

    def _next_session_id(self) -> str:
        self._session_counter += 1
        return "session.{0:04d}".format(self._session_counter)

    def _next_event_id(self) -> str:
        self._event_counter += 1
        return "event.{0:04d}".format(self._event_counter)

    def _strictness_profile(self, mode: str) -> str:
        if mode == "Study":
            return "supportive"
        if mode == "Practice":
            return "standard"
        return "strict"

    def _utc_now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _build_content_metadata_by_id(
        self,
        catalog: dict[str, dict[str, Any]],
    ) -> dict[str, dict[str, str]]:
        content_metadata_by_id = {}
        for topic_slug, bundle in catalog.items():
            topic_package = bundle.get("topic_package", {})
            canonical_content = topic_package.get("canonical_content", {})
            if not isinstance(canonical_content, dict):
                canonical_content = {}
            concepts = canonical_content.get("concepts", [])
            if not isinstance(concepts, list):
                continue

            for concept in concepts:
                if not isinstance(concept, dict):
                    continue
                content_id = _unwrap_payload(concept.get("id"))
                display_title = _unwrap_payload(concept.get("title"))
                if isinstance(content_id, str) and content_id:
                    content_metadata_by_id[content_id] = {
                        "topic_slug": topic_slug,
                        "display_title": (
                            display_title if isinstance(display_title, str) else topic_slug
                        ),
                    }

        return content_metadata_by_id
