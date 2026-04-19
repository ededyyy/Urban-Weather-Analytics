from __future__ import annotations

from typing import List, Optional, Union

from sqlalchemy import desc, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.city import WeatherObservation
from app.schemas.weather_observation import WeatherObservationUpdate


def _validate_weather_observation(obs: WeatherObservation) -> None:
    """Validate string lengths and numeric ranges on a mapped instance."""
    if len(obs.country) > 128:
        raise ValueError("country exceeds maximum length of 128 characters")
    if len(obs.location_name) > 128:
        raise ValueError("location_name exceeds maximum length of 128 characters")
    if obs.condition_text is not None and len(obs.condition_text) > 128:
        raise ValueError("condition_text exceeds maximum length of 128 characters")

    if obs.temperature_celsius is not None:  # Temperature in Celsius
        if not isinstance(obs.temperature_celsius, (int, float)):
            raise ValueError("temperature_celsius must be a number")
        if not -100 <= obs.temperature_celsius <= 60:
            raise ValueError("Temperature out of valid range (-100 to 60)")

    if obs.humidity is not None:  # Humidity in percentage
        if isinstance(obs.humidity, bool) or not isinstance(obs.humidity, int):
            raise ValueError("humidity must be an integer")
        if not 0 <= obs.humidity <= 100:
            raise ValueError("humidity must be between 0 and 100")

    if obs.uv_index is not None:
        if not isinstance(obs.uv_index, (int, float)):
            raise ValueError("uv_index must be a number")
        if not 0 <= obs.uv_index <= 20:
            raise ValueError("uv_index must be between 0 and 20")

    if obs.air_quality_pm2_5 is not None:
        if not isinstance(obs.air_quality_pm2_5, (int, float)):
            raise ValueError("air_quality_pm2_5 must be a number")
        if obs.air_quality_pm2_5 < 0:
            raise ValueError("air_quality_pm2_5 cannot be negative")

    if obs.air_quality_pm10 is not None:
        if not isinstance(obs.air_quality_pm10, (int, float)):
            raise ValueError("air_quality_pm10 must be a number")
        if obs.air_quality_pm10 < 0:
            raise ValueError("air_quality_pm10 cannot be negative")

    if obs.air_quality_us_epa_index is not None:
        if isinstance(obs.air_quality_us_epa_index, bool) or not isinstance(
            obs.air_quality_us_epa_index, int
        ):
            raise ValueError("air_quality_us_epa_index must be an integer")
        if not 0 <= obs.air_quality_us_epa_index <= 500:
            raise ValueError("air_quality_us_epa_index must be between 0 and 500")


def get_weather_observation_by_id(
    db: Session,
    observation_id: int,
) -> Optional[WeatherObservation]:
    """Return a single observation by primary key, or None if not found."""
    return db.get(WeatherObservation, observation_id)


def get_weather_by_city(
    db: Session,
    city_name: str,
    limit: int = 20,
    offset: int = 0,
    latest: bool = False,
) -> Union[Optional[WeatherObservation], List[WeatherObservation]]:
    """
    Query weather observations for a specific city, with pagination and option
    to return only the latest record for the city.
    """
    name = city_name.strip()
    if not name:
        return None if latest else []

    if limit < 1:
        limit = 1
    if limit > 100:
        limit = 100

    q = (
        db.query(WeatherObservation)
        .filter(WeatherObservation.location_name == name)
        .order_by(desc(WeatherObservation.last_updated))
    )

    if latest:
        return q.first()

    return q.limit(limit).offset(offset).all()


def get_temperature_stats_for_city(db: Session, city_name: str) -> dict:
    """Return aggregate temperature statistics for a city.

    Result keys: `location_name`, `average_temperature_celsius`,
    `max_temperature_celsius`, `min_temperature_celsius`, `count`.
    """
    name = city_name.strip()
    if not name:
        return None

    # First check if there are any records for this city
    cnt = db.query(func.count(WeatherObservation.id)).filter(
        WeatherObservation.location_name == name
    ).scalar()
    if not cnt:
        return None

    row = (
        db.query(
            func.count(WeatherObservation.id),
            func.avg(WeatherObservation.temperature_celsius),
            func.max(WeatherObservation.temperature_celsius),
            func.min(WeatherObservation.temperature_celsius),
        )
        .filter(WeatherObservation.location_name == name)
        .one()
    )
    count, avg, maxv, minv = row
    return {
        "location_name": name,
        "average_temperature_celsius": float(avg) if avg is not None else None,
        "max_temperature_celsius": float(maxv) if maxv is not None else None,
        "min_temperature_celsius": float(minv) if minv is not None else None,
        "count": int(count) if count is not None else 0,
    }


def create_weather_observation(
    db: Session,
    observation: WeatherObservation,
) -> WeatherObservation:
    """Create a new weather observation record in the database."""
    if not observation.country or not str(observation.country).strip():
        raise ValueError("country is required")
    if not observation.location_name or not str(observation.location_name).strip():
        raise ValueError("location_name is required")
    if not observation.last_updated:
        raise ValueError("last_updated is required")

    observation.country = str(observation.country).strip()
    observation.location_name = str(observation.location_name).strip()
    if observation.condition_text is not None:
        observation.condition_text = str(observation.condition_text).strip() or None

    _validate_weather_observation(observation)

    try:
        db.add(observation)
        db.commit()
        db.refresh(observation)
        return observation
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Database integrity error: {e}") from e


def update_weather_observation(
    db: Session,
    observation_id: int,
    data: WeatherObservationUpdate,
) -> Optional[WeatherObservation]:
    """Apply a partial update; returns None if the row does not exist."""
    obs = db.get(WeatherObservation, observation_id)
    if obs is None:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is None and key in ("country", "location_name", "last_updated"):
            raise ValueError(f"{key} cannot be set to null")
        if key in ("country", "location_name") and value is not None:
            value = str(value).strip()
            if not value:
                raise ValueError(f"{key} cannot be empty")
        if key == "condition_text" and value is not None:
            value = str(value).strip() or None
        setattr(obs, key, value)

    _validate_weather_observation(obs)

    try:
        db.commit()
        db.refresh(obs)
        return obs
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Database integrity error: {e}") from e


def delete_weather_observation(db: Session, observation_id: int) -> bool:
    """Delete by primary key. Returns True if a row was deleted."""
    obs = db.get(WeatherObservation, observation_id)
    if obs is None:
        return False
    db.delete(obs)
    db.commit()
    return True
