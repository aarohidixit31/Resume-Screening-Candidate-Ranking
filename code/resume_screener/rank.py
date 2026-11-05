"""Keyword-matching baselines: TF-IDF + cosine similarity, and BM25."""
from dataclasses import dataclass

from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class RankedCandidate:
    name: str
    tfidf_score: float
    bm25_score: float


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
    tfidf_scores = tfidf_rank(job_text, resume_texts)
    bm25_scores = bm25_rank(job_text, resume_texts)
    candidates = [
        RankedCandidate(name=name, tfidf_score=t, bm25_score=b)
        for name, t, b in zip(names, tfidf_scores, bm25_scores)
    ]
    return sorted(candidates, key=lambda c: c.tfidf_score, reverse=True)
