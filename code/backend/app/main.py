"""FastAPI backend for the resume screening & candidate ranking app.

Full-stack, multi-tenant version: every job/candidate/score row belongs to
the authenticated user who created it, backed by PostgreSQL via SQLAlchemy.
Ranking uses the TF-IDF / BM25 keyword baseline (resume_screener package);
semantic matching (Sentence-BERT) and the learning-to-rank model are a
later milestone.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from resume_screener.embeddings import semantic_rank
from resume_screener.parser import extract_text_from_bytes
from resume_screener.preprocess import clean_text
from resume_screener.rank import bm25_rank, blend_scores, tfidf_rank

from . import models, schemas
from .auth import create_access_token, get_current_user, hash_password, verify_password
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Resume Screening & Candidate Ranking API")

# Rate limiting: keyed by client IP. In-memory by default, which is fine for a
# single server instance; a multi-instance deployment would need a shared
# backend (e.g. Redis) via slowapi's storage_uri.
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS_ORIGINS: comma-separated list, e.g. "https://app.example.com,http://localhost:5173"
_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
allowed_origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", _default_origins).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


# --- Auth ---
# Rate-limited by client IP to blunt brute-force login attempts and signup spam.
@app.post("/auth/signup", response_model=schemas.TokenResponse)
@limiter.limit("5/hour")
def signup(request: Request, body: schemas.SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    user = models.User(email=body.email, hashed_password=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return schemas.TokenResponse(access_token=create_access_token(str(user.id)))


@app.post("/auth/login", response_model=schemas.TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, body: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return schemas.TokenResponse(access_token=create_access_token(str(user.id)))


@app.get("/auth/me", response_model=schemas.UserOut)
def read_current_user(current_user: models.User = Depends(get_current_user)):
    return current_user


# --- Jobs (all scoped to the authenticated user) ---
@app.get("/jobs", response_model=list[schemas.JobOut])
def list_jobs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.Job)
        .filter(models.Job.user_id == current_user.id)
        .order_by(models.Job.id.desc())
        .all()
    )


@app.post("/jobs", response_model=schemas.JobOut)
def create_job(
    job: schemas.JobCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_job = models.Job(user_id=current_user.id, title=job.title, description=job.description)
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


def _get_owned_job(job_id: int, db: Session, current_user: models.User) -> models.Job:
    job = db.get(models.Job, job_id)
    if job is None or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.patch("/jobs/{job_id}", response_model=schemas.JobOut)
def update_job(
    job_id: int,
    body: schemas.JobUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    job = _get_owned_job(job_id, db, current_user)
    if body.title is not None:
        job.title = body.title
    if body.description is not None:
        job.description = body.description
    db.commit()
    db.refresh(job)
    return job


@app.delete("/jobs/{job_id}", status_code=204)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    job = _get_owned_job(job_id, db, current_user)
    db.delete(job)  # cascades to candidates and scores via the ORM relationship config
    db.commit()


@app.post("/jobs/{job_id}/resumes", response_model=schemas.ResumeUploadResult)
async def upload_resumes(
    job_id: int,
    files: list[UploadFile],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    job = _get_owned_job(job_id, db, current_user)

    created = []
    failed = []
    for f in files:
        data = await f.read()
        try:
            text = extract_text_from_bytes(data, f.filename)
        except Exception as exc:
            # Isolated per file: one corrupt/unsupported resume shouldn't fail
            # the whole batch when the others parsed fine.
            failed.append(schemas.UploadFailure(file_name=f.filename, error=str(exc)))
            continue

        candidate = models.Candidate(job_id=job.id, file_name=f.filename, raw_text=text)
        db.add(candidate)
        created.append(candidate)

    db.commit()
    for c in created:
        db.refresh(c)
    return schemas.ResumeUploadResult(created=created, failed=failed)


@app.post("/jobs/{job_id}/rank", response_model=list[schemas.RankedResult])
def rank_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    job = _get_owned_job(job_id, db, current_user)

    candidates = db.query(models.Candidate).filter(models.Candidate.job_id == job.id).all()
    if not candidates:
        raise HTTPException(status_code=400, detail="No resumes uploaded for this job yet")

    job_text = clean_text(job.description)
    resume_texts = [clean_text(c.raw_text) for c in candidates]

    tfidf_scores = tfidf_rank(job_text, resume_texts)
    bm25_scores = bm25_rank(job_text, resume_texts)
    semantic_scores = semantic_rank(job_text, resume_texts)
    blended = blend_scores(semantic_scores, tfidf_scores, bm25_scores)

    # Zip candidates with their scores by position (both lists came from the
    # same `candidates` query, in the same order) rather than matching by
    # filename, which could collide if two resumes share a name.
    paired = sorted(zip(candidates, blended), key=lambda cb: cb[1].final_score, reverse=True)

    db.query(models.Score).filter(models.Score.job_id == job.id).delete()

    results = []
    for i, (candidate, b) in enumerate(paired, start=1):
        score = models.Score(
            candidate_id=candidate.id,
            job_id=job.id,
            semantic_score=b.semantic_score,
            tfidf_score=b.tfidf_score,
            bm25_score=b.bm25_score,
            final_score=b.final_score,
            rank=i,
        )
        db.add(score)
        results.append(
            schemas.RankedResult(
                rank=i,
                candidate_id=candidate.id,
                file_name=candidate.file_name,
                semantic_score=b.semantic_score,
                tfidf_score=b.tfidf_score,
                bm25_score=b.bm25_score,
                final_score=b.final_score,
            )
        )
    db.commit()
    return results


@app.get("/jobs/{job_id}/results", response_model=list[schemas.RankedResult])
def get_results(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    job = _get_owned_job(job_id, db, current_user)
    scores = (
        db.query(models.Score)
        .filter(models.Score.job_id == job.id)
        .order_by(models.Score.rank.asc())
        .all()
    )
    return [
        schemas.RankedResult(
            rank=s.rank,
            candidate_id=s.candidate_id,
            file_name=s.candidate.file_name,
            semantic_score=s.semantic_score,
            tfidf_score=s.tfidf_score,
            bm25_score=s.bm25_score,
            final_score=s.final_score,
        )
        for s in scores
    ]


@app.get("/candidates/{candidate_id}", response_model=schemas.CandidateDetail)
def get_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    candidate = db.get(models.Candidate, candidate_id)
    if candidate is None or candidate.job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate
