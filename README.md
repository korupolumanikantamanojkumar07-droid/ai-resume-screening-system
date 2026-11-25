# AI-Based Resume Screening System

An end-to-end, explainable NLP and Machine Learning web platform for automated resume parsing, semantic job matching, deterministic candidate ranking, analytics, and PDF/CSV reporting.

---

## 1. Key Features

- **Multi-Format & OCR Resume Extraction**: Parses `.pdf` and `.docx` resumes using **PyMuPDF** and **python-docx**, with automatic **RapidOCR / Tesseract** fallback for scanned PDFs and **SHA-256** duplicate resume detection.
- **NLP Preprocessing & Information Extraction**: Text normalization, tokenization, stop-word removal, lemmatization (**NLTK**), noun-phrase extraction, and **spaCy NER** (`en_core_web_sm`) + custom rules for candidate name, email, phone, location, education, degree, university, graduation year, work experience, projects, and certifications.
- **Structured Skill Taxonomy + Semantic Skill Inference**: Covers Programming, AI/ML, Data, Web, Cloud, DevOps, Databases, Soft Skills, and Domain skills with synonym normalization (e.g., `ML` → `Machine Learning`, `Natural Language Processing` → `NLP`) and semantic sentence-embedding matching.
- **Semantic Understanding**: Generates 384-dim dense embeddings using **Sentence Transformers (`all-MiniLM-L6-v2`)** and combines cosine similarity with **Scikit-learn TF-IDF** similarity.
- **Automated Job Description Analysis**: Extracts mandatory skills, preferred skills, minimum experience, and education requirements from pasted job descriptions.
- **Explainable, Fair, Deterministic Ranking**: Weighted scoring (default: 35% Required Skills, 25% Semantic Similarity, 20% Experience, 10% Education, 10% Preferred Skills — customizable in Settings). Excludes all protected characteristics and treats scores strictly as decision-support metadata.
- **Real Kaggle Dataset Integration**: Loads, inspects, deduplicates, and preprocesses three real Kaggle datasets while clearly distinguishing `public_dataset` records from `uploaded` resumes.
- **Analytics & Exports**: Interactive Recharts dashboards plus downloadable CSV rankings, CSV skill gap analyses, batch PDF reports, and individual candidate PDF reports (ReportLab).

---

## 2. Project Structure

```text
ai-resume-screening-system/
├── backend/
│   ├── app/
│   │   ├── datasets/        # Dataset inspection & reusable preprocessing pipeline
│   │   ├── nlp/             # Extractor, preprocessor, NER parser, taxonomy, embeddings, JD analyzer
│   │   ├── reports/         # CSV & ReportLab PDF exporters
│   │   ├── routers/         # FastAPI REST endpoints (dashboard, resumes, jobs, screening, analytics, reports, settings)
│   │   ├── scoring/         # Deterministic weighted candidate ranker
│   │   ├── config.py        # Settings & paths
│   │   ├── database.py      # SQLite + SQLAlchemy engine
│   │   ├── main.py          # FastAPI entrypoint
│   │   ├── models.py        # 8+ ORM tables (Users, Resumes, Candidates, JobDescriptions, Skills, CandidateSkills, ScreeningResults, ScreeningReports)
│   │   ├── schemas.py       # Pydantic validation schemas
│   │   └── services.py      # Seed defaults & privacy masking helpers
│   ├── tests/               # NLP pipeline & end-to-end API tests
│   ├── requirements.txt
│   └── Dockerfile
├── datasets/
│   ├── raw/                 # Downloaded Kaggle archives & extracted files
│   └── processed/           # Cleaned CSV/JSON outputs & inspection reports
├── frontend/
│   ├── src/
│   │   ├── components/      # Responsive sidebar layout & glassmorphism UI components
│   │   ├── pages/           # 10 complete pages (Landing, Dashboard, Upload, Jobs, Screening, Results, CandidateProfile, Analytics, Reports, Settings)
│   │   ├── api.js           # Backend REST API client
│   │   └── App.jsx
│   └── package.json
├── docker-compose.yml
├── start.sh
└── README.md
```

---

## 3. Dataset Download & Preparation

The platform integrates three public Kaggle datasets:

1. **Resume Dataset** (`snehaanbhawal/resume-dataset`):
   https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset
2. **Resume Entities for NLP** (`dataturks/resume-entities-for-ner`):
   https://www.kaggle.com/datasets/dataturks/resume-entities-for-ner
3. **Job Description Dataset** (`kshitizregmi/jobs-and-job-description`):
   https://www.kaggle.com/datasets/kshitizregmi/jobs-and-job-description

### Manual / Scripted Download

```bash
mkdir -p datasets/raw
curl -L "https://www.kaggle.com/api/v1/datasets/download/snehaanbhawal/resume-dataset" -o datasets/raw/resume-dataset.zip
curl -L "https://www.kaggle.com/api/v1/datasets/download/dataturks/resume-entities-for-ner" -o datasets/raw/resume-entities-for-ner.zip
curl -L "https://www.kaggle.com/api/v1/datasets/download/kshitizregmi/jobs-and-job-description" -o datasets/raw/jobs-and-job-description.zip
```

Extract into `datasets/raw/resume-dataset`, `datasets/raw/resume-entities-for-ner`, and `datasets/raw/jobs-and-job-description`. Then open **Settings & Datasets** in the web UI (or `POST /api/settings/datasets/load` / `POST /api/settings/datasets/load-initial`) to inspect nulls/duplicates, run the preprocessing pipeline, write cleaned outputs to `datasets/processed/`, and ingest records into SQLite with `source_type="public_dataset"` (or `source_type="synthetic_demo"` for `datasets/raw/initial_demo_dataset.csv`).

### Deploying to GitHub

```bash
git remote add origin https://github.com/<YOUR_USERNAME>/ai-resume-screening-system.git
git push -u origin main
```

---

## 4. Local Setup & Execution

### Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('omw-1.4')"

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Or run both together from the project root:

```bash
./start.sh
```

- Frontend UI: `http://localhost:5173`
- Backend API & Swagger Docs: `http://127.0.0.1:8000/docs`

---

## 5. Testing Instructions

Run the automated NLP pipeline and end-to-end API integration test suite:

```bash
cd backend
PYTHONPATH=. venv/bin/pytest -v
```

---

## 6. Cloud Deployment Instructions

### Option A: Docker Compose (AWS EC2 / DigitalOcean / Azure VM)

```bash
docker compose up --build -d
```

- Frontend served on port `80` (or `5173`), Backend FastAPI on port `8000`.
- For production, mount a persistent volume for `resume_screening.db` and `uploads/` (or switch `DATABASE_URL` in `.env` to PostgreSQL).

### Option B: Managed PaaS (Render / Railway + Vercel)

1. **Backend (Render / Railway)**:
   - Root directory: `backend`
   - Build command: `pip install -r requirements.txt && python -m spacy download en_core_web_sm`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Set environment variable `CORS_ORIGINS=["https://your-frontend.vercel.app"]`.
2. **Frontend (Vercel / Netlify)**:
   - Root directory: `frontend`
   - Build command: `npm run build`
   - Output directory: `dist`
   - Set environment variable `VITE_API_URL=https://your-backend.onrender.com/api`.
