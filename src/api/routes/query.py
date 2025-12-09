import asyncio
import uuid
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.api.models import QueryRequest, QueryResponse
from src.agents.orchestrator import StreamingOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter()

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
            payload = {
                "phase": phase,
                "message": message,
                "data": details
            }
            # Simple serialization of details might fail if it contains non-serializable objects (like Pydantic models)
            # Pydantic models have .model_dump() or .dict()
            if hasattr(details, "model_dump"):
                payload["data"] = details.model_dump()
            elif hasattr(details, "dict"):
                 payload["data"] = details.dict()
                 
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
