import re
import io
import hashlib
import zipfile
from typing import Any

# pyrefly: ignore [missing-import]
from docx import Document
# pyrefly: ignore [missing-import]
from pypdf import PdfReader
# pyrefly: ignore [missing-import]
from fastapi import HTTPException

from constants import SEARCHABLE_SKILLS, SKILL_GROUPS
from utils import _error
from database import resume_collection


def parse_query(query: str) -> dict[str, Any]:
    lowered = query.lower()
    found_skills = [s for s in SEARCHABLE_SKILLS if s in lowered]
    experience = None
    match = re.search(r"(\d+)\s*year", lowered)
    if match:
        experience = int(match.group(1))
    return {"skills": found_skills, "experience": experience}


def extract_experience_years(experience_value: str) -> int:
    if not experience_value or experience_value == "fresher":
        return 0
    match = re.search(r"(\d+)", experience_value)
    return int(match.group(1)) if match else 0


def rank_candidates(candidates: list[dict[str, Any]], filters: dict[str, Any]) -> list[dict[str, Any]]:
    """Enhanced ranking algorithm with multi-factor scoring."""
    from ai import get_highly_related_roles
    
    ranked = []
    
    role_keyword = filters.get("role_keyword")
    highly_related_roles = []
    if role_keyword:
        all_roles = tuple(sorted(list(set(c.get("role", "").strip() for c in candidates if c.get("role", "").strip()))))
        highly_related_roles = [r.lower().strip() for r in get_highly_related_roles(role_keyword, all_roles)]
    
    for candidate in candidates:
        score = 0
        if filters.get("list_all_candidates"):
            score += 1
        
        # Name matching (Hard Filter)
        candidate_name = filters.get("candidate_name")
        if candidate_name:
            if candidate_name.lower() not in candidate.get("name", "").lower():
                candidate["rank_score"] = 0
                ranked.append(candidate)
                continue
            else:
                score += 100  # Massive boost for matching name
        
        # Skill matching (highest priority)
        candidate_skills = set(s.lower().strip() for s in candidate.get("skills", []))
        filter_skills = set(filters.get("skills", []))
        
        if filter_skills:
            skill_matches = len(filter_skills & candidate_skills)
            score += skill_matches * 5  # 5 points per skill match
            
            # Bonus for having additional highly related skills
            extra_skills = candidate_skills - filter_skills
            related_extra_skills = 0
            for extra in extra_skills:
                is_related = False
                for f_skill in filter_skills:
                    for group in SKILL_GROUPS:
                        if extra in group and f_skill in group:
                            is_related = True
                            break
                    if is_related:
                        break
                if is_related:
                    related_extra_skills += 1
            
            score += min(related_extra_skills, 3)
        
        # Experience matching
        candidate_exp = extract_experience_years(candidate.get("experience", "0"))
        min_exp = filters.get("min_experience_years")
        max_exp = filters.get("max_experience_years")
        
        if min_exp is not None:
            if candidate_exp >= min_exp:
                score += 3  # Meets minimum experience
                # Extra bonus for exceeding minimum
                score += min((candidate_exp - min_exp) // 2, 2)
            else:
                # Hard penalty for not meeting minimum experience
                score = 0
                candidate["rank_score"] = score
                ranked.append(candidate)
                continue
        
        if max_exp is not None and candidate_exp > max_exp:
            score -= 1  # Small penalty for over-qualified
        
        # AI-powered Highly Related Role matching
        c_role = candidate.get("role", "").lower().strip()
        if c_role and c_role in highly_related_roles:
            score += 3
        
        # Ensure score is at least 0
        score = max(score, 0)
        candidate["rank_score"] = score
        ranked.append(candidate)
    
    sorted_ranked = sorted(ranked, key=lambda x: x["rank_score"], reverse=True)
    has_active_filters = bool(filters.get("skills") or filters.get("role_keyword") or filters.get("min_experience_years") or filters.get("max_experience_years") or filters.get("candidate_name") or filters.get("list_all_candidates"))
    
    if has_active_filters:
        sorted_ranked = [c for c in sorted_ranked if c["rank_score"] > 0]
        
    return sorted_ranked


def check_duplicate(file_bytes: bytes, filename: str) -> str | None:
    """Return existing document _id as string if an identical file was already uploaded."""
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    existing = resume_collection.find_one(
        {"file_hash": file_hash},
        {"_id": 1}
    )
    return str(existing["_id"]) if existing else None


def extract_text_from_upload(file_bytes: bytes, file_kind: str) -> str:
    if file_kind == "docx":
        try:
            if not zipfile.is_zipfile(io.BytesIO(file_bytes)):
                raise _error(400, "Invalid or corrupted DOCX file.", "invalid_file")
            doc = Document(io.BytesIO(file_bytes))
            return "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())
        except HTTPException:
            raise
        except Exception as exc:
            raise _error(400, "Could not read DOCX. Re-save as .docx and retry.", "parse_error") from exc

    if file_kind == "pdf":
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(p.strip() for p in pages if p.strip())

    if file_kind == "txt":
        return file_bytes.decode("utf-8", errors="ignore").strip()

    raise _error(400, "Unsupported file type.", "unsupported_type")
