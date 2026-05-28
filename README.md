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

If Vite dev mode has trouble on your Windows/Node version, use the verified production preview:

```powershell
cmd /c npm run build
cmd /c npm run serve
```

Open the Vite URL and use the seeded tenant `Acme Manufacturing`.

## Demo Uploads

Use files in `samples/`:

- `sap_fuel_procurement.csv`
- `utility_electricity.csv`
- `concur_travel.json`

## Deployment Notes

This repo can be deployed as one Render Blueprint service. The included `render.yaml` builds the React app, collects static assets, runs migrations, seeds demo reference data, and starts Django with Gunicorn.

On Render:

1. Create a new Blueprint from this GitHub repository.
2. Let Render detect `render.yaml`.
3. Deploy the web service and PostgreSQL database.
4. Open the generated `https://...onrender.com` URL.

The same deployed URL serves:

- React dashboard at `/`
- Django REST API at `/api/`
- Django admin at `/admin/`
