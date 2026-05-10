"""Smoke tests for the CLI hello-world. Verifies click + pytest
plumbing is wired correctly; the team extends with feature tests."""

from __future__ import annotations

from src.cli import main


def test_greet_default_name(runner) -> None:
    result = runner.invoke(main, ["greet"])
    assert result.exit_code == 0
    assert "Hello, World!" in result.output


def test_greet_custom_name(runner) -> None:
    result = runner.invoke(main, ["greet", "--name", "Alice"])
    assert result.exit_code == 0
    assert "Hello, Alice!" in result.output
