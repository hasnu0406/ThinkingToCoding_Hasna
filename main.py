from __future__ import annotations

import csv
import datetime
import hashlib
import io
import json
import re
import uuid
import zipfile
from typing import Any

from docx import Document
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from pymongo import MongoClient
from pypdf import PdfReader
from groq import Groq

from config import COLLECTION_NAME, DB_NAME, GROQ_API_KEY, MONGO_URL


app = FastAPI(
    title="Candidate Search Platform API",
    version="5.0.0",
    description=(
        "Backend business logic for resume parsing, candidate extraction, "
        "job recommendation, search history, and export."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost:4201",
        "http://127.0.0.1:4201",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Pydantic models ─────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)


class BotSearchRequest(BaseModel):
    """Natural language query for bot-style candidate search."""
    query: str = Field(..., min_length=1, description="Natural language query like 'Python developer with 2 years experience'")
    top_n: int = Field(default=10, ge=1, le=50, description="Number of top candidates to return")


class UpdateCandidateRequest(BaseModel):
    name: str | None = None
    role: str | None = None
    experience: str | None = None
    skills: list[str] | None = None
    age: str | None = None


# ─── DB connections ───────────────────────────────────────────────────────────

mongo_client = MongoClient(MONGO_URL)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]
resume_collection = db["resumes"]
search_history_collection = db["search_history"]


# ─── Groq setup ───────────────────────────────────────────────────────────────

groq_client: Groq | None = None
groq_available = bool(GROQ_API_KEY and GROQ_API_KEY != "YOUR_GROQ_API_KEY_HERE")

if groq_available:
    groq_client = Groq(api_key=GROQ_API_KEY)
else:
    print("WARNING: GROQ_API_KEY not set. AI endpoints will use fallback content.")


# ─── Constants ────────────────────────────────────────────────────────────────

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/msword": "docx",
    "application/octet-stream": "docx",
    "application/zip": "docx",
    "text/plain": "txt",
}

ALLOWED_EXTENSIONS = {
    "pdf": "pdf",
    "docx": "docx",
    "txt": "txt",
}

SEARCHABLE_SKILLS = [
    "python", "fastapi", "django", "flask", "angular", "react", "vue",
    "mongodb", "sql", "postgresql", "mysql", "docker", "aws", "azure",
    "kubernetes", "java", "node", "typescript", "javascript", "golang",
    "rust", "c++", "machine learning", "deep learning", "tensorflow", "pytorch",
]

DEFAULT_PROFILE: dict[str, Any] = {
    "name": "Unknown",
    "age": "Not specified",
    "experience": "fresher",
    "skills": [],
    "role": "Not specified",
    "job_roles": [],
}

QUERY_PARSING_PROMPT = """You are an expert recruiter parsing natural language job search queries.
Parse the user query and extract search filters.
Return ONLY valid JSON with this exact schema:
{
  "skills": ["string"],
  "min_experience_years": number or null,
  "max_experience_years": number or null,
  "keywords": ["string"]
}

Rules:
- skills: Extract technical skills mentioned (lowercase, deduplicated). Check against: python, fastapi, django, flask, angular, react, vue, mongodb, sql, postgresql, mysql, docker, aws, azure, kubernetes, java, node, typescript, javascript, golang, rust, c++, machine learning, deep learning, tensorflow, pytorch
- min_experience_years: Extract minimum experience requirement (e.g., "2 years" -> 2)
- max_experience_years: Set to null unless explicitly stated (e.g., "2-5 years" -> max is 5)
- keywords: Other relevant search terms that don't fit skills

Examples:
- "Python developer with 2 years experience" -> {"skills": ["python"], "min_experience_years": 2, "max_experience_years": null, "keywords": ["developer"]}
- "Frontend React candidate with 3-5 years" -> {"skills": ["react"], "min_experience_years": 3, "max_experience_years": 5, "keywords": ["frontend"]}
- "Senior Java and Spring developer" -> {"skills": ["java"], "min_experience_years": 5, "max_experience_years": null, "keywords": ["spring", "senior"]}
"""

