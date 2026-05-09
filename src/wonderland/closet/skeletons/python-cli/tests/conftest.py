"""Pytest fixtures for CLI testing.

Provides ``runner`` — Click's ``CliRunner`` for invoking the CLI
without subprocessing. Tests then call ``runner.invoke(cli, [...])``
and assert against the captured output.
"""

from __future__ import annotations

import pytest
from click.testing import CliRunner


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()
