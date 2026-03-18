from pathlib import Path

from fastapi import FastAPI, HTTPException

from sysdrill_backend.content_bundle_reader import load_topic_catalog
from sysdrill_backend.content_catalog_api import build_topic_detail, build_topic_summary


def create_app(
    content_export_root: str | Path | None = None,
    allow_draft_bundles: bool = False,
) -> FastAPI:
    catalog = {}
    if content_export_root is not None:
        catalog = load_topic_catalog(
            export_root=content_export_root,
            allow_draft_bundles=allow_draft_bundles,
        )

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

    return app


app = create_app()
