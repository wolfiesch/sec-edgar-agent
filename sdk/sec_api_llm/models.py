from pydantic import BaseModel

# --- Responses ---

class SearchResult(BaseModel):
    content: str
    metadata: dict
    score: float | None

class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]

class ChatResponse(BaseModel):
    answer: str
    citations: list[str]
    usage: dict

# --- Requests ---

class ChatMessage(BaseModel):
    role: str
    content: str

# Existing models...
class ParsedTable(BaseModel):
    markdown: str
    structured: list[dict]
    citation: str
    confidence: str
    section: str | None = None  # e.g., "Item 8"
    metadata: dict = {}

    def __str__(self) -> str:
        return self.markdown

    def __repr__(self) -> str:
        return f"ParsedTable(citation='{self.citation}', section='{self.section}', rows={len(self.structured)})"

class Filing(BaseModel):
    accession_no: str
    cik: str
    company: str
    filing_date: str
    form: str
