from __future__ import annotations

from fastapi import FastAPI

from app.db.init_db import init_db

app = FastAPI(title="Urban Weather Analytics")


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
