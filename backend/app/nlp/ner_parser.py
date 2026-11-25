import re
from datetime import datetime
from typing import Any

from .preprocessor import get_spacy_model

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)\d{3,4}[\s.-]?\d{3,5}")
EXP_YEARS_RE = re.compile(
    r"(\d{1,2}(?:\.\d)?)\s*\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp|work|industry|professional)?",
    re.IGNORECASE,
)
DATE_RANGE_RE = re.compile(
    r"\b((?:19|20)\d{2})\s*(?:-|to|\u2013|\u2014)\s*((?:19|20)\d{2}|present|current|now|till\s*date)\b",
    re.IGNORECASE,
)
GRAD_YEAR_RE = re.compile(r"\b(19[89]\d|20[0-3]\d)\b")

DEGREE_PATTERNS: list[tuple[str, str]] = [
    ("PhD", r"\b(?:ph\.?d\.?|doctorate|doctor of philosophy)\b"),
    ("Master's", r"\b(?:m\.?tech|m\.?e\.?|m\.?s\.?|m\.?sc\.?|m\.?b\.?a\.?|m\.?c\.?a\.?|master(?:'s)?|post\s*graduate)\b"),
    ("Bachelor's", r"\b(?:b\.?tech|b\.?e\.?|b\.?s\.?|b\.?sc\.?|b\.?c\.?a\.?|b\.?com|b\.?a\.?|bachelor(?:'s)?|undergraduate)\b"),
    ("Diploma", r"\b(?:diploma|associate degree|polytechnic)\b"),
]

DEGREE_RANK = {"PhD": 4, "Master's": 3, "Bachelor's": 2, "Diploma": 1, "Unspecified": 0}

CERT_KEYWORDS = [
    "aws certified", "azure", "google cloud", "pmp", "scrum master", "csm",
    "cka", "ckad", "cissp", "ceh", "tensorflow developer", "oracle certified",
    "coursera", "udemy", "nptel", "microsoft certified", "red hat", "comptia",
]

NON_NAME_HEADER_TOKENS = {
    "resume", "curriculum", "vitae", "cv", "profile", "summary", "objective",
    "experience", "education", "skills", "contact", "projects", "certifications",
    "developer", "engineer", "scientist", "analyst", "manager", "administrator",
    "consultant", "intern", "specialist", "architect", "designer",
}


def _split_sections(cleaned_text: str) -> dict[str, list[str]]:
    section_headers = {
        "experience": re.compile(r"^(?:work\s+)?(?:experience|employment|professional\s+experience|career\s+history)\b", re.I),
        "education": re.compile(r"^(?:education|academic|qualifications)\b", re.I),
        "projects": re.compile(r"^(?:projects|personal\s+projects|key\s+projects)\b", re.I),
        "certifications": re.compile(r"^(?:certifications?|licenses?|achievements?|awards)\b", re.I),
        "skills": re.compile(r"^(?:skills|technical\s+skills|core\s+competencies|technologies)\b", re.I),
    }

    sections: dict[str, list[str]] = {"header": [], "experience": [], "education": [], "projects": [], "certifications": [], "skills": [], "other": []}
    current = "header"
    for idx, line in enumerate(cleaned_text.split("\n")):
        stripped = line.strip()
        if not stripped:
            continue
        matched_section = None
        if len(stripped) <= 45:
            clean_hdr = re.sub(r"[:\-|]+$", "", stripped).strip()
            for sec_name, pat in section_headers.items():
                if pat.match(clean_hdr):
                    matched_section = sec_name
                    break
        if matched_section:
            current = matched_section
            continue
        if current == "header" and idx > 12:
            current = "other"
        sections[current].append(stripped)
    return sections


def _extract_name(cleaned_text: str, doc) -> str | None:
    lines = [ln.strip() for ln in cleaned_text.split("\n") if ln.strip()][:8]
    # 1. Check top header lines for clean 2-4 word alphabetic name
    for ln in lines:
        if "@" in ln or any(ch.isdigit() for ch in ln) or len(ln) > 45:
            continue
        words = re.findall(r"[A-Za-z][A-Za-z.\-']*", ln)
        if 2 <= len(words) <= 4:
            lowered = {w.lower().strip(".") for w in words}
            if not (lowered & NON_NAME_HEADER_TOKENS):
                if all(w[0].isupper() for w in words if len(w) > 1):
                    return " ".join(words)

    # 2. Fallback to spaCy PERSON entity near start of document
    if doc is not None:
        for ent in doc.ents:
            if ent.label_ == "PERSON" and ent.start_char < 350:
                words = ent.text.strip().split()
                if 2 <= len(words) <= 4 and not any(w.lower() in NON_NAME_HEADER_TOKENS for w in words):
                    return ent.text.strip()
    return None


