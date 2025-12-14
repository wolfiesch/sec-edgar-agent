from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from ...data.repositories.tables import TableRepository
from ...parsers.table_parser import TableParser
from ..dependencies import get_db
from ..models.requests import TableParseRequest
from ..models.responses import ParsedTableResponse

router = APIRouter()
parser = TableParser()  # Singleton for demo specific context maps

@router.post("/parse", response_model=ParsedTableResponse)
async def parse_table(
    request: TableParseRequest,
    session: Session = Depends(get_db)
) -> ParsedTableResponse:
    """
    Parse a table from SEC filing with 100% accuracy.

    Checks cache first, then parses if necessary.
    Returns structured Markdown table ready for LLM consumption.
    """
    repo = TableRepository(session)

    try:
        # 1. Check Cache
        cached = repo.get(
            ticker=request.ticker,
            form_type=request.form_type,
            year=request.year,
            table_name=request.table_name
        )

        if cached:
            return ParsedTableResponse(
                markdown=cached.markdown,
                structured=cached.structured,
                citation=cached.citation,
                confidence=cached.confidence,
                section=cached.section,
                metadata={
                    "source_method": cached.source_method + " (cached)",
                    "ticker": request.ticker,
                    "form_type": request.form_type,
                    "year": request.year,
                    "table_type": request.table_name
                }
            )

        # 2. Parse (Async)
        result = await parser.parse_from_filing(
            ticker=request.ticker,
            form_type=request.form_type,
            table_identifier=request.table_name,
            year=request.year
        )

        # 3. Save to Cache
        repo.create(
            domain_table=result,
            ticker=request.ticker,
            form_type=request.form_type,
            year=request.year,
            table_name=request.table_name
        )

        return ParsedTableResponse(
            markdown=result.markdown,
            structured=result.structured,
            citation=result.citation,
            confidence=result.confidence,
            section=result.section,
            metadata={
                "source_method": result.source_method,
                "ticker": request.ticker,
                "form_type": request.form_type,
                "year": request.year,
                "table_type": request.table_name
            }
        )
    except ValueError as e:
        # Parser raises ValueError for missing data
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse table: {str(e)}"
        )
