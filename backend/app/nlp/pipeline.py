from typing import Any, Optional

from .embeddings import embed_single, embed_texts
from .ner_parser import extract_entities_and_sections
from .preprocessor import preprocess_text
from .taxonomy import DEFAULT_SKILL_TAXONOMY, extract_skills_from_text


def run_resume_nlp_pipeline(
    raw_text: str,
    taxonomy: Optional[list[dict]] = None,
    enable_semantic_skills: bool = True,
) -> dict[str, Any]:
    """
    Complete NLP Pipeline for a resume:
    1. Preprocessing (cleaning, tokenization, normalization, lemmatization, phrases)
    2. Information & Entity Extraction (spaCy NER + regex + section rules)
    3. Structured Skill Extraction (exact + synonym + semantic embeddings)
    4. Semantic Document Embedding (all-MiniLM-L6-v2)
    """
    prep = preprocess_text(raw_text)
    cleaned_text = prep["cleaned_text"]
    entities = extract_entities_and_sections(cleaned_text)

    tax = taxonomy or DEFAULT_SKILL_TAXONOMY
    skill_matches = extract_skills_from_text(
        text=cleaned_text,
        taxonomy=tax,
        sentences=prep["sentences"],
        embed_fn=embed_texts if enable_semantic_skills else None,
        enable_semantic=enable_semantic_skills,
    )

    programming_languages = [m.name for m in skill_matches if m.category == "Programming"]
    soft_skills = [m.name for m in skill_matches if m.category == "Soft Skills"]
    tools_technologies = [
        m.name for m in skill_matches if m.category not in ("Programming", "Soft Skills")
    ]

    # Build rich semantic summary for embedding
    skill_names = ", ".join(m.name for m in skill_matches)
    semantic_input = (
        f"Skills: {skill_names}\n"
        f"Experience ({entities['total_experience_years']} years): {entities['experience_summary']}\n"
        f"Education: {entities['education_level']} {entities.get('degree') or ''}\n"
        f"Resume Content: {cleaned_text[:3500]}"
    )
    embedding = embed_single(semantic_input)

    return {
        "cleaned_text": cleaned_text,
        "normalized_text": prep["normalized_text"],
        "key_phrases": prep["key_phrases"],
        "entities": entities,
        "skills": skill_matches,
        "programming_languages": programming_languages,
        "soft_skills": soft_skills,
        "tools_technologies": tools_technologies,
        "embedding": embedding,
    }
