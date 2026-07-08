"""Launcher for the local web application."""

from __future__ import annotations

import sys

from backend.app.main import main


if __name__ == "__main__":
    sys.exit(main())
