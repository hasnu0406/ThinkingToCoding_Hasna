import logging
import re
from typing import Any
from bson import ObjectId
from fastapi import HTTPException

from constants import DEFAULT_PROFILE

# ── Structured Logging Configuration ──
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
)
logger = logging.getLogger("thinking_to_coding")

def _clean_json_payload(raw_text: str) -> str:
    cleaned = raw_text.strip()
    # Remove <think> blocks from reasoning models if present
    cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL).strip()
    
    # Extract from markdown block if present anywhere in the text
    json_match = re.search(r"```(?:json)?(.*?)```", cleaned, flags=re.DOTALL)
    if json_match:
        cleaned = json_match.group(1).strip()
    else:
        # Fallback: extract substring from first { or [ to last } or ]
        start_idx = cleaned.find("{")
        start_arr = cleaned.find("[")
        if start_idx != -1 and start_arr != -1:
            start = min(start_idx, start_arr)
        elif start_idx != -1:
            start = start_idx
        else:
            start = start_arr
            
        if start != -1:
            end_char = "]" if cleaned[start] == "[" else "}"
            end = cleaned.rfind(end_char)
            if end != -1 and end >= start:
                cleaned = cleaned[start:end+1]
                
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
