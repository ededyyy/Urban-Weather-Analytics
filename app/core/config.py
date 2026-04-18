from __future__ import annotations

from pydantic import BaseModel


class Settings(BaseModel):
    database_url: str = "sqlite:///./urban_weather.db"


settings = Settings()
