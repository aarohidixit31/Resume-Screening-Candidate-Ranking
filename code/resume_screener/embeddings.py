"""Semantic similarity between a job description and resumes, using
Sentence-BERT (all-MiniLM-L6-v2) whole-document embeddings and cosine
similarity. This is the f_doc feature from the project's documented
methodology; skill-level matching (NER + per-skill similarity) is a
later milestone.
"""
from functools import lru_cache

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    # Loaded once per process and cached; loading the model takes a few
    # seconds, so the first request after a server restart will be slower.
    return SentenceTransformer(MODEL_NAME)


def semantic_rank(job_text: str, resume_texts: list[str]) -> list[float]:
    """Cosine similarity between the job description and each resume's
    whole-document embedding. Returns one score per resume, same order
    as resume_texts."""
    model = _get_model()
    job_vec = model.encode([job_text])
    resume_vecs = model.encode(resume_texts)
    return cosine_similarity(job_vec, resume_vecs)[0].tolist()
