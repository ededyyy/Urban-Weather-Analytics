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


def _to_nullable_float(value: object) -> float | None:
    """Convert a CSV value to float, treating NaN and sentinel values as None.

    The dataset uses -9999 (and similar large negative placeholders) as missing
    data. Values <= -900 are treated as missing (real surface weather quantities
    in this export do not use that range).
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        v = float(value)
    except Exception:
        return None
    if v <= -900:
        return None
    return v


def _to_nullable_air_quality_float(value: object) -> float | None:
    """PM2.5 / PM10: concentration cannot be negative; any negative is invalid or sentinel."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        v = float(value)
    except Exception:
        return None
    if v < 0:
        return None
    return v


def _to_nullable_int(value: object) -> int | None:
    f = _to_nullable_float(value)
    return None if f is None else int(f)


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
                existing.temperature_celsius = _to_nullable_float(temperature_celsius)
                existing.condition_text = (
                    str(condition_text) if pd.notna(condition_text) else None
                )
                existing.humidity = _to_nullable_int(humidity)
                existing.uv_index = _to_nullable_float(uv_index)
                existing.air_quality_pm2_5 = _to_nullable_air_quality_float(pm2_5)
                existing.air_quality_pm10 = _to_nullable_air_quality_float(pm10)
                existing.air_quality_us_epa_index = _to_nullable_int(us_epa)
                updated += 1
            else:
                db.add(
                    WeatherObservation(
                        country=country,
                        location_name=location_name,
                        last_updated=last_updated,
                        temperature_celsius=_to_nullable_float(temperature_celsius),
                        condition_text=str(condition_text)
                        if pd.notna(condition_text)
                        else None,
                        humidity=_to_nullable_int(humidity),
                        uv_index=_to_nullable_float(uv_index),
                        air_quality_pm2_5=_to_nullable_air_quality_float(pm2_5),
                        air_quality_pm10=_to_nullable_air_quality_float(pm10),
                        air_quality_us_epa_index=_to_nullable_int(us_epa),
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

