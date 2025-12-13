import asyncio
from concurrent.futures import ThreadPoolExecutor

import structlog
from fastapi import APIRouter, Depends, HTTPException

from src.agents.orchestrator import Orchestrator
from src.api.middleware import verify_api_key
from src.api.models.requests import ChatRequest, ChatResponse

router = APIRouter()
logger = structlog.get_logger()

# Thread pool for running synchronous orchestrator
_executor = ThreadPoolExecutor(max_workers=4)


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    _api_key: str = Depends(verify_api_key),
):
    """
    Chat with SEC filings using the multi-agent orchestrator.

    This endpoint uses the full agent system with:
    - Planner: Analyzes query and creates task plan
    - Executor: Runs tools to fetch SEC data
    - Validator: Checks results (for complex queries)
    - Synthesizer: Generates final response
    """
    try:
        # Get the query from the last message
        current_query = request.messages[-1].content
        logger.info("Processing query via orchestrator", query=current_query)

        # Run the synchronous orchestrator in a thread pool
        orchestrator = Orchestrator()
        loop = asyncio.get_event_loop()
        answer = await loop.run_in_executor(
            _executor,
            orchestrator.run,
            current_query
        )

        logger.info("Orchestrator completed", answer_length=len(answer))

        return ChatResponse(
            answer=answer,
            citations=[],  # Citations are embedded in the answer
            usage={}
        )

    except Exception as e:
        logger.exception("Chat failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
