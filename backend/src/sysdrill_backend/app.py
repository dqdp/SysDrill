import os
from collections.abc import Mapping
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, NonNegativeInt, StrictStr

from sysdrill_backend.content_bundle_reader import load_topic_catalog
from sysdrill_backend.content_catalog_api import (
    build_topic_detail,
    build_topic_summary,
)
from sysdrill_backend.recommendation_engine import (
    NoRecommendationCandidatesError,
    RecommendationDecisionNotFoundError,
    RecommendationEngine,
)
from sysdrill_backend.session_runtime import (
    SessionNotFoundError,
    SessionRuntime,
    SessionRuntimeError,
    SessionRuntimeInvalidStateError,
    UnitModeIntentMismatchError,
    UnitNotFoundError,
)

_CONTENT_EXPORT_ROOT_ENV = "SYSDRILL_CONTENT_EXPORT_ROOT"
_ALLOW_DRAFT_BUNDLES_ENV = "SYSDRILL_ALLOW_DRAFT_BUNDLES"


class ManualStartSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: StrictStr
    mode: StrictStr
    session_intent: StrictStr
    unit_id: StrictStr
    source: StrictStr = "web"


class SubmitRuntimeAnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transcript: StrictStr
    response_modality: StrictStr
    submission_kind: StrictStr
    response_latency_ms: NonNegativeInt | None = None


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: StrictStr


class RecommendationActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: StrictStr
    session_intent: StrictStr
    target_type: StrictStr
    target_id: StrictStr
    difficulty_profile: StrictStr
    strictness_profile: StrictStr
    session_size: StrictStr
    delivery_profile: StrictStr
    rationale: StrictStr


class StartFromRecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: StrictStr
    decision_id: StrictStr
    action: RecommendationActionRequest
    source: StrictStr = "web"


