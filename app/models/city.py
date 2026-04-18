from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from typing import Optional


class WeatherObservation(Base):
    """
    Minimal schema for CWK analytics use-cases:
    - where/when: country, location_name, last_updated
    - weather: temperature_celsius, condition_text, humidity, uv_index
    - air quality: PM2.5, PM10, US EPA index
    """

    __tablename__ = "weather_observations"
    __table_args__ = (
        UniqueConstraint(
            "country",
            "location_name",
            "last_updated",
            name="uq_weather_observation_loc_time",
        ),
        Index("ix_weather_observation_location", "country", "location_name"),
        Index("ix_weather_observation_last_updated", "last_updated"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    country: Mapped[str] = mapped_column(String(128), nullable=False)
    location_name: Mapped[str] = mapped_column(String(128), nullable=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    temperature_celsius: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    condition_text: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    humidity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    uv_index: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    air_quality_pm2_5: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    air_quality_pm10: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    air_quality_us_epa_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
