"""Tests for the RAG service."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.rag import RAGService


@pytest.mark.asyncio
async def test_search_returns_te_chunks_preferentially():
    """T&E policy chunks are returned before noise chunks."""
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_collection.count.return_value = 10
    mock_collection.query.return_value = {
        "documents": [["clause about meals", "code of conduct text"]],
        "metadatas": [
            [
                {
                    "doc_id": "TEP-001",
                    "doc_title": "T&E Overview",
                    "section_id": "§2.1",
                    "section_title": "Meals",
                    "is_noise": "False",
                },
                {
                    "doc_id": "COC-001",
                    "doc_title": "Code of Conduct",
                    "section_id": "§1",
                    "section_title": "Ethics",
                    "is_noise": "True",
                },
            ]
        ],
    }
    mock_client.get_or_create_collection.return_value = mock_collection

    with patch("app.services.rag.chromadb.PersistentClient", return_value=mock_client):
        service = RAGService()
        results = await service.search("meal expense cap")

    assert results[0].doc_id == "TEP-001"
    assert all(not c.is_noise for c in results)


@pytest.mark.asyncio
async def test_search_falls_back_to_noise_when_no_te_chunks():
    """If only noise chunks match, they are returned as fallback."""
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_collection.count.return_value = 5
    mock_collection.query.return_value = {
        "documents": [["records retention policy"]],
        "metadatas": [
            [
                {
                    "doc_id": "REC-001",
                    "doc_title": "Records Retention",
                    "section_id": "§1",
                    "section_title": "Purpose",
                    "is_noise": "True",
                }
            ]
        ],
    }
    mock_client.get_or_create_collection.return_value = mock_collection

    with patch("app.services.rag.chromadb.PersistentClient", return_value=mock_client):
        service = RAGService()
        results = await service.search("stock price CEO salary")

    assert len(results) == 1
    assert results[0].doc_id == "REC-001"
