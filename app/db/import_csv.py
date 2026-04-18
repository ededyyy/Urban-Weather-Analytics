from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.init_db import init_db
from app.db.session import get_session
from app.models.city import WeatherObservation


def _to_datetime(value: object) -> datetime | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    # CSV example: "2024-05-16 13:15"
    return pd.to_datetime(value, errors="coerce").to_pydatetime()


def import_global_weather_csv(
    *,
    csv_path: Path,
    db: Session,
    batch_size: int = 2000,
) -> dict[str, int]:
    df = pd.read_csv(csv_path)

    required_cols = [
        "country",
        "location_name",
        "last_updated",
        "temperature_celsius",
        "condition_text",
        "humidity",
        "uv_index",
        "air_quality_PM2.5",
        "air_quality_PM10",
        "air_quality_us-epa-index",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")

    inserted = 0
    updated = 0

    records = df.to_dict(orient="records")
    for i in range(0, len(records), batch_size):
        chunk = records[i : i + batch_size]

        for row in chunk:
            country = str(row.get("country") or "").strip()
            location_name = str(row.get("location_name") or "").strip()
            last_updated = _to_datetime(row.get("last_updated"))
            if not country or not location_name or last_updated is None:
                continue

            temperature_celsius = row.get("temperature_celsius")
            condition_text = row.get("condition_text")
            humidity = row.get("humidity")
            uv_index = row.get("uv_index")
            pm2_5 = row.get("air_quality_PM2.5")
            pm10 = row.get("air_quality_PM10")
            us_epa = row.get("air_quality_us-epa-index")

            existing = db.scalar(
                select(WeatherObservation).where(
                    WeatherObservation.country == country,
                    WeatherObservation.location_name == location_name,
                    WeatherObservation.last_updated == last_updated,
                )
            )

            if existing:
                existing.temperature_celsius = (
                    float(temperature_celsius) if pd.notna(temperature_celsius) else None
                )
                existing.condition_text = (
                    str(condition_text) if pd.notna(condition_text) else None
                )
                existing.humidity = int(humidity) if pd.notna(humidity) else None
                existing.uv_index = float(uv_index) if pd.notna(uv_index) else None
                existing.air_quality_pm2_5 = float(pm2_5) if pd.notna(pm2_5) else None
                existing.air_quality_pm10 = float(pm10) if pd.notna(pm10) else None
                existing.air_quality_us_epa_index = int(us_epa) if pd.notna(us_epa) else None
                updated += 1
            else:
                db.add(
                    WeatherObservation(
                        country=country,
                        location_name=location_name,
                        last_updated=last_updated,
                        temperature_celsius=float(temperature_celsius)
                        if pd.notna(temperature_celsius)
                        else None,
                        condition_text=str(condition_text)
                        if pd.notna(condition_text)
                        else None,
                        humidity=int(humidity) if pd.notna(humidity) else None,
                        uv_index=float(uv_index) if pd.notna(uv_index) else None,
                        air_quality_pm2_5=float(pm2_5) if pd.notna(pm2_5) else None,
                        air_quality_pm10=float(pm10) if pd.notna(pm10) else None,
                        air_quality_us_epa_index=int(us_epa) if pd.notna(us_epa) else None,
                    )
                )
                inserted += 1

        try:
            db.commit()
        except IntegrityError:
            # If two rows in the same batch conflict, retry by flushing one-by-one.
            db.rollback()
            for row in chunk:
                country = str(row.get("country") or "").strip()
                location_name = str(row.get("location_name") or "").strip()
                last_updated = _to_datetime(row.get("last_updated"))
                if not country or not location_name or last_updated is None:
                    continue

                existing = db.scalar(
                    select(WeatherObservation).where(
                        WeatherObservation.country == country,
                        WeatherObservation.location_name == location_name,
                        WeatherObservation.last_updated == last_updated,
                    )
                )
                if existing:
                    continue
                db.add(
                    WeatherObservation(
                        country=country,
                        location_name=location_name,
                        last_updated=last_updated,
                    )
                )
                try:
                    db.commit()
                except IntegrityError:
                    db.rollback()

    return {"inserted": inserted, "updated": updated}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        required=True,
        help="Path to GlobalWeatherRepository.csv",
    )
    args = parser.parse_args()

    init_db()
    db = get_session()
    try:
        stats = import_global_weather_csv(csv_path=Path(args.csv), db=db)
    finally:
        db.close()
    print(stats)


if __name__ == "__main__":
    main()

