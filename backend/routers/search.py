import datetime
from typing import Any
# pyrefly: ignore [missing-import]
from bson import ObjectId
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Query, BackgroundTasks

from models import SearchRequest, BotSearchRequest
from database import resume_collection, search_history_collection
from ai import ai_parse_query, ai_generate_query_title
from logic import parse_query, rank_candidates
from utils import _serialize

def save_search_history_bg(query: str, filters: dict, total_results: int, candidates: list):
    title = ai_generate_query_title(query)
    candidate_ids = [c["id"] for c in candidates if "id" in c]
    search_history_collection.insert_one({
        "query": query,
        "title": title,
        "filters_used": filters,
        "total_results": total_results,
        "candidates": candidate_ids,
        "searched_at": datetime.datetime.utcnow(),
    })

def save_bot_search_history_bg(query: str, filters: dict, total_results: int, returned_results: int, candidates: list):
    title = ai_generate_query_title(query)
    candidate_ids = [c["id"] for c in candidates if "id" in c]
    search_history_collection.insert_one({
        "query": query,
        "title": title,
        "query_type": "bot",
        "filters_used": filters,
        "total_results": total_results,
        "returned_results": returned_results,
        "candidates": candidate_ids,
        "searched_at": datetime.datetime.utcnow(),
    })

router = APIRouter(prefix="/search", tags=["Search"])

@router.post("")
def search(data: SearchRequest, background_tasks: BackgroundTasks) -> dict[str, Any]:
    filters = parse_query(data.query)
    documents = [_serialize(d) for d in resume_collection.find({})]
    ranked_results = rank_candidates(documents, filters)

    # Save to search history in background
    background_tasks.add_task(
        save_search_history_bg,
        data.query,
        filters,
        len(ranked_results),
        ranked_results
    )

    return {
        "total_results": len(ranked_results),
        "filters_used": filters,
        "candidates": ranked_results,
    }


@router.post("/bot")
def bot_search(data: BotSearchRequest, background_tasks: BackgroundTasks) -> dict[str, Any]:
    """AI-powered bot-style candidate search with natural language query parsing."""
    # Use AI to parse the query
    filters = ai_parse_query(data.query)
    
    # Retrieve all candidates
    documents = [_serialize(d) for d in resume_collection.find({})]
    
    # Rank candidates using enhanced algorithm
    ranked_results = rank_candidates(documents, filters)
    
    # Return top N results
    top_results = ranked_results[:data.top_n]
    
    # Save to search history in background
    background_tasks.add_task(
        save_bot_search_history_bg,
        data.query,
        filters,
        len(ranked_results),
        len(top_results),
        top_results
    )

    return {
        "query": data.query,
        "total_results": len(ranked_results),
        "returned_results": len(top_results),
        "filters_used": {
            "skills": filters.get("skills", []),
            "min_experience": filters.get("min_experience_years"),
            "max_experience": filters.get("max_experience_years"),
            "role_keyword": filters.get("role_keyword"),
        },
        "candidates": top_results,
    }


@router.get("/history")
def get_search_history(limit: int = Query(default=20, le=100)) -> list[dict[str, Any]]:
    raw_entries = list(
        search_history_collection.find({}, {"_id": 0})
        .sort("searched_at", -1)
        .limit(limit)
    )

    normalized: list[dict[str, Any]] = []

    for entry in raw_entries:
        if "candidates" in entry and entry["candidates"] and isinstance(entry["candidates"][0], str):
            ids = entry["candidates"]
            object_ids = []
            for idx in ids:
                try:
                    object_ids.append(ObjectId(idx))
                except Exception:
                    pass
            found = {str(p["_id"]): _serialize(p) for p in resume_collection.find({"_id": {"$in": object_ids}})}
            entry["candidates"] = [found[cid] for cid in ids if cid in found]
        elif "candidates" not in entry and "results" in entry:
            results_list = entry.get("results", []) or []
            ids = [r.get("id") for r in results_list if r.get("id")]
            profiles = []
            if ids:
                object_ids = []
                for idx in ids:
                    try:
                        object_ids.append(ObjectId(idx))
                    except Exception:
                        pass
                
                # fetch full profiles for these ids
                found = {str(p["_id"]): p for p in resume_collection.find({"_id": {"$in": object_ids}})}
                for r in results_list:
                    cid = r.get("id")
                    profile = found.get(cid)
                    if profile:
                        profile = _serialize({**profile})
                        profile["rank_score"] = r.get("rank_score", profile.get("rank_score", 0))
                        profiles.append(profile)
                    else:
                        profiles.append({
                            "id": cid,
                            "name": r.get("name", "Unknown"),
                            "rank_score": r.get("rank_score", 0),
                            "skills": [],
                            "role": "Not specified",
                            "job_roles": [],
                            "recommended_jobs": [],
                        })
            entry["candidates"] = profiles

        if "candidates" in entry and not isinstance(entry["candidates"], list):
            entry["candidates"] = []

        entry.pop("results", None)
        entry.pop("returned_results", None)

        if "searched_at" in entry and isinstance(entry["searched_at"], datetime.datetime):
            dt = entry["searched_at"]
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            entry["searched_at"] = dt.isoformat()

        normalized.append(entry)

    return normalized


@router.delete("/history")
def clear_search_history() -> dict[str, str]:
    search_history_collection.delete_many({})
    return {"message": "Search history cleared."}
