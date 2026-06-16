"""API integration tests (no real Anthropic calls, isolated ChromaDB)."""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_session
from app.models.employee import Employee

TEST_DB = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(TEST_DB)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def client(session, tmp_path):
    """TestClient with DB and RAG dependencies isolated."""
    chroma_dir = str(tmp_path / "chroma")
    os.makedirs(chroma_dir, exist_ok=True)

    # Patch ChromaDB to avoid real indexing in API tests
    mock_chroma_client = MagicMock()
    mock_collection = MagicMock()
    mock_collection.count.return_value = 0
    mock_collection.get.return_value = {"ids": [], "metadatas": [], "documents": []}
    mock_collection.query.return_value = {"documents": [[]], "metadatas": [[]]}
    mock_chroma_client.get_or_create_collection.return_value = mock_collection

    with patch("app.services.rag.chromadb.PersistentClient", return_value=mock_chroma_client):
        # Reset singleton for isolation
        import app.services.rag as rag_module
        original = rag_module._rag_service
        rag_module._rag_service = None

        from app.main import create_app
        app = create_app()

        async def _override():
            yield session

        app.dependency_overrides[get_session] = _override

        with TestClient(app, raise_server_exceptions=False) as c:
            yield c

        rag_module._rag_service = original


@pytest_asyncio.fixture
async def seeded_employee(session):
    emp = Employee(
        id="NW-04821",
        name="Sarah Chen",
        grade=5,
        title="Operations Manager",
        department="Logistics Ops",
        manager_id="NW-03012",
        home_base="Irvine, CA",
    )
    session.add(emp)
    await session.commit()
    return emp


def test_get_employees_empty(client):
    resp = client.get("/api/employees")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_and_get_employee(client):
    payload = {
        "id": "NW-99999",
        "name": "Test User",
        "grade": 3,
        "title": "Analyst",
        "department": "Finance",
        "home_base": "Chicago, IL",
    }
    resp = client.post("/api/employees", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] == "NW-99999"
    assert data["name"] == "Test User"

    resp2 = client.get("/api/employees/NW-99999")
    assert resp2.status_code == 200
    assert resp2.json()["name"] == "Test User"


def test_create_submission(client, seeded_employee):
    payload = {
        "employee_id": "NW-04821",
        "trip_purpose": "Client meeting",
        "trip_start": "2025-04-14",
        "trip_end": "2025-04-16",
    }
    resp = client.post("/api/submissions", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["employee_id"] == "NW-04821"
    assert data["status"] == "pending"


def test_create_submission_invalid_employee(client):
    payload = {
        "employee_id": "NW-99999",
        "trip_purpose": "Trip",
        "trip_start": "2025-01-01",
        "trip_end": "2025-01-02",
    }
    resp = client.post("/api/submissions", json=payload)
    assert resp.status_code == 404


def test_unsupported_file_type_returns_422(client, seeded_employee):
    payload = {
        "employee_id": "NW-04821",
        "trip_purpose": "Test trip",
        "trip_start": "2025-04-14",
        "trip_end": "2025-04-16",
    }
    sub_resp = client.post("/api/submissions", json=payload)
    sub_id = sub_resp.json()["id"]

    resp = client.post(
        f"/api/submissions/{sub_id}/receipts",
        files={"file": ("test.docx", b"content", "application/octet-stream")},
    )
    assert resp.status_code == 422
