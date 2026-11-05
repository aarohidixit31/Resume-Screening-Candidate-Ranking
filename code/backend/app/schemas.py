from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# --- Auth ---
class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


# --- Jobs ---
class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=20000)


class JobUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1, max_length=20000)


class JobOut(BaseModel):
    id: int
    title: str
    description: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Candidates ---
class CandidateOut(BaseModel):
    id: int
    job_id: int
    file_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class CandidateDetail(CandidateOut):
    raw_text: str


class UploadFailure(BaseModel):
    file_name: str
    error: str


class ResumeUploadResult(BaseModel):
    created: list[CandidateOut]
    failed: list[UploadFailure]


# --- Results ---
class RankedResult(BaseModel):
    rank: int
    candidate_id: int
    file_name: str
    semantic_score: float
    tfidf_score: float
    bm25_score: float
    final_score: float
