import html
import re
from functools import lru_cache

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import sent_tokenize, word_tokenize

_NLTK_READY = False


def ensure_nltk_data() -> None:
    global _NLTK_READY
    if _NLTK_READY:
        return
    required = [
        ("tokenizers/punkt", "punkt"),
        ("tokenizers/punkt_tab", "punkt_tab"),
        ("corpora/stopwords", "stopwords"),
        ("corpora/wordnet", "wordnet"),
        ("corpora/omw-1.4", "omw-1.4"),
    ]
    for path, pkg in required:
        try:
            nltk.data.find(path)
        except LookupError:
            try:
                nltk.download(pkg, quiet=True)
            except Exception:
                pass
    _NLTK_READY = True


@lru_cache(maxsize=1)
def get_lemmatizer() -> WordNetLemmatizer:
    ensure_nltk_data()
    return WordNetLemmatizer()


@lru_cache(maxsize=1)
def get_stopwords() -> set[str]:
    ensure_nltk_data()
    try:
        return set(stopwords.words("english"))
    except LookupError:
        return {
            "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
            "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
            "to", "was", "were", "will", "with", "this", "or", "we", "you",
        }


@lru_cache(maxsize=1)
def get_spacy_model():
    import spacy

    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        return spacy.blank("en")


def strip_html_and_noise(text: str) -> str:
    """Clean raw resume or dataset text while preserving meaningful line breaks."""
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    # Normalize unicode bullets and dashes
    text = text.replace("\u2022", "\n- ").replace("\uf0b7", "\n- ").replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Remove non-printable characters except newlines/tabs
    text = re.sub(r"[^\x20-\x7E\n\t]", " ", text)
    # Collapse excessive spaces on each line
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.split("\n")]
    # Collapse >2 consecutive blank lines
    cleaned_lines: list[str] = []
    blank_run = 0
    for ln in lines:
        if not ln:
            blank_run += 1
            if blank_run <= 1:
                cleaned_lines.append("")
        else:
            blank_run = 0
            cleaned_lines.append(ln)
    return "\n".join(cleaned_lines).strip()


def preprocess_text(raw_text: str) -> dict:
    """
    Full Step 2 NLP preprocessing:
    - Clean text
    - Tokenization
    - Lowercase normalization
    - Stop-word removal
    - Lemmatization
    - Meaningful sentence & key-phrase extraction
    """
    ensure_nltk_data()
    cleaned_text = strip_html_and_noise(raw_text)
    lower_text = cleaned_text.lower()

    try:
        sentences = [s.strip() for s in sent_tokenize(cleaned_text) if len(s.strip()) > 12]
    except LookupError:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", cleaned_text) if len(s.strip()) > 12]

    try:
        raw_tokens = word_tokenize(lower_text)
    except LookupError:
        raw_tokens = re.findall(r"[a-z0-9+#.\-]+", lower_text)

    stop_words = get_stopwords()
    lemmatizer = get_lemmatizer()

    filtered_tokens: list[str] = []
    lemmatized_tokens: list[str] = []
    for tok in raw_tokens:
        tok_clean = re.sub(r"^[^a-z0-9+#]+|[^a-z0-9+#]+$", "", tok)
        if not tok_clean or len(tok_clean) < 2:
            continue
        if tok_clean in stop_words:
            continue
        filtered_tokens.append(tok_clean)
        try:
            lemma = lemmatizer.lemmatize(tok_clean)
        except Exception:
            lemma = tok_clean
        lemmatized_tokens.append(lemma)

    # Meaningful phrase extraction using spaCy noun chunks (fallback to bigrams)
    key_phrases: list[str] = []
    nlp = get_spacy_model()
    if nlp.has_pipe("parser"):
        doc = nlp(cleaned_text[:20000])
        seen_phrases = set()
        for chunk in doc.noun_chunks:
            phrase = re.sub(r"\s+", " ", chunk.text.strip())
            words = phrase.split()
            if 2 <= len(words) <= 6 and len(phrase) >= 5:
                key_low = phrase.lower()
                if key_low not in seen_phrases:
                    seen_phrases.add(key_low)
                    key_phrases.append(phrase)
            if len(key_phrases) >= 40:
                break
    else:
        for i in range(len(filtered_tokens) - 1):
            bg = f"{filtered_tokens[i]} {filtered_tokens[i+1]}"
            if bg not in key_phrases:
                key_phrases.append(bg)
            if len(key_phrases) >= 30:
                break

    return {
        "cleaned_text": cleaned_text,
        "normalized_text": " ".join(lemmatized_tokens),
        "tokens": filtered_tokens,
        "lemmatized_tokens": lemmatized_tokens,
        "sentences": sentences[:60],
        "key_phrases": key_phrases,
    }
