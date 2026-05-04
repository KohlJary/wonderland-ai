"""Smoke test — verify the package imports and reports a version."""

import wonderland


def test_version_present() -> None:
    assert wonderland.__version__
    assert isinstance(wonderland.__version__, str)
