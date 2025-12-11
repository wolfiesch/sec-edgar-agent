from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TableParseRequest(BaseModel):
    """Request to parse a specific table from a filing."""
    ticker: str = Field(
        ...,
        description="Stock ticker symbol",
        json_schema_extra={"example": "AAPL"}
    )
    form_type: str = Field(
        ...,
        description="SEC form type (e.g., 10-K, 10-Q)",
        json_schema_extra={"example": "10-K"}
    )
    year: Optional[int] = Field(
        None,
        ge=2000,
        le=2030,
        description="Filing year (defaults to latest if not specified)",
        json_schema_extra={"example": 2024}
    )
    table_name: str = Field(
        ...,
        description="Table identifier (e.g., 'segment_information', 'lease_maturity')",
        json_schema_extra={"example": "segment_information"}
    )
