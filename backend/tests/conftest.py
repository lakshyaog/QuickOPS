"""
pytest fixtures — shared across all test modules.

Strategy
--------
1. Set DATABASE_URL to SQLite BEFORE app.main is imported so that
   `Base.metadata.create_all(bind=engine)` in main.py uses SQLite,
   not the real PostgreSQL engine.
2. Override the `get_db` FastAPI dependency so every TestClient request
   uses the same in-memory session as the test itself.

No running PostgreSQL or Docker container is required.
"""
import os

# ── MUST happen before any app imports ────────────────────────────────────────
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

# ── In-memory SQLite engine ────────────────────────────────────────────────────
# StaticPool keeps the same in-memory DB across all connections in one process.
SQLITE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Session fixture ────────────────────────────────────────────────────────────
@pytest.fixture(scope="function")
def db():
    """Create all tables before each test, yield a fresh session, drop tables after."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# ── HTTP client fixture ────────────────────────────────────────────────────────
@pytest.fixture(scope="function")
def client(db):
    """
    FastAPI TestClient wired to the in-memory SQLite session.
    The `get_db` dependency is overridden so API routes use the test DB.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass  # lifecycle managed by `db` fixture above

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()
