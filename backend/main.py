import datetime
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from utils import logger

# Import AI/groq status to expose in health check
from ai import llm_available

# Import Routers
from routers import search
from routers import resume
from routers import export
from routers import chat
from routers import auth


app = FastAPI(
    title="Candidate Search Platform API",
    version="6.0.0",
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


# Include Routers
app.include_router(auth.router)
app.include_router(search.router)
app.include_router(resume.router)
app.include_router(resume.resumes_router)
app.include_router(export.router)
app.include_router(chat.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred."})


# ─── System Routes ───────────────────────────────────────────────────────────

@app.get("/")
def home() -> dict[str, str]:
    return {"message": "Candidate Search Platform API v6 is running."}


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "groq_available": llm_available,
        "llm_available": llm_available,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
