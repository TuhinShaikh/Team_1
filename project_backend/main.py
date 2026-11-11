
from fastapi import FastAPI

from routers import endpoints 

app = FastAPI( title ="lynceus project")


app.include_router(endpoints.router)



# curl http://127.0.0.1:8000/health

@app.get("/health")
def health():
    return {"status": "ok"}









