"""Pytest plumbing for Textual app tests.

Textual tests are async — pytest-asyncio is wired in pyproject's
[tool.pytest.ini_options] asyncio_mode = "auto" so individual
tests can just be ``async def``.
"""
