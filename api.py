from fastapi import FastAPI, HTTPException
from main import run_sync

app = FastAPI(title="ET Automation API")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/sync")
def sync():
    try:
        result = run_sync()
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))