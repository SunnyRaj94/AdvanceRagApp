import yaml
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

from frontend.ui import router as ui_router
from backend.api import router as api_router

# Load settings
with open("config/settings.yaml", "r") as f:
    settings = yaml.safe_load(f)

app = FastAPI(title=settings["app"]["name"], debug=settings["app"]["debug"])

# Middleware
app.add_middleware(SessionMiddleware, secret_key="your-session-secret-key")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static assets and templates
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

# Include routers
app.include_router(ui_router)
app.include_router(api_router)

print("Mounting UI and API routes...")
print("UI Routes:", ui_router.routes)
print("API Routes:", api_router.routes)

# For standalone execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings["app"]["host"],
        port=settings["app"]["port"],
        reload=True,
    )
