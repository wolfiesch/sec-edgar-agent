"""Repository for ParsedTable access."""
import json
from datetime import datetime

from sqlmodel import Session, select

from src.data.db_models import ParsedTable
from src.parsers.table_parser import ParsedTable as DomainParsedTable


class TableRepository:
    """Repository for managing parsed table persistence."""

    def __init__(self, session: Session):
        self.session = session

    def get(self, ticker: str, form_type: str, year: int, table_name: str) -> DomainParsedTable | None:
        """Retrieve a specific table from cache."""
        statement = select(ParsedTable).where(
            ParsedTable.ticker == ticker,
            ParsedTable.form_type == form_type,
            ParsedTable.year == year,
            ParsedTable.table_name == table_name
        )
        result = self.session.exec(statement).first()

        if not result:
            return None

        return DomainParsedTable(
            markdown=result.markdown,
            structured=json.loads(result.structured_data_json),
            citation=result.citation_json, # It's a string in domain model
            confidence=result.confidence,
            source_method=result.source_method
        )

    def create(self, domain_table: DomainParsedTable, ticker: str, form_type: str, year: int, table_name: str) -> ParsedTable:
        """Save a parsed table to the database."""
        # Check if exists to avoid duplicates (could use upsert logic, simplified here)
        existing = self.get(ticker, form_type, year, table_name)
        if existing:
            # We already have it, maybe update? For now, just return what we would have saved
            # This logic is a bit circular if we return Domain object, but here we return DB object
            # Let's actually delete old and replace to be safe on updates
            statement = select(ParsedTable).where(
                ParsedTable.ticker == ticker,
                ParsedTable.form_type == form_type,
                ParsedTable.year == year,
                ParsedTable.table_name == table_name
            )
            db_obj = self.session.exec(statement).first()
            if db_obj:
               self.session.delete(db_obj)
               self.session.commit()

        db_table = ParsedTable(
            ticker=ticker,
            form_type=form_type,
            year=year,
            table_name=table_name,
            markdown=domain_table.markdown,
            structured_data_json=json.dumps(domain_table.structured),
            citation_json=domain_table.citation,
            source_method=domain_table.source_method,
            confidence=domain_table.confidence,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        self.session.add(db_table)
        self.session.commit()
        self.session.refresh(db_table)
        return db_table
