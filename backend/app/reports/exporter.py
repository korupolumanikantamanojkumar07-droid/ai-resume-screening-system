import csv
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..config import settings


def _candidate_label(candidate, include_pii: bool) -> str:
    if include_pii and candidate.full_name:
        return f"{candidate.full_name} ({candidate.anonymous_id})"
    return candidate.anonymous_id


def export_rankings_csv(job, results: list[tuple[Any, Any, Any]], include_pii: bool = False) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = settings.REPORTS_DIR / f"rankings_job_{job.id}_{ts}.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Rank",
            "Candidate",
            "Anonymous ID",
            "Source Type",
            "Overall Score (%)",
            "Required Skills (%)",
            "Semantic Similarity (%)",
            "TF-IDF Similarity (%)",
            "Experience Score (%)",
            "Education Score (%)",
            "Preferred Skills (%)",
            "Experience (Years)",
            "Education Level",
            "Matched Skills",
            "Missing Skills",
            "Status",
        ])
        for sr, cand, resume in results:
            writer.writerow([
                sr.rank_position,
                _candidate_label(cand, include_pii),
                cand.anonymous_id,
                resume.source_type,
                f"{sr.overall_score:.2f}",
                f"{sr.required_skill_score:.2f}",
                f"{sr.semantic_similarity_score:.2f}",
                f"{sr.tfidf_similarity_score:.2f}",
                f"{sr.experience_score:.2f}",
                f"{sr.education_score:.2f}",
                f"{sr.preferred_skill_score:.2f}",
                f"{cand.total_experience_years:.1f}",
                cand.education_level,
                "; ".join(sr.matched_skills_json or []),
                "; ".join(sr.missing_skills_json or []),
                sr.screening_status,
            ])
    return out_path


def export_skills_analysis_csv(job, results: list[tuple[Any, Any, Any]]) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = settings.REPORTS_DIR / f"skills_analysis_job_{job.id}_{ts}.csv"

    skill_stats: dict[str, dict[str, int]] = {}
    for req in (job.required_skills_json or []):
        skill_stats[req] = {"matched_count": 0, "missing_count": 0, "type": "Required"}
    for pref in (job.preferred_skills_json or []):
        if pref not in skill_stats:
            skill_stats[pref] = {"matched_count": 0, "missing_count": 0, "type": "Preferred"}

    for sr, _cand, _res in results:
        for s in (sr.matched_skills_json or []):
            skill_stats.setdefault(s, {"matched_count": 0, "missing_count": 0, "type": "Required"})
            skill_stats[s]["matched_count"] += 1
        for s in (sr.missing_skills_json or []):
            skill_stats.setdefault(s, {"matched_count": 0, "missing_count": 0, "type": "Required"})
            skill_stats[s]["missing_count"] += 1
        for s in (sr.matched_preferred_json or []):
            skill_stats.setdefault(s, {"matched_count": 0, "missing_count": 0, "type": "Preferred"})
            skill_stats[s]["matched_count"] += 1

    total = max(1, len(results))
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Skill", "Requirement Type", "Candidates Matched", "Candidates Missing", "Match Rate (%)"])
        for sk, st in sorted(skill_stats.items(), key=lambda kv: (-kv[1]["matched_count"], kv[0])):
            rate = (st["matched_count"] / total) * 100.0
            writer.writerow([sk, st["type"], st["matched_count"], st["missing_count"], f"{rate:.1f}"])
    return out_path


