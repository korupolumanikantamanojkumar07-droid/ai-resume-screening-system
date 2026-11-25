import re
from typing import Any, Optional

from .embeddings import embed_single, embed_texts
from .ner_parser import DEGREE_PATTERNS, DEGREE_RANK, EXP_YEARS_RE
from .preprocessor import preprocess_text
from .taxonomy import DEFAULT_SKILL_TAXONOMY, extract_skills_from_text

PREFERRED_SECTION_RE = re.compile(
    r"(?:preferred|nice\s+to\s+have|good\s+to\s+have|bonus|plus|optional|desired)\s*(?:skills|qualifications|requirements)?[:\-]?",
    re.IGNORECASE,
)
REQUIRED_SECTION_RE = re.compile(
    r"(?:required|must\s+have|mandatory|minimum|core)\s*(?:skills|qualifications|requirements)?[:\-]?",
    re.IGNORECASE,
)


def analyze_job_description(
    title: str,
    description: str,
    taxonomy: Optional[list[dict]] = None,
) -> dict[str, Any]:
    """
    Automatically extract structured requirements from a job description:
    - mandatory / required skills
    - preferred skills
    - minimum experience years
    - education requirements
    - additional qualifications
    - semantic embedding
    """
    full_text = f"{title}\n{description}".strip()
    prep = preprocess_text(full_text)
    cleaned = prep["cleaned_text"]

    # Split lines into required vs preferred context
    req_lines: list[str] = []
    pref_lines: list[str] = []
    mode = "required"
    for line in cleaned.split("\n"):
        low = line.lower()
        if PREFERRED_SECTION_RE.search(low):
            mode = "preferred"
            pref_lines.append(line)
            continue
        if REQUIRED_SECTION_RE.search(low):
            mode = "required"
            req_lines.append(line)
            continue
        if any(k in low for k in ("nice to have", "preferred:", "bonus:", "good to have", "plus:")):
            pref_lines.append(line)
        elif mode == "preferred":
            pref_lines.append(line)
        else:
            req_lines.append(line)

    req_text = "\n".join(req_lines) if req_lines else cleaned
    pref_text = "\n".join(pref_lines)

    tax = taxonomy or DEFAULT_SKILL_TAXONOMY
    req_matches = extract_skills_from_text(
        req_text,
        taxonomy=tax,
        sentences=prep["sentences"],
        embed_fn=embed_texts,
        enable_semantic=True,
    )
    pref_matches = extract_skills_from_text(
        pref_text,
        taxonomy=tax,
        sentences=None,
        embed_fn=None,
        enable_semantic=False,
    ) if pref_text.strip() else []

    required_skills = [m.name for m in req_matches]
    preferred_skills = [m.name for m in pref_matches if m.name not in required_skills]

    # Minimum experience extraction
    exp_vals = [float(m.group(1)) for m in EXP_YEARS_RE.finditer(cleaned) if float(m.group(1)) <= 30]
    min_exp = min(exp_vals) if exp_vals else 0.0

    # Education requirement extraction
    edu_req = "Bachelor's"
    best_rank = 0
    for level, pat in DEGREE_PATTERNS:
        if re.search(pat, cleaned, re.IGNORECASE):
            # Take minimum required if multiple degrees mentioned ("Bachelor's or Master's")
            if best_rank == 0 or DEGREE_RANK[level] < best_rank:
                best_rank = DEGREE_RANK[level]
                edu_req = level
    if best_rank == 0:
        edu_req = "Unspecified"

    # Additional qualifications (lines mentioning certifications, clearance, remote, degree, etc.)
    qual_lines = [
        ln.strip()
        for ln in cleaned.split("\n")
        if any(k in ln.lower() for k in ("certification", "certified", "portfolio", "publication", "open source", "agile"))
    ][:5]

    embedding = embed_single(f"Job Title: {title}\n{cleaned[:4000]}")

    return {
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "min_experience_years": min_exp,
        "education_requirement": edu_req,
        "additional_qualifications": "\n".join(qual_lines),
        "key_phrases": prep["key_phrases"][:20],
        "embedding": embedding,
    }
