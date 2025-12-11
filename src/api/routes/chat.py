import structlog
from fastapi import APIRouter, Depends, HTTPException
from openai import AsyncOpenAI

from src.api.models.requests import ChatRequest, ChatResponse
from src.config import settings
from src.data.vector_store import FilingVectorStore, get_vector_store

router = APIRouter()
logger = structlog.get_logger()

# Helper to format citations
def format_source(doc) -> str:
    meta = doc.get("metadata", {})
    ticker = meta.get("ticker", "UNKNOWN")
    section = meta.get("section_name", "Section")
    return f"[{ticker} {section}]"


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    vector_store: FilingVectorStore = Depends(get_vector_store),
):
    """
    Chat with SEC filings.
    """
    try:
        # 1. Build Query from last message
        current_query = request.messages[-1].content

        # 2. Retrieve Context
        # Search for chunks
        search_results = vector_store.search(
            query=current_query,
            ticker=request.ticker,
            limit=5
        )

        context_str = ""
        citations = []
        for res in search_results:
            source = format_source(res)
            # Add citation to list if unique
            if source not in citations:
                citations.append(source)

            # Simple context format
            context_str += f"Source {source}:\n{res['content']}\n\n"

        # 3. Construct System Prompt
        system_prompt = f"""You are a helpful financial analyst assistant.
Answer the user's question based ONLY on the provided context.
If the answer is not in the context, say regular things but mention you don't have specific data.
Always cite your sources using the format [TICKER SECTION].

Context:
{context_str}
"""

        # 4. Call OpenAI
        # We need an Async client. Ideally initialized once, but for now:
        client = AsyncOpenAI(api_key=settings.openai_api_key)

        messages = [{"role": "system", "content": system_prompt}]
        # Add history (excluding last msg which we use for query? Or include all?)
        # Let's simple format: system + user (with intent).
        # Actually standard RAG is: System (with context) + User (query).
        # History handling is more complex (condensing).
        # MVP: Just System + User Query. Ignore history for retrieval context,
        # but maybe pass history to LLM?
        # Let's pass full history but replace the last system message?
        # Easier: System + User.
        messages.append({"role": "user", "content": current_query})

        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            temperature=0,
        )

        answer = response.choices[0].message.content
        usage = response.usage.model_dump() if response.usage else {}

        return ChatResponse(
            answer=answer,
            citations=citations,
            usage=usage
        )

    except Exception as e:
        logger.exception("Chat failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
