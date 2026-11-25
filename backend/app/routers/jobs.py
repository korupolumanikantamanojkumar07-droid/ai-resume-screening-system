from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..datasets.loader import get_taxonomy_from_db
from ..database import get_db
from ..models import JobDescription
from ..nlp.embeddings import embed_single
from ..nlp.jd_analyzer import analyze_job_description
from ..nlp.taxonomy import normalize_skill_name
from ..schemas import JobAnalyzeRequest, JobDescriptionCreate, JobDescriptionUpdate

router = APIRouter(prefix="/jobs", tags=["Job Descriptions"])


def _serialize_job(j: JobDescription) -> dict:
    return {
        "id": j.id,
        "title": j.title,
        "department": j.department,
        "description": j.description,
        "required_skills": j.required_skills_json or [],
        "preferred_skills": j.preferred_skills_json or [],
        "min_experience_years": j.min_experience_years,
        "education_requirement": j.education_requirement,
        "additional_qualifications": j.additional_qualifications,
        "auto_extracted": j.auto_extracted_json or {},
        "source_type": j.source_type,
        "status": j.status,
        "created_at": j.created_at,
        "updated_at": j.updated_at,
    }


@router.get("")
def list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(JobDescription).order_by(JobDescription.created_at.desc()).all()
    return {"items": [_serialize_job(j) for j in jobs], "total": len(jobs)}


@router.post("/analyze")
def analyze_job_preview(payload: JobAnalyzeRequest, db: Session = Depends(get_db)):
    taxonomy = get_taxonomy_from_db(db)
    analyzed = analyze_job_description(payload.title, payload.description, taxonomy=taxonomy)
    analyzed.pop("embedding", None)
    return analyzed


@router.post("")
def create_job(payload: JobDescriptionCreate, db: Session = Depends(get_db)):
    taxonomy = get_taxonomy_from_db(db)
    analyzed = analyze_job_description(payload.title, payload.description, taxonomy=taxonomy) if payload.auto_extract else {}

    req_skills = [normalize_skill_name(s, taxonomy) for s in payload.required_skills if s.strip()]
    if not req_skills and analyzed.get("required_skills"):
        req_skills = analyzed["required_skills"]
    else:
        req_skills = list(dict.fromkeys(req_skills))

    pref_skills = [normalize_skill_name(s, taxonomy) for s in payload.preferred_skills if s.strip()]
    if not pref_skills and analyzed.get("preferred_skills"):
        pref_skills = [s for s in analyzed["preferred_skills"] if s not in req_skills]
    else:
        pref_skills = list(dict.fromkeys(s for s in pref_skills if s not in req_skills))

    min_exp = payload.min_experience_years
    if min_exp == 0.0 and analyzed.get("min_experience_years"):
        min_exp = analyzed["min_experience_years"]

    edu_req = payload.education_requirement
    if (not edu_req or edu_req == "Unspecified") and analyzed.get("education_requirement"):
        edu_req = analyzed["education_requirement"]

    add_qual = payload.additional_qualifications or analyzed.get("additional_qualifications", "")
    embedding = analyzed.get("embedding") or embed_single(f"Job Title: {payload.title}\n{payload.description[:4000]}")
    if "embedding" in analyzed:
        analyzed = {k: v for k, v in analyzed.items() if k != "embedding"}

    job = JobDescription(
        title=payload.title.strip(),
        department=payload.department.strip(),
        description=payload.description.strip(),
        required_skills_json=req_skills,
        preferred_skills_json=pref_skills,
        min_experience_years=min_exp,
        education_requirement=edu_req,
        additional_qualifications=add_qual,
        auto_extracted_json=analyzed,
        embedding_json=embedding,
        source_type="custom",
        status="active",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return _serialize_job(job)


@router.put("/{job_id}")
def update_job(job_id: int, payload: JobDescriptionUpdate, db: Session = Depends(get_db)):
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job description not found.")

    taxonomy = get_taxonomy_from_db(db)
    if payload.title is not None:
        job.title = payload.title.strip()
    if payload.department is not None:
        job.department = payload.department.strip()
    if payload.description is not None:
        job.description = payload.description.strip()
    if payload.required_skills is not None:
        job.required_skills_json = list(dict.fromkeys(normalize_skill_name(s, taxonomy) for s in payload.required_skills if s.strip()))
    if payload.preferred_skills is not None:
        job.preferred_skills_json = list(dict.fromkeys(normalize_skill_name(s, taxonomy) for s in payload.preferred_skills if s.strip()))
    if payload.min_experience_years is not None:
        job.min_experience_years = payload.min_experience_years
    if payload.education_requirement is not None:
        job.education_requirement = payload.education_requirement
    if payload.additional_qualifications is not None:
        job.additional_qualifications = payload.additional_qualifications
    if payload.status is not None:
        job.status = payload.status

    job.embedding_json = embed_single(f"Job Title: {job.title}\n{job.description[:4000]}")
    db.commit()
    db.refresh(job)
    return _serialize_job(job)


@router.delete("/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job description not found.")
    db.delete(job)
    db.commit()
    return {"deleted": True, "job_id": job_id}
