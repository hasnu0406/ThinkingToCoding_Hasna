from pydantic import BaseModel, Field

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

class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6)

class UserLoginRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6)


class ChatSessionCreateRequest(BaseModel):
    user_email: str = Field(..., min_length=3, max_length=100)


class ChatMessageSendRequest(BaseModel):
    session_id: str | None = None
    user_email: str = Field(..., min_length=3, max_length=100)
    message: str = Field(..., min_length=1)


