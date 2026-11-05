"""Command-line entry point: rank a folder of resumes against one job description.

Usage:
    python -m resume_screener.cli --job sample_data/job_description.docx --resumes sample_data/resumes
"""
import argparse
from pathlib import Path

from .parser import extract_text
from .preprocess import clean_text
from .rank import rank_candidates


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank resumes against a job description (keyword baseline).")
    parser.add_argument("--job", required=True, help="Path to the job description (PDF or DOCX)")
    parser.add_argument("--resumes", required=True, help="Folder of resumes (PDF or DOCX)")
    args = parser.parse_args()

    job_text = clean_text(extract_text(Path(args.job)))

    resume_paths = sorted(
        p for p in Path(args.resumes).iterdir() if p.suffix.lower() in (".pdf", ".docx")
    )
    if not resume_paths:
        raise SystemExit(f"No .pdf or .docx resumes found in {args.resumes}")

    names = [p.stem for p in resume_paths]
    resume_texts = [clean_text(extract_text(p)) for p in resume_paths]

    ranked = rank_candidates(job_text, names, resume_texts)

    print(f"\nJob description: {args.job}")
    print(f"Candidates ranked: {len(ranked)}\n")
    print(f"{'Rank':<5}{'Candidate':<30}{'TF-IDF cosine':<16}{'BM25 score':<12}")
    for i, c in enumerate(ranked, start=1):
        print(f"{i:<5}{c.name:<30}{c.tfidf_score:<16.4f}{c.bm25_score:<12.4f}")


if __name__ == "__main__":
    main()
