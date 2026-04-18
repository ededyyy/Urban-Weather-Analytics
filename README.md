# Urban-Weather-Analytics
Urban climate API for historical weather, air quality, temperature, and city trend analytics

## Quick start

Install deps:

```bash
pip install -r requirements.txt
```

Initialize DB + import CSV:

```bash
python -m app.db.import_csv --csv "data/raw/kaggle/GlobalWeatherRepository.csv"
```

Run API:

```bash
uvicorn app.main:app --reload
```
