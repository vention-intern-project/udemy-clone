from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings

media_root = Path(settings.MEDIA_ROOT)
(media_root / "lessons" / "video").mkdir(parents=True, exist_ok=True)
(media_root / "lessons" / "pdf").mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)
app.mount("/media", StaticFiles(directory=settings.MEDIA_ROOT), name="media")


@app.get("/")
async def root():
    return {"message": "Hello World"}
