# Urban Weather Analytics

A small **FastAPI** service backed by **SQLite** for storing and querying urban weather and air-quality observations. It features a specialized CSV ingestion pipeline designed for standardized weather datasets (e.g., Kaggle’s Global Weather Repository), and exposes a JSON **REST API** for full CRUD on weather observations.

## Project overview

| Area | Description |
|------|-------------|
| **API** | FastAPI application in `app/main.py`; weather routes live under `app/routers/weather.py`. |
| **Data model** | `WeatherObservation` in `app/models/city.py` — country, location, timestamp, temperature, conditions, humidity, UV, PM2.5, PM10, US EPA index. |
| **Persistence** | SQLAlchemy ORM; default database is SQLite file `urban_weather.db` in the **current working directory**. |
| **Bulk import** | `python -m app.db.import_csv --csv <path>` reads CSV columns such as `country`, `location_name`, `last_updated`, and air-quality fields; the importer normalises common missing-value sentinels (for example very large negative placeholders) into NULLs. A small demo CSV is included at `data/example/demo.csv` for quick runnable demos. |

## Prerequisites

- **Python 3.10+** (3.11 recommended)

## Setup

1. **Clone the repository** and open a terminal in the project root.

2. **Create and activate a virtual environment** (recommended):

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Prepare your CSV**. For quick demos a small sample is included at `data/example/demo.csv`; place larger/full datasets under `data/raw/` (for example `data/raw/kaggle/GlobalWeatherRepository.csv`). The importer expects columns including:

   `country`, `location_name`, `last_updated`, `temperature_celsius`, `condition_text`, `humidity`, `uv_index`, `air_quality_PM2.5`, `air_quality_PM10`, `air_quality_us-epa-index`.

5. **Create tables and import data:**

   ```bash
   # import the demo CSV
   python -m app.db.import_csv --csv data/example/demo.csv

   # or import a larger/full CSV
   python -m app.db.import_csv --csv "data/raw/kaggle/GlobalWeatherRepository.csv"
   ```

   This creates `urban_weather.db` in the working directory where you run the command.

## Running the API

From the project root:

```bash
uvicorn app.main:app --reload
```

Default URL: **http://127.0.0.1:8000**

- **Deployed (Render):** https://urban-weather-analytics.onrender.com

- **Root:** `GET /` — short welcome JSON.
- **Health:** `GET /health` — `{"status":"ok"}` for uptime checks.
- **Interactive docs (Swagger UI):** http://127.0.0.1:8000/docs — try all endpoints in the browser.
- **ReDoc:** http://127.0.0.1:8000/redoc
- **OpenAPI schema (JSON):** http://127.0.0.1:8000/openapi.json

## Using the API

All weather endpoints are prefixed with **`/api/v1`**. Base URL example: `http://127.0.0.1:8000/api/v1/weather`.

Deployed base URL (Render): `https://urban-weather-analytics.onrender.com/api/v1/weather`

API Doc：[Urban-Weather-Analytics-API.pdf](Urban-Weather-Analytics-API.pdf)

Weather endpoints require **HTTP Basic Auth**.

- Username env var: `API_AUTH_USERNAME` (default: `admin`)
- Password env var: `API_AUTH_PASSWORD` (default: `admin123`)

To customize these credentials, set the env vars. (PowerShell: `$env:API_AUTH_USERNAME="..."` and `$env:API_AUTH_PASSWORD="..."` before starting `uvicorn`).

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/weather/observations` | Create record. Returns **201** on success. |
| `GET` | `/weather/observations/{id}` | Fetch one row by numeric `id`. **404** if missing. |
| `GET` | `/weather/observations?city=<name>` | List observations for a city (`limit`, `offset` optional). Add `latest=true` for the single newest row (**404** if none). |
| `PATCH` | `/weather/observations/{id}` | Partial update (JSON body with any subset of fields). |
| `DELETE` | `/weather/observations/{id}` | Delete a row. **204** with empty body on success; **404** if not found. |

Validation errors return **422** with a JSON `detail` payload. Business rule or duplicate-key issues may return **400** or **409** depending on the case.

### Quick examples

Replace host/port if you deploy elsewhere.

```bash
curl -s http://127.0.0.1:8000/health
```

```bash
curl.exe -v -u wrong:wrong "http://localhost:8000/api/v1/weather/observations?city=Tirana"
```

```bash
curl -s -u admin:admin123 "http://127.0.0.1:8000/api/v1/weather/observations?city=London&limit=5"
```

```bash
curl -s -u admin:admin123 -X POST http://127.0.0.1:8000/api/v1/weather/observations ^
  -H "Content-Type: application/json" ^
  -d "{\"country\":\"UK\",\"location_name\":\"London\",\"last_updated\":\"2024-05-16T13:15:00\",\"temperature_celsius\":18.5}"
```

(On PowerShell, escaping quotes in inline JSON can be awkward; using **Swagger UI** at `/docs` is often easier for `POST`/`PATCH`.)

## Brief project layout、

```
app/
  main.py              # FastAPI app, router mount, startup DB init
  routers/weather.py   # HTTP routes
  crud/weather.py      # Database CRUD logic
  models/city.py       # SQLAlchemy models
  schemas/             # Pydantic request/response models
  db/                  # Engine, sessions, CSV import, init_db
```

## Licence

See `LICENSE` in the repository.
