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

The backend includes `Procfile`, `runtime.txt`, and production settings for Render/Railway-style deployments. Set:

- `SECRET_KEY`
- `DEBUG=false`
- `ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`
- `DATABASE_URL`

The frontend can be deployed on Vercel/Netlify with:

- `VITE_API_BASE_URL=https://your-backend.example.com/api`
