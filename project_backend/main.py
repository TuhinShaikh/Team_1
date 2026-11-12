
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# The hybrid search API lives in the repository root. Load its router package
# before the older backend-local routers package with the same name.
REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPOSITORY_ROOT / ".env")
sys.path.insert(0, str(REPOSITORY_ROOT))
from routers import endpoints, search_api

app = FastAPI()

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



# curl http://127.0.0.1:8000/health

@app.get("/health")
def health():
    return {"status": "ok"}









