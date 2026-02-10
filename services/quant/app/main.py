from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import recommend

app = FastAPI(title="LPQuant Engine", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recommend.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
