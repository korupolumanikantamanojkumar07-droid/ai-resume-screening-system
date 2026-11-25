from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..datasets.loader import get_taxonomy_from_db
from ..database import get_db
from ..models import Candidate, JobDescription, Resume, ScreeningResult
from ..schemas import ScreeningRunRequest, ScreeningStatusUpdate
from ..scoring.ranker import score_candidate_for_job
from ..services import (
    display_candidate_identity,
    get_candidate_skills_list,
    get_privacy_settings,
    get_scoring_weights,
)

router = APIRouter(tags=["Screening & Candidates"])


@router.post("/screening/run")
def run_ai_screening(payload: ScreeningRunRequest, db: Session = Depends(get_db)):
    job = db.query(JobDescription).filter(JobDescription.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job description not found.")

    weights = payload.weights.model_dump() if payload.weights else get_scoring_weights(db)
    taxonomy = get_taxonomy_from_db(db)
    privacy = get_privacy_settings(db)

    q = (
        db.query(Candidate, Resume)
        .join(Resume, Candidate.resume_id == Resume.id)
        .filter(Resume.processing_status == "completed")
    )
    if payload.resume_ids:
        q = q.filter(Resume.id.in_(payload.resume_ids))

    rows = q.all()
    if not rows:
        raise HTTPException(status_code=400, detail="No processed resumes found to screen.")

    job_data = {
        "title": job.title,
        "description": job.description,
        "required_skills": job.required_skills_json or [],
        "preferred_skills": job.preferred_skills_json or [],
        "min_experience_years": job.min_experience_years,
        "education_requirement": job.education_requirement,
        "embedding": job.embedding_json,
    }

    computed: list[tuple[Candidate, Resume, dict]] = []
    for cand, res in rows:
        skills_list = get_candidate_skills_list(db, cand.id)
        cand_data = {
            "skills": [s["name"] for s in skills_list],
            "total_experience_years": cand.total_experience_years,
            "education_level": cand.education_level,
            "cleaned_text": res.cleaned_text,
            "embedding": cand.embedding_json,
        }
        scored = score_candidate_for_job(cand_data, job_data, weights=weights, taxonomy=taxonomy)
        computed.append((cand, res, scored))

    # Deterministic ranking order
    computed.sort(
        key=lambda item: (
            -item[2]["overall_score"],
            -item[2]["required_skill_score"],
            -item[2]["semantic_similarity_score"],
            item[0].id,
        )
    )

    saved_items = []
    for rank, (cand, res, sc) in enumerate(computed, start=1):
        sr = (
            db.query(ScreeningResult)
            .filter(ScreeningResult.job_id == job.id, ScreeningResult.candidate_id == cand.id)
            .first()
        )
        if not sr:
            sr = ScreeningResult(job_id=job.id, candidate_id=cand.id)
            db.add(sr)

        sr.overall_score = sc["overall_score"]
        sr.required_skill_score = sc["required_skill_score"]
        sr.preferred_skill_score = sc["preferred_skill_score"]
        sr.semantic_similarity_score = sc["semantic_similarity_score"]
        sr.tfidf_similarity_score = sc["tfidf_similarity_score"]
        sr.experience_score = sc["experience_score"]
        sr.education_score = sc["education_score"]
        sr.matched_skills_json = sc["matched_skills"]
        sr.missing_skills_json = sc["missing_skills"]
        sr.matched_preferred_json = sc["matched_preferred"]
        sr.explanation_json = sc["explanation"]
        sr.weights_used_json = sc["weights_used"]
        sr.rank_position = rank
        if sr.screening_status not in ("shortlisted", "rejected"):
            sr.screening_status = "shortlisted" if sc["overall_score"] >= 75.0 else "screened"

        db.flush()
        ident = display_candidate_identity(cand, privacy)
        saved_items.append({
            "id": sr.id,
            "job_id": job.id,
            "candidate_id": cand.id,
            "resume_id": res.id,
            "rank_position": rank,
            "candidate_name": ident["display_name"],
            "anonymous_id": cand.anonymous_id,
            "source_type": res.source_type,
            "overall_score": sr.overall_score,
            "required_skill_score": sr.required_skill_score,
            "preferred_skill_score": sr.preferred_skill_score,
            "semantic_similarity_score": sr.semantic_similarity_score,
            "tfidf_similarity_score": sr.tfidf_similarity_score,
            "experience_score": sr.experience_score,
            "education_score": sr.education_score,
            "matched_skills": sr.matched_skills_json,
            "missing_skills": sr.missing_skills_json,
            "matched_preferred": sr.matched_preferred_json,
            "experience_years": cand.total_experience_years,
            "education_level": cand.education_level,
            "screening_status": sr.screening_status,
            "explanation": sr.explanation_json,
        })

    # Re-normalize ranks across ALL existing screening results for this job if only a subset was screened
    all_job_srs = (
        db.query(ScreeningResult)
        .filter(ScreeningResult.job_id == job.id)
        .order_by(
            ScreeningResult.overall_score.desc(),
            ScreeningResult.required_skill_score.desc(),
            ScreeningResult.semantic_similarity_score.desc(),
            ScreeningResult.candidate_id.asc(),
        )
        .all()
    )
    for idx, sr_row in enumerate(all_job_srs, start=1):
        sr_row.rank_position = idx

    db.commit()
    return {
        "job_id": job.id,
        "job_title": job.title,
        "screened_count": len(saved_items),
        "weights_used": weights,
        "results": saved_items,
    }


@router.get("/screening/results")
def list_screening_results(
    job_id: Optional[int] = None,
    min_score: float = Query(0.0, ge=0.0, le=100.0),
    skill: Optional[str] = None,
    min_experience: float = Query(0.0, ge=0.0),
    education_level: Optional[str] = None,
    source_type: str = Query("all", pattern="^(all|uploaded|public_dataset|synthetic_demo)$"),
    status: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query("overall_score"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    privacy = get_privacy_settings(db)
    q = (
        db.query(ScreeningResult, Candidate, Resume, JobDescription)
        .join(Candidate, ScreeningResult.candidate_id == Candidate.id)
        .join(Resume, Candidate.resume_id == Resume.id)
        .join(JobDescription, ScreeningResult.job_id == JobDescription.id)
    )
    if job_id:
        q = q.filter(ScreeningResult.job_id == job_id)
    if min_score > 0:
        q = q.filter(ScreeningResult.overall_score >= min_score)
    if min_experience > 0:
        q = q.filter(Candidate.total_experience_years >= min_experience)
    if education_level and education_level != "all":
        q = q.filter(Candidate.education_level == education_level)
    if source_type != "all":
        q = q.filter(Resume.source_type == source_type)
    if status and status != "all":
        q = q.filter(ScreeningResult.screening_status == status)

    rows = q.all()
    items = []
    skill_lower = skill.strip().lower() if skill and skill.strip() else None
    search_lower = search.strip().lower() if search and search.strip() else None

    for sr, cand, res, job in rows:
        cand_skills = get_candidate_skills_list(db, cand.id)
        cand_skill_names = [s["name"] for s in cand_skills]
        if skill_lower and not any(skill_lower in s.lower() for s in cand_skill_names):
            continue
        ident = display_candidate_identity(cand, privacy)
        if search_lower:
            haystack = f"{ident['display_name']} {cand.anonymous_id} {job.title} {' '.join(cand_skill_names)}".lower()
            if search_lower not in haystack:
                continue

        items.append({
            "id": sr.id,
            "job_id": job.id,
            "job_title": job.title,
            "candidate_id": cand.id,
            "resume_id": res.id,
            "filename": res.filename,
            "source_type": res.source_type,
            "dataset_category": res.dataset_category,
            "rank_position": sr.rank_position,
            "candidate_name": ident["display_name"],
            "anonymous_id": cand.anonymous_id,
            "overall_score": sr.overall_score,
            "required_skill_score": sr.required_skill_score,
            "preferred_skill_score": sr.preferred_skill_score,
            "semantic_similarity_score": sr.semantic_similarity_score,
            "tfidf_similarity_score": sr.tfidf_similarity_score,
            "experience_score": sr.experience_score,
            "education_score": sr.education_score,
            "matched_skills": sr.matched_skills_json or [],
            "missing_skills": sr.missing_skills_json or [],
            "matched_preferred": sr.matched_preferred_json or [],
            "all_skills": cand_skill_names,
            "experience_years": cand.total_experience_years,
            "education_level": cand.education_level,
            "screening_status": sr.screening_status,
            "explanation": sr.explanation_json or {},
            "screened_at": sr.screened_at,
        })

    reverse = sort_dir == "desc"
    sort_key_map = {
        "overall_score": lambda x: x["overall_score"],
        "rank_position": lambda x: x["rank_position"],
        "experience_years": lambda x: x["experience_years"],
        "semantic_similarity_score": lambda x: x["semantic_similarity_score"],
        "required_skill_score": lambda x: x["required_skill_score"],
    }
    key_fn = sort_key_map.get(sort_by, sort_key_map["overall_score"])
    items.sort(key=key_fn, reverse=reverse)
    return {"items": items, "total": len(items)}


@router.patch("/screening/results/{result_id}/status")
def update_screening_status(result_id: int, payload: ScreeningStatusUpdate, db: Session = Depends(get_db)):
    sr = db.query(ScreeningResult).filter(ScreeningResult.id == result_id).first()
    if not sr:
        raise HTTPException(status_code=404, detail="Screening result not found.")
    sr.screening_status = payload.screening_status
    db.commit()
    return {"id": sr.id, "screening_status": sr.screening_status}


@router.get("/candidates/{candidate_id}")
def get_candidate_profile(candidate_id: int, db: Session = Depends(get_db)):
    cand = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    res = cand.resume
    privacy = get_privacy_settings(db)
    ident = display_candidate_identity(cand, privacy)
    skills = get_candidate_skills_list(db, cand.id)

    sr_rows = (
        db.query(ScreeningResult, JobDescription)
        .join(JobDescription, ScreeningResult.job_id == JobDescription.id)
        .filter(ScreeningResult.candidate_id == cand.id)
        .order_by(ScreeningResult.overall_score.desc())
        .all()
    )
    evaluations = [
        {
            "screening_id": sr.id,
            "job_id": job.id,
            "job_title": job.title,
            "department": job.department,
            "rank_position": sr.rank_position,
            "overall_score": sr.overall_score,
            "required_skill_score": sr.required_skill_score,
            "preferred_skill_score": sr.preferred_skill_score,
            "semantic_similarity_score": sr.semantic_similarity_score,
            "tfidf_similarity_score": sr.tfidf_similarity_score,
            "experience_score": sr.experience_score,
            "education_score": sr.education_score,
            "matched_skills": sr.matched_skills_json or [],
            "missing_skills": sr.missing_skills_json or [],
            "matched_preferred": sr.matched_preferred_json or [],
            "explanation": sr.explanation_json or {},
            "weights_used": sr.weights_used_json or {},
            "screening_status": sr.screening_status,
            "screened_at": sr.screened_at,
        }
        for sr, job in sr_rows
    ]

    return {
        "id": cand.id,
        "resume_id": res.id,
        "filename": res.filename,
        "source_type": res.source_type,
        "dataset_name": res.dataset_name,
        "dataset_category": res.dataset_category,
        "ocr_used": res.ocr_used,
        "display_name": ident["display_name"],
        "anonymous_id": cand.anonymous_id,
        "anonymized": ident["anonymized"],
        "email": ident["email"],
        "phone": ident["phone"],
        "location": cand.location,
        "total_experience_years": cand.total_experience_years,
        "experience_summary": cand.experience_summary,
        "education_level": cand.education_level,
        "degree": cand.degree,
        "university": cand.university,
        "graduation_year": cand.graduation_year,
        "education": cand.education_json or [],
        "work_experience": cand.work_experience_json or [],
        "projects": cand.projects_json or [],
        "certifications": cand.certifications_json or [],
        "soft_skills": cand.soft_skills_json or [],
        "programming_languages": cand.programming_languages_json or [],
        "tools_technologies": cand.tools_technologies_json or [],
        "key_phrases": cand.key_phrases_json or [],
        "skills": skills,
        "evaluations": evaluations,
        "cleaned_text_preview": (res.cleaned_text or "")[:3000],
    }
