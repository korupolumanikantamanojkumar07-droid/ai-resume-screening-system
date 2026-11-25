import io
import docx
import pymupdf
from PIL import Image, ImageDraw, ImageFont

from app.nlp.extractor import extract_resume_text
from app.nlp.jd_analyzer import analyze_job_description
from app.nlp.pipeline import run_resume_nlp_pipeline
from app.nlp.taxonomy import normalize_skill_name
from app.scoring.ranker import score_candidate_for_job


def _make_sample_pdf(text: str) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    data = doc.tobytes()
    doc.close()
    return data


def _make_scanned_pdf(text: str) -> bytes:
    img = Image.new("RGB", (1200, 300), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    except Exception:
        font = ImageFont.load_default(size=36)
    draw.text((40, 60), text, fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    doc = pymupdf.open()
    page = doc.new_page(width=1200, height=300)
    page.insert_image(page.rect, stream=buf.getvalue())
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def _make_sample_docx(text: str) -> bytes:
    d = docx.Document()
    for line in text.split("\n"):
        d.add_paragraph(line)
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


SAMPLE_RESUME = """Aarav Sharma
aarav.sharma@example.com | +91 98765 43210 | Bengaluru, India

SUMMARY
Senior ML Engineer with 5+ years of experience building Natural Language Processing and Deep Learning systems.

EXPERIENCE
Senior Machine Learning Engineer - TechNova AI (2021 - Present)
- Built production RAG and LLM pipelines using Python, PyTorch, Hugging Face Transformers, and FastAPI.
- Deployed microservices on AWS and Docker with CI/CD pipelines.

Data Scientist - DataPulse (2019 - 2021)
- Developed predictive models with Scikit-learn, Pandas, NumPy, and SQL.

EDUCATION
Master's in Computer Science (M.Tech)
Indian Institute of Technology Delhi, 2019

PROJECTS
- Semantic Resume Matcher using sentence transformers and spaCy NER.

CERTIFICATIONS
- AWS Certified Machine Learning - Specialty
"""


def test_pdf_and_docx_extraction():
    pdf_bytes = _make_sample_pdf(SAMPLE_RESUME)
    res_pdf = extract_resume_text("aarav.pdf", pdf_bytes)
    assert res_pdf["file_type"] == "pdf"
    assert "Aarav Sharma" in res_pdf["text"]

    docx_bytes = _make_sample_docx(SAMPLE_RESUME)
    res_docx = extract_resume_text("aarav.docx", docx_bytes)
    assert res_docx["file_type"] == "docx"
    assert "Natural Language Processing" in res_docx["text"]


def test_scanned_pdf_ocr_fallback():
    scanned_bytes = _make_scanned_pdf("Python Machine Learning Engineer NLP FastAPI Docker")
    res_ocr = extract_resume_text("scanned_cv.pdf", scanned_bytes)
    assert res_ocr["ocr_used"] is True
    assert len(res_ocr["text"]) >= 20


def test_synonym_normalization_and_nlp_pipeline():
    assert normalize_skill_name("ML") == "Machine Learning"
    assert normalize_skill_name("Natural Language Processing") == "NLP"

    out = run_resume_nlp_pipeline(SAMPLE_RESUME, enable_semantic_skills=True)
    ents = out["entities"]
    assert ents["email"] == "aarav.sharma@example.com"
    assert ents["total_experience_years"] >= 5.0
    assert ents["education_level"] == "Master's"
    skill_names = {s.name for s in out["skills"]}
    assert {"Python", "NLP", "Machine Learning", "PyTorch", "FastAPI", "AWS"}.issubset(skill_names)
    assert len(out["embedding"]) == 384


def test_jd_analysis_and_deterministic_scoring():
    jd_text = """
    Required Skills: Python, NLP, Machine Learning, FastAPI, Docker.
    Minimum 4 years of experience and Bachelor's degree in Computer Science.
    Preferred Skills: Kubernetes, PyTorch, AWS.
    """
    analyzed = analyze_job_description("Senior NLP Engineer", jd_text)
    assert "Python" in analyzed["required_skills"]
    assert "NLP" in analyzed["required_skills"]
    assert analyzed["min_experience_years"] == 4.0

    cand_out = run_resume_nlp_pipeline(SAMPLE_RESUME, enable_semantic_skills=True)
    cand_data = {
        "skills": [s.name for s in cand_out["skills"]],
        "total_experience_years": cand_out["entities"]["total_experience_years"],
        "education_level": cand_out["entities"]["education_level"],
        "cleaned_text": cand_out["cleaned_text"],
        "embedding": cand_out["embedding"],
    }
    job_data = {
        "title": "Senior NLP Engineer",
        "description": jd_text,
        "required_skills": analyzed["required_skills"],
        "preferred_skills": analyzed["preferred_skills"],
        "min_experience_years": analyzed["min_experience_years"],
        "education_requirement": analyzed["education_requirement"],
        "embedding": analyzed["embedding"],
    }

    score1 = score_candidate_for_job(cand_data, job_data)
    score2 = score_candidate_for_job(cand_data, job_data)
    assert score1["overall_score"] == score2["overall_score"]
    assert score1["overall_score"] >= 75.0
    assert "NLP" in score1["matched_skills"]
