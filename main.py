import yaml
from fastapi import FastAPI, HTTPException
from backend.rag.query import query_rag_system
from frontend.ui import router as ui_router
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

# Load settings
with open("config/settings.yaml", "r") as f:
    settings = yaml.safe_load(f)

from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


app = FastAPI(title=settings["app"]["name"], debug=settings["app"]["debug"])

app.add_middleware(SessionMiddleware, secret_key="your-session-secret-key")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
app.include_router(ui_router)

print("Mounting UI routes...")
print("Available routes:", ui_router.routes)

# Serve templates
templates = Jinja2Templates(directory="frontend/templates")


@app.post("/api/chat")
async def query(request: QueryRequest):
    try:
        print(f"Received query: {request.query}, top_k: {request.top_k}")
        response = query_rag_system(request.query, request.top_k)
        print(f"Generated response: {response}")
        return {"response": response}
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"RAG Error: {str(e)}")


# Only needed for local script execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings["app"]["host"],
        port=settings["app"]["port"],
        reload=True,
    )
