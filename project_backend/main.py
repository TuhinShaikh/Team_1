
from fastapi import FastAPI

from routers import endpoints 

app = FastAPI( title ="lynceus project")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Keep your existing app.include_router(...) below.
app.include_router(endpoints.router)


# curl http://127.0.0.1:8000/health

@app.get("/health")
def health():
    return {"status": "ok"}









