import asyncio
import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect

from src.agents.orchestrator import Orchestrator, StreamingOrchestrator
from src.api.config import settings
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
async def chat_websocket(
    websocket: WebSocket,
    api_key: str = Query(None, alias="api_key"),
):
    """
    WebSocket endpoint for streaming chat with SEC filings.

    Connect with: ws://host/api/v1/chat/ws?api_key=YOUR_KEY

    Send JSON message:
        {"query": "What was Apple's revenue in 2023?"}

    Receive streaming progress updates:
        {"phase": "planning", "message": "Analyzing your query...", "data": null}
        {"phase": "executing", "message": "Executing research tasks...", "data": null}
        {"phase": "task_complete", "message": "Completed: Get company info", "data": {...}}
        {"phase": "complete", "message": "Final answer here...", "data": {"elapsed": 5.2}}
    """
    # Verify API key
    if api_key is None or api_key != settings.API_KEY:
        await websocket.close(code=4001, reason="Invalid or missing API key")
        return

    await websocket.accept()
    connection_id = str(uuid.uuid4())[:8]

    logger.info("WebSocket connection established", connection_id=connection_id)

    try:
        while True:
            # Wait for client message
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                query = message.get("query", "").strip()
            except json.JSONDecodeError:
                await websocket.send_json({
                    "phase": "error",
                    "message": "Invalid JSON. Send: {\"query\": \"your question\"}",
                    "data": None,
                })
                continue

            if not query:
                await websocket.send_json({
                    "phase": "error",
                    "message": "Missing 'query' field in message",
                    "data": None,
                })
                continue

            request_id = str(uuid.uuid4())[:8]
            start_time = time.time()

            logger.info(
                "WebSocket query received",
                connection_id=connection_id,
                request_id=request_id,
                query=query[:100] + "..." if len(query) > 100 else query,
            )

            # Run streaming orchestrator in thread pool
            orchestrator = StreamingOrchestrator()
            loop = asyncio.get_event_loop()

            # Create a generator wrapper that runs in executor
            def run_streaming():
                return list(orchestrator.run_streaming(query))

            try:
                # Execute the streaming orchestrator
                results = await loop.run_in_executor(_executor, run_streaming)

                # Send each result as a WebSocket message
                for phase, message_text, data in results:
                    response = {
                        "phase": phase,
                        "message": message_text,
                        "data": _serialize_for_json(data),
                    }
                    await websocket.send_json(response)

                elapsed = time.time() - start_time
                logger.info(
                    "WebSocket query completed",
                    connection_id=connection_id,
                    request_id=request_id,
                    elapsed_seconds=round(elapsed, 2),
                )

            except Exception as e:
                elapsed = time.time() - start_time
                error_msg = str(e)

                logger.exception(
                    "WebSocket query failed",
                    connection_id=connection_id,
                    request_id=request_id,
                    error=error_msg,
                    elapsed_seconds=round(elapsed, 2),
                )

                await websocket.send_json({
                    "phase": "error",
                    "message": f"Error processing query: {error_msg}",
                    "data": None,
                })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", connection_id=connection_id)
    except Exception as e:
        logger.exception("WebSocket error", connection_id=connection_id, error=str(e))
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except Exception:
            pass
