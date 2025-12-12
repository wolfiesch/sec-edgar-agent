"""Tests for vector store functionality."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from src.data.vector_store import FilingVectorStore, get_vector_store


class TestVectorStoreInit:
    """Tests for FilingVectorStore initialization."""

    @patch("src.data.vector_store.chromadb.PersistentClient")
    def test_init_creates_client_and_collection(self, mock_client_class: Mock) -> None:
        """Test that initialization sets up ChromaDB client and collection."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client

        store = FilingVectorStore()

        assert store.client == mock_client
        assert store.collection == mock_collection
        mock_client_class.assert_called_once()
        mock_client.get_or_create_collection.assert_called_once_with(
            name="sec_filings",
            metadata={"description": "SEC filing sections for semantic search"},
        )

    @patch("src.data.vector_store.chromadb.PersistentClient")
    def test_init_creates_persist_dir(self, mock_client_class: Mock, tmp_path: Path) -> None:
        """Test that persist directory is created if it doesn't exist."""
        test_dir = tmp_path / "test_chroma"
        assert not test_dir.exists()

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        FilingVectorStore(persist_dir=test_dir)

        assert test_dir.exists()


class TestAddFilingSection:
    """Tests for add_filing_section method."""

    @patch("src.data.vector_store.chromadb.PersistentClient")
    def test_add_filing_section_short_content(self, mock_client_class: Mock) -> None:
        """Test adding a filing section with short content (no chunking)."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client

        store = FilingVectorStore()

        doc_id = store.add_filing_section(
            ticker="AAPL",
            accession_number="0000320193-23-000106",
            section_name="Risk Factors",
            content="Our business faces various risks...",
            metadata={"form_type": "10-K", "filing_date": "2023-10-27"},
        )

        # Verify upsert was called once (no chunking)
        assert mock_collection.upsert.call_count == 1
        call_args = mock_collection.upsert.call_args

        assert len(call_args.kwargs["ids"]) == 1
        assert call_args.kwargs["documents"][0] == "Our business faces various risks..."
        assert call_args.kwargs["metadatas"][0]["ticker"] == "AAPL"
        assert call_args.kwargs["metadatas"][0]["accession_number"] == "0000320193-23-000106"
        assert call_args.kwargs["metadatas"][0]["section_name"] == "Risk Factors"
        assert call_args.kwargs["metadatas"][0]["form_type"] == "10-K"
        assert isinstance(doc_id, str)

    @patch("src.data.vector_store.chromadb.PersistentClient")
    def test_add_filing_section_long_content_chunked(self, mock_client_class: Mock) -> None:
        """Test that long content is chunked appropriately."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client

        store = FilingVectorStore()

        # Create content > 8000 chars
        long_content = "A" * 9000

        store.add_filing_section(
            ticker="MSFT",
            accession_number="0001564590-23-012345",
            section_name="Business",
            content=long_content,
        )

        # Verify multiple upsert calls (chunking occurred)
        assert mock_collection.upsert.call_count >= 2

    @patch("src.data.vector_store.chromadb.PersistentClient")
    def test_add_filing_section_normalizes_ticker(self, mock_client_class: Mock) -> None:
        """Test that ticker is normalized to uppercase."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client

        store = FilingVectorStore()

        store.add_filing_section(
            ticker="aapl",  # lowercase
            accession_number="123",
            section_name="Test",
            content="Content",
        )

        call_args = mock_collection.upsert.call_args
        assert call_args.kwargs["metadatas"][0]["ticker"] == "AAPL"


class TestSearch:
    """Tests for search method."""

    @patch("src.data.vector_store.chromadb.PersistentClient")
    def test_search_no_filters(self, mock_client_class: Mock) -> None:
        """Test basic search without filters."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client

        # Mock search results
        mock_collection.query.return_value = {
            "documents": [["Risk content 1", "Risk content 2"]],
            "metadatas": [[{"ticker": "AAPL"}, {"ticker": "MSFT"}]],
            "distances": [[0.1, 0.2]],
        }

        store = FilingVectorStore()
        results = store.search("What are the main risks?", limit=2)

        assert len(results) == 2
        assert results[0]["content"] == "Risk content 1"
        assert results[0]["metadata"]["ticker"] == "AAPL"
        assert results[0]["distance"] == 0.1

        # Verify query was called correctly
        mock_collection.query.assert_called_once_with(
            query_texts=["What are the main risks?"],
            n_results=2,
            where=None,
        )

    @patch("src.data.vector_store.chromadb.PersistentClient")
    def test_search_with_ticker_filter(self, mock_client_class: Mock) -> None:
        """Test search filtered by ticker."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client

        mock_collection.query.return_value = {
            "documents": [["Content"]],
            "metadatas": [[{"ticker": "AAPL"}]],
            "distances": [[0.1]],
        }

        store = FilingVectorStore()
        store.search("risks", ticker="aapl", limit=5)

        call_args = mock_collection.query.call_args
        assert call_args.kwargs["where"] == {"ticker": "AAPL"}

    @patch("src.data.vector_store.chromadb.PersistentClient")
    def test_search_with_section_filter(self, mock_client_class: Mock) -> None:
        """Test search filtered by section."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client

        mock_collection.query.return_value = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

        store = FilingVectorStore()
        store.search("revenue", section_name="MD&A", limit=3)

        call_args = mock_collection.query.call_args
        assert call_args.kwargs["where"] == {"section_name": "MD&A"}

    @patch("src.data.vector_store.chromadb.PersistentClient")
    def test_search_with_multiple_filters(self, mock_client_class: Mock) -> None:
        """Test search with both ticker and section filters."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client

        mock_collection.query.return_value = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

        store = FilingVectorStore()
        store.search("revenue", ticker="AAPL", section_name="MD&A")

        call_args = mock_collection.query.call_args
        assert call_args.kwargs["where"] == {
            "$and": [{"ticker": "AAPL"}, {"section_name": "MD&A"}]
        }

    @patch("src.data.vector_store.chromadb.PersistentClient")
    def test_search_empty_results(self, mock_client_class: Mock) -> None:
        """Test search with no results."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client

        mock_collection.query.return_value = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

        store = FilingVectorStore()
        results = store.search("nonexistent query")

        assert results == []


