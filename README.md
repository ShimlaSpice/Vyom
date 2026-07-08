# VYOM Trader AI Web

VYOM Trader AI has been migrated from a desktop shell to a local web application.

## Stack

- `FastAPI` for the backend API
- `React + TypeScript` for the frontend
- `SQLite` for local persistence
- `Alembic` for database migrations
- `SQLAlchemy` for ORM access
- A heuristic AI/decision engine scaffold for market signals

## Project Layout

- `backend/` - FastAPI application, service layer, and API schemas.
- `frontend/` - React + TypeScript UI built with Vite.
- `data/` - Shared SQLAlchemy models and the local SQLite database.
- `migrations/` - Alembic migration environment and revisions.
- `config.py` - Shared runtime settings loader.
- `main.py` - Local web server launcher.

## Local Setup

1. Create and activate the Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   cd ..
   ```
4. Run the database migration:
   ```bash
   alembic upgrade head
   ```

## Run The App

- Start the backend API:
  ```bash
  python main.py
  ```
- Start the frontend in a second terminal:
  ```bash
  cd frontend
  npm run dev
  ```

Open the frontend at `http://127.0.0.1:5173`.

## API Endpoints

- `GET /api/health`
- `GET /api/dashboard`
- `GET /api/symbols`
- `POST /api/symbols`
- `GET /api/market/snapshots`
- `POST /api/market/snapshots`
- `GET /api/news/items`
- `POST /api/news/items`
- `GET /api/decisions`
- `POST /api/decisions/run`

## Notes

- The backend seeds demo market data automatically on first boot.
- The legacy desktop files remain in the repository, but the active entrypoint is now the web app.
