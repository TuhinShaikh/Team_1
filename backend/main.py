
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPOSITORY_ROOT / ".env")
from backend.routers import endpoints, search_api

app = FastAPI(title="Lynceus API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(endpoints.router)
app.include_router(search_api.router)



@app.get("/health")
def health():
    return {"status": "ok"}









