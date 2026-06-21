import io
import csv
# pyrefly: ignore [missing-import]
from fastapi import APIRouter
# pyrefly: ignore [missing-import]
from fastapi.responses import StreamingResponse

from database import resume_collection
from utils import _serialize

router = APIRouter(prefix="/export", tags=["Export"])

@router.get("/candidates")
def export_candidates_csv() -> StreamingResponse:
    documents = [_serialize(d) for d in resume_collection.find({}, {"resume_text": 0})]

    output = io.StringIO()
    fieldnames = ["id", "name", "age", "role", "experience", "skills", "job_roles", "recommended_jobs", "file_name", "created_at"]
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
