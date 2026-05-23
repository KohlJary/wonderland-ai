#!/usr/bin/env python3
"""Run the Finance TUI frontend."""
from src.frontend.app import FinanceTUIApp

if __name__ == "__main__":
    app = FinanceTUIApp()
    app.run()
