from functools import lru_cache
from typing import Iterable, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..config import settings


@lru_cache(maxsize=1)
def get_embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.EMBEDDING_MODEL_NAME)


def embed_texts(texts: Iterable[str]) -> np.ndarray:
    """Generate L2-normalized Sentence Transformer embeddings for texts."""
    text_list = [t if (t and t.strip()) else "empty" for t in texts]
    if not text_list:
        return np.zeros((0, 384), dtype=np.float32)
    model = get_embedding_model()
    vecs = model.encode(
        text_list,
        normalize_embeddings=True,
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    return np.asarray(vecs, dtype=np.float32)


def embed_single(text: str) -> list[float]:
    vec = embed_texts([text])[0]
    return [round(float(x), 6) for x in vec.tolist()]


def cosine_sim_vectors(vec_a: Optional[list[float]], vec_b: Optional[list[float]]) -> float:
    """Cosine similarity in [0.0, 1.0] for two normalized or unnormalized vectors."""
    if not vec_a or not vec_b:
        return 0.0
    a = np.asarray(vec_a, dtype=np.float32)
    b = np.asarray(vec_b, dtype=np.float32)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom <= 1e-12:
        return 0.0
    sim = float(np.dot(a, b) / denom)
    # Clamp cosine similarity to [0, 1] for scoring interpretability
    return max(0.0, min(1.0, sim))


def compute_tfidf_similarity(text_a: str, text_b: str) -> float:
    """Compute TF-IDF cosine similarity between two texts using scikit-learn."""
    if not text_a or not text_b or not text_a.strip() or not text_b.strip():
        return 0.0
    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=5000,
        )
        matrix = vectorizer.fit_transform([text_a, text_b])
        sim = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
        return max(0.0, min(1.0, sim))
    except ValueError:
        return 0.0
