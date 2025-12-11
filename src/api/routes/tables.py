from fastapi import APIRouter, HTTPException
from ...parsers.table_parser import TableParser
from ..models.requests import TableParseRequest
from ..models.responses import ParsedTableResponse
from ..exceptions import SecApiError, ParsingError

router = APIRouter()
parser = TableParser()  # Singleton for demo specific context maps

@router.post("/parse", response_model=ParsedTableResponse)
async def parse_table(request: TableParseRequest):
    """
    Parse a table from SEC filing with 100% accuracy.

    Returns structured Markdown table ready for LLM consumption.
    """
    try:
        result = parser.parse_from_filing(
            ticker=request.ticker,
            form_type=request.form_type,
            table_identifier=request.table_name,
            year=request.year
        )

        # Mock citation if missing? result.citation should have it.
        # result.citation from parser is string "[AAPL 10-K 2024]"
        # Response model expects citation string.

        return ParsedTableResponse(
            markdown=result.markdown,
            structured=result.structured,
            citation=result.citation,
            confidence=result.confidence,
            metadata={
                "source_method": result.source_method,
                "ticker": request.ticker,
                "form_type": request.form_type,
                "year": request.year
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
