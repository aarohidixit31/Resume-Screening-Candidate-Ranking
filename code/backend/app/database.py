"""SQLAlchemy engine/session setup. Reads DATABASE_URL from the environment
(.env file in backend/), which should be a PostgreSQL connection string in
production (e.g. a Neon connection string)."""
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Create backend/.env (see backend/.env.example) "
        "with your PostgreSQL connection string."
    )

# SQLite needs this flag for use across FastAPI's worker threads; Postgres ignores it
# (this branch exists only for local dev before a real DATABASE_URL is set).
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
