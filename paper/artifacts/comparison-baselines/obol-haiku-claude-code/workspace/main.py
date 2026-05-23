#!/usr/bin/env python3
"""Entry point for finance dashboard."""
from finance_dashboard.app import FinanceDashboard

if __name__ == "__main__":
    dashboard = FinanceDashboard("finance.db")
    dashboard.run()
