# VYOM Trader AI

VYOM Trader AI is a production-grade desktop application skeleton for Indian intraday trading workflows.

## Project Structure

- `app.py` - Primary desktop application entry point.
- `config.py` - Central JSON configuration loader and typed settings model.
- `core/` - Infrastructure services such as logging, database, scheduler, and cache.
- `market/` - Market-domain service boundary.
- `news/` - News-domain service boundary.
- `ai/` - AI decision-engine boundary.
- `ui/` - PySide6 desktop user interface.
- `data/` - Data access and ORM primitives.
- `tests/` - Import and bootstrap validation.
- `assets/` - Static application assets.
- `logs/` - Runtime log output.

## Runtime Files

- `settings.json` contains the canonical runtime configuration.
- SQLite data is stored under the configured `data/` directory.
- Log files are written under the configured `logs/` directory.

## Notes

- The repository intentionally contains architecture only.
- Trading, scanner, analytics, and AI logic are not implemented yet.