class TestSearchSimilar:
    """Tests for search_similar method."""

    @patch("src.data.vector_store.chromadb.PersistentClient")
    def test_search_similar_no_filter(self, mock_client_class: Mock) -> None:
        """Test finding similar content without exclusions."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client

        mock_collection.query.return_value = {
            "documents": [["Similar disclosure 1", "Similar disclosure 2"]],
            "metadatas": [[{"ticker": "MSFT"}, {"ticker": "GOOGL"}]],
            "distances": [[0.15, 0.25]],
        }

        store = FilingVectorStore()
        results = store.search_similar("Risk disclosure text...", limit=2)

        assert len(results) == 2
        # Content should be truncated to 500 chars max
        assert len(results[0]["content"]) <= 503  # 500 + "..."

        mock_collection.query.assert_called_once()
        call_args = mock_collection.query.call_args
        assert call_args.kwargs["where"] is None

    @patch("src.data.vector_store.chromadb.PersistentClient")
    def test_search_similar_with_exclusion(self, mock_client_class: Mock) -> None:
        """Test finding similar content excluding a specific ticker."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client

        mock_collection.query.return_value = {
            "documents": [["Content"]],
            "metadatas": [[{"ticker": "MSFT"}]],
            "distances": [[0.1]],
        }

        store = FilingVectorStore()
        store.search_similar("Content", exclude_ticker="aapl")

        call_args = mock_collection.query.call_args
        assert call_args.kwargs["where"] == {"ticker": {"$ne": "AAPL"}}

    @patch("src.data.vector_store.chromadb.PersistentClient")
    def test_search_similar_truncates_long_content(self, mock_client_class: Mock) -> None:
        """Test that long result content is truncated."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client

        long_doc = "A" * 1000
        mock_collection.query.return_value = {
            "documents": [[long_doc]],
            "metadatas": [[{"ticker": "TEST"}]],
            "distances": [[0.1]],
        }

        store = FilingVectorStore()
        results = store.search_similar("query")

        # Should be truncated to 500 chars + "..."
        assert len(results[0]["content"]) == 503
        assert results[0]["content"].endswith("...")


class TestGetIndexedFilings:
    """Tests for get_indexed_filings method."""

    @patch("src.data.vector_store.chromadb.PersistentClient")
    def test_get_indexed_filings_success(self, mock_client_class: Mock) -> None:
        """Test retrieving indexed filings."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client

        mock_collection.get.return_value = {
            "metadatas": [
                {"ticker": "AAPL", "accession_number": "123", "section_name": "Risk"},
                {"ticker": "AAPL", "accession_number": "123", "section_name": "Risk"},  # Duplicate
                {"ticker": "MSFT", "accession_number": "456", "section_name": "Business"},
            ]
        }

        store = FilingVectorStore()
        filings = store.get_indexed_filings()

        # Should deduplicate by ticker:accession combination
        assert len(filings) == 2
        assert any(f["ticker"] == "AAPL" and f["accession_number"] == "123" for f in filings)
        assert any(f["ticker"] == "MSFT" and f["accession_number"] == "456" for f in filings)

    @patch("src.data.vector_store.chromadb.PersistentClient")
    def test_get_indexed_filings_empty(self, mock_client_class: Mock) -> None:
        """Test when no filings are indexed."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client

        mock_collection.get.return_value = {"metadatas": []}

        store = FilingVectorStore()
        filings = store.get_indexed_filings()

        assert filings == []


class TestDeleteFiling:
    """Tests for delete_filing method."""

    @patch("src.data.vector_store.chromadb.PersistentClient")
    def test_delete_filing_success(self, mock_client_class: Mock) -> None:
        """Test deleting a filing and its chunks."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client

        # Mock that we find 3 chunks to delete
        mock_collection.get.return_value = {
            "ids": ["doc1_0", "doc1_1", "doc1_2"]
        }

        store = FilingVectorStore()
        count = store.delete_filing("AAPL", "0000320193-23-000106")

        assert count == 3
        mock_collection.delete.assert_called_once_with(
            ids=["doc1_0", "doc1_1", "doc1_2"]
        )

    @patch("src.data.vector_store.chromadb.PersistentClient")
    def test_delete_filing_not_found(self, mock_client_class: Mock) -> None:
        """Test deleting a filing that doesn't exist."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client

        mock_collection.get.return_value = {"ids": []}

        store = FilingVectorStore()
        count = store.delete_filing("INVALID", "000")

        assert count == 0
        mock_collection.delete.assert_not_called()


class TestClear:
    """Tests for clear method."""

    @patch("src.data.vector_store.chromadb.PersistentClient")
    def test_clear_deletes_and_recreates(self, mock_client_class: Mock) -> None:
        """Test that clear deletes collection and recreates it."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client_class.return_value = mock_client

        store = FilingVectorStore()

        # Clear initial call count
        mock_client.get_or_create_collection.reset_mock()

        store.clear()

        mock_client.delete_collection.assert_called_once_with("sec_filings")
        # Should recreate collection after deletion
        mock_client.get_or_create_collection.assert_called_once()


