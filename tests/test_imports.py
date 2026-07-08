"""Import verification for the production skeleton."""

from __future__ import annotations


def test_package_imports() -> None:
    """Ensure the core application modules import cleanly."""

    import app  # noqa: F401
    import assets  # noqa: F401
    import config  # noqa: F401
    import core  # noqa: F401
    import data  # noqa: F401
    import market  # noqa: F401
    import logs  # noqa: F401
    import news  # noqa: F401
    import ui  # noqa: F401
