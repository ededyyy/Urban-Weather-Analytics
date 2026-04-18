from __future__ import annotations

from typing import List, Optional, Union

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.city import WeatherObservation


def get_weather_by_city(
	db: Session,
	city_name: str,
	limit: int = 20,
	offset: int = 0,
	latest: bool = False,  # If True, return only the latest record for the city
) -> Union[Optional[WeatherObservation], List[WeatherObservation]]:
	"""
	Query weather observations for a specific city, with pagination and option to get only the latest record.    
	"""

	# Limit should be between 1 and 100 to prevent excessive data retrieval
	if limit < 1:
		limit = 1
	if limit > 100:
		limit = 100

    # Query the database for weather observations matching the city name, ordered by last_updated descending
	q = db.query(WeatherObservation).filter(
		WeatherObservation.location_name == city_name
	).order_by(desc(WeatherObservation.last_updated))

	if latest:
		return q.first()

	return q.limit(limit).offset(offset).all()