class TestChunkContent:
    """Tests for _chunk_content private method."""

    @patch("src.data.vector_store.chromadb.PersistentClient")
    def test_chunk_content_short_text(self, mock_client_class: Mock) -> None:
        """Test that short content is not chunked."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        store = FilingVectorStore()

        short_text = "This is short content."
        chunks = store._chunk_content(short_text, max_chars=1000)

        assert len(chunks) == 1
        assert chunks[0] == short_text

    @patch("src.data.vector_store.chromadb.PersistentClient")
    def test_chunk_content_by_paragraphs(self, mock_client_class: Mock) -> None:
        """Test that content is chunked by paragraph boundaries."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        store = FilingVectorStore()

        # Create content with paragraphs
        text = "Paragraph 1.\n\n" + "A" * 100 + "\n\n" + "Paragraph 3."
        chunks = store._chunk_content(text, max_chars=150)

        # Should chunk by paragraph boundaries
        assert len(chunks) >= 1

    @patch("src.data.vector_store.chromadb.PersistentClient")
    def test_chunk_content_long_paragraph(self, mock_client_class: Mock) -> None:
        """Test handling of paragraphs longer than max_chars."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        store = FilingVectorStore()

        # Single long paragraph exceeding max_chars
        long_para = "A" * 500
        chunks = store._chunk_content(long_para, max_chars=100)

        # Should be split into multiple chunks
        assert len(chunks) >= 5


class TestGetVectorStore:
    """Tests for get_vector_store singleton function."""

    @patch("src.data.vector_store.chromadb.PersistentClient")
    def test_get_vector_store_creates_instance(self, mock_client_class: Mock) -> None:
        """Test that get_vector_store creates an instance."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Reset global state
        import src.data.vector_store
        src.data.vector_store._vector_store = None

        store = get_vector_store()

        assert isinstance(store, FilingVectorStore)

    @patch("src.data.vector_store.chromadb.PersistentClient")
    def test_get_vector_store_returns_singleton(self, mock_client_class: Mock) -> None:
        """Test that get_vector_store returns the same instance."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Reset global state
        import src.data.vector_store
        src.data.vector_store._vector_store = None

        store1 = get_vector_store()
        store2 = get_vector_store()

        assert store1 is store2
