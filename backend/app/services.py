from typing import Any
from sqlalchemy.orm import Session

from .config import settings
from .models import AppSetting, Candidate, CandidateSkill, Resume, Skill, User
from .nlp.taxonomy import DEFAULT_SKILL_TAXONOMY


def seed_defaults(db: Session) -> None:
    """Ensure default recruiter user, skill taxonomy, and app settings exist."""
    if not db.query(User).filter(User.email == "recruiter@resumescreening.ai").first():
        db.add(
            User(
                email="recruiter@resumescreening.ai",
                full_name="Lead Technical Recruiter",
                role="recruiter",
                organization="AI-Based Resume Screening System",
            )
        )

    existing_skills = {s.name for s in db.query(Skill.name).all()}
    for item in DEFAULT_SKILL_TAXONOMY:
        if item["name"] not in existing_skills:
            db.add(
                Skill(
                    name=item["name"],
                    category=item["category"],
                    synonyms_json=item.get("synonyms", []),
                    is_custom=False,
                )
            )

    if not db.query(AppSetting).filter(AppSetting.key == "scoring_weights").first():
        db.add(AppSetting(key="scoring_weights", value_json=settings.DEFAULT_WEIGHTS))

    if not db.query(AppSetting).filter(AppSetting.key == "privacy_retention").first():
        db.add(
            AppSetting(
                key="privacy_retention",
                value_json={
                    "anonymize_candidates": False,
                    "mask_contact_info": True,
                    "file_retention_days": 90,
                },
            )
        )

    db.commit()


def get_scoring_weights(db: Session) -> dict[str, float]:
    row = db.query(AppSetting).filter(AppSetting.key == "scoring_weights").first()
    if row and isinstance(row.value_json, dict):
        return {k: float(v) for k, v in row.value_json.items()}
    return dict(settings.DEFAULT_WEIGHTS)


def get_privacy_settings(db: Session) -> dict[str, Any]:
    row = db.query(AppSetting).filter(AppSetting.key == "privacy_retention").first()
    if row and isinstance(row.value_json, dict):
        return row.value_json
    return {"anonymize_candidates": False, "mask_contact_info": True, "file_retention_days": 90}


def get_candidate_skills_list(db: Session, candidate_id: int) -> list[dict[str, Any]]:
    rows = (
        db.query(CandidateSkill, Skill)
        .join(Skill, CandidateSkill.skill_id == Skill.id)
        .filter(CandidateSkill.candidate_id == candidate_id)
        .all()
    )
    return [
        {
            "id": sk.id,
            "name": sk.name,
            "category": sk.category,
            "match_method": cs.match_method,
            "confidence": cs.confidence,
        }
        for cs, sk in rows
    ]


def display_candidate_identity(candidate: Candidate, privacy: dict[str, Any]) -> dict[str, Any]:
    anonymize = bool(privacy.get("anonymize_candidates", False))
    mask_contact = bool(privacy.get("mask_contact_info", True))

    name = candidate.anonymous_id if anonymize else (candidate.full_name or candidate.anonymous_id)
    if anonymize:
        email = "[Hidden for blind review]"
        phone = "[Hidden for blind review]"
    elif mask_contact:
        email = _mask_email(candidate.email) if candidate.email else None
        phone = _mask_phone(candidate.phone) if candidate.phone else None
    else:
        email = candidate.email
        phone = candidate.phone

    return {
        "display_name": name,
        "anonymous_id": candidate.anonymous_id,
        "email": email,
        "phone": phone,
        "anonymized": anonymize,
    }


def _mask_email(email: str) -> str:
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        return f"**@{domain}"
    return f"{local[:2]}***@{domain}"


def _mask_phone(phone: str) -> str:
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) < 4:
        return "***"
    return f"***-***-{digits[-4:]}"
