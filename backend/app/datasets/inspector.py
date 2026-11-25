import json
from pathlib import Path
from typing import Any

import pandas as pd

from ..config import settings


def inspect_all_datasets() -> dict[str, Any]:
    """Inspect the actual downloaded Kaggle dataset files without fabrication."""
    raw_dir = settings.DATASETS_RAW_DIR
    report: dict[str, Any] = {"datasets": []}

    # 0. Initial User-Provided Synthetic Demo Dataset
    demo_csv = raw_dir / "initial_demo_dataset.csv"
    if demo_csv.exists():
        df_d = pd.read_csv(demo_csv)
        nulls_d = {col: int(cnt) for col, cnt in df_d.isnull().sum().items()}
        unique_cands = int(df_d["candidate_id"].nunique()) if "candidate_id" in df_d.columns else 0
        unique_jobs = int(df_d["job_id"].nunique()) if "job_id" in df_d.columns else 0
        report["datasets"].append({
            "key": "initial_demo_dataset",
            "name": "Initial Synthetic Demo Dataset (User Provided)",
            "url": "local://datasets/raw/initial_demo_dataset.csv",
            "file_path": str(demo_csv),
            "exists": True,
            "row_count": int(len(df_d)),
            "columns": df_d.columns.tolist(),
            "null_counts": nulls_d,
            "duplicate_count": int(len(df_d) - unique_cands),
            "categories": {"unique_candidates": unique_cands, "unique_jobs": unique_jobs},
        })

    # 1. Resume Dataset (snehaanbhawal)
    resume_csv = raw_dir / "resume-dataset" / "Resume" / "Resume.csv"
    if resume_csv.exists():
        df = pd.read_csv(resume_csv)
        nulls = {col: int(cnt) for col, cnt in df.isnull().sum().items()}
        dups = int(df["Resume_str"].astype(str).str.strip().duplicated().sum()) if "Resume_str" in df.columns else 0
        cats = {str(k): int(v) for k, v in df["Category"].value_counts().items()} if "Category" in df.columns else {}
        report["datasets"].append({
            "key": "kaggle_resume_dataset",
            "name": "Resume Dataset (Kaggle - snehaanbhawal)",
            "url": "https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset",
            "file_path": str(resume_csv),
            "exists": True,
            "row_count": int(len(df)),
            "columns": df.columns.tolist(),
            "null_counts": nulls,
            "duplicate_count": dups,
            "categories": cats,
        })
    else:
        report["datasets"].append({
            "key": "kaggle_resume_dataset",
            "name": "Resume Dataset (Kaggle - snehaanbhawal)",
            "url": "https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset",
            "exists": False,
        })

    # 2. Resume Entities for NER (dataturks)
    ner_json = raw_dir / "resume-entities-for-ner" / "Entity Recognition in Resumes.json"
    if ner_json.exists():
        records = []
        with open(ner_json, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        label_counts: dict[str, int] = {}
        seen_contents = set()
        dups = 0
        null_annotations = 0
        for rec in records:
            c = str(rec.get("content", "")).strip()
            if c in seen_contents:
                dups += 1
            seen_contents.add(c)
            anns = rec.get("annotation") or []
            if not anns:
                null_annotations += 1
            for ann in anns:
                for lbl in (ann.get("label") or []):
                    label_counts[lbl] = label_counts.get(lbl, 0) + 1

        report["datasets"].append({
            "key": "kaggle_resume_ner",
            "name": "Resume Entities for NLP (Kaggle - dataturks)",
            "url": "https://www.kaggle.com/datasets/dataturks/resume-entities-for-ner",
            "file_path": str(ner_json),
            "exists": True,
            "row_count": len(records),
            "columns": list(records[0].keys()) if records else [],
            "null_counts": {"empty_annotation": null_annotations},
            "duplicate_count": dups,
            "categories": label_counts,
        })
    else:
        report["datasets"].append({
            "key": "kaggle_resume_ner",
            "name": "Resume Entities for NLP (Kaggle - dataturks)",
            "url": "https://www.kaggle.com/datasets/dataturks/resume-entities-for-ner",
            "exists": False,
        })

    # 3. Job Description Dataset (kshitizregmi)
    jobs_csv = raw_dir / "jobs-and-job-description" / "job_title_des.csv"
    if jobs_csv.exists():
        df_j = pd.read_csv(jobs_csv)
        nulls = {col: int(cnt) for col, cnt in df_j.isnull().sum().items()}
        dups = int(df_j["Job Description"].astype(str).str.strip().duplicated().sum()) if "Job Description" in df_j.columns else 0
        titles = {str(k): int(v) for k, v in df_j["Job Title"].value_counts().items()} if "Job Title" in df_j.columns else {}
        report["datasets"].append({
            "key": "kaggle_job_descriptions",
            "name": "Job Description Dataset (Kaggle - kshitizregmi)",
            "url": "https://www.kaggle.com/datasets/kshitizregmi/jobs-and-job-description",
            "file_path": str(jobs_csv),
            "exists": True,
            "row_count": int(len(df_j)),
            "columns": df_j.columns.tolist(),
            "null_counts": nulls,
            "duplicate_count": dups,
            "categories": titles,
        })
    else:
        report["datasets"].append({
            "key": "kaggle_job_descriptions",
            "name": "Job Description Dataset (Kaggle - kshitizregmi)",
            "url": "https://www.kaggle.com/datasets/kshitizregmi/jobs-and-job-description",
            "exists": False,
        })

    return report
