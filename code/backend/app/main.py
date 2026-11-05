"""FastAPI backend for the resume screening & candidate ranking app.

Full-stack, multi-tenant version: every job/candidate/score row belongs to
the authenticated user who created it, backed by PostgreSQL via SQLAlchemy.
Ranking uses the TF-IDF / BM25 keyword baseline (resume_screener package);
semantic matching (Sentence-BERT) and the learning-to-rank model are a
later milestone.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import Depends, FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from resume_screener.parser import extract_text_from_bytes
from resume_screener.preprocess import clean_text
from resume_screener.rank import rank_candidates

from . import models, schemas
from .auth import create_access_token, get_current_user, hash_password, verify_password
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Resume Screening & Candidate Ranking API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Auth ---
@app.post("/auth/signup", response_model=schemas.TokenResponse)
def signup(body: schemas.SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    user = models.User(email=body.email, hashed_password=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return schemas.TokenResponse(access_token=create_access_token(str(user.id)))


@app.post("/auth/login", response_model=schemas.TokenResponse)
def login(body: schemas.LoginRequest, db: Session = Depends(get_db)):
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


@app.post("/jobs/{job_id}/resumes", response_model=list[schemas.CandidateOut])
async def upload_resumes(
    job_id: int,
    files: list[UploadFile],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    job = _get_owned_job(job_id, db, current_user)

    created = []
    for f in files:
        data = await f.read()
        try:
            text = extract_text_from_bytes(data, f.filename)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        candidate = models.Candidate(job_id=job.id, file_name=f.filename, raw_text=text)
        db.add(candidate)
        created.append(candidate)

    db.commit()
    for c in created:
        db.refresh(c)
    return created


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
    names = [c.file_name for c in candidates]
    name_to_candidate = {c.file_name: c for c in candidates}

    ranked = rank_candidates(job_text, names, resume_texts)

    db.query(models.Score).filter(models.Score.job_id == job.id).delete()

    results = []
    for i, c in enumerate(ranked, start=1):
        candidate = name_to_candidate[c.name]
        score = models.Score(
            candidate_id=candidate.id,
            job_id=job.id,
            tfidf_score=c.tfidf_score,
            bm25_score=c.bm25_score,
            rank=i,
        )
        db.add(score)
        results.append(
            schemas.RankedResult(
                rank=i,
                candidate_id=candidate.id,
                file_name=candidate.file_name,
                tfidf_score=c.tfidf_score,
                bm25_score=c.bm25_score,
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
            tfidf_score=s.tfidf_score,
            bm25_score=s.bm25_score,
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
