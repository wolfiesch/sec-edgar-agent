import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from src.data.repositories.tables import TableRepository
from src.parsers.table_parser import ParsedTable as DomainParsedTable


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_create_and_get_table(session: Session):
    repo = TableRepository(session)

    # Create domain object
    domain_table = DomainParsedTable(
        markdown="| Col1 | Col2 |\n|---|---|\n| Val1 | Val2 |",
        structured=[{"Col1": "Val1", "Col2": "Val2"}],
        citation="[TEST 10-K 2024]",
        confidence="high",
        source_method="inline-xbrl",
        section="Item 8"
    )

    # Save
    saved = repo.create(
        domain_table=domain_table,
        ticker="TEST",
        form_type="10-K",
        year=2024,
        table_name="balance_sheet"
    )

    assert saved.id is not None
    assert saved.ticker == "TEST"

    # Retrieve
    retrieved = repo.get("TEST", "10-K", 2024, "balance_sheet")

    assert retrieved is not None
    assert retrieved.markdown == domain_table.markdown
    assert retrieved.structured == domain_table.structured
    assert retrieved.citation == domain_table.citation
    assert retrieved.confidence == domain_table.confidence

def test_get_non_existent(session: Session):
    repo = TableRepository(session)
    result = repo.get("NONEXISTENT", "10-K", 2024, "balance_sheet")
    assert result is None
