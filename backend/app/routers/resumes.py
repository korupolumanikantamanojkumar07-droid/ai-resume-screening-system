import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from ..config import settings
from ..datasets.loader import _next_anonymous_id, ensure_skill_in_db, get_taxonomy_from_db
from ..database import get_db
from ..models import Candidate, CandidateSkill, Resume
from ..nlp.extractor import extract_resume_text, validate_upload_file
from ..nlp.pipeline import run_resume_nlp_pipeline
from ..services import display_candidate_identity, get_candidate_skills_list, get_privacy_settings

router = APIRouter(prefix="/resumes", tags=["Resumes"])


def _process_and_store_resume(
    db: Session,
    filename: str,
    content: bytes,
    existing_resume: Optional[Resume] = None,
) -> dict:
    ext, file_hash = validate_upload_file(filename, content)

    dup = db.query(Resume).filter(Resume.file_hash == file_hash).first()
    if dup and (existing_resume is None or dup.id != existing_resume.id):
        raise HTTPException(
            status_code=409,
            detail=f"Duplicate resume detected: '{filename}' matches existing file '{dup.filename}' (ID {dup.id}).",
        )

    extracted = extract_resume_text(filename, content)
    taxonomy = get_taxonomy_from_db(db)
    nlp_res = run_resume_nlp_pipeline(extracted["text"], taxonomy=taxonomy, enable_semantic_skills=True)
    entities = nlp_res["entities"]

    safe_name = f"{uuid.uuid4().hex[:12]}_{Path(filename).name}"
    stored_path = settings.UPLOAD_DIR / safe_name
    stored_path.write_bytes(content)

    if existing_resume is not None:
        # Remove old file if exists
        if existing_resume.stored_path and Path(existing_resume.stored_path).exists():
            try:
                Path(existing_resume.stored_path).unlink()
            except OSError:
                pass
        if existing_resume.candidate:
            db.delete(existing_resume.candidate)
            db.flush()
        resume = existing_resume
        resume.filename = Path(filename).name
        resume.stored_path = str(stored_path)
        resume.file_type = extracted["file_type"]
        resume.file_size = extracted["file_size"]
        resume.file_hash = file_hash
        resume.raw_text = extracted["text"]
        resume.cleaned_text = nlp_res["cleaned_text"]
        resume.ocr_used = extracted["ocr_used"]
        resume.processing_status = "completed"
        resume.error_message = None
    else:
        resume = Resume(
            filename=Path(filename).name,
            stored_path=str(stored_path),
            file_type=extracted["file_type"],
            file_size=extracted["file_size"],
            file_hash=file_hash,
            source_type="uploaded",
            dataset_name=None,
            dataset_category="Uploaded",
            raw_text=extracted["text"],
            cleaned_text=nlp_res["cleaned_text"],
            ocr_used=extracted["ocr_used"],
            processing_status="completed",
        )
        db.add(resume)
        db.flush()

    candidate = Candidate(
        resume_id=resume.id,
        anonymous_id=_next_anonymous_id(db, "CND"),
        full_name=entities.get("full_name"),
        email=entities.get("email"),
        phone=entities.get("phone"),
        location=entities.get("location"),
        total_experience_years=entities.get("total_experience_years", 0.0),
        experience_summary=entities.get("experience_summary", ""),
        education_level=entities.get("education_level", "Unspecified"),
        degree=entities.get("degree"),
        university=entities.get("university"),
        graduation_year=entities.get("graduation_year"),
        education_json=entities.get("education", []),
        work_experience_json=entities.get("work_experience", []),
        projects_json=entities.get("projects", []),
        certifications_json=entities.get("certifications", []),
        soft_skills_json=nlp_res.get("soft_skills", []),
        programming_languages_json=nlp_res.get("programming_languages", []),
        tools_technologies_json=nlp_res.get("tools_technologies", []),
        key_phrases_json=nlp_res.get("key_phrases", []),
        embedding_json=nlp_res.get("embedding"),
    )
    db.add(candidate)
    db.flush()

    seen_skill_ids = set()
    for match in nlp_res["skills"]:
        sk = ensure_skill_in_db(db, match.name, match.category)
        if sk.id not in seen_skill_ids:
            seen_skill_ids.add(sk.id)
            db.add(
                CandidateSkill(
                    candidate_id=candidate.id,
                    skill_id=sk.id,
                    match_method=match.match_method,
                    confidence=match.confidence,
                )
            )

    db.commit()
    db.refresh(resume)
    db.refresh(candidate)
    return {
        "resume_id": resume.id,
        "candidate_id": candidate.id,
        "filename": resume.filename,
        "anonymous_id": candidate.anonymous_id,
        "full_name": candidate.full_name,
        "skills_extracted": len(seen_skill_ids),
        "experience_years": candidate.total_experience_years,
        "education_level": candidate.education_level,
        "ocr_used": resume.ocr_used,
        "status": resume.processing_status,
    }


