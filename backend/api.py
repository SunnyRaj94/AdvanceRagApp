from fastapi import APIRouter, Request, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import os


from backend.rag.query import query_rag_system
from backend.rag.vector_store import VectorStore
from backend.rag.ingest import file_metadata_store, ingest_data
from config import settings

router = APIRouter()
DOCS_UPLOAD_DIR = settings.get("path", {}).get("upload_dir", "./data/uploaded_docs")


# Used for JSON API chat requests
class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    source: Optional[str] = "all"
    file_id: Optional[str] = None
    link_id: Optional[str] = None


def get_user_context(session, user):
    # Retrieve the user's chat history from the session
    return session.get(f"chat_history_{user}", [])


def save_user_context(session, user, chat_history):
    # Save the user's chat history to the session
    session[f"chat_history_{user}"] = chat_history


@router.post("/chat")
async def chat_json(request: Request, payload: QueryRequest):
    user = request.session.get("user", "anonymous")
    chat_history = get_user_context(request.session, user)

    try:
        print("--------------------------------------")
        print(payload)
        print("---------------------------------")
        context_limit = 5  # limit previous turns for context
        prior_context = "\n".join(chat_history[-context_limit:])

        full_query = (
            f"Previous:{prior_context}\n\nCurrent: {payload.query}"
            if prior_context
            else payload.query
        )

        response = query_rag_system(
            query=full_query,
            top_k=payload.top_k,
            source=payload.source,
            file_id=payload.file_id,
            link_id=payload.link_id,
        )

        chat_history.append(f"User: {payload.query}\nBot: {response}")
        # request.session.modified = True
        # Save chat history to session (or database for persistence)
        save_user_context(request.session, user, chat_history)

        # log_query(user=user, question=payload.query, answer=response)
        return JSONResponse({"response": response})

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/ingest/file")
async def upload_and_ingest_file(file: UploadFile, request: Request):
    try:

        file_path = os.path.join(DOCS_UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        file_id = ingest_data(file_path, source_type="file")
        return {"message": "File ingested", "file_id": file_id}

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/ingest/link")
async def ingest_link(url: str = Form(...)):
    try:
        link_id = ingest_data(url, source_type="url")
        return {"message": "Link ingested", "link_id": link_id}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/context/files")
async def list_ingested_files():
    """
    List all ingested files tracked in the JSON metadata store.
    """
    items = file_metadata_store.list()
    links = [
        {"id": k, "source": v.get("source"), "filename": k}
        for k, v in items.items()
        if v.get("type") == "file"
    ]
    return {"link-list": links}


@router.get("/context/links")
def list_ingested_links():
    items = file_metadata_store.list()
    links = [
        {"id": k, "source": v.get("source"), "filename": k}
        for k, v in items.items()
        if v.get("type") == "url"
    ]
    return {"link-list": links}


@router.delete("/delete/file/{file_id}")
def delete_file(file_id: str):
    try:
        vectorstore = VectorStore(2)
        vectorstore.load()
        file_metadata_store.delete("file", file_id)
        vectorstore.delete("file", file_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


@router.delete("/delete/link/{link_id}")
def delete_link(link_id: str):
    try:
        vectorstore = VectorStore(2)
        vectorstore.load()
        file_metadata_store.delete("link", link_id)
        vectorstore.delete("link", link_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete link: {str(e)}")
