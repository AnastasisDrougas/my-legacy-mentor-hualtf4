from fastapi import FastAPI

app = FastAPI(title="Knowledge Legacy AI API")

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "knowledge-legacy-backend"
    }