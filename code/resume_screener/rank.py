"""Candidate ranking: keyword baselines (TF-IDF, BM25) plus a blended
score that also folds in semantic similarity (see embeddings.py).

The CLI (cli.py) still uses the plain keyword baseline only, so it stays
lightweight and doesn't require the sentence-transformers/torch install.
The full web app uses blend_scores, which combines all three signals.
"""
from dataclasses import dataclass

from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Weights for the blended final score. Semantic similarity is weighted
# heaviest since it's the project's actual differentiator over keyword
# matching; BM25 and TF-IDF remain as secondary signals. These mirror the
# project's documented weighted-sum approach (f_doc-dominant, pending the
# skill-level NER features for a future milestone).
WEIGHT_SEMANTIC = 0.6
WEIGHT_TFIDF = 0.25
WEIGHT_BM25 = 0.15


@dataclass
class RankedCandidate:
    name: str
    tfidf_score: float
    bm25_score: float


@dataclass
class BlendedScore:
    semantic_score: float
    tfidf_score: float
    bm25_score: float
    final_score: float


def tfidf_rank(job_text: str, resume_texts: list[str]) -> list[float]:
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform([job_text] + resume_texts)
    job_vec, resume_vecs = matrix[0:1], matrix[1:]
    return cosine_similarity(job_vec, resume_vecs)[0].tolist()


def bm25_rank(job_text: str, resume_texts: list[str]) -> list[float]:
    tokenized_resumes = [text.split() for text in resume_texts]
    bm25 = BM25Okapi(tokenized_resumes)
    return bm25.get_scores(job_text.split()).tolist()


def rank_candidates(job_text: str, names: list[str], resume_texts: list[str]) -> list[RankedCandidate]:
    """Keyword-only baseline (TF-IDF + BM25), used by the CLI."""
    tfidf_scores = tfidf_rank(job_text, resume_texts)
    bm25_scores = bm25_rank(job_text, resume_texts)
    candidates = [
        RankedCandidate(name=name, tfidf_score=t, bm25_score=b)
        for name, t, b in zip(names, tfidf_scores, bm25_scores)
    ]
    return sorted(candidates, key=lambda c: c.tfidf_score, reverse=True)


def blend_scores(
    semantic_scores: list[float],
    tfidf_scores: list[float],
    bm25_scores: list[float],
) -> list[BlendedScore]:
    """Combine semantic similarity with the keyword baselines into one
    final score per resume, returned in the SAME order as the input lists
    (not sorted, no name/identity field) so the caller can zip the result
    back against its own candidate records by position — avoids any risk
    of misattributing a score if two resumes share a filename.

    BM25 is unbounded, so it's min-max normalized against the max score in
    this candidate pool before blending (raw bm25_score is still returned
    for display)."""
    max_bm25 = max(bm25_scores) if bm25_scores and max(bm25_scores) > 0 else 1.0

    results = []
    for sem, tfidf, bm25 in zip(semantic_scores, tfidf_scores, bm25_scores):
        normalized_bm25 = bm25 / max_bm25
        final = WEIGHT_SEMANTIC * max(sem, 0.0) + WEIGHT_TFIDF * tfidf + WEIGHT_BM25 * normalized_bm25
        results.append(
            BlendedScore(semantic_score=sem, tfidf_score=tfidf, bm25_score=bm25, final_score=final)
        )
    return results
