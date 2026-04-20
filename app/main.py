from __future__ import annotations

from fastapi import FastAPI

from app.db.init_db import init_db
from app.routers import weather as weather_router

app = FastAPI(title="Urban Weather Analytics")
app.include_router(weather_router.router, prefix="/api/v1")
# Same routes without the /api/v1 prefix (e.g. /weather/observations); hidden from OpenAPI to avoid duplicates.
app.include_router(
    weather_router.router, prefix="", include_in_schema=False
)


@app.on_event("startup")
def _startup() -> None:
    init_db()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Weather Analytics API"}

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
