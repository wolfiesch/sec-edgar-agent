"""Vector store for semantic search of SEC filings."""

import hashlib
from pathlib import Path
from typing import Any

import chromadb
import structlog
from chromadb.config import Settings as ChromaSettings

from src.config import settings

logger = structlog.get_logger()


class FilingVectorStore:
    """
    ChromaDB-based vector store for SEC filing sections.

    Enables semantic search across filing content.
    """

    def __init__(self, persist_dir: Path | None = None):
        """Initialize the persistent Chroma collection and embeddings."""
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=ChromaSettings(
                anonymized_telemetry=False,
            ),
        )

        # Initialize Embedding Function
        from chromadb.utils import embedding_functions

        # Use OpenAI if key is present, otherwise default (good for local dev/demo without costs)
        # Use OpenAI embedding function
        if settings.openai_api_key:
            self.embedding_fn: Any = embedding_functions.OpenAIEmbeddingFunction(
                api_key=settings.openai_api_key,
                model_name="text-embedding-3-small"
            )
            logger.info("Using OpenAI embeddings")
        else:
            self.embedding_fn = None # Uses Chroma default (all-MiniLM-L6-v2)
            logger.warning("Using default Chroma embeddings (no OpenAI key found)")

        # Get or create collection for filings
        self.collection = self.client.get_or_create_collection(
            name="sec_filings",
            metadata={"description": "SEC filing sections for semantic search"},
            embedding_function=self.embedding_fn
        )

        logger.info("Vector store initialized", path=str(self.persist_dir))

    def add_filing_section(
        self,
        ticker: str,
        accession_number: str,
        section_name: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Add a filing section to the vector store.

        Returns the document ID.
        """
        # Generate unique ID for the section
        doc_id = hashlib.sha256(
            f"{ticker}:{accession_number}:{section_name}".encode()
        ).hexdigest()[:16]

        # Prepare base metadata
        base_metadata = {
            "ticker": ticker.upper(),
            "accession_number": accession_number,
            "section_name": section_name,
            **(metadata or {}),
        }

        # Chunk content using token-aware splitter
        chunks = self._chunk_content(content)

        ids = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_{i}"
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({**base_metadata, "chunk_index": i})

        if ids:
            self.collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,  # type: ignore
            )

        logger.debug(
            "Added chunks to vector store",
            ticker=ticker,
            section=section_name,
            chunk_count=len(chunks),
        )
        return doc_id

    def search(
        self,
        query: str,
        ticker: str | None = None,
        section_name: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Search for relevant filing sections.

        Args:
            query: Search query
            ticker: Filter by ticker symbol
            section_name: Filter by section name
            limit: Maximum results to return

        Returns:
            List of matching documents with metadata
        """
        # Build where filter
        # Build where filter
        where_filter: dict[str, Any] | None = {}
        conditions: list[dict[str, str]] = []

        if ticker:
            conditions.append({"ticker": ticker.upper()})
        if section_name:
            conditions.append({"section_name": section_name})

        if len(conditions) == 1:
            where_filter = conditions[0]
        elif len(conditions) > 1:
            where_filter = {"$and": conditions}
        else:
            where_filter = None

        results = self.collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_filter,  # type: ignore
        )

        # Format results
        formatted = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                formatted.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None,
                })

        return formatted

    def search_similar(
        self,
        content: str,
        exclude_ticker: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Find similar content across all filings.
        """
        where_filter = None
        if exclude_ticker:
            where_filter = {"ticker": {"$ne": exclude_ticker.upper()}}

        # Truncate query if too long (Chroma issue with very long queries)
        query_text = content[:8000]

        results = self.collection.query(
            query_texts=[query_text],
            n_results=limit,
            where=where_filter,  # type: ignore
        )

        formatted = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                formatted.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None,
                })

        return formatted

    def get_indexed_filings(self) -> list[dict[str, Any]]:
        """Get list of indexed filings."""
        # Get all unique ticker/accession combinations
        # Note: listing all is expensive in Chroma, better to use SQL tracker later.
        # For now, just getting a subset or implementing via metadata scan ?
        # Chroma .get() without ids gets everything.
        results = self.collection.get(
            include=["metadatas"],
        )

        seen = set()
        filings = []

        if results["metadatas"]:
            for meta in results["metadatas"]:
                key = f"{meta.get('ticker')}:{meta.get('accession_number')}"
                if key not in seen:
                    seen.add(key)
                    filings.append({
                        "ticker": meta.get("ticker"),
                        "accession_number": meta.get("accession_number"),
                        "section_name": meta.get("section_name"),
                    })

        return filings

    def delete_filing(self, ticker: str, accession_number: str) -> int:
        """Delete all chunks for a filing. Returns count deleted."""
        # Find all IDs for this filing
        # Chroma delete with where filter is efficient
        where_filter = {
            "$and": [
                {"ticker": ticker.upper()},
                {"accession_number": accession_number},
            ]
        }

        # We need to get IDs first to know count, or just delete.
        # Chroma delete supports where filter directly.

        # Check count first for return value
        results = self.collection.get(where=where_filter)  # type: ignore
        count = len(results["ids"])

        if count > 0:
            self.collection.delete(where=where_filter)  # type: ignore
            logger.info("Deleted filing chunks", ticker=ticker, count=count)

        return count

    def clear(self) -> None:
        """Clear all data from the vector store."""
        self.client.delete_collection("sec_filings")
        self.collection = self.client.get_or_create_collection(
            name="sec_filings",
            metadata={"description": "SEC filing sections for semantic search"},
        )
        logger.info("Vector store cleared")

    def _chunk_content(self, content: str, chunk_size: int = 1000, chunk_overlap: int = 100) -> list[str]:
        """
        Split content using Markdown-aware splitter.
        """
        from langchain_text_splitters import MarkdownTextSplitter

        text_splitter = MarkdownTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        return text_splitter.split_text(content)


# Global vector store instance
_vector_store: FilingVectorStore | None = None


def get_vector_store() -> FilingVectorStore:
    """Get or create the global vector store."""
    global _vector_store
    if _vector_store is None:
        _vector_store = FilingVectorStore()
    return _vector_store
