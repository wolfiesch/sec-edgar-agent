"""Vector store for semantic search of SEC filings."""

import hashlib
import logging
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

from src.config import settings

logger = logging.getLogger(__name__)


class FilingVectorStore:
    """
    ChromaDB-based vector store for SEC filing sections.

    Enables semantic search across filing content.
    """

    def __init__(self, persist_dir: Path | None = None):
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(
                anonymized_telemetry=False,
            ),
        )

        # Get or create collection for filings
        self.collection = self.client.get_or_create_collection(
            name="sec_filings",
            metadata={"description": "SEC filing sections for semantic search"},
        )

        logger.info(f"Vector store initialized at {self.persist_dir}")

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
        # Generate unique ID
        doc_id = hashlib.sha256(
            f"{ticker}:{accession_number}:{section_name}".encode()
        ).hexdigest()[:16]

        # Prepare metadata
        doc_metadata = {
            "ticker": ticker.upper(),
            "accession_number": accession_number,
            "section_name": section_name,
            **(metadata or {}),
        }

        # Chunk content if too long (ChromaDB has limits)
        chunks = self._chunk_content(content, max_chars=8000)

        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_{i}" if len(chunks) > 1 else doc_id

            self.collection.upsert(
                ids=[chunk_id],
                documents=[chunk],
                metadatas=[{**doc_metadata, "chunk_index": i}],
            )

        logger.debug(f"Added {len(chunks)} chunks for {ticker}/{section_name}")
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
        where_filter = None
        if ticker or section_name:
            conditions = []
            if ticker:
                conditions.append({"ticker": ticker.upper()})
            if section_name:
                conditions.append({"section_name": section_name})

            if len(conditions) == 1:
                where_filter = conditions[0]
            else:
                where_filter = {"$and": conditions}

        results = self.collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_filter,
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

        Useful for finding companies with similar disclosures.
        """
        where_filter = None
        if exclude_ticker:
            where_filter = {"ticker": {"$ne": exclude_ticker.upper()}}

        results = self.collection.query(
            query_texts=[content[:8000]],  # Truncate if needed
            n_results=limit,
            where=where_filter,
        )

        formatted = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                formatted.append({
                    "content": doc[:500] + "..." if len(doc) > 500 else doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None,
                })

        return formatted

    def get_indexed_filings(self) -> list[dict[str, Any]]:
        """Get list of indexed filings."""
        # Get all unique ticker/accession combinations
        results = self.collection.get(
            include=["metadatas"],
        )

        seen = set()
        filings = []

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
        results = self.collection.get(
            where={
                "$and": [
                    {"ticker": ticker.upper()},
                    {"accession_number": accession_number},
                ]
            },
        )

        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            return len(results["ids"])

        return 0

    def clear(self) -> None:
        """Clear all data from the vector store."""
        self.client.delete_collection("sec_filings")
        self.collection = self.client.get_or_create_collection(
            name="sec_filings",
            metadata={"description": "SEC filing sections for semantic search"},
        )
        logger.info("Vector store cleared")

    def _chunk_content(self, content: str, max_chars: int = 8000) -> list[str]:
        """Split content into chunks, trying to preserve paragraph boundaries."""
        if len(content) <= max_chars:
            return [content]

        chunks = []
        current_chunk = ""

        # Split by paragraphs
        paragraphs = content.split("\n\n")

        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= max_chars:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # Handle paragraphs longer than max_chars
                if len(para) > max_chars:
                    # Split by sentences or just hard split
                    for i in range(0, len(para), max_chars):
                        chunks.append(para[i:i + max_chars])
                    current_chunk = ""
                else:
                    current_chunk = para + "\n\n"

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks


# Global vector store instance
_vector_store: FilingVectorStore | None = None


def get_vector_store() -> FilingVectorStore:
    """Get or create the global vector store."""
    global _vector_store
    if _vector_store is None:
        _vector_store = FilingVectorStore()
    return _vector_store