EXTRACTION_PROMPT = """You are an expert resume parser.
Extract structured candidate information from the resume text below.
Return ONLY valid JSON with this exact schema:
{
  "name": "string",
  "age": "string",
  "experience": "string",
  "skills": ["string"],
  "role": "string",
  "job_roles": ["string"]
}

Rules:
- If a field is missing, use "Not specified" except:
  - name -> "Unknown"
  - experience -> "fresher"
  - skills -> []
  - job_roles -> []
- skills must be lowercase, deduplicated, and relevant.
- experience should be a concise string like "3 years" or "fresher".
- job_roles should be readable titles such as "Backend Developer at ABC Corp (2021-2024)".
"""

JOB_RECOMMENDATION_PROMPT = """You are a senior technical recruiter.
Suggest exactly 5 job titles that best match this candidate.
Return ONLY a JSON array of 5 strings.

Candidate:
- Name: {name}
- Experience: {experience}
- Skills: {skills}
- Current Role: {role}
- Previous Roles: {job_roles}
"""

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _clean_json_payload(raw_text: str) -> str:
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", cleaned)
    cleaned = re.sub(r"\n?```$", "", cleaned)
    return cleaned.strip()


def _safe_profile(payload: dict[str, Any] | None) -> dict[str, Any]:
    profile = {**DEFAULT_PROFILE}
    if payload:
        profile.update(payload)
    profile["skills"] = sorted({str(s).strip().lower() for s in profile.get("skills", []) if str(s).strip()})
    profile["job_roles"] = [str(r).strip() for r in profile.get("job_roles", []) if str(r).strip()]
    return profile


def _error(status: int, detail: str, code: str = "error") -> HTTPException:
    return HTTPException(status_code=status, detail={"detail": detail, "code": code})


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


def call_groq_json(prompt: str, *, fallback: dict[str, Any] | list[str]) -> dict[str, Any] | list[str]:
    if not groq_available or groq_client is None:
        return fallback
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
        return json.loads(_clean_json_payload(completion.choices[0].message.content or ""))
    except Exception as exc:
        print(f"Groq request failed: {exc}")
        return fallback


def ai_extract_resume(text_content: str) -> dict[str, Any]:
    if not text_content.strip():
        return _safe_profile(None)
    fallback = _safe_profile(None)
    response = call_groq_json(f"{EXTRACTION_PROMPT}\n\nResume content:\n{text_content}", fallback=fallback)
    return _safe_profile(response) if isinstance(response, dict) else fallback


def ai_recommend_jobs(profile: dict[str, Any]) -> list[str]:
    prompt = JOB_RECOMMENDATION_PROMPT.format(
        name=profile.get("name", "Unknown"),
        experience=profile.get("experience", "fresher"),
        skills=", ".join(profile.get("skills", [])) or "Not specified",
        role=profile.get("role", "Not specified"),
        job_roles=", ".join(profile.get("job_roles", [])) or "Not specified",
    )
    fallback = ["Backend Developer", "Python Developer", "API Engineer", "Software Engineer", "Application Developer"]
    response = call_groq_json(prompt, fallback=fallback)
    return ([str(i) for i in response][:5] or fallback) if isinstance(response, list) else fallback


def parse_query(query: str) -> dict[str, Any]:
    lowered = query.lower()
    found_skills = [s for s in SEARCHABLE_SKILLS if s in lowered]
    experience = None
    match = re.search(r"(\d+)\s*year", lowered)
    if match:
        experience = int(match.group(1))
    return {"skills": found_skills, "experience": experience}


