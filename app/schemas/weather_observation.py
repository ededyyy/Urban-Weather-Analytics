from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class WeatherObservationBase(BaseModel):
    """Base schema for weather observations, used for both creation and reading."""
    country: str = Field(..., max_length=128)
    location_name: str = Field(..., max_length=128)
    last_updated: datetime

    temperature_celsius: Optional[float] = None
    condition_text: Optional[str] = Field(None, max_length=128)
    humidity: Optional[int] = None
    uv_index: Optional[float] = None

    air_quality_pm2_5: Optional[float] = None
    air_quality_pm10: Optional[float] = None
    air_quality_us_epa_index: Optional[int] = None


class WeatherObservationCreate(WeatherObservationBase):
    """For creating records: Required fields are `country`, `location_name`, `last_updated`, others are optional."""


class WeatherObservationUpdate(BaseModel):
    """For partial updates: All fields are optional."""
    country: Optional[str] = Field(None, max_length=128)
    location_name: Optional[str] = Field(None, max_length=128)
    last_updated: Optional[datetime] = None

    temperature_celsius: Optional[float] = None
    condition_text: Optional[str] = Field(None, max_length=128)
    humidity: Optional[int] = None
    uv_index: Optional[float] = None

    air_quality_pm2_5: Optional[float] = None
    air_quality_pm10: Optional[float] = None
    air_quality_us_epa_index: Optional[int] = None


class WeatherObservationRead(WeatherObservationBase):
    """For reading records: All fields are included, with `id`."""
    model_config = ConfigDict(from_attributes=True)

    id: int