def create_app(
    content_export_root: str | Path | None = None,
    allow_draft_bundles: bool = False,
) -> FastAPI:
    catalog = {}
    runtime = None
    recommendation_engine = None
    if content_export_root is not None:
        catalog = load_topic_catalog(
            export_root=content_export_root,
            allow_draft_bundles=allow_draft_bundles,
        )
        runtime = SessionRuntime(catalog)
        recommendation_engine = RecommendationEngine(runtime)

    app = FastAPI(title="System Design Trainer API")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/content/topics")
    def list_topics() -> list[dict]:
        return [build_topic_summary(catalog[topic_slug]) for topic_slug in sorted(catalog)]

    @app.get("/content/topics/{topic_slug}")
    def get_topic(topic_slug: str) -> dict:
        bundle = catalog.get(topic_slug)
        if bundle is None:
            raise HTTPException(status_code=404, detail="topic not found")
        return build_topic_detail(bundle)

    @app.post("/runtime/sessions/manual-start")
    def manual_start_session(request: ManualStartSessionRequest) -> dict:
        if runtime is None:
            raise HTTPException(status_code=503, detail="runtime content is not configured")
        try:
            return runtime.start_manual_session(
                user_id=request.user_id,
                mode=request.mode,
                session_intent=request.session_intent,
                unit_id=request.unit_id,
                source=request.source,
            )
        except UnitNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except UnitModeIntentMismatchError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except SessionRuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/runtime/manual-launch-options")
    def get_manual_launch_options(mode: str, session_intent: str) -> dict:
        if runtime is None:
            raise HTTPException(status_code=503, detail="runtime content is not configured")
        try:
            return {
                "mode": mode,
                "session_intent": session_intent,
                "items": runtime.list_manual_launch_options(
                    mode=mode,
                    session_intent=session_intent,
                ),
            }
        except UnitModeIntentMismatchError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except SessionRuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/recommendations/next")
    def get_next_recommendation(request: RecommendationRequest) -> dict:
        if runtime is None or recommendation_engine is None:
            raise HTTPException(status_code=503, detail="runtime content is not configured")
        try:
            return recommendation_engine.next_recommendation(user_id=request.user_id)
        except NoRecommendationCandidatesError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/runtime/sessions/start-from-recommendation")
    def start_session_from_recommendation(request: StartFromRecommendationRequest) -> dict:
        if runtime is None or recommendation_engine is None:
            raise HTTPException(status_code=503, detail="runtime content is not configured")
        try:
            decision = recommendation_engine.get_decision(request.decision_id)
        except RecommendationDecisionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

        action = request.action.model_dump()
        if decision["user_id"] != request.user_id:
            raise HTTPException(status_code=400, detail="decision_id does not belong to user_id")
        if action != decision["chosen_action"]:
            raise HTTPException(
                status_code=400,
                detail="request action does not match stored chosen_action",
            )

        try:
            session = runtime.start_session_from_recommendation(
                user_id=request.user_id,
                decision_id=request.decision_id,
                action=action,
                source=request.source,
            )
            recommendation_engine.mark_accepted(request.decision_id, session["session_id"])
            return session
        except UnitNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except UnitModeIntentMismatchError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except SessionRuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/runtime/sessions/{session_id}")
    def get_runtime_session(session_id: str) -> dict:
        if runtime is None:
            raise HTTPException(status_code=503, detail="runtime content is not configured")
        try:
            return runtime.get_session(session_id)
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/runtime/sessions/{session_id}/answer")
    def submit_runtime_answer(session_id: str, request: SubmitRuntimeAnswerRequest) -> dict:
        if runtime is None:
            raise HTTPException(status_code=503, detail="runtime content is not configured")
        try:
            result = runtime.submit_answer(
                session_id=session_id,
                transcript=request.transcript,
                response_modality=request.response_modality,
                submission_kind=request.submission_kind,
                response_latency_ms=request.response_latency_ms,
            )
            return {
                "session_id": result["session"]["session_id"],
                "state": result["session"]["state"],
                "submitted_unit_id": result["submitted_unit_id"],
                "evaluation_request": result["evaluation_request"],
            }
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except SessionRuntimeInvalidStateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except SessionRuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/runtime/sessions/{session_id}/evaluate")
    def evaluate_runtime_session(session_id: str) -> dict:
        if runtime is None:
            raise HTTPException(status_code=503, detail="runtime content is not configured")
        try:
            result = runtime.evaluate_pending_session(session_id)
            if recommendation_engine is not None:
                decision_id = result["session"].get("recommendation_decision_id")
                if isinstance(decision_id, str) and decision_id:
                    recommendation_engine.mark_completed(decision_id, session_id)
            return {
                "session_id": result["session"]["session_id"],
                "state": result["session"]["state"],
                "evaluation_result": result["evaluation_result"],
                "review_report": result["review_report"],
            }
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except SessionRuntimeInvalidStateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except SessionRuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/runtime/sessions/{session_id}/review")
    def get_runtime_review(session_id: str) -> dict:
        if runtime is None:
            raise HTTPException(status_code=503, detail="runtime content is not configured")
        try:
            result = runtime.get_review(session_id)
            return {
                "session_id": result["session"]["session_id"],
                "state": result["session"]["state"],
                "evaluation_result": result["evaluation_result"],
                "review_report": result["review_report"],
            }
        except SessionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except SessionRuntimeInvalidStateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except SessionRuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app


def _parse_bool_env(raw_value: str | None, env_name: str) -> bool:
    if raw_value is None:
        return False

    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off", ""}:
        return False
    raise RuntimeError("environment variable {0} must be a boolean value".format(env_name))


def create_app_from_env(env: Mapping[str, str] | None = None) -> FastAPI:
    resolved_env = os.environ if env is None else env
    content_export_root = resolved_env.get(_CONTENT_EXPORT_ROOT_ENV)
    if content_export_root is None or not content_export_root.strip():
        return create_app()

    return create_app(
        content_export_root=content_export_root,
        allow_draft_bundles=_parse_bool_env(
            resolved_env.get(_ALLOW_DRAFT_BUNDLES_ENV),
            _ALLOW_DRAFT_BUNDLES_ENV,
        ),
    )


app = create_app_from_env()
