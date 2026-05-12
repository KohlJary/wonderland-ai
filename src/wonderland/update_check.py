"""PyPI update check — best-effort fetch of the latest released
version of the ``wonderland-ai`` package so the TUI can surface a
"new version available" modal on startup.

The check is intentionally simple: a single HTTPS GET to PyPI's
JSON API, parsed for the ``info.version`` field, compared against
the installed version via PEP 440 packaging. Network failures
swallow silently — a disconnected operator still gets a working TUI.

Comparison delegates to ``packaging.version`` when available;
falls back to string-compare for the rare environment without
``packaging`` installed (an unsupported configuration in practice
because ``pip`` depends on it, but the fallback keeps the path
total).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import metadata
from urllib.error import URLError
from urllib.request import Request, urlopen

PACKAGE_NAME = "wonderland-ai"
PYPI_JSON_URL = f"https://pypi.org/pypi/{PACKAGE_NAME}/json"
DEFAULT_TIMEOUT_SECONDS = 4.0


@dataclass(frozen=True)
class UpdateCheckResult:
    installed: str
    latest: str
    update_available: bool


def installed_version() -> str:
    """Return the installed package version via importlib.metadata.
    Returns ``"0.0.0"`` if the package can't be resolved (e.g. running
    from a source checkout that wasn't ``pip install -e``'d), which
    flags as "any released version is newer" — same outcome the user
    would want anyway."""
    try:
        return metadata.version(PACKAGE_NAME)
    except metadata.PackageNotFoundError:
        return "0.0.0"


def _compare_versions(installed: str, latest: str) -> bool:
    """True when ``latest > installed`` per PEP 440 semantics. Falls
    back to string compare if packaging isn't importable."""
    try:
        from packaging.version import Version

        return Version(latest) > Version(installed)
    except Exception:  # noqa: BLE001
        return latest != installed and latest > installed


def fetch_latest_version(
    *, timeout: float = DEFAULT_TIMEOUT_SECONDS
) -> str | None:
    """Hit PyPI's JSON API and pull the latest released version.
    Returns ``None`` on any error so callers can degrade silently —
    no exceptions escape this function.
    """
    request = Request(
        PYPI_JSON_URL,
        headers={"Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                return None
            payload = json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None
    info = payload.get("info") or {}
    version = info.get("version")
    if not isinstance(version, str) or not version.strip():
        return None
    return version.strip()


def check_for_update(
    *, timeout: float = DEFAULT_TIMEOUT_SECONDS
) -> UpdateCheckResult | None:
    """End-to-end update check. Returns an ``UpdateCheckResult`` on
    success, ``None`` on any failure (network / parse / package
    missing). Callers should treat ``None`` as "skip the modal."
    """
    latest = fetch_latest_version(timeout=timeout)
    if latest is None:
        return None
    installed = installed_version()
    return UpdateCheckResult(
        installed=installed,
        latest=latest,
        update_available=_compare_versions(installed, latest),
    )


__all__ = [
    "PACKAGE_NAME",
    "UpdateCheckResult",
    "check_for_update",
    "fetch_latest_version",
    "installed_version",
]
