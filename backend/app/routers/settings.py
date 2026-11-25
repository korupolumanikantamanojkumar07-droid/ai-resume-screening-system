from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..datasets.inspector import inspect_all_datasets
from ..datasets.loader import load_initial_demo_dataset, load_public_datasets
from ..database import get_db
from ..models import AppSetting, DatasetBatch, Resume, Skill
from ..schemas import DatasetLoadRequest, PrivacyRetentionSettings, ScoringWeights, SkillCreate
from ..services import get_privacy_settings, get_scoring_weights

router = APIRouter(prefix="/settings", tags=["Settings & Datasets"])


@router.get("")
def get_all_settings(db: Session = Depends(get_db)):
    weights = get_scoring_weights(db)
    privacy = get_privacy_settings(db)
    skills = db.query(Skill).order_by(Skill.category.asc(), Skill.name.asc()).all()
    batches = db.query(DatasetBatch).all()
    raw_inspection = inspect_all_datasets()

    return {
        "scoring_weights": weights,
        "privacy_retention": privacy,
        "skills_taxonomy": [
            {
                "id": s.id,
                "name": s.name,
                "category": s.category,
                "synonyms": s.synonyms_json or [],
                "is_custom": s.is_custom,
            }
            for s in skills
        ],
        "dataset_batches": [
            {
                "dataset_key": b.dataset_key,
                "display_name": b.display_name,
                "source_url": b.source_url,
                "raw_row_count": b.raw_row_count,
                "duplicates_removed": b.duplicates_removed,
                "nulls_handled": b.nulls_handled,
                "loaded_count": b.loaded_count,
                "categories": b.categories_json or {},
                "columns": b.columns_json or [],
                "status": b.status,
                "loaded_at": b.loaded_at,
            }
            for b in batches
        ],
        "raw_dataset_inspection": raw_inspection,
    }


@router.put("/weights")
def update_scoring_weights(payload: ScoringWeights, db: Session = Depends(get_db)):
    row = db.query(AppSetting).filter(AppSetting.key == "scoring_weights").first()
    data = payload.model_dump()
    if not row:
        row = AppSetting(key="scoring_weights", value_json=data)
        db.add(row)
    else:
        row.value_json = data
    db.commit()
    return {"scoring_weights": data}


@router.put("/privacy")
def update_privacy_settings(payload: PrivacyRetentionSettings, db: Session = Depends(get_db)):
    row = db.query(AppSetting).filter(AppSetting.key == "privacy_retention").first()
    data = payload.model_dump()
    if not row:
        row = AppSetting(key="privacy_retention", value_json=data)
        db.add(row)
    else:
        row.value_json = data
    db.commit()
    return {"privacy_retention": data}


@router.post("/purge-expired")
def purge_expired_uploads(db: Session = Depends(get_db)):
    privacy = get_privacy_settings(db)
    days = int(privacy.get("file_retention_days", 90))
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    expired = db.query(Resume).filter(Resume.source_type == "uploaded", Resume.created_at < cutoff).all()
    removed = 0
    for r in expired:
        if r.stored_path and Path(r.stored_path).exists():
            try:
                Path(r.stored_path).unlink()
            except OSError:
                pass
        db.delete(r)
        removed += 1
    db.commit()
    return {"purged_count": removed, "retention_days": days}


@router.post("/skills")
def add_skill(payload: SkillCreate, db: Session = Depends(get_db)):
    existing = db.query(Skill).filter(Skill.name.ilike(payload.name.strip())).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Skill '{existing.name}' already exists.")
    sk = Skill(
        name=payload.name.strip(),
        category=payload.category.strip(),
        synonyms_json=[s.strip() for s in payload.synonyms if s.strip()],
        is_custom=True,
    )
    db.add(sk)
    db.commit()
    db.refresh(sk)
    return {
        "id": sk.id,
        "name": sk.name,
        "category": sk.category,
        "synonyms": sk.synonyms_json,
        "is_custom": sk.is_custom,
    }


@router.delete("/skills/{skill_id}")
def delete_skill(skill_id: int, db: Session = Depends(get_db)):
    sk = db.query(Skill).filter(Skill.id == skill_id).first()
    if not sk:
        raise HTTPException(status_code=404, detail="Skill not found.")
    db.delete(sk)
    db.commit()
    return {"deleted": True, "skill_id": skill_id}


@router.get("/datasets/inspect")
def inspect_datasets_endpoint():
    return inspect_all_datasets()


@router.post("/datasets/load")
def load_datasets_endpoint(payload: DatasetLoadRequest, db: Session = Depends(get_db)):
    return load_public_datasets(
        db=db,
        resume_limit=payload.resume_limit,
        ner_limit=payload.ner_limit,
        jobs_limit=payload.jobs_limit,
        clear_existing_dataset=payload.clear_existing_dataset,
    )


@router.post("/datasets/load-initial")
def load_initial_demo_endpoint(db: Session = Depends(get_db)):
    return load_initial_demo_dataset(db)