def generate_batch_pdf_report(job, results: list[tuple[Any, Any, Any]], include_pii: bool = False) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = settings.REPORTS_DIR / f"screening_report_job_{job.id}_{ts}.pdf"
    doc = SimpleDocTemplate(str(out_path), pagesize=letter, leftMargin=0.6 * inch, rightMargin=0.6 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("ReportTitle", parent=styles["Heading1"], fontSize=18, textColor=colors.HexColor("#0F172A"))
    sub_style = ParagraphStyle("SubTitle", parent=styles["Normal"], fontSize=10, textColor=colors.HexColor("#475569"))

    story = [
        Paragraph("AI-Based Resume Screening System — Screening Report", title_style),
        Spacer(1, 6),
        Paragraph(f"<b>Job Role:</b> {job.title} ({job.department}) &nbsp;|&nbsp; <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", sub_style),
        Paragraph(f"<b>Required Skills:</b> {', '.join(job.required_skills_json or []) or 'None specified'}", sub_style),
        Paragraph(f"<b>Min Experience:</b> {job.min_experience_years} yrs &nbsp;|&nbsp; <b>Education:</b> {job.education_requirement}", sub_style),
        Spacer(1, 14),
    ]

    avg_score = sum(sr.overall_score for sr, _, _ in results) / max(1, len(results))
    story.append(Paragraph(f"<b>Total Candidates Screened:</b> {len(results)} &nbsp;|&nbsp; <b>Average Compatibility:</b> {avg_score:.2f}%", styles["Normal"]))
    story.append(Spacer(1, 12))

    table_data = [["Rank", "Candidate", "Score", "Req Skill", "Semantic", "Exp (Yrs)", "Education", "Status"]]
    for sr, cand, _res in results[:40]:
        table_data.append([
            str(sr.rank_position),
            _candidate_label(cand, include_pii)[:26],
            f"{sr.overall_score:.1f}%",
            f"{sr.required_skill_score:.0f}%",
            f"{sr.semantic_similarity_score:.0f}%",
            f"{cand.total_experience_years:.1f}",
            (cand.education_level or "")[:14],
            sr.screening_status.title(),
        ])

    tbl = Table(table_data, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 1), (5, -1), "CENTER"),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 14))
    story.append(Paragraph(
        "<i>Decision-Support Notice: Scores are computed deterministically from skills, semantic alignment, experience, and education. "
        "No protected attributes are used.</i>",
        sub_style,
    ))
    doc.build(story)
    return out_path


def generate_candidate_pdf_report(candidate, resume, skills: list[dict], results: list[tuple[Any, Any]], include_pii: bool = False) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = settings.REPORTS_DIR / f"candidate_{candidate.anonymous_id}_{ts}.pdf"
    doc = SimpleDocTemplate(str(out_path), pagesize=letter, leftMargin=0.65 * inch, rightMargin=0.65 * inch)
    styles = getSampleStyleSheet()

    label = _candidate_label(candidate, include_pii)
    story = [
        Paragraph(f"Candidate Screening Profile: {label}", styles["Heading1"]),
        Spacer(1, 6),
        Paragraph(
            f"<b>Source:</b> {resume.source_type} ({resume.filename}) &nbsp;|&nbsp; "
            f"<b>Experience:</b> {candidate.total_experience_years} yrs &nbsp;|&nbsp; "
            f"<b>Education:</b> {candidate.education_level}",
            styles["Normal"],
        ),
    ]
    if include_pii and candidate.email:
        story.append(Paragraph(f"<b>Email:</b> {candidate.email} &nbsp;|&nbsp; <b>Location:</b> {candidate.location or 'N/A'}", styles["Normal"]))
    story.append(Spacer(1, 10))

    skill_names = ", ".join(s["name"] for s in skills) or "None extracted"
    story.append(Paragraph("<b>Extracted Skills:</b>", styles["Heading3"]))
    story.append(Paragraph(skill_names, styles["Normal"]))
    story.append(Spacer(1, 8))

    if candidate.degree or candidate.university:
        story.append(Paragraph("<b>Education Details:</b>", styles["Heading3"]))
        story.append(Paragraph(f"{candidate.degree or ''} — {candidate.university or ''} ({candidate.graduation_year or ''})", styles["Normal"]))
        story.append(Spacer(1, 8))

    if results:
        story.append(Paragraph("<b>Job Screening Evaluations:</b>", styles["Heading3"]))
        tbl_data = [["Job Title", "Rank", "Overall", "Req Skill", "Semantic", "Matched Skills", "Missing Skills"]]
        for sr, job in results:
            tbl_data.append([
                job.title[:24],
                f"#{sr.rank_position}",
                f"{sr.overall_score:.1f}%",
                f"{sr.required_skill_score:.0f}%",
                f"{sr.semantic_similarity_score:.0f}%",
                ", ".join(sr.matched_skills_json or [])[:35] or "-",
                ", ".join(sr.missing_skills_json or [])[:35] or "-",
            ])
        tbl = Table(tbl_data, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ]))
        story.append(tbl)

    doc.build(story)
    return out_path
