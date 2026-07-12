"""Application package for Vyom."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from .market.market_data_provider import MarketDataProvider
from .scanner.scanner import ScannerEngine

_app_entry_path = Path(__file__).resolve().parent.parent / "app.py"
if _app_entry_path.exists():
    _spec = spec_from_file_location("vyom_app_entry", _app_entry_path)
    if _spec is not None and _spec.loader is not None:
        _module = module_from_spec(_spec)
        _spec.loader.exec_module(_module)
        main = _module.main
        build_container = _module.build_container
        TraderApplication = _module.TraderApplication
    else:
        main = None
        build_container = None
        TraderApplication = None
else:
    main = None
    build_container = None
    TraderApplication = None

__all__ = ["ScannerEngine", "MarketDataProvider", "main", "build_container", "TraderApplication"]
