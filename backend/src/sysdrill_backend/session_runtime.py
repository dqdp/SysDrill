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
            }
            self._sessions[session_id] = session

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
                    "review is not available when session state is '{0}'".format(
                        session["state"]
                    )
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
