"""Chat endpoints backed by the multi-agent orchestrator."""
import asyncio
import json
import time
import uuid
from collections.abc import AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket
from fastapi.responses import StreamingResponse

from src.agents.orchestrator import Orchestrator, StreamingOrchestrator
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
) -> ChatResponse:
    """
    Chat with SEC filings using the multi-agent orchestrator.

    This endpoint uses the full agent system with:
    - Planner: Analyzes query and creates task plan
    - Executor: Runs tools to fetch SEC data
    - Validator: Checks results (for complex queries)
    - Synthesizer: Generates final response
    """
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    try:
        # Get the query from the last message
        current_query = request.messages[-1].content
        message_count = len(request.messages)

        logger.info(
            "Chat request received",
            request_id=request_id,
            query=current_query[:100] + "..." if len(current_query) > 100 else current_query,
            query_length=len(current_query),
            message_count=message_count,
        )

        # Run the synchronous orchestrator in a thread pool
        orchestrator = Orchestrator()
        loop = asyncio.get_event_loop()
        answer = await loop.run_in_executor(
            _executor,
            orchestrator.run,
            current_query
        )

        elapsed = time.time() - start_time
        logger.info(
            "Chat request completed",
            request_id=request_id,
            answer_length=len(answer),
            elapsed_seconds=round(elapsed, 2),
        )

        return ChatResponse(
            answer=answer,
            citations=[],  # Citations are embedded in the answer
            usage={}
        )

    except ValueError as e:
        elapsed = time.time() - start_time
        logger.warning(
            "Chat request validation failed",
            request_id=request_id,
            error=str(e),
            elapsed_seconds=round(elapsed, 2),
        )
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request: {e}"
        ) from e

    except TimeoutError as e:
        elapsed = time.time() - start_time
        logger.error(
            "Chat request timed out",
            request_id=request_id,
            elapsed_seconds=round(elapsed, 2),
        )
        raise HTTPException(
            status_code=504,
            detail="Request timed out. The query may be too complex. Try a simpler question."
        ) from e

    except Exception as e:
        elapsed = time.time() - start_time
        error_type = type(e).__name__
        logger.exception(
            "Chat request failed",
            request_id=request_id,
            error=str(e),
            error_type=error_type,
            elapsed_seconds=round(elapsed, 2),
        )

        # Provide user-friendly error messages based on error type
        if "rate limit" in str(e).lower():
            detail = "The SEC EDGAR API rate limit was exceeded. Please wait a moment and try again."
        elif "connection" in str(e).lower() or "timeout" in str(e).lower():
            detail = "Could not connect to SEC EDGAR. Please check your internet connection and try again."
        elif "not found" in str(e).lower():
            detail = f"The requested company or filing was not found: {e}"
        else:
            detail = f"An error occurred while processing your query: {e}"

        raise HTTPException(status_code=500, detail=detail) from e


def _serialize_for_json(obj: Any) -> Any:
    """Convert objects to JSON-serializable format."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return {k: _serialize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize_for_json(item) for item in obj]
    if hasattr(obj, "__dict__"):
        # Convert Pydantic models and other objects
        return _serialize_for_json(obj.__dict__)
    # Handle basic types
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time chat...
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()


@router.get("/stream")
async def chat_stream(
    query: str = Query(..., description="The question to ask about SEC filings"),
    _api_key: str = Depends(verify_api_key),
) -> StreamingResponse:
    """
    Server-Sent Events (SSE) endpoint for streaming chat with SEC filings.

    Usage:
        GET /api/v1/chat/stream?query=What+was+Apple's+revenue+in+2023?
        Headers: X-API-Key: YOUR_KEY

    Response format (text/event-stream):
        data: {"phase": "planning", "message": "Analyzing your query...", "data": null}

        data: {"phase": "executing", "message": "Executing research tasks...", "data": null}

        data: {"phase": "complete", "message": "Final answer here...", "data": {"elapsed": 5.2}}

    Phases:
        - planning: Creating task plan
        - planned: Plan created
        - executing: Running research tasks
        - task_complete: Individual task finished
        - validating: Checking results
        - validated: Results validated
        - synthesizing: Generating response
        - complete: Final answer (in message field)
        - error: Error occurred
    """
    request_id = str(uuid.uuid4())[:8]

    logger.info(
        "SSE stream request received",
        request_id=request_id,
        query=query[:100] + "..." if len(query) > 100 else query,
    )

    async def event_generator() -> AsyncGenerator[str, None]:
        """Yield server-sent events as orchestration phases complete."""
        start_time = time.time()

        try:
            # Run streaming orchestrator in thread pool
            orchestrator = StreamingOrchestrator()
            loop = asyncio.get_event_loop()

            # Create a queue to communicate between threads
            queue: asyncio.Queue = asyncio.Queue()

            def run_streaming() -> None:
                """Run orchestrator and put results in queue."""
                try:
                    for phase, message_text, data in orchestrator.run_streaming(query):
                        # Put result in queue (use thread-safe call_soon_threadsafe)
                        loop.call_soon_threadsafe(queue.put_nowait, (phase, message_text, data))
                    # Signal completion
                    loop.call_soon_threadsafe(queue.put_nowait, None)
                except Exception as e:
                    # Signal error
                    loop.call_soon_threadsafe(queue.put_nowait, ("error", str(e), None))
                    loop.call_soon_threadsafe(queue.put_nowait, None)

            # Start streaming in background thread
            _executor.submit(run_streaming)

            # Yield events as they arrive
            while True:
                result = await queue.get()
                if result is None:  # Completion signal
                    break

                phase, message_text, data = result
                event_data = {
                    "phase": phase,
                    "message": message_text,
                    "data": _serialize_for_json(data),
                }
                yield f"data: {json.dumps(event_data)}\n\n"

            elapsed = time.time() - start_time
            logger.info(
                "SSE stream completed",
                request_id=request_id,
                elapsed_seconds=round(elapsed, 2),
            )

        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = str(e)

            logger.exception(
                "SSE stream failed",
                request_id=request_id,
                error=error_msg,
                elapsed_seconds=round(elapsed, 2),
            )

            error_event = {
                "phase": "error",
                "message": f"Error processing query: {error_msg}",
                "data": None,
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