def ai_parse_query(query: str) -> dict[str, Any]:
    """Use AI to intelligently parse natural language queries into structured filters."""
    fallback = parse_query(query)
    
    response = call_groq_json(f"{QUERY_PARSING_PROMPT}\n\nUser query: {query}", fallback=fallback)
    
    if isinstance(response, dict):
        # Normalize the response to match our expected format
        skills = response.get("skills", [])
        min_exp = response.get("min_experience_years")
        max_exp = response.get("max_experience_years")
        
        # Use min_experience_years as the primary experience filter
        experience = min_exp if min_exp is not None else fallback.get("experience")
        
        return {
            "skills": [s.lower().strip() for s in skills if s],
            "experience": experience,
            "min_experience": min_exp,
            "max_experience": max_exp,
            "keywords": response.get("keywords", []),
        }
    
    return fallback


def extract_experience_years(experience_value: str) -> int:
    if not experience_value or experience_value == "fresher":
        return 0
    match = re.search(r"(\d+)", experience_value)
    return int(match.group(1)) if match else 0


def rank_candidates(candidates: list[dict[str, Any]], filters: dict[str, Any]) -> list[dict[str, Any]]:
    """Enhanced ranking algorithm with multi-factor scoring."""
    ranked = []
    
    for candidate in candidates:
        score = 0
        
        # Skill matching (highest priority)
        candidate_skills = set(s.lower().strip() for s in candidate.get("skills", []))
        filter_skills = set(filters.get("skills", []))
        
        if filter_skills:
            skill_matches = len(filter_skills & candidate_skills)
            score += skill_matches * 5  # 5 points per skill match
            # Bonus for having additional relevant skills
            score += min(len(candidate_skills - filter_skills), 3)
        
        # Experience matching
        candidate_exp = extract_experience_years(candidate.get("experience", "0"))
        min_exp = filters.get("min_experience")
        max_exp = filters.get("max_experience")
        
        if min_exp is not None:
            if candidate_exp >= min_exp:
                score += 3  # Meets minimum experience
                # Extra bonus for exceeding minimum
                score += min((candidate_exp - min_exp) // 2, 2)
            else:
                score -= 2  # Penalize for insufficient experience
        
        if max_exp is not None and candidate_exp > max_exp:
            score -= 1  # Small penalty for over-qualified
        
        # Keyword matching in name/role
        keywords = [k.lower() for k in filters.get("keywords", [])]
        candidate_text = (
            f"{candidate.get('name', '')} {candidate.get('role', '')} "
            f"{' '.join(candidate.get('job_roles', []))}"
        ).lower()
        
        for keyword in keywords:
            if keyword in candidate_text:
                score += 1
        
        # Ensure score is at least 0
        score = max(score, 0)
        candidate["rank_score"] = score
        ranked.append(candidate)
    
    return sorted(ranked, key=lambda x: x["rank_score"], reverse=True)


def check_duplicate(file_bytes: bytes, filename: str) -> str | None:
    """Return existing candidate_id if an identical file was already uploaded."""
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    existing = resume_collection.find_one(
        {"file_hash": file_hash},
        {"candidate_id": 1, "_id": 0}
    )
    return existing["candidate_id"] if existing else None


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def home() -> dict[str, str]:
    return {"message": "Candidate Search Platform API v5 is running."}


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "groq_available": groq_available,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }


# Search
@app.post("/search")
def search(data: SearchRequest) -> dict[str, Any]:
    filters = parse_query(data.query)
    documents = list(resume_collection.find({}, {"_id": 0}))
    ranked_results = rank_candidates(documents, filters)

    # Save to search history
    search_history_collection.insert_one({
        "query": data.query,
        "filters_used": filters,
        "total_results": len(ranked_results),
        "candidates": ranked_results,
        "searched_at": datetime.datetime.utcnow(),
    })

    return {
        "total_results": len(ranked_results),
        "filters_used": filters,
        "candidates": ranked_results,
    }


