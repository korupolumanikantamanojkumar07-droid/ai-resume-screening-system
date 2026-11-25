from typing import Any, Optional

from ..config import settings
from ..nlp.embeddings import compute_tfidf_similarity, cosine_sim_vectors, embed_single
from ..nlp.ner_parser import DEGREE_RANK
from ..nlp.taxonomy import normalize_skill_name


def _score_skill_list(required: list[str], candidate_skills: set[str], taxonomy: Optional[list[dict]] = None) -> tuple[float, list[str], list[str]]:
    if not required:
        return 100.0, [], []
    matched: list[str] = []
    missing: list[str] = []
    cand_lower = {s.lower(): s for s in candidate_skills}

    for req in required:
        canon = normalize_skill_name(req, taxonomy)
        if canon.lower() in cand_lower or req.lower() in cand_lower:
            matched.append(canon)
        else:
            missing.append(canon)

    # Deduplicate preserving order
    matched = list(dict.fromkeys(matched))
    missing = list(dict.fromkeys(missing))
    total = len(matched) + len(missing)
    pct = (len(matched) / total) * 100.0 if total > 0 else 100.0
    return round(pct, 2), matched, missing


def _score_experience(candidate_years: float, required_years: float) -> tuple[float, str]:
    if required_years <= 0:
        score = min(100.0, 75.0 + min(25.0, candidate_years * 5.0))
        return round(score, 2), f"{candidate_years:.1f} yrs found (no minimum required)"
    ratio = candidate_years / required_years
    if ratio >= 1.0:
        # Exceeding gets full marks (100) without penalizing seniority
        return 100.0, f"{candidate_years:.1f} yrs meets/exceeds {required_years:.1f} yrs requirement"
    score = max(0.0, min(99.0, ratio * 100.0))
    return round(score, 2), f"{candidate_years:.1f} yrs vs {required_years:.1f} yrs required ({ratio * 100:.0f}%)"


def _score_education(candidate_level: str, required_level: str) -> tuple[float, str]:
    req_rank = DEGREE_RANK.get(required_level or "Unspecified", 0)
    cand_rank = DEGREE_RANK.get(candidate_level or "Unspecified", 0)
    if req_rank == 0:
        return (100.0 if cand_rank > 0 else 75.0), f"Candidate: {candidate_level} (No strict requirement)"
    if cand_rank >= req_rank:
        return 100.0, f"{candidate_level} meets/exceeds {required_level}"
    if cand_rank == 0:
        return 35.0, f"Education level not explicitly detected (Expected {required_level})"
    diff = req_rank - cand_rank
    score = max(40.0, 100.0 - diff * 30.0)
    return round(score, 2), f"{candidate_level} vs {required_level} required"


def score_candidate_for_job(
    candidate_data: dict[str, Any],
    job_data: dict[str, Any],
    weights: Optional[dict[str, float]] = None,
    taxonomy: Optional[list[dict]] = None,
) -> dict[str, Any]:
    """
    Deterministic, explainable candidate scoring engine.
    Protected attributes (age, gender, religion, caste, photo, nationality) are NEVER used.
    Score is decision-support information out of 100, not a guarantee of job performance.
    """
    w = dict(weights or settings.DEFAULT_WEIGHTS)
    total_w = sum(w.values()) or 100.0
    norm_w = {k: (v / total_w) * 100.0 for k, v in w.items()}

    cand_skills = set(candidate_data.get("skills", []))
    req_skills = job_data.get("required_skills", [])
    pref_skills = job_data.get("preferred_skills", [])

    req_score, matched_req, missing_req = _score_skill_list(req_skills, cand_skills, taxonomy)
    pref_score, matched_pref, missing_pref = _score_skill_list(pref_skills, cand_skills, taxonomy)

    cand_emb = candidate_data.get("embedding")
    job_emb = job_data.get("embedding")
    if not cand_emb and candidate_data.get("cleaned_text"):
        cand_emb = embed_single(candidate_data["cleaned_text"][:3500])
    if not job_emb and job_data.get("description"):
        job_emb = embed_single(f"{job_data.get('title', '')}\n{job_data['description'][:3500]}")

    raw_sem_sim = cosine_sim_vectors(cand_emb, job_emb)
    tfidf_sim = compute_tfidf_similarity(
        candidate_data.get("cleaned_text", ""),
        f"{job_data.get('title', '')} {job_data.get('description', '')}",
    )
    # Combined semantic score (scaled meaningfully from cosine sim [0.15..0.85] -> [0..100], deterministic)
    semantic_score = round(min(100.0, max(0.0, (raw_sem_sim * 0.85 + tfidf_sim * 0.15) * 115.0)), 2)

    exp_score, exp_note = _score_experience(
        float(candidate_data.get("total_experience_years", 0.0)),
        float(job_data.get("min_experience_years", 0.0)),
    )
    edu_score, edu_note = _score_education(
        candidate_data.get("education_level", "Unspecified"),
        job_data.get("education_requirement", "Unspecified"),
    )

    overall = (
        req_score * (norm_w["required_skills"] / 100.0)
        + semantic_score * (norm_w["semantic_similarity"] / 100.0)
        + exp_score * (norm_w["experience_match"] / 100.0)
        + edu_score * (norm_w["education_match"] / 100.0)
        + pref_score * (norm_w["preferred_skills"] / 100.0)
    )
    overall = round(min(100.0, max(0.0, overall)), 2)

    explanation = {
        "decision_support_notice": (
            "This compatibility score is deterministic decision-support metadata derived solely from skills, "
            "experience, education, and semantic text alignment. No protected characteristics are used."
        ),
        "contributions": {
            "required_skills": round(req_score * (norm_w["required_skills"] / 100.0), 2),
            "semantic_similarity": round(semantic_score * (norm_w["semantic_similarity"] / 100.0), 2),
            "experience_match": round(exp_score * (norm_w["experience_match"] / 100.0), 2),
            "education_match": round(edu_score * (norm_w["education_match"] / 100.0), 2),
            "preferred_skills": round(pref_score * (norm_w["preferred_skills"] / 100.0), 2),
        },
        "experience_note": exp_note,
        "education_note": edu_note,
        "raw_cosine_similarity": round(raw_sem_sim, 4),
        "tfidf_cosine_similarity": round(tfidf_sim, 4),
        "missing_preferred_skills": missing_pref,
    }

    return {
        "overall_score": overall,
        "required_skill_score": req_score,
        "preferred_skill_score": pref_score,
        "semantic_similarity_score": semantic_score,
        "tfidf_similarity_score": round(tfidf_sim * 100.0, 2),
        "experience_score": exp_score,
        "education_score": edu_score,
        "matched_skills": matched_req,
        "missing_skills": missing_req,
        "matched_preferred": matched_pref,
        "explanation": explanation,
        "weights_used": norm_w,
    }
