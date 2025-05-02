from fastapi import APIRouter, Request, Form
from fastapi.responses import JSONResponse
from config import settings
from backend.llm_engine import get_response_from_llm
from backend.storage import log_chat

router = APIRouter()

@router.post("/chat")
async def chat(query: str = Form(...), request: Request = None):
    user = request.session.get("user", "anonymous")

    try:
        # TODO: Add doc retrieval / RAG logic here
        context = ""  # Placeholder for retrieved context
        response = get_response_from_llm(query, context)

        # Log in MongoDB
        log_chat(user=user, question=query, answer=response)

        return JSONResponse({"response": response})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
