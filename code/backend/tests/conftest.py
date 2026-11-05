"""Test configuration. Sets env vars BEFORE importing the app (database.py
and auth.py both read them at import time), and swaps in an isolated
in-memory SQLite database so tests never touch the real Neon database.
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import itertools

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, get_db
from backend.app.main import app, limiter

# One shared in-memory connection for the whole test run (StaticPool keeps
# the same connection alive across requests; plain :memory: would otherwise
# give each connection a fresh, empty database).
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=test_engine)
Base.metadata.create_all(bind=test_engine)


def _override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Each test gets a fresh rate-limit counter so tests don't interfere
    with each other via slowapi's shared in-memory storage."""
    limiter.reset()
    yield


@pytest.fixture()
def client():
    return TestClient(app)


# Module-level (not per-test) so emails stay unique across the whole run —
# the in-memory DB persists for the full test session, not just one test.
_email_counter = itertools.count(1)


@pytest.fixture()
def make_user(client):
    """Returns a function that signs up a fresh user and returns (email, auth_headers)."""

    def _make_user():
        email = f"user{next(_email_counter)}@example.com"
        res = client.post("/auth/signup", json={"email": email, "password": "testpass123"})
        assert res.status_code == 200, res.text
        token = res.json()["access_token"]
        return email, {"Authorization": f"Bearer {token}"}

    return _make_user
