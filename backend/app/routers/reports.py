from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Candidate, JobDescription, Resume, ScreeningReport, ScreeningResult
from ..reports.exporter import (
    export_rankings_csv,
    export_skills_analysis_csv,
    generate_batch_pdf_report,
    generate_candidate_pdf_report,
)
from ..schemas import ReportGenerateRequest
from ..services import get_candidate_skills_list

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("")
def list_reports(db: Session = Depends(get_db)):
    reports = db.query(ScreeningReport).order_by(ScreeningReport.created_at.desc()).limit(50).all()
    return {
        "items": [
            {
                "id": r.id,
                "job_id": r.job_id,
                "candidate_id": r.candidate_id,
                "report_type": r.report_type,
                "title": r.title,
                "summary": r.summary_json or {},
                "created_at": r.created_at,
                "file_exists": Path(r.file_path).exists(),
            }
            for r in reports
        ]
    }


@router.post("/generate")
def generate_report(payload: ReportGenerateRequest, db: Session = Depends(get_db)):
    if payload.report_type in ("batch_pdf", "rankings_csv", "skills_csv"):
        if not payload.job_id:
            raise HTTPException(status_code=400, detail="job_id is required for job screening reports.")
        job = db.query(JobDescription).filter(JobDescription.id == payload.job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job description not found.")

        rows = (
            db.query(ScreeningResult, Candidate, Resume)
            .join(Candidate, ScreeningResult.candidate_id == Candidate.id)
            .join(Resume, Candidate.resume_id == Resume.id)
            .filter(ScreeningResult.job_id == job.id)
            .order_by(ScreeningResult.rank_position.asc())
            .all()
        )
        if not rows:
            raise HTTPException(status_code=400, detail="No screening results exist for this job yet. Run AI Screening first.")

        if payload.report_type == "rankings_csv":
            out_path = export_rankings_csv(job, rows, include_pii=payload.include_pii)
            title = payload.title or f"Candidate Rankings CSV - {job.title}"
        elif payload.report_type == "skills_csv":
            out_path = export_skills_analysis_csv(job, rows)
            title = payload.title or f"Skill Matching Analysis CSV - {job.title}"
        else:
            out_path = generate_batch_pdf_report(job, rows, include_pii=payload.include_pii)
            title = payload.title or f"AI Screening Report PDF - {job.title}"

        rep = ScreeningReport(
            job_id=job.id,
            candidate_id=None,
            report_type=payload.report_type,
            title=title,
            file_path=str(out_path),
            summary_json={"candidates_count": len(rows), "job_title": job.title},
        )
    else:
        if not payload.candidate_id:
            raise HTTPException(status_code=400, detail="candidate_id is required for candidate_pdf.")
        cand = db.query(Candidate).filter(Candidate.id == payload.candidate_id).first()
        if not cand:
            raise HTTPException(status_code=404, detail="Candidate not found.")
        skills = get_candidate_skills_list(db, cand.id)
        eval_rows = (
            db.query(ScreeningResult, JobDescription)
            .join(JobDescription, ScreeningResult.job_id == JobDescription.id)
            .filter(ScreeningResult.candidate_id == cand.id)
            .order_by(ScreeningResult.overall_score.desc())
            .all()
        )
        out_path = generate_candidate_pdf_report(cand, cand.resume, skills, eval_rows, include_pii=payload.include_pii)
        title = payload.title or f"Candidate Report PDF - {cand.anonymous_id}"
        rep = ScreeningReport(
            job_id=None,
            candidate_id=cand.id,
            report_type="candidate_pdf",
            title=title,
            file_path=str(out_path),
            summary_json={"anonymous_id": cand.anonymous_id, "evaluations_count": len(eval_rows)},
        )

    db.add(rep)
    db.commit()
    db.refresh(rep)
    return {
        "id": rep.id,
        "report_type": rep.report_type,
        "title": rep.title,
        "summary": rep.summary_json,
        "created_at": rep.created_at,
        "download_url": f"/api/reports/{rep.id}/download",
    }


@router.get("/{report_id}/download")
def download_report(report_id: int, db: Session = Depends(get_db)):
    rep = db.query(ScreeningReport).filter(ScreeningReport.id == report_id).first()
    if not rep:
        raise HTTPException(status_code=404, detail="Report not found.")
    path = Path(rep.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report file missing on disk.")
    media_type = "text/csv" if path.suffix.lower() == ".csv" else "application/pdf"
    return FileResponse(path=str(path), media_type=media_type, filename=path.name)