@app.post("/search/bot")
def bot_search(data: BotSearchRequest) -> dict[str, Any]:
    """AI-powered bot-style candidate search with natural language query parsing."""
    # Use AI to parse the query
    filters = ai_parse_query(data.query)
    
    # Retrieve all candidates
    documents = list(resume_collection.find({}, {"_id": 0}))
    
    # Rank candidates using enhanced algorithm
    ranked_results = rank_candidates(documents, filters)
    
    # Return top N results
    top_results = ranked_results[:data.top_n]
    
    # Save to search history
    search_history_collection.insert_one({
        "query": data.query,
        "query_type": "bot",
        "filters_used": filters,
        "total_results": len(ranked_results),
        "returned_results": len(top_results),
        "candidates": top_results,
        "searched_at": datetime.datetime.utcnow(),
    })

    return {
        "query": data.query,
        "total_results": len(ranked_results),
        "returned_results": len(top_results),
        "filters_used": {
            "skills": filters.get("skills", []),
            "min_experience": filters.get("min_experience"),
            "max_experience": filters.get("max_experience"),
            "keywords": filters.get("keywords", []),
        },
        "candidates": top_results,
    }


@app.get("/search/history")
def get_search_history(limit: int = Query(default=20, le=100)) -> list[dict[str, Any]]:
    raw_entries = list(
        search_history_collection.find({}, {"_id": 0})
        .sort("searched_at", -1)
        .limit(limit)
    )

    normalized: list[dict[str, Any]] = []

    for entry in raw_entries:
        # Prefer canonical key `candidates` (new format). If old `results` exists,
        # expand it by fetching full profiles from the resume collection when possible.
        if "candidates" not in entry and "results" in entry:
            results_list = entry.get("results", []) or []
            ids = [r.get("candidate_id") for r in results_list if r.get("candidate_id")]
            profiles = []
            if ids:
                # fetch full profiles for these ids
                found = {p.get("candidate_id"): p for p in resume_collection.find({"candidate_id": {"$in": ids}}, {"_id": 0})}
                for r in results_list:
                    cid = r.get("candidate_id")
                    profile = found.get(cid)
                    if profile:
                        # preserve rank_score from history if present
                        profile = {**profile}
                        profile["rank_score"] = r.get("rank_score", profile.get("rank_score", 0))
                        profiles.append(profile)
                    else:
                        # fallback to minimal shape
                        profiles.append({
                            "candidate_id": cid,
                            "name": r.get("name", "Unknown"),
                            "rank_score": r.get("rank_score", 0),
                            "skills": [],
                            "role": "Not specified",
                            "job_roles": [],
                            "recommended_jobs": [],
                        })
            entry["candidates"] = profiles

        # Ensure `candidates` exists and is a list
        if "candidates" in entry and not isinstance(entry["candidates"], list):
            entry["candidates"] = []

        # Clean up old keys to avoid confusion in the frontend
        entry.pop("results", None)
        entry.pop("returned_results", None)

        if "searched_at" in entry and isinstance(entry["searched_at"], datetime.datetime):
            dt = entry["searched_at"]
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            entry["searched_at"] = dt.isoformat()

        normalized.append(entry)

    return normalized


@app.delete("/search/history")
def clear_search_history() -> dict[str, str]:
    search_history_collection.delete_many({})
    return {"message": "Search history cleared."}


# Resume CRUD
@app.post("/resume/upload")
async def upload_resume(file: UploadFile = File(...)) -> dict[str, Any]:
    file_ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else ""
    file_kind = ALLOWED_TYPES.get(file.content_type)

    if file_ext in ALLOWED_EXTENSIONS:
        file_kind = ALLOWED_EXTENSIONS[file_ext]

    if file_kind is None:
        raise _error(400, "Unsupported file type. Upload PDF, DOCX, or TXT only.", "unsupported_type")

    file_bytes = await file.read()

    # Duplicate detection
    dup_id = check_duplicate(file_bytes, file.filename or "")
    if dup_id:
        existing = resume_collection.find_one({"candidate_id": dup_id}, {"_id": 0})
        if existing:
            existing["duplicate"] = True
            return existing

    resume_text = extract_text_from_upload(file_bytes, file_kind)
    if not resume_text.strip():
        raise _error(400, "Could not extract readable text from the uploaded resume.", "empty_content")

    parsed = ai_extract_resume(resume_text)
    recommended_jobs = ai_recommend_jobs(parsed)
    candidate_id = str(uuid.uuid4())

    document = {
        "candidate_id": candidate_id,
        "file_name": file.filename,
        "file_hash": hashlib.sha256(file_bytes).hexdigest(),
        "name": parsed.get("name", "Unknown"),
        "age": parsed.get("age", "Not specified"),
        "experience": parsed.get("experience", "fresher"),
        "skills": parsed.get("skills", []),
        "role": parsed.get("role", "Not specified"),
        "job_roles": parsed.get("job_roles", []),
        "recommended_jobs": recommended_jobs,
        "resume_text": resume_text,
        "created_at": datetime.datetime.utcnow(),
    }

    resume_collection.insert_one(document)
    document.pop("_id", None)
    return document


