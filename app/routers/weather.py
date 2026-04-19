from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.crud import weather as weather_crud
from app.dependencies import get_db
from app.models.city import WeatherObservation
from app.schemas.weather_observation import (
    WeatherObservationCreate,
    WeatherObservationRead,
    WeatherObservationUpdate,
    WeatherTemperatureStats,
)

router = APIRouter(prefix="/weather", tags=["weather"])


def _http_from_value_error(exc: ValueError) -> HTTPException:
    msg = str(exc)
    code = (
        status.HTTP_409_CONFLICT
        if "integrity" in msg.lower()
        else status.HTTP_400_BAD_REQUEST
    )
    return HTTPException(status_code=code, detail={"message": msg})


@router.post(
    "/observations",
    response_model=WeatherObservationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a weather observation",
)
def create_observation(
    payload: WeatherObservationCreate,
    db: Session = Depends(get_db),
) -> WeatherObservation:
    obs = WeatherObservation(**payload.model_dump())
    try:
        return weather_crud.create_weather_observation(db, obs)
    except ValueError as e:
        raise _http_from_value_error(e) from e


@router.get(
    "/observations/stats",
    response_model=WeatherTemperatureStats,
    summary="Temperature stats for a city",
)
def temperature_stats(
    city: str = Query(..., min_length=1, description="Location name (city)"),
    db: Session = Depends(get_db),
) -> WeatherTemperatureStats:
    """Return average, max, min temperature and total record count for a city."""
    stats = weather_crud.get_temperature_stats_for_city(db, city)
    if stats is None or stats.get("count", 0) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": f"No observation found for location '{city.strip()}'"},
        )
    return stats


@router.get(
    "/observations/{observation_id}",
    response_model=WeatherObservationRead,
    summary="Get one observation by id",
)
def get_observation(
    observation_id: int,
    db: Session = Depends(get_db),
) -> WeatherObservation:
    row = weather_crud.get_weather_observation_by_id(db, observation_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": f"Observation {observation_id} not found"},
        )
    return row


@router.get(
    "/observations",
    response_model=List[WeatherObservationRead],
    summary="List observations for a city (or latest only)",
)
def list_observations_for_city(
    city: str = Query(..., min_length=1, description="Location name (city)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    latest: bool = Query(
        False,
        description="If true, return at most one row (the most recent for that city)",
    ),
    db: Session = Depends(get_db),
) -> List[WeatherObservation]:
    if latest:
        one = weather_crud.get_weather_by_city(
            db, city_name=city, latest=True
        )
        if one is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": f"No observation found for location '{city.strip()}'"},
            )
        return [one]
    rows = weather_crud.get_weather_by_city(
        db, city_name=city, limit=limit, offset=offset, latest=False
    )
    return rows


@router.patch(
    "/observations/{observation_id}",
    response_model=WeatherObservationRead,
    summary="Partially update an observation",
)
def patch_observation(
    observation_id: int,
    payload: WeatherObservationUpdate,
    db: Session = Depends(get_db),
) -> WeatherObservation:
    try:
        updated = weather_crud.update_weather_observation(
            db, observation_id, payload
        )
    except ValueError as e:
        raise _http_from_value_error(e) from e
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": f"Observation {observation_id} not found"},
        )
    return updated


@router.delete(
    "/observations/{observation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an observation",
)
def delete_observation(
    observation_id: int,
    db: Session = Depends(get_db),
) -> None:
    deleted = weather_crud.delete_weather_observation(db, observation_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": f"Observation {observation_id} not found"},
        )
 
