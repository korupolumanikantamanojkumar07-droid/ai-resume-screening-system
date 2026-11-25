import io
import os
import tempfile
import pymupdf
from fastapi.testclient import TestClient

# Point tests to an isolated temporary SQLite database
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


def test_end_to_end_workflow():
    with TestClient(app) as client:
        # 1. Health check
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

        # 2. Upload resume
        pdf_bytes = _make_pdf(
            "Priya Nair\npriya.nair@devmail.com\n"
            "Software Engineer with 4 years of experience in Python, React, FastAPI, SQL, Docker, AWS.\n"
            "Education: Bachelor of Technology in Computer Science, 2020.\n"
        )
        up = client.post(
            "/api/resumes/upload",
            files=[("files", ("priya_nair_cv.pdf", io.BytesIO(pdf_bytes), "application/pdf"))],
        )
        assert up.status_code == 200
        up_data = up.json()
        assert up_data["uploaded_count"] >= 1 or up_data["error_count"] >= 0

        # Fetch resumes list
        res_list = client.get("/api/resumes").json()
        assert res_list["total"] >= 1
        resume_id = res_list["items"][0]["id"]
        candidate_id = res_list["items"][0]["candidate_id"]

        # 3. Create Job Description
        job_resp = client.post(
            "/api/jobs",
            json={
                "title": "Full Stack AI Engineer",
                "department": "Engineering",
                "description": "Required: Python, React, FastAPI, Docker, SQL. Minimum 3 years experience. Bachelor's degree.",
                "auto_extract": True,
            },
        )
        assert job_resp.status_code == 200
        job_id = job_resp.json()["id"]

        # 4. Run AI Screening
        scr = client.post("/api/screening/run", json={"job_id": job_id, "resume_ids": [resume_id]})
        assert scr.status_code == 200
        assert scr.json()["screened_count"] == 1

        # 5. Candidate Profile
        prof = client.get(f"/api/candidates/{candidate_id}")
        assert prof.status_code == 200
        assert len(prof.json()["evaluations"]) >= 1

        # 6. Analytics & Dashboard
        dash = client.get("/api/dashboard/overview")
        assert dash.status_code == 200
        assert dash.json()["stats"]["total_resumes"] >= 1

        ana = client.get(f"/api/analytics/overview?job_id={job_id}")
        assert ana.status_code == 200

        # 7. Export CSV & PDF reports
        csv_rep = client.post("/api/reports/generate", json={"job_id": job_id, "report_type": "rankings_csv"})
        assert csv_rep.status_code == 200
        dl_csv = client.get(csv_rep.json()["download_url"])
        assert dl_csv.status_code == 200
        assert "Overall Score" in dl_csv.text

        pdf_rep = client.post("/api/reports/generate", json={"job_id": job_id, "report_type": "batch_pdf"})
        assert pdf_rep.status_code == 200
        dl_pdf = client.get(pdf_rep.json()["download_url"])
        assert dl_pdf.status_code == 200
        assert dl_pdf.content.startswith(b"%PDF")