@app.get("/resumes")
def get_all_resumes(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    skip = (page - 1) * limit
    total = resume_collection.count_documents({})
    documents = list(resume_collection.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit))
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "candidates": documents,
    }


@app.get("/resume/{candidate_id}")
def get_resume(candidate_id: str) -> dict[str, Any]:
    document = resume_collection.find_one({"candidate_id": candidate_id}, {"_id": 0})
    if not document:
        raise _error(404, "Resume not found.", "not_found")
    return document


@app.patch("/resume/{candidate_id}")
def update_resume(candidate_id: str, updates: UpdateCandidateRequest) -> dict[str, Any]:
    document = resume_collection.find_one({"candidate_id": candidate_id}, {"_id": 0})
    if not document:
        raise _error(404, "Resume not found.", "not_found")

    update_data: dict[str, Any] = {}
    if updates.name is not None:
        update_data["name"] = updates.name.strip()
    if updates.role is not None:
        update_data["role"] = updates.role.strip()
    if updates.experience is not None:
        update_data["experience"] = updates.experience.strip()
    if updates.age is not None:
        update_data["age"] = updates.age.strip()
    if updates.skills is not None:
        update_data["skills"] = sorted({s.strip().lower() for s in updates.skills if s.strip()})

    if not update_data:
        return document

    update_data["updated_at"] = datetime.datetime.utcnow()
    resume_collection.update_one({"candidate_id": candidate_id}, {"$set": update_data})

    updated = resume_collection.find_one({"candidate_id": candidate_id}, {"_id": 0})
    return updated  # type: ignore[return-value]


@app.delete("/resume/{candidate_id}")
def delete_resume(candidate_id: str) -> dict[str, str]:
    result = resume_collection.delete_one({"candidate_id": candidate_id})
    if result.deleted_count == 0:
        raise _error(404, "Resume not found.", "not_found")
    return {"message": "Resume deleted successfully."}


@app.get("/resume/{candidate_id}/recommend")
def refresh_recommendations(candidate_id: str) -> dict[str, Any]:
    document = resume_collection.find_one({"candidate_id": candidate_id}, {"_id": 0})
    if not document:
        raise _error(404, "Resume not found.", "not_found")

    recommended_jobs = ai_recommend_jobs(document)
    resume_collection.update_one(
        {"candidate_id": candidate_id},
        {"$set": {"recommended_jobs": recommended_jobs}},
    )
    return {"candidate_id": candidate_id, "recommended_jobs": recommended_jobs}


# Export
@app.get("/export/candidates")
def export_candidates_csv() -> StreamingResponse:
    documents = list(resume_collection.find({}, {"_id": 0, "resume_text": 0}))

    output = io.StringIO()
    fieldnames = ["candidate_id", "name", "age", "role", "experience", "skills", "job_roles", "recommended_jobs", "file_name", "created_at"]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()

    for doc in documents:
        doc["skills"] = ", ".join(doc.get("skills", []))
        doc["job_roles"] = " | ".join(doc.get("job_roles", []))
        doc["recommended_jobs"] = ", ".join(doc.get("recommended_jobs", []))
        writer.writerow(doc)

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=candidates.csv"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
