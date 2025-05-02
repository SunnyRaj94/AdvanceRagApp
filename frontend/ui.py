from fastapi import APIRouter, Request, Form, UploadFile, File, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
import shutil
import os

from config import settings

router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates")

UPLOAD_DIR = settings["paths"]["upload_dir"]
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_current_user(request: Request):
    return request.session.get("user")

@router.get("/test", response_class=HTMLResponse)
async def test_page(request: Request):
    return HTMLResponse(content="Test page works!")


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/chat")
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    # For demo, accept any user (replace with real auth later)
    request.session["user"] = username
    return RedirectResponse(url="/chat", status_code=302)


@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    if not get_current_user(request):
        return RedirectResponse(url="/")
    return templates.TemplateResponse("upload.html", {"request": request})


@router.post("/upload", response_class=HTMLResponse)
async def upload_file(request: Request, file: UploadFile = File(...)):
    if not get_current_user(request):
        return RedirectResponse(url="/")
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return templates.TemplateResponse("upload.html", {"request": request, "msg": f"Uploaded {file.filename}"})


@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    if not get_current_user(request):
        return RedirectResponse(url="/")
    return templates.TemplateResponse("chat.html", {"request": request})
