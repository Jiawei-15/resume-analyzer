import logging

from fastapi import FastAPI

from app.routers.resume import router as resume_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AI Resume Analyzer API")

app.include_router(resume_router)


@app.get("/", tags=["System"])
def read_root():
    return {
        "success": True,
        "data": {
            "message": "API is running"
        }
    }