import hashlib
import json
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Candidate, CandidateSkill, DatasetBatch, JobDescription, Resume, Skill
from ..nlp.jd_analyzer import analyze_job_description
from ..nlp.pipeline import run_resume_nlp_pipeline
from ..nlp.preprocessor import strip_html_and_noise
from ..nlp.taxonomy import normalize_skill_name
from .inspector import inspect_all_datasets


def get_taxonomy_from_db(db: Session) -> list[dict]:
    skills = db.query(Skill).all()
    return [
        {"name": s.name, "category": s.category, "synonyms": s.synonyms_json or []}
        for s in skills
    ]


def ensure_skill_in_db(db: Session, name: str, category: str) -> Skill:
    skill = db.query(Skill).filter(Skill.name == name).first()
    if not skill:
        skill = Skill(name=name, category=category, synonyms_json=[], is_custom=False)
        db.add(skill)
        db.flush()
    return skill


def _next_anonymous_id(db: Session, prefix: str = "CND") -> str:
    count = db.query(Candidate).count() + 1
    while True:
        cand_id = f"{prefix}-{count:04d}"
        if not db.query(Candidate).filter(Candidate.anonymous_id == cand_id).first():
            return cand_id
        count += 1


def _persist_processed_resume(
    db: Session,
    filename: str,
    raw_text: str,
    file_hash: str,
    source_type: str,
    dataset_name: str | None,
    dataset_category: str | None,
    taxonomy: list[dict],
    ner_overrides: dict[str, Any] | None = None,
) -> Resume | None:
    if db.query(Resume).filter(Resume.file_hash == file_hash).first():
        return None

    nlp_res = run_resume_nlp_pipeline(
        raw_text=raw_text,
        taxonomy=taxonomy,
        enable_semantic_skills=False,  # Fast deterministic batch ingestion; exact+synonym skills + full MiniLM doc embedding
    )
    entities = nlp_res["entities"]
    if ner_overrides:
        for k in ("full_name", "email", "degree", "university", "graduation_year"):
            if not entities.get(k) and ner_overrides.get(k):
                entities[k] = " ".join(str(ner_overrides[k]).split())[:120]

    resume = Resume(
        filename=filename,
        stored_path=None,
        file_type="dataset",
        file_size=len(raw_text.encode("utf-8")),
        file_hash=file_hash,
        source_type=source_type,
        dataset_name=dataset_name,
        dataset_category=dataset_category,
        raw_text=raw_text,
        cleaned_text=nlp_res["cleaned_text"],
        ocr_used=False,
        processing_status="completed",
    )
    db.add(resume)
    db.flush()

    candidate = Candidate(
        resume_id=resume.id,
        anonymous_id=_next_anonymous_id(db, "PUB" if source_type == "public_dataset" else "CND"),
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

    return resume


def load_public_datasets(
    db: Session,
    resume_limit: int = 60,
    ner_limit: int = 30,
    jobs_limit: int = 15,
    clear_existing_dataset: bool = False,
) -> dict[str, Any]:
    """
    Reusable preprocessing & dataset ingestion pipeline for the 3 Kaggle datasets.
    Clearly tags all loaded records with source_type='public_dataset'.
    """
    if clear_existing_dataset:
        db.query(Resume).filter(Resume.source_type == "public_dataset").delete()
        db.query(JobDescription).filter(JobDescription.source_type == "public_dataset").delete()
        db.query(DatasetBatch).delete()
        db.commit()

    inspection = inspect_all_datasets()
    taxonomy = get_taxonomy_from_db(db)
    raw_dir = settings.DATASETS_RAW_DIR
    proc_dir = settings.DATASETS_PROCESSED_DIR

    summary: dict[str, Any] = {"batches": [], "inspection": inspection}

    # --- 1. Kaggle Resume.csv ---
    resume_csv = raw_dir / "resume-dataset" / "Resume" / "Resume.csv"
    if resume_csv.exists():
        df = pd.read_csv(resume_csv)
        raw_rows = len(df)
        nulls_handled = int(df.isnull().sum().sum())
        df = df.dropna(subset=["Resume_str", "Category"]).copy()
        df["cleaned_preview"] = df["Resume_str"].astype(str).apply(strip_html_and_noise)
        df = df[df["cleaned_preview"].str.len() >= 100]
        before_dedup = len(df)
        df = df.drop_duplicates(subset=["cleaned_preview"]).reset_index(drop=True)
        dups_removed = before_dedup - len(df)

        # Save full cleaned dataset artifact
        df[["ID", "Category", "cleaned_preview"]].rename(columns={"cleaned_preview": "Cleaned_Resume"}).to_csv(
            proc_dir / "cleaned_resumes.csv", index=False
        )

        # Stratified balanced sample prioritizing tech & diverse categories
        priority_cats = [
            "INFORMATION-TECHNOLOGY", "ENGINEERING", "DATA SCIENCE", "FINANCE",
            "HR", "BUSINESS-DEVELOPMENT", "CONSULTANT", "HEALTHCARE", "BANKING", "SALES",
        ]
        selected_rows = []
        cats_available = list(df["Category"].unique())
        ordered_cats = [c for c in priority_cats if c in cats_available] + [c for c in cats_available if c not in priority_cats]
        per_cat = max(2, resume_limit // max(1, len(ordered_cats[:12])))
        for cat in ordered_cats:
            if len(selected_rows) >= resume_limit:
                break
            sub = df[df["Category"] == cat].head(per_cat)
            for _, row in sub.iterrows():
                if len(selected_rows) < resume_limit:
                    selected_rows.append(row)

        loaded = 0
        cat_counts: dict[str, int] = {}
        for row in selected_rows:
            raw_txt = str(row["Resume_str"])
            fhash = hashlib.sha256(f"kaggle_resume_{row['ID']}".encode("utf-8")).hexdigest()
            res = _persist_processed_resume(
                db=db,
                filename=f"kaggle_resume_{row['ID']}.txt",
                raw_text=raw_txt,
                file_hash=fhash,
                source_type="public_dataset",
                dataset_name="Kaggle Resume Dataset (snehaanbhawal)",
                dataset_category=str(row["Category"]),
                taxonomy=taxonomy,
            )
            if res is not None:
                loaded += 1
                cat = str(row["Category"])
                cat_counts[cat] = cat_counts.get(cat, 0) + 1

        batch = db.query(DatasetBatch).filter(DatasetBatch.dataset_key == "kaggle_resume_dataset").first()
        if not batch:
            batch = DatasetBatch(
                dataset_key="kaggle_resume_dataset",
                display_name="Resume Dataset (Kaggle - snehaanbhawal)",
                source_url="https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset",
            )
            db.add(batch)
        batch.raw_row_count = raw_rows
        batch.duplicates_removed = dups_removed
        batch.nulls_handled = nulls_handled
        batch.loaded_count = db.query(Resume).filter(Resume.dataset_name == "Kaggle Resume Dataset (snehaanbhawal)").count()
        batch.categories_json = {str(k): int(v) for k, v in df["Category"].value_counts().items()}
        batch.columns_json = ["ID", "Resume_str", "Resume_html", "Category"]
        batch.status = "loaded"
        db.commit()
        summary["batches"].append({"dataset": "kaggle_resume_dataset", "newly_loaded": loaded, "total_in_db": batch.loaded_count})

    # --- 2. Kaggle NER Resumes JSON ---
    ner_json = raw_dir / "resume-entities-for-ner" / "Entity Recognition in Resumes.json"
    if ner_json.exists():
        records = []
        with open(ner_json, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        raw_ner = len(records)
        seen_txt = set()
        cleaned_ner_records = []
        dups = 0
        null_anns = 0
        label_counts: dict[str, int] = {}

        for idx, rec in enumerate(records):
            content = strip_html_and_noise(str(rec.get("content", "")))
            if len(content) < 80:
                null_anns += 1
                continue
            if content in seen_txt:
                dups += 1
                continue
            seen_txt.add(content)
            anns = rec.get("annotation") or []
            if not anns:
                null_anns += 1
            extracted_ents: dict[str, list[str]] = {}
            for ann in anns:
                for lbl in (ann.get("label") or []):
                    label_counts[lbl] = label_counts.get(lbl, 0) + 1
                    pts = ann.get("points") or []
                    for pt in pts:
                        val = str(pt.get("text", "")).strip()
                        if val:
                            extracted_ents.setdefault(lbl, []).append(val)
            cleaned_ner_records.append({"idx": idx, "content": content, "entities": extracted_ents})

        with open(proc_dir / "cleaned_ner_resumes.json", "w", encoding="utf-8") as f:
            json.dump(cleaned_ner_records[:100], f, indent=2)

        loaded_ner = 0
        for item in cleaned_ner_records[:ner_limit]:
            ents = item["entities"]
            overrides = {
                "full_name": ents.get("Name", [None])[0],
                "email": ents.get("Email Address", [None])[0],
                "degree": ents.get("Degree", [None])[0],
                "university": ents.get("College Name", [None])[0],
                "graduation_year": ents.get("Graduation Year", [None])[0],
            }
            fhash = hashlib.sha256(f"kaggle_ner_{item['idx']}_{item['content'][:80]}".encode("utf-8")).hexdigest()
            res = _persist_processed_resume(
                db=db,
                filename=f"kaggle_ner_resume_{item['idx']}.txt",
                raw_text=item["content"],
                file_hash=fhash,
                source_type="public_dataset",
                dataset_name="Kaggle Resume Entities NER (dataturks)",
                dataset_category="NER-ANNOTATED",
                taxonomy=taxonomy,
                ner_overrides=overrides,
            )
            if res is not None:
                loaded_ner += 1

        batch = db.query(DatasetBatch).filter(DatasetBatch.dataset_key == "kaggle_resume_ner").first()
        if not batch:
            batch = DatasetBatch(
                dataset_key="kaggle_resume_ner",
                display_name="Resume Entities for NLP (Kaggle - dataturks)",
                source_url="https://www.kaggle.com/datasets/dataturks/resume-entities-for-ner",
            )
            db.add(batch)
        batch.raw_row_count = raw_ner
        batch.duplicates_removed = dups
        batch.nulls_handled = null_anns
        batch.loaded_count = db.query(Resume).filter(Resume.dataset_name == "Kaggle Resume Entities NER (dataturks)").count()
        batch.categories_json = label_counts
        batch.columns_json = ["content", "annotation", "extras"]
        batch.status = "loaded"
        db.commit()
        summary["batches"].append({"dataset": "kaggle_resume_ner", "newly_loaded": loaded_ner, "total_in_db": batch.loaded_count})

    # --- 3. Kaggle Job Description Dataset ---
    jobs_csv = raw_dir / "jobs-and-job-description" / "job_title_des.csv"
    if jobs_csv.exists():
        df_j = pd.read_csv(jobs_csv)
        raw_jobs = len(df_j)
        nulls_j = int(df_j.isnull().sum().sum())
        if "Unnamed: 0" in df_j.columns:
            df_j = df_j.drop(columns=["Unnamed: 0"])
        df_j = df_j.dropna(subset=["Job Title", "Job Description"]).copy()
        df_j["Job Title"] = df_j["Job Title"].astype(str).str.strip()
        df_j["Cleaned_Description"] = df_j["Job Description"].astype(str).apply(strip_html_and_noise)
        before_j = len(df_j)
        df_j = df_j.drop_duplicates(subset=["Job Title", "Cleaned_Description"]).reset_index(drop=True)
        dups_j = before_j - len(df_j)

        df_j[["Job Title", "Cleaned_Description"]].to_csv(proc_dir / "cleaned_jobs.csv", index=False)

        # Pick 1 representative rich JD per unique Job Title up to jobs_limit
        unique_titles = list(df_j["Job Title"].unique())
        loaded_jobs = 0
        for title in unique_titles[:jobs_limit]:
            subset = df_j[df_j["Job Title"] == title]
            # Choose a well-detailed description (> 400 chars if available)
            rich = subset[subset["Cleaned_Description"].str.len() >= 400]
            chosen = rich.iloc[0] if len(rich) > 0 else subset.iloc[0]
            desc_text = str(chosen["Cleaned_Description"])

            existing = db.query(JobDescription).filter(
                JobDescription.title == title,
                JobDescription.source_type == "public_dataset",
            ).first()
            if existing:
                continue

            analyzed = analyze_job_description(title, desc_text, taxonomy=taxonomy)
            jd = JobDescription(
                title=title,
                department="Technology",
                description=desc_text,
                required_skills_json=analyzed["required_skills"],
                preferred_skills_json=analyzed["preferred_skills"],
                min_experience_years=analyzed["min_experience_years"],
                education_requirement=analyzed["education_requirement"],
                additional_qualifications=analyzed["additional_qualifications"],
                auto_extracted_json=analyzed,
                embedding_json=analyzed["embedding"],
                source_type="public_dataset",
                status="active",
            )
            db.add(jd)
            loaded_jobs += 1
        db.flush()

        batch = db.query(DatasetBatch).filter(DatasetBatch.dataset_key == "kaggle_job_descriptions").first()
        if not batch:
            batch = DatasetBatch(
                dataset_key="kaggle_job_descriptions",
                display_name="Job Description Dataset (Kaggle - kshitizregmi)",
                source_url="https://www.kaggle.com/datasets/kshitizregmi/jobs-and-job-description",
            )
            db.add(batch)
        batch.raw_row_count = raw_jobs
        batch.duplicates_removed = dups_j
        batch.nulls_handled = nulls_j
        batch.loaded_count = db.query(JobDescription).filter(JobDescription.source_type == "public_dataset").count()
        batch.categories_json = {str(k): int(v) for k, v in df_j["Job Title"].value_counts().items()}
        batch.columns_json = ["Job Title", "Job Description"]
        batch.status = "loaded"
        db.commit()
        summary["batches"].append({"dataset": "kaggle_job_descriptions", "newly_loaded": loaded_jobs, "total_in_db": batch.loaded_count})

    with open(proc_dir / "dataset_inspection_report.json", "w", encoding="utf-8") as f:
        json.dump(inspection, f, indent=2)

    return summary


def load_initial_demo_dataset(db: Session) -> dict[str, Any]:
    """
    Load the user-provided initial synthetic demo dataset (datasets/raw/initial_demo_dataset.csv).
    Clearly marks records with source_type='synthetic_demo' (record_type='synthetic_demo_not_real_candidate_data').
    Deduplicates by candidate_id and job_id.
    """
    demo_csv = settings.DATASETS_RAW_DIR / "initial_demo_dataset.csv"
    if not demo_csv.exists():
        return {"loaded": False, "reason": "initial_demo_dataset.csv not found"}

    df = pd.read_csv(demo_csv)
    raw_rows = len(df)
    nulls_handled = int(df.isnull().sum().sum())
    taxonomy = get_taxonomy_from_db(db)

    # 1. Deduplicate and ingest unique candidates
    cand_df = df.drop_duplicates(subset=["candidate_id"]).reset_index(drop=True)
    dups_removed = raw_rows - len(cand_df)
    loaded_cands = 0

    for _, row in cand_df.iterrows():
        cid = str(row["candidate_id"]).strip()
        cname = str(row["candidate_name"]).strip()
        edu_str = str(row["education"]).strip()
        exp_yrs = float(row["experience_years"])
        skills_raw = [s.strip() for s in str(row["candidate_skills"]).split(";") if s.strip()]
        resume_body = (
            f"{cname}\n"
            f"Summary: {row['resume_text']}\n"
            f"Education: {edu_str}\n"
            f"Experience: {exp_yrs} years\n"
            f"Skills: {', '.join(skills_raw)}\n"
        )
        fhash = hashlib.sha256(f"initial_demo_{cid}_{cname}".encode("utf-8")).hexdigest()
        res = _persist_processed_resume(
            db=db,
            filename=f"demo_{cid}_{cname.lower().replace(' ', '_')}.txt",
            raw_text=resume_body,
            file_hash=fhash,
            source_type="synthetic_demo",
            dataset_name="Initial Synthetic Demo Dataset",
            dataset_category=str(row.get("record_type", "synthetic_demo_not_real_candidate_data")),
            taxonomy=taxonomy,
            ner_overrides={"full_name": cname, "degree": edu_str},
        )
        if res is not None:
            db.flush()
            cand = res.candidate
            cand.total_experience_years = exp_yrs
            cand.degree = edu_str
            # Ensure explicit CSV skills are normalized & linked
            existing_sk_ids = {
                row_id[0]
                for row_id in db.query(CandidateSkill.skill_id)
                .filter(CandidateSkill.candidate_id == cand.id)
                .all()
            }
            for raw_sk in skills_raw:
                canon = normalize_skill_name(raw_sk, taxonomy)
                sk = ensure_skill_in_db(db, canon, "Domain")
                if sk.id not in existing_sk_ids:
                    existing_sk_ids.add(sk.id)
                    db.add(
                        CandidateSkill(
                            candidate_id=cand.id,
                            skill_id=sk.id,
                            match_method="exact",
                            confidence=1.0,
                        )
                    )
            loaded_cands += 1

    # 2. Deduplicate and ingest unique jobs
    job_df = df.drop_duplicates(subset=["job_id"]).reset_index(drop=True)
    loaded_jobs = 0
    for _, row in job_df.iterrows():
        jtitle = str(row["job_title"]).strip()
        jdesc = str(row["job_description"]).strip()
        existing = db.query(JobDescription).filter(
            JobDescription.title == jtitle,
            JobDescription.source_type == "synthetic_demo",
        ).first()
        if existing:
            continue

        req_skills = list(
            dict.fromkeys(
                normalize_skill_name(s.strip(), taxonomy)
                for s in str(row["required_skills"]).split(";")
                if s.strip()
            )
        )
        pref_skills = list(
            dict.fromkeys(
                normalize_skill_name(s.strip(), taxonomy)
                for s in str(row["preferred_skills"]).split(";")
                if s.strip()
            )
        )
        analyzed = analyze_job_description(jtitle, jdesc, taxonomy=taxonomy)
        emb = analyzed.pop("embedding", None)
        jd = JobDescription(
            title=jtitle,
            department="Synthetic Demo",
            description=jdesc,
            required_skills_json=req_skills or analyzed.get("required_skills", []),
            preferred_skills_json=pref_skills or analyzed.get("preferred_skills", []),
            min_experience_years=analyzed.get("min_experience_years", 0.0),
            education_requirement=analyzed.get("education_requirement", "Bachelor's"),
            additional_qualifications="",
            auto_extracted_json=analyzed,
            embedding_json=emb,
            source_type="synthetic_demo",
            status="active",
        )
        db.add(jd)
        loaded_jobs += 1

    db.flush()
    batch = db.query(DatasetBatch).filter(DatasetBatch.dataset_key == "initial_demo_dataset").first()
    if not batch:
        batch = DatasetBatch(
            dataset_key="initial_demo_dataset",
            display_name="Initial Synthetic Demo Dataset (User Provided)",
            source_url="local://datasets/raw/initial_demo_dataset.csv",
        )
        db.add(batch)
    batch.raw_row_count = raw_rows
    batch.duplicates_removed = dups_removed
    batch.nulls_handled = nulls_handled
    batch.loaded_count = db.query(Resume).filter(Resume.source_type == "synthetic_demo").count()
    batch.categories_json = {"unique_candidates": len(cand_df), "unique_jobs": len(job_df)}
    batch.columns_json = df.columns.tolist()
    batch.status = "loaded"
    db.commit()

    return {
        "loaded": True,
        "candidates_loaded": loaded_cands,
        "jobs_loaded": loaded_jobs,
        "total_demo_resumes_in_db": batch.loaded_count,
    }
