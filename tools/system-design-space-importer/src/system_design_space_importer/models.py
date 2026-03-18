from system_design_space_importer.utils import sha256_text


def provenance_ref(document_id, fragment_ids, extraction_mode, confidence, notes=None):
    payload = {
        "document_id": document_id,
        "fragment_ids": fragment_ids,
        "extraction_mode": extraction_mode,
        "confidence": confidence,
    }
    if notes:
        payload["notes"] = notes
    return payload


def draft_field(value, provenance, review_required):
    return {
        "value": value,
        "provenance": provenance,
        "review_required": review_required,
    }


def source_document(
    document_id,
    source_name,
    source_url,
    fetched_at,
    fetch_mode,
    http_status,
    content_type,
    source_hash,
    raw_html_path,
    normalized_text_path,
    parser_version,
    canonical_url=None,
    discovered_from=None,
    charset=None,
    locale=None,
):
    payload = {
        "document_id": document_id,
        "source_name": source_name,
        "source_url": source_url,
        "fetched_at": fetched_at,
        "fetch_mode": fetch_mode,
        "http_status": http_status,
        "content_type": content_type,
        "source_hash": source_hash,
        "raw_html_path": raw_html_path,
        "normalized_text_path": normalized_text_path,
        "parser_version": parser_version,
    }
    optional = {
        "canonical_url": canonical_url,
        "discovered_from": discovered_from,
        "charset": charset,
        "locale": locale,
    }
    payload.update({key: value for key, value in optional.items() if value is not None})
    return payload


def parsed_source_fragment(
    fragment_id,
    document_id,
    kind,
    heading_path,
    order,
    text,
    links,
    source_selector=None,
    dom_path=None,
):
    payload = {
        "fragment_id": fragment_id,
        "document_id": document_id,
        "kind": kind,
        "heading_path": heading_path,
        "order": order,
        "text": text,
        "links": links,
        "fragment_hash": sha256_text(text),
    }
    if source_selector is not None:
        payload["source_selector"] = source_selector
    if dom_path is not None:
        payload["dom_path"] = dom_path
    return payload
