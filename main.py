from fastapi import FastAPI, HTTPException, Request
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
import yaml
import os
from backend.rag.query import query_rag_system
from frontend.ui import router as ui_router

from fastapi.templating import Jinja2Templates
from pathlib import Path

# Load config
with open("config/settings.yaml", "r") as f:
    settings = yaml.safe_load(f)

app = FastAPI(title=settings["app"]["name"], debug=settings["app"]["debug"])

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:8000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware (secret key should ideally come from env var)
app.add_middleware(SessionMiddleware, secret_key="your-session-secret-key")

# Mount static files (optional)
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Include frontend routes
app.include_router(ui_router)

# Placeholder for backend routes to be added later
# from backend.api import router as api_router
# app.include_router(api_router, prefix="/api")
# Serve templates
templates = Jinja2Templates(directory="frontend/templates")

# # Endpoint to serve HTML
# @app.get("/")
# async def get_home(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})


@app.post("/query")
async def query(query: str, top_k: int = 5):
    try:
        response = query_rag_system(query, top_k)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))






if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings["app"]["host"], port=settings["app"]["port"], reload=True)
