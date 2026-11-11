from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import endpoints, search_api

app = FastAPI(title="lynceus project")

app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(endpoints.router)
app.include_router(search_api.router)


@app.get("/health")
def health():
    return {"status": "ok"}