"""Import verification for the local web application."""

from __future__ import annotations


def test_package_imports() -> None:
    """Ensure the backend and shared modules import cleanly."""

    import backend.app.main  # noqa: F401
    import config  # noqa: F401
    import core  # noqa: F401
    import data  # noqa: F401
    import market  # noqa: F401
    import news  # noqa: F401
