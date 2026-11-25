from pathlib import Path
from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent


class Settings(BaseSettings):
    APP_NAME: str = "AI-Based Resume Screening System"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"

    DATABASE_URL: str = f"sqlite:///{(BASE_DIR / 'resume_screening.db').as_posix()}"
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    REPORTS_DIR: Path = BASE_DIR / "reports_out"
    DATASETS_RAW_DIR: Path = PROJECT_ROOT / "datasets" / "raw"
    DATASETS_PROCESSED_DIR: Path = PROJECT_ROOT / "datasets" / "processed"

    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: tuple[str, ...] = (".pdf", ".docx")

    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    SPACY_MODEL_NAME: str = "en_core_web_sm"

    # Default scoring weights (must sum to 100)
    DEFAULT_WEIGHTS: dict[str, float] = {
        "required_skills": 35.0,
        "semantic_similarity": 25.0,
        "experience_match": 20.0,
        "education_match": 10.0,
        "preferred_skills": 10.0,
    }

    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
settings.DATASETS_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
