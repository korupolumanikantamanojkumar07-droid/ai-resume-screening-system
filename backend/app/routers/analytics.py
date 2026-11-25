from collections import Counter
from statistics import median
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Candidate, CandidateSkill, Resume, ScreeningResult, Skill

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview")
def get_analytics_overview(job_id: Optional[int] = None, db: Session = Depends(get_db)):
    sr_q = db.query(ScreeningResult)
    if job_id:
        sr_q = sr_q.filter(ScreeningResult.job_id == job_id)
    screenings = sr_q.all()

    scores = [sr.overall_score for sr in screenings]
    bins = [
        {"range": "0-20%", "min": 0, "max": 20, "count": 0},
        {"range": "20-40%", "min": 20, "max": 40, "count": 0},
        {"range": "40-60%", "min": 40, "max": 60, "count": 0},
        {"range": "60-80%", "min": 60, "max": 80, "count": 0},
        {"range": "80-100%", "min": 80, "max": 101, "count": 0},
    ]
    for sc in scores:
        for b in bins:
            if b["min"] <= sc < b["max"]:
                b["count"] += 1
                break

    score_distribution = [{"range": b["range"], "count": b["count"]} for b in bins]

    # Most common skills across all candidates
    common_skill_rows = (
        db.query(Skill.name, Skill.category, func.count(CandidateSkill.id).label("cnt"))
        .join(CandidateSkill, Skill.id == CandidateSkill.skill_id)
        .group_by(Skill.id)
        .order_by(func.count(CandidateSkill.id).desc())
        .limit(12)
        .all()
    )
    most_common_skills = [
        {"skill": name, "category": cat, "count": int(cnt)}
        for name, cat, cnt in common_skill_rows
    ]

    # Missing skills analysis from screening results
    missing_counter: Counter[str] = Counter()
    matched_counter: Counter[str] = Counter()
    for sr in screenings:
        for ms in (sr.missing_skills_json or []):
            missing_counter[ms] += 1
        for mt in (sr.matched_skills_json or []):
            matched_counter[mt] += 1

    missing_skills_analysis = [
        {"skill": k, "missing_count": v, "matched_count": matched_counter.get(k, 0)}
        for k, v in missing_counter.most_common(10)
    ]

    # Experience distribution across candidates
    candidates = db.query(Candidate).all()
    exp_buckets = Counter({"0-1 yrs": 0, "1-3 yrs": 0, "3-5 yrs": 0, "5-10 yrs": 0, "10+ yrs": 0})
    edu_counter: Counter[str] = Counter()
    for c in candidates:
        y = c.total_experience_years or 0.0
        if y < 1:
            exp_buckets["0-1 yrs"] += 1
        elif y < 3:
            exp_buckets["1-3 yrs"] += 1
        elif y < 5:
            exp_buckets["3-5 yrs"] += 1
        elif y < 10:
            exp_buckets["5-10 yrs"] += 1
        else:
            exp_buckets["10+ yrs"] += 1
        edu_counter[c.education_level or "Unspecified"] += 1

    experience_distribution = [{"bucket": k, "count": v} for k, v in exp_buckets.items()]
    education_distribution = [{"level": k, "count": v} for k, v in edu_counter.most_common()]

    # Source breakdown
    uploaded_cnt = db.query(Resume).filter(Resume.source_type == "uploaded").count()
    dataset_cnt = db.query(Resume).filter(Resume.source_type == "public_dataset").count()

    # Ranking statistics
    if scores:
        sorted_scores = sorted(scores)
        p90_idx = min(len(sorted_scores) - 1, int(0.9 * len(sorted_scores)))
        ranking_stats = {
            "total_screened": len(scores),
            "mean_score": round(sum(scores) / len(scores), 2),
            "median_score": round(float(median(scores)), 2),
            "min_score": round(min(scores), 2),
            "max_score": round(max(scores), 2),
            "p90_score": round(sorted_scores[p90_idx], 2),
            "shortlisted_count": sum(1 for sr in screenings if sr.screening_status == "shortlisted"),
        }
    else:
        ranking_stats = {
            "total_screened": 0,
            "mean_score": 0.0,
            "median_score": 0.0,
            "min_score": 0.0,
            "max_score": 0.0,
            "p90_score": 0.0,
            "shortlisted_count": 0,
        }

    return {
        "score_distribution": score_distribution,
        "most_common_skills": most_common_skills,
        "missing_skills_analysis": missing_skills_analysis,
        "experience_distribution": experience_distribution,
        "education_distribution": education_distribution,
        "source_breakdown": [
            {"source": "Uploaded Resumes", "count": uploaded_cnt},
            {"source": "Public Dataset Resumes", "count": dataset_cnt},
        ],
        "ranking_stats": ranking_stats,
    }
