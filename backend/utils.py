import re
from typing import Any
from bson import ObjectId
from fastapi import HTTPException

from constants import DEFAULT_PROFILE

def _clean_json_payload(raw_text: str) -> str:
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", cleaned)
    cleaned = re.sub(r"\n?```$", "", cleaned)
    cleaned = cleaned.strip()
    # Remove trailing commas inside arrays and objects to prevent JSON decode errors
    cleaned = re.sub(r",\s*\]", "]", cleaned)
    cleaned = re.sub(r",\s*\}", "}", cleaned)
    return cleaned


def _safe_profile(payload: dict[str, Any] | None) -> dict[str, Any]:
    profile = {**DEFAULT_PROFILE}
    if payload:
        profile.update(payload)
    profile["skills"] = sorted({str(s).strip().lower() for s in profile.get("skills", []) if str(s).strip()})
    profile["job_roles"] = [str(r).strip() for r in profile.get("job_roles", []) if str(r).strip()]
    return profile

def _error(status: int, detail: str, code: str = "error") -> HTTPException:
    return HTTPException(status_code=status, detail={"detail": detail, "code": code})

def _get_object_id(id: str) -> ObjectId:
    try:
        return ObjectId(id)
    except Exception:
        raise _error(400, "Invalid ID format.", "invalid_id")

def _serialize(doc: dict[str, Any]) -> dict[str, Any]:
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    return doc
