
from fastapi import FastAPI


app = FastAPI( title ="lynceus project")




# curl http://127.0.0.1:8000/health

@app.get("/health")
def health():
    return {"status": "ok"}









