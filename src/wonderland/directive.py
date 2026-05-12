"""Directive presets — saved directive snippets the TUI's NewRunScreen
picks from when composing a run.

Composes with closet's existing skeleton + workflow patterns. Bundled
presets live at ``closet/directives/<name>.yaml``; per-project presets
live at ``<project_root>/.wonderland/directives/<name>.yaml``. The
TUI lists both, with project presets taking precedence on name
collisions.

Schema (one YAML per preset):

    name: pomodoro
    title: Build a Pomodoro timer app
    description: |
      Standard 25-min focus / 5-min break cycle with daily review
      and persistent settings. The directive analyses 029-032 used
      to validate the substrate convergence + tdd-serial workflow.
    body: |
      Build a Pomodoro timer app: focus sessions, configurable
      breaks, daily review, persistent settings.
    suggested_workflow: tdd-serial   # optional; UI pre-selects
    suggested_skeleton: fullstack-fastapi-react  # optional
    tags: [greenfield, feature-rich]

The body is what gets fed to the runner verbatim. title + description
are display-only — they help users browse the preset list and
remember what a directive asked for. Suggested workflow/skeleton are
hints the UI may pre-select but never lock; the user can always
override.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class DirectivePreset(BaseModel):
    """A reusable directive saved as data on disk."""

    name: str = Field(
        description=(
            "Slug-shaped identifier used for the YAML filename. "
            "Should be unique within its scope (bundled or per-project)."
        ),
    )
    title: str = Field(
        description=(
            "Human-readable label shown in the preset picker. "
            "Should be short (one line, ~50 chars)."
        ),
    )
    description: str = Field(
        default="",
        description=(
            "Paragraph explaining what this directive asks for. "
            "Shown as a hover/preview when the user picks the preset."
        ),
    )
    body: str = Field(
        description=(
            "The actual directive text fed to the runner verbatim. "
            "Multi-line is fine; trailing whitespace is stripped on "
            "save."
        ),
    )
    suggested_workflow: str | None = Field(
        default=None,
        description=(
            "Workflow name (e.g. 'tdd-serial') the UI may pre-select. "
            "Always overridable."
        ),
    )
    suggested_skeleton: str | None = Field(
        default=None,
        description=(
            "Skeleton name (e.g. 'fullstack-fastapi-react') the UI "
            "may pre-select for new-project flows. Always overridable."
        ),
    )
    tags: list[str] = Field(
        default_factory=list,
        description=(
            "Free-form tags for filtering / grouping the preset list. "
            "e.g. ['greenfield', 'feature-rich']."
        ),
    )
    category: str | None = Field(
        default=None,
        description=(
            "Higher-level grouping shown in the preset picker as a "
            "dropdown header. Free-form string; normalized to lower "
            "case via ``normalized_category`` before comparison so "
            "'Demo', 'demo', 'DEMO' all collapse. Examples: "
            "'demo' (showcase directives for kicking off projects), "
            "'utility' (project-underway housekeeping), 'workflow' "
            "(directives written for a specific workflow). ``None`` "
            "means uncategorized — they sort at the bottom under "
            "an 'Other' header."
        ),
    )

    @property
    def normalized_category(self) -> str:
        """Case-insensitive category for grouping. Empty / None
        normalises to ``"other"`` so uncategorized presets cluster
        at the bottom of the picker under a single bucket."""
        if self.category is None:
            return "other"
        stripped = self.category.strip().lower()
        return stripped or "other"


def directives_dir() -> Path:
    """Directory holding the bundled directive YAML files."""
    import wonderland

    return Path(wonderland.__file__).parent / "closet" / "directives"


def project_directives_dir(project_root: Path) -> Path:
    """Per-project directive directory inside ``.wonderland/``.
    Doesn't have to exist; ``list_project_directives`` returns []
    when missing.
    """
    return project_root / ".wonderland" / "directives"


def list_directives() -> list[str]:
    """Names of bundled directive presets (without ``.yaml``).
    Sorted alphabetically for stable display.
    """
    d = directives_dir()
    if not d.is_dir():
        return []
    return sorted(p.stem for p in d.glob("*.yaml"))


def list_project_directives(project_root: Path) -> list[str]:
    """Names of per-project directive presets.

    Returns [] if ``project_root/.wonderland/directives/`` doesn't
    exist, which is the default state for fresh projects.
    """
    d = project_directives_dir(project_root)
    if not d.is_dir():
        return []
    return sorted(p.stem for p in d.glob("*.yaml"))


def load_directive(name_or_path: str | Path) -> DirectivePreset:
    """Load a preset by name (bundled) or path (project-local).

    - ``load_directive("pomodoro")`` → bundled preset.
    - ``load_directive(Path("/abs/path/to/foo.yaml"))`` → from path.

    Raises ``FileNotFoundError`` with the available bundled names
    on miss.
    """
    if isinstance(name_or_path, Path):
        path = name_or_path
    elif "/" in name_or_path or name_or_path.endswith(".yaml"):
        path = Path(name_or_path)
    else:
        path = directives_dir() / f"{name_or_path}.yaml"

    if not path.is_file():
        available = list_directives()
        raise FileNotFoundError(
            f"directive preset not found: {path}. Bundled: {available}"
        )
    with path.open() as f:
        data = yaml.safe_load(f)
    return DirectivePreset.model_validate(data)


def load_project_directive(name: str, project_root: Path) -> DirectivePreset:
    """Load a per-project preset by name. Same shape as
    ``load_directive`` but scoped to ``project_root/.wonderland/
    directives/``."""
    path = project_directives_dir(project_root) / f"{name}.yaml"
    if not path.is_file():
        available = list_project_directives(project_root)
        raise FileNotFoundError(
            f"project directive preset not found: {path}. "
            f"Available: {available}"
        )
    with path.open() as f:
        data = yaml.safe_load(f)
    return DirectivePreset.model_validate(data)


def save_directive(
    preset: DirectivePreset,
    project_root: Path,
) -> Path:
    """Persist a preset to ``project_root/.wonderland/directives/
    <preset.name>.yaml``. Creates the directory if missing. Returns
    the written path. Used by the TUI's save-as-preset feature.
    """
    d = project_directives_dir(project_root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{preset.name}.yaml"
    # model_dump preserves field order from the model definition,
    # which gives a stable, human-readable serialization.
    data = preset.model_dump(exclude_none=True)
    # Strip trailing whitespace from body for cleaner storage.
    if "body" in data:
        data["body"] = data["body"].rstrip() + "\n"
    with path.open("w") as f:
        yaml.safe_dump(
            data,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )
    return path


__all__ = [
    "DirectivePreset",
    "directives_dir",
    "list_directives",
    "list_project_directives",
    "load_directive",
    "load_project_directive",
    "project_directives_dir",
    "save_directive",
]
