import datetime
import hashlib
import bson
from typing import Any
from fastapi import APIRouter, File, Query, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
import os
from fpdf import FPDF

from models import UpdateCandidateRequest
from database import resume_collection
from constants import ALLOWED_TYPES, ALLOWED_EXTENSIONS
from ai import ai_extract_resume, ai_recommend_jobs
from logic import check_duplicate, extract_text_from_upload
from utils import _serialize, _get_object_id, _error, logger
import drive_service

router = APIRouter(prefix="/resume", tags=["Resume"])

@router.post("/upload")
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
        existing = resume_collection.find_one({"_id": _get_object_id(dup_id)})
        if existing:
            _serialize(existing)
            existing["duplicate"] = True
            return existing

    resume_text = extract_text_from_upload(file_bytes, file_kind)
    if not resume_text.strip():
        raise _error(400, "Could not extract readable text from the uploaded resume.", "empty_content")

    parsed = ai_extract_resume(resume_text)
    recommended_jobs = ai_recommend_jobs(parsed)
    candidate_name = parsed.get("name", "Unknown")
    
    candidate_id = bson.ObjectId()
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    
    # Save exact original file locally as fallback buffer
    original_ext = file_ext if file_ext else ("pdf" if file_kind == "pdf" else "docx")
    saved_filename = f"{str(candidate_id)}.{original_ext}"
    local_path = os.path.join("uploads", saved_filename)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    
    with open(local_path, "wb") as f:
        f.write(file_bytes)

    # Determine MIME type and Google Drive conversion flag
    # For DOCX/DOC/TXT, converting to Google Doc preserves all layouts, hyperlinks, fonts & tables
    convert_to_doc = file_kind in ["docx", "doc", "txt"]
    if file_kind == "docx":
        upload_mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif file_kind == "doc":
        upload_mime = "application/msword"
    elif file_kind == "txt":
        upload_mime = "text/plain"
    else:
        upload_mime = "application/pdf"

    drive_file_id = None
    drive_view_link = None
    stored_path = local_path

    try:
        drive_res = drive_service.upload_to_drive(
            file_bytes=file_bytes,
            filename=f"{candidate_name}_{saved_filename}",
            mime_type=upload_mime,
            convert_to_doc=convert_to_doc
        )
        drive_file_id = drive_res.get("id")
        drive_view_link = drive_res.get("web_view_link")
        
        # If successfully uploaded to Drive, remove local buffer (or keep if desired)
        if drive_file_id and os.path.exists(local_path):
            os.remove(local_path)
            stored_path = None
    except Exception as e:
        logger.warning(f"[ResumeUpload] Google Drive upload failed/token expired ({e}). Storing file locally.")
        drive_file_id = None
        drive_view_link = None
        stored_path = local_path

    document = {
        "_id": candidate_id,
        "file_hash": file_hash,
        "file_name": file.filename or saved_filename,
        "file_kind": file_kind,
        "drive_file_id": drive_file_id,
        "drive_view_link": drive_view_link,
        "pdf_path": stored_path,
        "name": candidate_name,
        "age": parsed.get("age", "Not specified"),
        "experience": parsed.get("experience", "fresher"),
        "skills": parsed.get("skills", []),
        "role": parsed.get("role", "Not specified"),
        "job_roles": parsed.get("job_roles", []),
        "recommended_jobs": recommended_jobs,
        "resume_text": resume_text,
        "created_at": datetime.datetime.utcnow(),
    }

    result = resume_collection.insert_one(document)
    document["id"] = str(result.inserted_id)
    document.pop("_id", None)
    return document


# Note: this route path doesn't start with /resume prefix because the original was /resumes.
# So we add a separate router or specify path explicitly.
resumes_router = APIRouter(tags=["Resume"])

@resumes_router.get("/resumes")
def get_all_resumes(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    skip = (page - 1) * limit
    total = resume_collection.count_documents({})
    documents = [_serialize(d) for d in resume_collection.find({}).sort("created_at", -1).skip(skip).limit(limit)]
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "candidates": documents,
    }


@router.get("/{id}")
def get_resume(id: str) -> dict[str, Any]:
    document = resume_collection.find_one({"_id": _get_object_id(id)})
    if not document:
        raise _error(404, "Resume not found.", "not_found")
    return _serialize(document)


@router.patch("/{id}")
def update_resume(id: str, updates: UpdateCandidateRequest) -> dict[str, Any]:
    oid = _get_object_id(id)
    document = resume_collection.find_one({"_id": oid})
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
        return _serialize(document)

    update_data["updated_at"] = datetime.datetime.utcnow()
    resume_collection.update_one({"_id": oid}, {"$set": update_data})

    updated = resume_collection.find_one({"_id": oid})
    return _serialize(updated)  # type: ignore[return-value]


@router.delete("/{id}")
def delete_resume(id: str) -> dict[str, str]:
    document = resume_collection.find_one({"_id": _get_object_id(id)})
    if not document:
        raise _error(404, "Resume not found.", "not_found")
        
    result = resume_collection.delete_one({"_id": _get_object_id(id)})
    if result.deleted_count > 0:
        drive_file_id = document.get("drive_file_id")
        if drive_file_id:
            drive_service.delete_from_drive(drive_file_id)
            
        pdf_path = document.get("pdf_path")
        if pdf_path and os.path.exists(pdf_path):
            os.remove(pdf_path)
            
    return {"message": "Resume deleted successfully."}

@router.get("/{id}/download")
def download_resume(id: str):
    document = resume_collection.find_one({"_id": _get_object_id(id)})
    if not document:
        raise _error(404, "Resume not found.", "not_found")
        
    safe_name = document.get('name', 'Resume').replace(' ', '_')
    drive_file_id = document.get("drive_file_id")
    
    if drive_file_id:
        try:
            file_stream = drive_service.download_from_drive(drive_file_id)
            return StreamingResponse(
                file_stream, 
                media_type="application/pdf", 
                headers={"Content-Disposition": f"attachment; filename=\"{safe_name}_Resume.pdf\""}
            )
        except Exception as e:
            logger.warning(f"[ResumeDownload] Failed to stream from Google Drive ({e}). Falling back to local/generated PDF.")
        
    pdf_path = document.get("pdf_path")
    if pdf_path and os.path.exists(pdf_path):
        return FileResponse(pdf_path, media_type="application/pdf", filename=f"{safe_name}_Resume.pdf")

    # Generate on the fly using FPDF from resume_text
    resume_text = document.get("resume_text", "")
    if resume_text:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", size=12)
        clean_text = resume_text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, txt=clean_text)
        pdf_bytes = bytes(pdf.output())
        import io
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=\"{safe_name}_Resume.pdf\""}
        )
        
    raise _error(404, "Resume content not available for download.", "not_found")


@router.get("/{id}/recommend")
def refresh_recommendations(id: str) -> dict[str, Any]:
    oid = _get_object_id(id)
    document = resume_collection.find_one({"_id": oid})
    if not document:
        raise _error(404, "Resume not found.", "not_found")

    recommended_jobs = ai_recommend_jobs(document)
    resume_collection.update_one(
        {"_id": oid},
        {"$set": {"recommended_jobs": recommended_jobs}},
    )
    return {"id": id, "recommended_jobs": recommended_jobs}
