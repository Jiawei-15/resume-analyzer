import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

from app.routers.resume import router as resume_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AI Resume Analyzer API")

app.include_router(resume_router)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/", tags=["System"])
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )