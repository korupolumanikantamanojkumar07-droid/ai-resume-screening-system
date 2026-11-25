import io
import os
import tempfile
import pymupdf
from fastapi.testclient import TestClient

_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp_db.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db.name}"
os.environ["AUTO_SEED_DEMO"] = "0"

from app.main import app


def _make_pdf(text: str) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    b = doc.tobytes()
    doc.close()
    return b


def test_file_validation_duplicate_and_replace():
    with TestClient(app) as client:
        # 1. Reject unsupported file extension
        bad = client.post(
            "/api/resumes/upload",
            files=[("files", ("malware.exe", io.BytesIO(b"MZ123456"), "application/octet-stream"))],
        )
        assert bad.status_code == 200
        assert bad.json()["error_count"] == 1
        assert "Unsupported file format" in bad.json()["errors"][0]["error"]

        # 2. Reject empty file
        empty = client.post(
            "/api/resumes/upload",
            files=[("files", ("empty.pdf", io.BytesIO(b""), "application/pdf"))],
        )
        assert empty.status_code == 200
        assert empty.json()["error_count"] == 1

        # 3. Upload valid PDF and verify duplicate detection
        pdf_bytes = _make_pdf(
            "Riya Sen\nriya.sen@example.com | +91 98111 22334\n"
            "Data Analyst with 3 years experience in SQL, Python, Power BI, Excel.\n"
            "Education: B.Sc Statistics, 2021."
        )
        up1 = client.post(
            "/api/resumes/upload",
            files=[("files", ("riya_cv.pdf", io.BytesIO(pdf_bytes), "application/pdf"))],
        )
        assert up1.status_code == 200
        assert up1.json()["uploaded_count"] == 1
        resume_id = up1.json()["uploaded"][0]["resume_id"]

        up_dup = client.post(
            "/api/resumes/upload",
            files=[("files", ("riya_copy.pdf", io.BytesIO(pdf_bytes), "application/pdf"))],
        )
        assert up_dup.status_code == 200
        assert up_dup.json()["error_count"] == 1
        assert "Duplicate resume detected" in up_dup.json()["errors"][0]["error"]

        # 4. Replace resume with updated PDF
        new_pdf = _make_pdf(
            "Riya Sen\nriya.sen@example.com\n"
            "Senior Data Analyst with 4 years experience in SQL, Python, Tableau, AWS.\n"
            "Education: Master's in Data Science, 2022."
        )
        rep = client.put(
            f"/api/resumes/{resume_id}/replace",
            files={"file": ("riya_updated.pdf", io.BytesIO(new_pdf), "application/pdf")},
        )
        assert rep.status_code == 200
        assert rep.json()["education_level"] == "Master's"


def test_privacy_blind_mode_weights_and_all_reports():
    with TestClient(app) as client:
        # 1. Invalid weights (must sum to 100)
        bad_w = client.put(
            "/api/settings/weights",
            json={
                "required_skills": 50,
                "semantic_similarity": 50,
                "experience_match": 20,
                "education_match": 10,
                "preferred_skills": 10,
            },
        )
        assert bad_w.status_code == 422

        # 2. Valid custom weights
        ok_w = client.put(
            "/api/settings/weights",
            json={
                "required_skills": 40,
                "semantic_similarity": 20,
                "experience_match": 20,
                "education_match": 10,
                "preferred_skills": 10,
            },
        )
        assert ok_w.status_code == 200

        # 3. Upload candidate + create job + screen + test Blind Mode masking
        pdf_bytes = _make_pdf(
            "Karan Verma\nkaran.verma@secretmail.com | +91 99887 76655\n"
            "Backend Developer with 5 years of experience in Python, FastAPI, Docker, PostgreSQL.\n"
            "Bachelor's in Computer Science, 2019."
        )
        up = client.post(
            "/api/resumes/upload",
            files=[("files", ("karan.pdf", io.BytesIO(pdf_bytes), "application/pdf"))],
        )
        assert up.status_code == 200
        cand_id = up.json()["uploaded"][0]["candidate_id"]

        job = client.post(
            "/api/jobs",
            json={
                "title": "Backend Python Engineer",
                "description": "Required: Python, FastAPI, Docker, PostgreSQL. Minimum 3 years experience.",
                "auto_extract": True,
            },
        ).json()

        scr = client.post("/api/screening/run", json={"job_id": job["id"]})
        assert scr.status_code == 200
        sr_id = scr.json()["results"][0]["id"]

        # Update status -> shortlisted
        st = client.patch(f"/api/screening/results/{sr_id}/status", json={"screening_status": "shortlisted"})
        assert st.status_code == 200
        assert st.json()["screening_status"] == "shortlisted"

        # Enable blind mode
        priv = client.put(
            "/api/settings/privacy",
            json={"anonymize_candidates": True, "mask_contact_info": True, "file_retention_days": 60},
        )
        assert priv.status_code == 200

        prof = client.get(f"/api/candidates/{cand_id}").json()
        assert prof["display_name"] == prof["anonymous_id"]
        assert prof["email"] == "[Hidden for blind review]"
        assert prof["phone"] == "[Hidden for blind review]"

        # Test all 4 report export types
        for rtype in ("rankings_csv", "skills_csv", "batch_pdf", "candidate_pdf"):
            payload = {"report_type": rtype}
            if rtype == "candidate_pdf":
                payload["candidate_id"] = cand_id
            else:
                payload["job_id"] = job["id"]
            rep = client.post("/api/reports/generate", json=payload)
            assert rep.status_code == 200
            dl = client.get(rep.json()["download_url"])
            assert dl.status_code == 200
            assert len(dl.content) > 50

        # Test custom skill add + duplicate + delete
        sk = client.post("/api/settings/skills", json={"name": "LangGraph", "category": "AI/ML", "synonyms": ["lang graph"]})
        assert sk.status_code == 200
        sk_id = sk.json()["id"]
        sk_dup = client.post("/api/settings/skills", json={"name": "LangGraph", "category": "AI/ML", "synonyms": []})
        assert sk_dup.status_code == 409
        sk_del = client.delete(f"/api/settings/skills/{sk_id}")
        assert sk_del.status_code == 200
