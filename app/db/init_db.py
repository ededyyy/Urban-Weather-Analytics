from __future__ import annotations

from app.db.session import engine
from app.db.base import Base

# Import models so SQLAlchemy registers them on Base.metadata
from app.models.city import WeatherObservation  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

