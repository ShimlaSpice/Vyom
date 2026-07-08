"""User interface package for VYOM Trader AI."""

# UI code remains separated from the domain and data layers so the desktop
# surface can evolve without tangling business logic.

from ui.main_window import MainWindow

__all__ = ["MainWindow"]
