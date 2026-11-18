
from contextlib import asynccontextmanager
from app.routers.documents import router as documents_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.conversations import router as conversations_router
from app.config import settings
from app.database import init_db
from app.routers.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite on application startup
    init_db()
    yield


app = FastAPI(
    title="Knowledge Legacy AI API",
    lifespan=lifespan,
)

# Allow configured frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(conversations_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "knowledge-legacy-backend",
    }
