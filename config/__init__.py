"""Compatibility package that re-exports the root configuration module."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _load_root_config() -> ModuleType:
    """Load the root-level `config.py` module without name collisions."""

    module_path = Path(__file__).resolve().parents[1] / "config.py"
    spec = importlib.util.spec_from_file_location("_vyom_root_config", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load configuration module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_impl = _load_root_config()

ApplicationConfig = _impl.ApplicationConfig
CacheConfig = _impl.CacheConfig
ConfigManager = _impl.ConfigManager
ConfigurationError = _impl.ConfigurationError
DatabaseConfig = _impl.DatabaseConfig
LoggingConfig = _impl.LoggingConfig
PathConfig = _impl.PathConfig
SchedulerConfig = _impl.SchedulerConfig
SchedulerJobDefaults = _impl.SchedulerJobDefaults
Settings = _impl.Settings

__all__ = [
    "ApplicationConfig",
    "CacheConfig",
    "ConfigManager",
    "ConfigurationError",
    "DatabaseConfig",
    "LoggingConfig",
    "PathConfig",
    "SchedulerConfig",
    "SchedulerJobDefaults",
    "Settings",
]
