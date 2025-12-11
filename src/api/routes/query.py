import asyncio
import uuid
import logging
from typing import Any
from datetime import date, datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.api.models import QueryRequest, QueryResponse
from src.agents.orchestrator import StreamingOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter()


def serialize_for_json(obj: Any) -> Any:
    """
    Recursively serialize objects to JSON-compatible format.
    Handles Pydantic models, dates, and nested structures.
    """
    if obj is None:
        return None

    # Handle Pydantic models
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode='json')

    # Handle dates and datetimes
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()

    # Handle dictionaries
    if isinstance(obj, dict):
        return {key: serialize_for_json(value) for key, value in obj.items()}

    # Handle lists and tuples
    if isinstance(obj, (list, tuple)):
        return [serialize_for_json(item) for item in obj]

    # Handle sets
    if isinstance(obj, set):
        return [serialize_for_json(item) for item in obj]

    # Primitives (str, int, float, bool) pass through
    if isinstance(obj, (str, int, float, bool)):
        return obj

    # Last resort: convert to string
    try:
        return str(obj)
    except Exception:
        return None

@router.post("", response_model=QueryResponse)
async def start_query(request: QueryRequest):
    """
    Start a new query session.
    
    In a real app, this might initialize some state or DB record.
    For now, it just generates an ID for the client to use with the WebSocket.
    """
    query_id = str(uuid.uuid4())
    logger.info(f"Generated query ID: {query_id}")
    return QueryResponse(query_id=query_id, status="started")

@router.websocket("/{query_id}/stream")
async def websocket_endpoint(websocket: WebSocket, query_id: str):
    await websocket.accept()
    logger.info(f"WebSocket connected for query {query_id}")
    
    try:
        # Wait for the client to send the query string (or we could store it from the POST)
        # But simpler for now: client connects and sends the query as the first message
        # OR we assume the frontend sends the query in the POST and we store it.
        # Let's support the client sending the query over WS if they want, 
        # or we just take the first message as the query.
        
        data = await websocket.receive_text()
        query_text = data
        
        orchestrator = StreamingOrchestrator()
        
        # Run the generator in a thread pool to avoid blocking the event loop
        # since the orchestrator might be synchronous or CPU bound
        # But StreamingOrchestrator.run_streaming is a generator.
        # If it's a sync generator, we can iterate it directly if it doesn't block too much,
        # otherwise we might need to run it in a separate thread and queue messages.
        # Given the agent does network calls, async is better, but the current agent seems sync.
        # We will iterate synchronously for now, but be aware it might block the event loop.
        # To strictly avoid blocking, we should run it in run_in_executor, but that complicates the generator.
        # For this prototype, direct iteration is acceptable if concurrent users are low.
        
        # ACTUALLY: The agent uses sync network calls (requests/httpx sync). 
        # So we MUST run this in a thread to not block the WebSocket heartbeat.
        # But iterating a generator from a thread and sending to WS is tricky.
        # Let's try direct iteration first. If it blocks pings, we'll refactor.
        
        for phase, message, details in orchestrator.run_streaming(query_text):
            # Serialize details using our recursive serializer
            serialized_details = serialize_for_json(details)

            payload = {
                "phase": phase,
                "message": message,
                "data": serialized_details
            }

            await websocket.send_json(payload)
            # Give the event loop a chance to breathe (and process pings)
            await asyncio.sleep(0.01)
            
        await websocket.close()
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for query {query_id}")
    except Exception as e:
        logger.exception(f"Error in websocket for query {query_id}: {e}")
        try:
            await websocket.send_json({"phase": "error", "message": str(e), "data": None})
            await websocket.close(code=1011)
        except:
            pass
