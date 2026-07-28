import datetime
from typing import Any
from fastapi import APIRouter, Query, BackgroundTasks
from bson import ObjectId

from database import resume_collection, chat_sessions_collection
from models import ChatSessionCreateRequest, ChatMessageSendRequest
from ai import ai_parse_query, ai_chatbot_reply, ai_generate_query_title
from logic import rank_candidates
from utils import _serialize, _get_object_id, _error

router = APIRouter(prefix="/chat", tags=["Chatbot"])


def update_title_bg(session_id: str, message: str) -> None:
    """Generate a clean, AI-powered summary title in the background and update the database."""
    try:
        title = ai_generate_query_title(message)
        chat_sessions_collection.update_one(
            {"_id": _get_object_id(session_id)},
            {"$set": {"title": title}}
        )
    except Exception as e:
        print(f"[ChatRouter] Failed to update session title in background: {e}")


@router.post("/session")
def create_chat_session(data: ChatSessionCreateRequest) -> dict[str, Any]:
    """Create a new chat session for a user."""
    session_doc = {
        "user_email": data.user_email,
        "title": "New Chat",
        "messages": [],
        "created_at": datetime.datetime.utcnow(),
        "updated_at": datetime.datetime.utcnow(),
    }
    result = chat_sessions_collection.insert_one(session_doc)
    session_doc["id"] = str(result.inserted_id)
    session_doc.pop("_id", None)
    
    # Ensure datetime fields are serialized to strings
    if "created_at" in session_doc:
        session_doc["created_at"] = session_doc["created_at"].isoformat()
    if "updated_at" in session_doc:
        session_doc["updated_at"] = session_doc["updated_at"].isoformat()
        
    return session_doc


@router.get("/sessions")
def get_chat_sessions(user_email: str = Query(..., min_length=3)) -> list[dict[str, Any]]:
    """List all chat sessions for a specific user, sorted by updated_at descending."""
    raw_sessions = list(
        chat_sessions_collection.find({"user_email": user_email})
        .sort("updated_at", -1)
    )
    
    sessions = []
    for s in raw_sessions:
        s["id"] = str(s.pop("_id"))
        
        # Serialize datetime fields
        if "created_at" in s and isinstance(s["created_at"], datetime.datetime):
            s["created_at"] = s["created_at"].isoformat()
        if "updated_at" in s and isinstance(s["updated_at"], datetime.datetime):
            s["updated_at"] = s["updated_at"].isoformat()
            
        # Add a preview of the first message
        preview = ""
        if s.get("messages"):
            first_msg = s["messages"][0]
            preview = first_msg.get("content", "")[:60]
            if len(first_msg.get("content", "")) > 60:
                preview += "..."
        s["preview"] = preview
        
        sessions.append(s)
        
    return sessions


@router.get("/sessions/{session_id}")
def get_chat_session(session_id: str) -> dict[str, Any]:
    """Retrieve full details of a chat session, including complete message history."""
    oid = _get_object_id(session_id)
    session = chat_sessions_collection.find_one({"_id": oid})
    if not session:
        raise _error(404, "Chat session not found.", "not_found")
        
    session["id"] = str(session.pop("_id"))
    
    if "created_at" in session and isinstance(session["created_at"], datetime.datetime):
        session["created_at"] = session["created_at"].isoformat()
    if "updated_at" in session and isinstance(session["updated_at"], datetime.datetime):
        session["updated_at"] = session["updated_at"].isoformat()
        
    return session


@router.delete("/sessions/{session_id}")
def delete_chat_session(session_id: str) -> dict[str, str]:
    """Delete a specific chat session."""
    oid = _get_object_id(session_id)
    result = chat_sessions_collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise _error(404, "Chat session not found.", "not_found")
    return {"message": "Chat session deleted successfully."}


@router.delete("/sessions")
def clear_chat_sessions(user_email: str = Query(..., min_length=3)) -> dict[str, str]:
    """Delete all chat sessions for a specific user."""
    chat_sessions_collection.delete_many({"user_email": user_email})
    return {"message": "All chat sessions deleted successfully."}


@router.post("")
def chat(data: ChatMessageSendRequest, background_tasks: BackgroundTasks) -> dict[str, Any]:
    """
    Send a message within a chat session.
    Retrieves full chat history context, ranks candidates, and invokes the AI chatbot.
    Saves the user query, assistant reply, and candidates to the session's history.
    """
    user_email = data.user_email.strip()
    session_id = data.session_id
    
    # 1. Resolve or create chat session
    if not session_id:
        # Create a new session on the fly
        session_doc = {
            "user_email": user_email,
            "title": "New Chat",
            "messages": [],
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow(),
        }
        result = chat_sessions_collection.insert_one(session_doc)
        session_id = str(result.inserted_id)
        session = session_doc
    else:
        oid = _get_object_id(session_id)
        session = chat_sessions_collection.find_one({"_id": oid})
        if not session:
            raise _error(404, "Chat session not found.", "not_found")

    # 2. Build conversation context for history and query parsing
    # Convert saved messages format to what key_manager and query parser expect (role, content)
    messages_history = []
    for m in session.get("messages", []):
        messages_history.append({
            "role": m["role"],
            "content": m["content"]
        })
        
    # Extract Technical filters from the user query (with history context)
    filters = ai_parse_query(data.message, messages_history)
    
    # 3. Retrieve and rank candidates
    all_candidates = [_serialize(d) for d in resume_collection.find({})]
    has_active_filters = bool(filters.get("skills") or filters.get("role_keyword") or filters.get("min_experience_years") or filters.get("max_experience_years") or filters.get("candidate_name"))
    
    if has_active_filters:
        ranked_results = rank_candidates(all_candidates, filters)
        top_results = ranked_results[:3]
    else:
        top_results = []
        
    ui_candidates = top_results if filters.get("requests_resumes") else []
    
    # Append the new user message for the LLM reply context
    messages_history.append({
        "role": "user",
        "content": data.message
    })
    
    # 5. Fetch AI conversational reply
    reply = ai_chatbot_reply(messages_history, top_results, filters, len(all_candidates))
    if not reply:
        reply = "Sorry, I'm having trouble connecting right now. Please try again! 🤖"
        
    # 6. Save messages to the database
    user_message_doc = {
        "role": "user",
        "content": data.message,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    
    assistant_message_doc = {
        "role": "assistant",
        "content": reply,
        "candidates": ui_candidates,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    
    # Update title in the background if it is the first message in the session
    title = session.get("title", "New Chat")
    should_update_title = len(session.get("messages", [])) == 0 or title == "New Chat"
    
    if should_update_title:
        # Trigger background title generation task
        background_tasks.add_task(update_title_bg, session_id, data.message)
        # Create a quick temporary title using first 4 words of the query
        words = data.message.split()
        title = " ".join(words[:4]) + "..." if len(words) > 4 else data.message
        
    chat_sessions_collection.update_one(
        {"_id": _get_object_id(session_id)},
        {
            "$set": {
                "title": title,
                "updated_at": datetime.datetime.utcnow()
            },
            "$push": {
                "messages": {
                    "$each": [user_message_doc, assistant_message_doc]
                }
            }
        }
    )
    
    return {
        "session_id": session_id,
        "title": title,
        "reply": reply,
        "candidates": ui_candidates
    }
