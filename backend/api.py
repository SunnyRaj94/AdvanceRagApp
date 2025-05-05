from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from backend.rag.query import query_rag_system

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    source: str = "all"


def handle_query(query: str, top_k: int, source: str, user: str = "anonymous"):
    """
    Common logic to process the query using RAG system and log the result.
    """
    print(f"Handling query: '{query}', top_k={top_k}, source='{source}', user='{user}'")
    response = query_rag_system(query, top_k, source)
    # log_query(user=user, question=query, answer=response)
    return response


@router.post("/chat")
async def chat_handler(
    request: Request,
    query: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    top_k: Optional[int] = Form(None),
):
    """
    Unified handler for both form submissions and JSON payloads.
    """
    user = request.session.get("user", "anonymous")

    # Try to use form data first
    if query:
        final_query = query
        final_source = source if source else "all"
        final_top_k = top_k if top_k is not None else 5
    else:
        # Try to read JSON body
        try:
            json_data = await request.json()
            body = QueryRequest(**json_data)
            final_query = body.query
            final_top_k = body.top_k
            final_source = body.source
        except Exception as e:
            print("Error parsing JSON body:", e)
            raise HTTPException(status_code=422, detail="Invalid request body")

    if not final_query:
        raise HTTPException(status_code=400, detail="Query is required")

    # Handle query and return result
    try:
        response = handle_query(final_query, final_top_k, final_source, user)
        return JSONResponse(content={"response": response})
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"RAG Error: {str(e)}")
