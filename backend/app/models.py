from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="recruiter", nullable=False)
    organization = Column(String(255), default="TalentAI Labs")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    resumes = relationship("Resume", back_populates="uploader")
    jobs = relationship("JobDescription", back_populates="creator")
    reports = relationship("ScreeningReport", back_populates="creator")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    stored_path = Column(String(512), nullable=True)
    file_type = Column(String(20), nullable=False)  # pdf, docx, dataset
    file_size = Column(Integer, default=0, nullable=False)
    file_hash = Column(String(64), unique=True, nullable=False, index=True)
    source_type = Column(String(30), default="uploaded", nullable=False, index=True)  # uploaded | public_dataset
    dataset_name = Column(String(120), nullable=True)
    dataset_category = Column(String(120), nullable=True, index=True)
    raw_text = Column(Text, default="", nullable=False)
    cleaned_text = Column(Text, default="", nullable=False)
    ocr_used = Column(Boolean, default=False, nullable=False)
    processing_status = Column(String(30), default="pending", nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    uploader = relationship("User", back_populates="resumes")
    candidate = relationship("Candidate", back_populates="resume", uselist=False, cascade="all, delete-orphan")


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), unique=True, nullable=False)
    anonymous_id = Column(String(32), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(64), nullable=True)
    location = Column(String(255), nullable=True)
    total_experience_years = Column(Float, default=0.0, nullable=False)
    experience_summary = Column(Text, default="", nullable=False)
    education_level = Column(String(80), default="Unspecified", nullable=False)
    degree = Column(String(255), nullable=True)
    university = Column(String(255), nullable=True)
    graduation_year = Column(String(20), nullable=True)
    education_json = Column(JSON, default=list, nullable=False)
    work_experience_json = Column(JSON, default=list, nullable=False)
    projects_json = Column(JSON, default=list, nullable=False)
    certifications_json = Column(JSON, default=list, nullable=False)
    soft_skills_json = Column(JSON, default=list, nullable=False)
    programming_languages_json = Column(JSON, default=list, nullable=False)
    tools_technologies_json = Column(JSON, default=list, nullable=False)
    key_phrases_json = Column(JSON, default=list, nullable=False)
    embedding_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    resume = relationship("Resume", back_populates="candidate")
    candidate_skills = relationship("CandidateSkill", back_populates="candidate", cascade="all, delete-orphan")
    screening_results = relationship("ScreeningResult", back_populates="candidate", cascade="all, delete-orphan")


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    department = Column(String(120), default="Engineering", nullable=False)
    description = Column(Text, nullable=False)
    required_skills_json = Column(JSON, default=list, nullable=False)
    preferred_skills_json = Column(JSON, default=list, nullable=False)
    min_experience_years = Column(Float, default=0.0, nullable=False)
    education_requirement = Column(String(120), default="Bachelor's", nullable=False)
    additional_qualifications = Column(Text, default="", nullable=False)
    auto_extracted_json = Column(JSON, default=dict, nullable=False)
    embedding_json = Column(JSON, nullable=True)
    source_type = Column(String(30), default="custom", nullable=False)  # custom | public_dataset
    status = Column(String(30), default="active", nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    creator = relationship("User", back_populates="jobs")
    screening_results = relationship("ScreeningResult", back_populates="job", cascade="all, delete-orphan")
    reports = relationship("ScreeningReport", back_populates="job", cascade="all, delete-orphan")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), unique=True, nullable=False, index=True)
    category = Column(String(80), nullable=False, index=True)
    synonyms_json = Column(JSON, default=list, nullable=False)
    is_custom = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    candidate_skills = relationship("CandidateSkill", back_populates="skill", cascade="all, delete-orphan")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"
    __table_args__ = (UniqueConstraint("candidate_id", "skill_id", name="uq_candidate_skill"),)

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    match_method = Column(String(30), default="exact", nullable=False)  # exact | synonym | semantic
    confidence = Column(Float, default=1.0, nullable=False)

    candidate = relationship("Candidate", back_populates="candidate_skills")
    skill = relationship("Skill", back_populates="candidate_skills")


class ScreeningResult(Base):
    __tablename__ = "screening_results"
    __table_args__ = (UniqueConstraint("job_id", "candidate_id", name="uq_job_candidate_screening"),)

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    overall_score = Column(Float, nullable=False, index=True)
    required_skill_score = Column(Float, nullable=False)
    preferred_skill_score = Column(Float, nullable=False)
    semantic_similarity_score = Column(Float, nullable=False)
    tfidf_similarity_score = Column(Float, default=0.0, nullable=False)
    experience_score = Column(Float, nullable=False)
    education_score = Column(Float, nullable=False)
    matched_skills_json = Column(JSON, default=list, nullable=False)
    missing_skills_json = Column(JSON, default=list, nullable=False)
    matched_preferred_json = Column(JSON, default=list, nullable=False)
    explanation_json = Column(JSON, default=dict, nullable=False)
    weights_used_json = Column(JSON, default=dict, nullable=False)
    rank_position = Column(Integer, default=1, nullable=False)
    screening_status = Column(String(30), default="screened", nullable=False)
    screened_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    job = relationship("JobDescription", back_populates="screening_results")
    candidate = relationship("Candidate", back_populates="screening_results")


class ScreeningReport(Base):
    __tablename__ = "screening_reports"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="SET NULL"), nullable=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="SET NULL"), nullable=True)
    report_type = Column(String(40), nullable=False)  # batch_pdf | candidate_pdf | rankings_csv | skills_csv
    title = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    summary_json = Column(JSON, default=dict, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    job = relationship("JobDescription", back_populates="reports")
    creator = relationship("User", back_populates="reports")


class AppSetting(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(120), unique=True, nullable=False, index=True)
    value_json = Column(JSON, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class DatasetBatch(Base):
    __tablename__ = "dataset_batches"

    id = Column(Integer, primary_key=True, index=True)
    dataset_key = Column(String(120), unique=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    source_url = Column(String(512), nullable=False)
    raw_row_count = Column(Integer, default=0, nullable=False)
    duplicates_removed = Column(Integer, default=0, nullable=False)
    nulls_handled = Column(Integer, default=0, nullable=False)
    loaded_count = Column(Integer, default=0, nullable=False)
    categories_json = Column(JSON, default=dict, nullable=False)
    columns_json = Column(JSON, default=list, nullable=False)
    status = Column(String(30), default="ready", nullable=False)
    loaded_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