@router.post("/upload")
async def upload_resumes(files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    results = []
    errors = []
    for f in files:
        content = await f.read()
        try:
            res = _process_and_store_resume(db, f.filename or "resume.pdf", content)
            results.append(res)
        except HTTPException as exc:
            errors.append({"filename": f.filename, "error": exc.detail})
        except ValueError as exc:
            errors.append({"filename": f.filename, "error": str(exc)})
        except Exception as exc:
            db.rollback()
            errors.append({"filename": f.filename, "error": f"Processing failed: {exc}"})

    return {
        "uploaded": results,
        "errors": errors,
        "uploaded_count": len(results),
        "error_count": len(errors),
    }


@router.put("/{resume_id}/replace")
async def replace_resume(resume_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")
    content = await file.read()
    try:
        return _process_and_store_resume(db, file.filename or "resume.pdf", content, existing_resume=resume)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("")
def list_resumes(
    source_type: str = Query("all", pattern="^(all|uploaded|public_dataset|synthetic_demo)$"),
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
):
    privacy = get_privacy_settings(db)
    q = db.query(Resume).outerjoin(Candidate, Resume.id == Candidate.resume_id)
    if source_type != "all":
        q = q.filter(Resume.source_type == source_type)
    if category and category != "all":
        q = q.filter(Resume.dataset_category == category)
    if search:
        term = f"%{search.strip()}%"
        q = q.filter(
            (Resume.filename.ilike(term))
            | (Candidate.full_name.ilike(term))
            | (Candidate.anonymous_id.ilike(term))
            | (Resume.dataset_category.ilike(term))
        )

    resumes = q.order_by(Resume.source_type.desc(), Resume.created_at.desc()).limit(limit).all()
    items = []
    for r in resumes:
        cand = r.candidate
        skills = get_candidate_skills_list(db, cand.id) if cand else []
        ident = display_candidate_identity(cand, privacy) if cand else {"display_name": r.filename, "anonymous_id": None}
        items.append({
            "id": r.id,
            "filename": r.filename,
            "file_type": r.file_type,
            "file_size": r.file_size,
            "source_type": r.source_type,
            "dataset_name": r.dataset_name,
            "dataset_category": r.dataset_category,
            "ocr_used": r.ocr_used,
            "processing_status": r.processing_status,
            "error_message": r.error_message,
            "candidate_id": cand.id if cand else None,
            "candidate_name": ident["display_name"],
            "anonymous_id": ident["anonymous_id"],
            "skills_count": len(skills),
            "skills_preview": [s["name"] for s in skills[:6]],
            "experience_years": cand.total_experience_years if cand else 0.0,
            "education_level": cand.education_level if cand else "Unspecified",
            "created_at": r.created_at,
        })

    return {"items": items, "total": len(items)}


@router.delete("/{resume_id}")
def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")
    if resume.stored_path and Path(resume.stored_path).exists():
        try:
            Path(resume.stored_path).unlink()
        except OSError:
            pass
    db.delete(resume)
    db.commit()
    return {"deleted": True, "resume_id": resume_id}
