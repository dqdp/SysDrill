import os
from collections.abc import Mapping
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, NonNegativeInt, StrictStr

from sysdrill_backend.content_bundle_reader import load_topic_catalog
from sysdrill_backend.content_catalog_api import build_topic_detail, build_topic_summary
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


def create_app(
    content_export_root: str | Path | None = None,
    allow_draft_bundles: bool = False,
) -> FastAPI:
    catalog = {}
    runtime = None
    if content_export_root is not None:
        catalog = load_topic_catalog(
            export_root=content_export_root,
            allow_draft_bundles=allow_draft_bundles,
        )
        runtime = SessionRuntime(catalog)

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
    raise RuntimeError(
        "environment variable {0} must be a boolean value".format(env_name)
    )


def create_app_from_env(env: Mapping[str, str] | None = None) -> FastAPI:
    resolved_env = os.environ if env is None else env
    return create_app(
        content_export_root=resolved_env.get(_CONTENT_EXPORT_ROOT_ENV),
        allow_draft_bundles=_parse_bool_env(
            resolved_env.get(_ALLOW_DRAFT_BUNDLES_ENV),
            _ALLOW_DRAFT_BUNDLES_ENV,
        ),
    )


app = create_app_from_env()
