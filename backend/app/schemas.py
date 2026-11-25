from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


class ScoringWeights(BaseModel):
    required_skills: float = Field(35.0, ge=0, le=100)
    semantic_similarity: float = Field(25.0, ge=0, le=100)
    experience_match: float = Field(20.0, ge=0, le=100)
    education_match: float = Field(10.0, ge=0, le=100)
    preferred_skills: float = Field(10.0, ge=0, le=100)

    @field_validator("preferred_skills")
    @classmethod
    def check_total(cls, v, info):
        total = (
            info.data.get("required_skills", 0)
            + info.data.get("semantic_similarity", 0)
            + info.data.get("experience_match", 0)
            + info.data.get("education_match", 0)
            + v
        )
        if abs(total - 100.0) > 0.01:
            raise ValueError(f"Scoring weights must sum to 100 (got {total:.2f})")
        return v


class ResumeSummary(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    source_type: str
    dataset_name: Optional[str] = None
    dataset_category: Optional[str] = None
    ocr_used: bool
    processing_status: str
    error_message: Optional[str] = None
    candidate_id: Optional[int] = None
    candidate_name: Optional[str] = None
    anonymous_id: Optional[str] = None
    skills_count: int = 0
    experience_years: float = 0.0
    education_level: str = "Unspecified"
    created_at: datetime


class JobDescriptionCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    department: str = Field("Engineering", max_length=120)
    description: str = Field(..., min_length=20)
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    min_experience_years: float = Field(0.0, ge=0, le=50)
    education_requirement: str = Field("Bachelor's", max_length=120)
    additional_qualifications: str = ""
    auto_extract: bool = True


class JobDescriptionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    department: Optional[str] = Field(None, max_length=120)
    description: Optional[str] = Field(None, min_length=20)
    required_skills: Optional[list[str]] = None
    preferred_skills: Optional[list[str]] = None
    min_experience_years: Optional[float] = Field(None, ge=0, le=50)
    education_requirement: Optional[str] = None
    additional_qualifications: Optional[str] = None
    status: Optional[str] = None


class JobAnalyzeRequest(BaseModel):
    title: str = ""
    description: str = Field(..., min_length=15)


class ScreeningRunRequest(BaseModel):
    job_id: int
    resume_ids: list[int] = Field(default_factory=list)
    weights: Optional[ScoringWeights] = None


class ScreeningStatusUpdate(BaseModel):
    screening_status: str = Field(..., pattern="^(screened|shortlisted|review|rejected)$")


class SkillCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    category: str = Field(..., min_length=2, max_length=80)
    synonyms: list[str] = Field(default_factory=list)


class PrivacyRetentionSettings(BaseModel):
    anonymize_candidates: bool = False
    mask_contact_info: bool = True
    file_retention_days: int = Field(90, ge=1, le=3650)


class DatasetLoadRequest(BaseModel):
    resume_limit: int = Field(60, ge=10, le=500)
    ner_limit: int = Field(30, ge=5, le=220)
    jobs_limit: int = Field(15, ge=5, le=100)
    clear_existing_dataset: bool = False


class ReportGenerateRequest(BaseModel):
    job_id: Optional[int] = None
    candidate_id: Optional[int] = None
    report_type: str = Field(..., pattern="^(batch_pdf|candidate_pdf|rankings_csv|skills_csv)$")
    title: Optional[str] = None
    include_pii: bool = False
