# Breathe ESG Data Ingestion Prototype

Django REST + React prototype for ingesting enterprise ESG source data, normalizing it, and giving analysts a review dashboard before records are locked for audit.

## What This Builds

- SAP fuel/procurement CSV ingestion with plant lookup, German/English header aliases, date parsing, and unit normalization.
- Utility electricity CSV ingestion with billing periods, meters, tariff names, kWh/MWh normalization, and suspicious period checks.
- Concur-like corporate travel JSON ingestion for flights, hotels, rail, rental car, taxi, and rideshare categories.
- Analyst dashboard for ingestion status, failed/suspicious records, approval, rejection, editing, and audit locking.
- Required assignment docs: `MODEL.md`, `DECISIONS.md`, `TRADEOFFS.md`, and `SOURCES.md`.

## Local Setup

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Frontend:

```powershell
cd frontend
cmd /c npm install
cmd /c npm run dev
```

## Demo Uploads

Use files in `samples/`:

- `sap_fuel_procurement.csv`
- `utility_electricity.csv`
- `concur_travel.json`
