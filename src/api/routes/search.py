from fastapi import APIRouter, HTTPException, Depends
from src.data.vector_store import get_vector_store, FilingVectorStore
from src.api.models.requests import SearchRequest
from src.api.models.responses import SearchResponse, SearchResult

router = APIRouter()


@router.post("/", response_model=SearchResponse)
async def search_filings(
    request: SearchRequest,
    vector_store: FilingVectorStore = Depends(get_vector_store),
):
    """
    Semantic search across SEC filings.
    """
    try:
        results = vector_store.search(
            query=request.query,
            ticker=request.ticker,
            section_name=request.section,
            limit=request.limit,
        )

        search_results = []
        for res in results:
            metadata = res.get("metadata", {})
            # Construct citation string
            ticker = metadata.get("ticker", "UNKNOWN")
            section = metadata.get("section_name", "Unknown Section")
            # Ideally we'd have year/form in metadata too, adding in Day 2
            citation = f"[{ticker} {section}]"

            search_results.append(
                SearchResult(
                    content=str(res["content"]),
                    citation=citation,
                    metadata=metadata,
                    distance=res.get("distance"),
                )
            )

        return SearchResponse(results=search_results, total=len(search_results))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
