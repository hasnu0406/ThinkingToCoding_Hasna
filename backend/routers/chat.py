import datetime
from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel

from database import resume_collection, search_history_collection
from ai import ai_parse_query, ai_chatbot_reply, ai_generate_query_title
from logic import rank_candidates
from utils import _serialize

router = APIRouter(prefix="/chat", tags=["Chatbot"])


class ChatMessage(BaseModel):
    role: str   # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


@router.post("")
def chat(data: ChatRequest) -> dict[str, Any]:
    """
    Conversational AI chatbot endpoint.
    Returns BOTH a conversational text reply AND the ranked candidates array.
    """
    user_messages = [m for m in data.messages if m.role == "user"]
    if not user_messages:
        return {"reply": "Please ask me something! 😊", "candidates": []}

    latest_query = user_messages[-1].content

    # Step 1: Parse the query using AI (same as bot_search)
    filters = ai_parse_query(latest_query)

    # Step 2: Fetch all candidates and rank them (same as bot_search)
    all_candidates = [_serialize(d) for d in resume_collection.find({})]
    ranked_results = rank_candidates(all_candidates, filters)
    top_results = ranked_results[:10]

    # Step 3: Build conversation history for AI
    conversation = [{"role": m.role, "content": m.content} for m in data.messages]

    # Step 4: Get conversational text reply from AI
    reply = ai_chatbot_reply(conversation, top_results, filters, len(all_candidates))

    if not reply:
        reply = "Sorry, I'm having trouble connecting right now. Please try again! 🤖"

    # Save to search history (as requested, treat chat like search history)
    search_history_collection.insert_one({
        "query": latest_query,
        "title": ai_generate_query_title(latest_query),
        "query_type": "chat",
        "filters_used": filters,
        "total_results": len(ranked_results),
        "returned_results": len(top_results),
        "candidates": top_results,
        "searched_at": datetime.datetime.utcnow(),
    })

    return {
        "reply": reply,
        "candidates": top_results   # send full candidate data back to frontend
    }