def _extract_education(cleaned_text: str, edu_lines: list[str], doc) -> dict[str, Any]:
    target_text = "\n".join(edu_lines) if edu_lines else cleaned_text
    best_level = "Unspecified"
    best_rank = 0
    degree_snippet = None

    for level, pat in DEGREE_PATTERNS:
        m = re.search(pat, target_text, re.IGNORECASE)
        if m and DEGREE_RANK[level] > best_rank:
            best_rank = DEGREE_RANK[level]
            best_level = level
            # Grab surrounding line for degree name
            for ln in target_text.split("\n"):
                if re.search(pat, ln, re.IGNORECASE):
                    degree_snippet = ln[:160].strip()
                    break

    # Fallback check across full text if education section didn't match
    if best_level == "Unspecified" and edu_lines:
        for level, pat in DEGREE_PATTERNS:
            m = re.search(pat, cleaned_text, re.IGNORECASE)
            if m and DEGREE_RANK[level] > best_rank:
                best_rank = DEGREE_RANK[level]
                best_level = level
                degree_snippet = m.group(0)

    university = None
    for ln in target_text.split("\n"):
        if re.search(r"\b(university|institute|college|school of|academy|iit|nit|mit|stanford)\b", ln, re.I):
            university = ln[:160].strip()
            break
    if not university and doc is not None:
        for ent in doc.ents:
            if ent.label_ == "ORG" and re.search(r"university|institute|college", ent.text, re.I):
                university = ent.text.strip()
                break

    grad_year = None
    years = GRAD_YEAR_RE.findall(target_text)
    if years:
        grad_year = max(years)

    entries = edu_lines[:6] if edu_lines else ([degree_snippet] if degree_snippet else [])
    return {
        "education_level": best_level,
        "degree": degree_snippet,
        "university": university,
        "graduation_year": grad_year,
        "education_entries": entries,
    }


def _extract_experience(cleaned_text: str, exp_lines: list[str], doc) -> dict[str, Any]:
    explicit_years = [float(m.group(1)) for m in EXP_YEARS_RE.finditer(cleaned_text[:3000]) if float(m.group(1)) <= 45]
    max_explicit = max(explicit_years) if explicit_years else 0.0

    # Date-range calculation across experience section or full text
    current_year = datetime.now().year
    intervals: list[tuple[int, int]] = []
    source_for_dates = "\n".join(exp_lines) if exp_lines else cleaned_text
    for m in DATE_RANGE_RE.finditer(source_for_dates):
        start_yr = int(m.group(1))
        end_raw = m.group(2).lower()
        end_yr = current_year if any(k in end_raw for k in ("present", "current", "now", "till")) else int(end_raw)
        if 1980 <= start_yr <= end_yr <= current_year + 1 and (end_yr - start_yr) <= 40:
            intervals.append((start_yr, end_yr))

    range_years = 0.0
    if intervals:
        intervals.sort()
        merged: list[list[int]] = []
        for s, e in intervals:
            if not merged or s > merged[-1][1]:
                merged.append([s, e])
            else:
                merged[-1][1] = max(merged[-1][1], e)
        range_years = sum(max(1, e - s) for s, e in merged)

    total_years = round(max(max_explicit, min(40.0, float(range_years))), 1)

    work_entries: list[str] = []
    for ln in exp_lines:
        if len(ln) >= 12 and not ln.startswith("- "):
            work_entries.append(ln[:180])
        if len(work_entries) >= 8:
            break
    if not work_entries and doc is not None:
        orgs = list(dict.fromkeys(ent.text.strip() for ent in doc.ents if ent.label_ == "ORG" and len(ent.text.strip()) > 2))
        work_entries = orgs[:5]

    summary = " ".join(exp_lines[:4])[:450] if exp_lines else cleaned_text[:350]
    return {
        "total_experience_years": total_years,
        "experience_summary": summary,
        "work_experience": work_entries,
    }


def extract_entities_and_sections(cleaned_text: str) -> dict[str, Any]:
    """Step 3 NLP Information Extraction via spaCy NER + regex + section rules."""
    nlp = get_spacy_model()
    doc = nlp(cleaned_text[:18000]) if cleaned_text else None
    sections = _split_sections(cleaned_text)

    email_match = EMAIL_RE.search(cleaned_text)
    email = email_match.group(0) if email_match else None

    phone = None
    for m in PHONE_RE.finditer(cleaned_text[:1500]):
        digits = re.sub(r"\D", "", m.group(0))
        if 10 <= len(digits) <= 13:
            phone = m.group(0).strip()
            break

    location = None
    if doc is not None:
        for ent in doc.ents:
            if ent.label_ in ("GPE", "LOC") and ent.start_char < 600:
                if "@" not in ent.text and len(ent.text.strip()) > 2:
                    location = ent.text.strip()
                    break

    full_name = _extract_name(cleaned_text, doc)
    edu_info = _extract_education(cleaned_text, sections["education"], doc)
    exp_info = _extract_experience(cleaned_text, sections["experience"], doc)

    # Projects
    projects = [ln.lstrip("- ").strip()[:180] for ln in sections["projects"][:8] if len(ln.strip()) > 8]

    # Certifications (section lines + keyword scan)
    certs: list[str] = [ln.lstrip("- ").strip()[:160] for ln in sections["certifications"][:8] if len(ln.strip()) > 5]
    if not certs:
        for ln in cleaned_text.split("\n"):
            if any(kw in ln.lower() for kw in CERT_KEYWORDS) and len(ln.strip()) <= 160:
                certs.append(ln.strip())
                if len(certs) >= 6:
                    break

    return {
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "location": location,
        "total_experience_years": exp_info["total_experience_years"],
        "experience_summary": exp_info["experience_summary"],
        "work_experience": exp_info["work_experience"],
        "education_level": edu_info["education_level"],
        "degree": edu_info["degree"],
        "university": edu_info["university"],
        "graduation_year": edu_info["graduation_year"],
        "education": edu_info["education_entries"],
        "projects": projects,
        "certifications": certs,
    }
