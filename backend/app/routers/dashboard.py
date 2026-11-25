from collections import Counter
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Candidate, CandidateSkill, JobDescription, Resume, ScreeningResult, Skill
from ..services import display_candidate_identity, get_privacy_settings

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview")
def get_dashboard_overview(db: Session = Depends(get_db)):
    privacy = get_privacy_settings(db)
    total_resumes = db.query(Resume).count()
    uploaded_resumes = db.query(Resume).filter(Resume.source_type == "uploaded").count()
    dataset_resumes = db.query(Resume).filter(Resume.source_type == "public_dataset").count()
    total_candidates = db.query(Candidate).count()
    active_jobs = db.query(JobDescription).filter(JobDescription.status == "active").count()
    total_screenings = db.query(ScreeningResult).count()

    avg_score_raw = db.query(func.avg(ScreeningResult.overall_score)).scalar()
    avg_matching_score = round(float(avg_score_raw), 2) if avg_score_raw is not None else 0.0

    # Top ranked screenings
    top_rows = (
        db.query(ScreeningResult, Candidate, JobDescription, Resume)
        .join(Candidate, ScreeningResult.candidate_id == Candidate.id)
        .join(JobDescription, ScreeningResult.job_id == JobDescription.id)
        .join(Resume, Candidate.resume_id == Resume.id)
        .order_by(ScreeningResult.overall_score.desc(), ScreeningResult.screened_at.desc())
        .limit(8)
        .all()
    )
    ranking_overview = []
    for sr, cand, job, res in top_rows:
        ident = display_candidate_identity(cand, privacy)
        ranking_overview.append({
            "id": sr.id,
            "candidate_id": cand.id,
            "candidate_name": ident["display_name"],
            "anonymous_id": cand.anonymous_id,
            "job_id": job.id,
            "job_title": job.title,
            "overall_score": sr.overall_score,
            "rank_position": sr.rank_position,
            "screening_status": sr.screening_status,
            "source_type": res.source_type,
            "screened_at": sr.screened_at,
        })

    # Recent activity (latest screenings + uploads)
    recent_screenings = (
        db.query(ScreeningResult, Candidate, JobDescription)
        .join(Candidate, ScreeningResult.candidate_id == Candidate.id)
        .join(JobDescription, ScreeningResult.job_id == JobDescription.id)
        .order_by(ScreeningResult.screened_at.desc())
        .limit(6)
        .all()
    )
    recent_activity = []
    for sr, cand, job in recent_screenings:
        ident = display_candidate_identity(cand, privacy)
        recent_activity.append({
            "type": "screening",
            "title": f"Screened {ident['display_name']} for {job.title}",
            "score": sr.overall_score,
            "status": sr.screening_status,
            "timestamp": sr.screened_at,
        })

    recent_uploads = db.query(Resume).order_by(Resume.created_at.desc()).limit(4).all()
    for res in recent_uploads:
        recent_activity.append({
            "type": "upload" if res.source_type == "uploaded" else "dataset",
            "title": f"{'Uploaded' if res.source_type == 'uploaded' else 'Dataset loaded'}: {res.filename}",
            "score": None,
            "status": res.processing_status,
            "timestamp": res.created_at,
        })
    recent_activity.sort(key=lambda x: x["timestamp"], reverse=True)

    # Skills distribution
    skill_counts = (
        db.query(Skill.name, Skill.category, func.count(CandidateSkill.id).label("cnt"))
        .join(CandidateSkill, Skill.id == CandidateSkill.skill_id)
        .group_by(Skill.id)
        .order_by(func.count(CandidateSkill.id).desc())
        .limit(12)
        .all()
    )
    skills_distribution = [
        {"name": name, "category": cat, "count": int(cnt)} for name, cat, cnt in skill_counts
    ]

    # Dataset vs uploaded categories
    cat_rows = db.query(Resume.dataset_category, Resume.source_type).all()
    cat_counter: Counter[str] = Counter()
    for cat, src in cat_rows:
        if src == "synthetic_demo":
            label = "Synthetic Demo"
        elif cat:
            label = cat
        else:
            label = "Uploaded Resumes" if src == "uploaded" else "Uncategorized"
        cat_counter[label] += 1
    category_distribution = [
        {"category": k, "count": v} for k, v in cat_counter.most_common(10)
    ]

    return {
        "stats": {
            "total_resumes": total_resumes,
            "uploaded_resumes": uploaded_resumes,
            "dataset_resumes": dataset_resumes,
            "total_candidates": total_candidates,
            "active_jobs": active_jobs,
            "total_screenings": total_screenings,
            "average_matching_score": avg_matching_score,
        },
        "ranking_overview": ranking_overview,
        "recent_activity": recent_activity[:8],
        "skills_distribution": skills_distribution,
        "category_distribution": category_distribution,
    }
