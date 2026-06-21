import json
import threading
from typing import Any
from groq import Groq
from openai import OpenAI

from config import GROQ_API_KEYS, OPENROUTER_API_KEY
from constants import (
    EXTRACTION_PROMPT,
    JOB_RECOMMENDATION_PROMPT,
    QUERY_PARSING_PROMPT
)
from utils import _clean_json_payload, _safe_profile
from logic import parse_query


# ─────────────────────────────────────────────
# Multi-Provider AI Manager
# ─────────────────────────────────────────────
class AIClientManager:
    """
    Manages a pool of AI clients (Groq and OpenRouter) with automatic
    round-robin rotation and on-error failover. Thread-safe.
    """

    def __init__(self, groq_keys: list[str], openrouter_key: str | None) -> None:
        self._clients = []
        self._index = 0
        self._lock = threading.Lock()
        
        # Add Groq clients
        for k in groq_keys:
            self._clients.append({
                "provider": "groq",
                "client": Groq(api_key=k),
                "model": "llama-3.3-70b-versatile"
            })
            
        # Add OpenRouter client if key exists
        if openrouter_key:
            self._clients.append({
                "provider": "openrouter",
                "client": OpenAI(base_url="https://openrouter.ai/api/v1", api_key=openrouter_key),
                "model": "meta-llama/llama-3.3-70b-instruct"
            })

    @property
    def available(self) -> bool:
        return len(self._clients) > 0

    def _current_client(self) -> dict:
        with self._lock:
            return self._clients[self._index % len(self._clients)]

    def _rotate(self) -> None:
        """Move to the next key/provider in the pool."""
        with self._lock:
            self._index = (self._index + 1) % len(self._clients)

    def call_json(self, prompt: str, *, fallback: Any) -> Any:
        """
        Try all keys/providers in round-robin order. On rate-limit or error,
        auto-rotate to the next one. Returns fallback only if all fail.
        """
        if not self.available:
            return fallback

        for attempt in range(len(self._clients)):
            client_info = self._current_client()
            client = client_info["client"]
            model = client_info["model"]
            provider = client_info["provider"]
            
            try:
                completion = client.chat.completions.create(
                    model=model,
                    temperature=0.1,
                    max_tokens=1200,
                    messages=[{"role": "user", "content": prompt}],
                )
                return json.loads(
                    _clean_json_payload(completion.choices[0].message.content or "")
                )
            except Exception as exc:
                error_str = str(exc).lower()
                if "rate" in error_str or "429" in error_str or "quota" in error_str:
                    print(f"[KeyManager] {provider} rate-limited. Rotating.")
                    self._rotate()
                else:
                    print(f"[KeyManager] {provider} JSON request failed: {exc}")
                    self._rotate()

        print("[KeyManager] All providers exhausted. Returning fallback.")
        return fallback

    def call_text(self, messages: list[dict]) -> str:
        """
        Stream-friendly text call for the chatbot endpoint.
        Rotates on rate-limit errors.
        """
        if not self.available:
            return ""

        for attempt in range(len(self._clients)):
            client_info = self._current_client()
            client = client_info["client"]
            model = client_info["model"]
            provider = client_info["provider"]
            
            try:
                completion = client.chat.completions.create(
                    model=model,
                    temperature=0.6,
                    max_tokens=1024,
                    messages=messages,
                )
                return completion.choices[0].message.content or ""
            except Exception as exc:
                error_str = str(exc).lower()
                if "rate" in error_str or "429" in error_str or "quota" in error_str:
                    print(f"[KeyManager] {provider} rate-limited. Rotating.")
                    self._rotate()
                else:
                    print(f"[KeyManager] {provider} text call failed: {exc}")
                    self._rotate()

        return ""


# ─────────────────────────────────────────────
# Singleton Manager
# ─────────────────────────────────────────────
key_manager = AIClientManager(GROQ_API_KEYS, OPENROUTER_API_KEY)
groq_available = key_manager.available

if not groq_available:
    print("WARNING: No API Keys set. AI endpoints will use fallback content.")


# ─────────────────────────────────────────────
# Public AI Functions
# ─────────────────────────────────────────────
def call_groq_json(prompt: str, *, fallback: dict[str, Any] | list[str]) -> dict[str, Any] | list[str]:
    return key_manager.call_json(prompt, fallback=fallback)


