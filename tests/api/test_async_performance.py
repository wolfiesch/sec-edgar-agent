import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient, ASGITransport

from src.api.main import app

@pytest.mark.asyncio
async def test_endpoint_concurrency():
    """
    Verify that long-running download operations do not block other endpoints.
    
    We simulate a 'download' by patching the TableParser to sleep.
    While one request is 'downloading', we fire a health check request.
    If the health check waits for the download, then we are blocking.
    """
    
    # Mock the parser to sleep for 1 second instead of doing work
    async def mock_parse_slow(*args, **kwargs):
        await asyncio.sleep(1)
        # return a dummy object that matches response model
        from src.parsers.table_parser import ParsedTable
        return ParsedTable(
            markdown="| Test |", 
            structured=[], 
            citation="[Test]", 
            confidence="high", 
            source_method="mock"
        )

    with patch("src.api.routes.tables.parser.parse_from_filing", side_effect=mock_parse_slow):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            
            # 1. Start slow request
            start_time = time.time()
            task_slow = asyncio.create_task(
                client.post("/api/v1/tables/parse", json={
                    "ticker": "AAPL",
                    "form_type": "10-K",
                    "year": 2024,
                    "table_name": "balance_sheet"
                })
            )
            
            # 2. Immediately fire fast request (health check)
            # Give the slow task a tiny head start to reach the await sleep
            await asyncio.sleep(0.1)
            
            response_health = await client.get("/health/")
            end_time_health = time.time()
            
            # 3. Validation
            assert response_health.status_code == 200
            
            # Health check should complete almost instantly, well before the 1s sleep finishes
            duration_health = end_time_health - start_time
            
            # If blocking, duration would be > 1.0s. 
            # If non-blocking, it should be just over 0.1s (the wait we added)
            assert duration_health < 0.5, f"Health check took too long: {duration_health}s. Main loop blocked?"
            
            # Cleanup
            await task_slow
