# AI-Powered Automatic Block Planning

An Indian Railways maintenance-block optimizer that combines timetable data,
CP-SAT scheduling, a FastAPI backend, and a React operations dashboard.

## Architecture

```text
React dashboard -> FastAPI -> CP-SAT optimizer -> SQLite
       ^                                      |
       +------------- REST API --------------+
```

## Tech stack

- Python, FastAPI, SQLAlchemy, SQLite
- Google OR-Tools CP-SAT
- React, Vite, CSS

## Setup

### Backend

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`. Tables are created automatically on
startup. The default database is `railway_blocks.db`; set `DATABASE_URL` in
`.env` to use another database.

### Frontend

```powershell
cd Railway
npm install
npm run dev
```

The dashboard runs at `http://localhost:5173`. For a deployed backend, set
`VITE_API_BASE_URL` in `Railway/.env` before running `npm run build`.

## Data and optimization

The scripts in `scripts/` ingest train movements, seed maintenance requests,
run the CP-SAT optimizer, and validate the resulting schedule:

```powershell
python scripts/ingest_trains.py
python scripts/seed_maintenance.py
python scripts/run_optimizer.py
python scripts/validate_step2.py
```

The optimizer avoids train conflicts, respects incompatible departments, and
clusters compatible maintenance requests into integrated blocks.

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | Service health |
| GET | `/api/tracks` | Railway sections |
| GET | `/api/trains` | Train movements |
| GET/POST | `/api/maintenance` | Maintenance requests |
| GET | `/api/blocks` | Allocated blocks |
| GET | `/api/kpis` | Before/after KPIs |
| POST | `/api/optimization/run` | Run CP-SAT optimization |
| GET | `/api/optimization/latest` | Latest optimized blocks |

Interactive OpenAPI documentation is available at `/docs`.

## Testing

```powershell
python -m unittest discover -s tests -v
cd Railway
npm run build
```