def ai_extract_resume(text_content: str) -> dict[str, Any]:
    if not text_content.strip():
        return _safe_profile(None)
    fallback = _safe_profile(None)
    response = call_groq_json(
        f"{EXTRACTION_PROMPT}\n\nResume content:\n{text_content}", fallback=fallback
    )
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


def ai_parse_query(query: str) -> dict[str, Any]:
    """Use AI to intelligently parse natural language queries into structured filters."""
    fallback = parse_query(query)
    response = call_groq_json(
        f"{QUERY_PARSING_PROMPT}\n\nUser query: {query}", fallback=fallback
    )
    if isinstance(response, dict):
        skills = response.get("skills", [])
        min_exp = response.get("min_experience_years")
        max_exp = response.get("max_experience_years")
        experience = min_exp if min_exp is not None else fallback.get("experience")
        return {
            "skills": [s.lower().strip() for s in skills if s],
            "experience": experience,
            "min_experience": min_exp,
            "max_experience": max_exp,
            "role_keyword": response.get("role_keyword"),
        }
    return fallback


def get_highly_related_roles(keyword: str, candidate_roles: list[str]) -> list[str]:
    if not keyword or not candidate_roles:
        return []

    prompt = f"""You are an expert technical recruiter.
I will give you a target job search keyword and a list of candidate roles.
Return ONLY a JSON array of strings containing the candidate roles that are highly related to the keyword.
If a role is completely unrelated, do not include it.

Target Keyword: "{keyword}"
Candidate Roles: {json.dumps(candidate_roles)}

Return ONLY the JSON array (e.g. ["Role 1", "Role 2"])."""

    fallback: list[str] = []
    response = call_groq_json(prompt, fallback=fallback)
    return [str(r) for r in response] if isinstance(response, list) else fallback


def ai_chatbot_reply(conversation: list[dict], ranked_candidates: list[dict], filters: dict, total_in_db: int) -> str:
    """
    Given a conversation history and pre-ranked candidates (from the same engine
    as AI Intelligent Search), produce a friendly ChatGPT-style text response.
    """
    role_keyword = filters.get("role_keyword", "")
    skills = filters.get("skills", [])
    experience = filters.get("experience")

    # Build a structured summary of ranked candidates for the AI
    if ranked_candidates:
        candidates_text = []
        for i, c in enumerate(ranked_candidates, 1):
            candidates_text.append(
                f"{i}. {c.get('name', 'Unknown')} | Role: {c.get('role', 'N/A')} | "
                f"Experience: {c.get('experience', 'N/A')} yrs | "
                f"Score: {c.get('rank_score', 0)} | "
                f"Skills: {', '.join(c.get('skills', [])[:6])}"
            )
        ranked_text = "\n".join(candidates_text)
    else:
        ranked_text = "No candidates matched."

    system_prompt = f"""You are SearchBot, a friendly and smart AI recruitment assistant for the Candidate Search Platform.

I have already run the user's query through our AI-powered ranking engine (the same engine as AI Intelligent Search).
Here are the TOP ranked candidates from our database, sorted by match score:

{ranked_text}

Search filters extracted from the query:
- Role searched: {role_keyword or 'Not specified'}
- Skills required: {', '.join(skills) if skills else 'Not specified'}
- Experience required: {f'{experience} years' if experience else 'Not specified'}
- Total candidates in database: {total_in_db}

Your task:
1. Reply in a friendly, conversational ChatGPT-style response.
2. Present the top candidates clearly — mention their name, role, experience, skills, and match score naturally in your text.
3. If no candidates matched, say so and suggest what types of profiles exist in the database.
4. Keep the tone professional but friendly.
5. Do NOT use JSON or code blocks. Write naturally like a smart recruiter assistant.
6. Use emojis sparingly to make the response feel alive.
7. Keep your response concise and to the point."""

    messages = [{"role": "system", "content": system_prompt}] + conversation
    return key_manager.call_text(messages)


def ai_generate_query_title(query: str) -> str:
    """Generate a short 3-5 word title for a search query (similar to ChatGPT chat titles)."""
    prompt = f"""You are a helpful assistant.
Given a user query for candidates, generate a concise, 3-5 word title summarizing the query.
Do NOT use quotes, do NOT add introductory text, and do NOT use punctuation. Return ONLY the title text.

User Query: "{query}"

Title:"""
    
    messages = [{"role": "user", "content": prompt}]
    title = key_manager.call_text(messages)
    title = title.strip().strip('"').strip("'")
    if not title:
        title = query[:50] + "..." if len(query) > 50 else query
    return title


