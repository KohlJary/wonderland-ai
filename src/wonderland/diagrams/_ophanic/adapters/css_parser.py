"""CSS layout parser for extracting flex/grid structure."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from ..models import Direction, Proportion


@dataclass
class CSSRule:
    """A CSS rule with selector and properties."""

    selector: str
    properties: dict[str, str] = field(default_factory=dict)


@dataclass
class LayoutInfo:
    """Extracted layout information from CSS."""

    direction: Direction | None = None
    width: str | None = None  # Could be %, px, fr, etc.
    height: str | None = None
    grid_columns: list[str] | None = None
    grid_rows: list[str] | None = None
    gap: str | None = None
    is_flex: bool = False
    is_grid: bool = False
    order: int | None = None
    flex_grow: float | None = None
    flex_shrink: float | None = None
    flex_basis: str | None = None


def parse_css_file(path: str | Path) -> dict[str, CSSRule]:
    """Parse a CSS file into rules by selector.

    Returns dict mapping selector → CSSRule.
    """
    path = Path(path)
    if not path.exists():
        return {}

    text = path.read_text(encoding="utf-8")
    return parse_css(text)


def parse_css(text: str) -> dict[str, CSSRule]:
    """Parse CSS text into rules.

    Handles:
    - Regular rules: .class { ... }
    - Media queries: @media (...) { .class { ... } }
    - Nested selectors (basic support)
    """
    rules: dict[str, CSSRule] = {}

    # Remove comments
    text = re.sub(r"/\*[\s\S]*?\*/", "", text)

    # Parse rules (simplified - doesn't handle all edge cases)
    rule_pattern = re.compile(
        r"([^{@]+?)\s*\{([^{}]*)\}",
        re.MULTILINE,
    )

    # First pass: top-level rules
    for match in rule_pattern.finditer(text):
        selector = match.group(1).strip()
        props_text = match.group(2)

        # Skip if this looks like a media query inner
        if selector.startswith("@"):
            continue

        props = _parse_properties(props_text)
        if props:
            rules[selector] = CSSRule(selector=selector, properties=props)

    # Second pass: media query rules (extract with breakpoint prefix)
    media_pattern = re.compile(
        r"@media\s*([^{]+)\s*\{([\s\S]*?)\n\}",
        re.MULTILINE,
    )

    for media_match in media_pattern.finditer(text):
        media_query = media_match.group(1).strip()
        media_body = media_match.group(2)

        # Extract breakpoint from media query
        breakpoint = _extract_breakpoint(media_query)

        # Parse rules inside media query
        for rule_match in rule_pattern.finditer(media_body):
            selector = rule_match.group(1).strip()
            props_text = rule_match.group(2)
            props = _parse_properties(props_text)

            if props:
                # Key includes breakpoint info
                key = f"{selector}@{breakpoint}" if breakpoint else selector
                rules[key] = CSSRule(selector=selector, properties=props)

    return rules


def _parse_properties(text: str) -> dict[str, str]:
    """Parse CSS properties from rule body."""
    props = {}
    for line in text.split(";"):
        line = line.strip()
        if ":" in line:
            key, value = line.split(":", 1)
            props[key.strip()] = value.strip()
    return props


def _extract_breakpoint(media_query: str) -> str | None:
    """Extract a breakpoint identifier from a media query."""
    # Look for max-width or min-width
    match = re.search(r"(max|min)-width:\s*(\d+)px", media_query)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    return None


def extract_layout_info(rule: CSSRule) -> LayoutInfo:
    """Extract layout information from a CSS rule."""
    props = rule.properties
    info = LayoutInfo()

    # Display type
    display = props.get("display", "")
    info.is_flex = "flex" in display
    info.is_grid = "grid" in display

    # Flex direction
    flex_dir = props.get("flex-direction", "")
    if flex_dir == "column" or flex_dir == "column-reverse":
        info.direction = Direction.COLUMN
    elif info.is_flex:
        info.direction = Direction.ROW

    # Grid direction (infer from template)
    if info.is_grid:
        cols = props.get("grid-template-columns", "")
        rows = props.get("grid-template-rows", "")
        if cols:
            info.grid_columns = _parse_grid_template(cols)
            info.direction = Direction.ROW  # Primary axis is columns
        if rows:
            info.grid_rows = _parse_grid_template(rows)

    # Dimensions
    info.width = props.get("width")
    info.height = props.get("height")

    # Gap
    info.gap = props.get("gap") or props.get("grid-gap")

    # Flex properties
    if "flex-grow" in props:
        try:
            info.flex_grow = float(props["flex-grow"])
        except ValueError:
            pass

    if "flex-shrink" in props:
        try:
            info.flex_shrink = float(props["flex-shrink"])
        except ValueError:
            pass

    info.flex_basis = props.get("flex-basis")

    # Order
    if "order" in props:
        try:
            info.order = int(props["order"])
        except ValueError:
            pass

    return info


def _parse_grid_template(template: str) -> list[str]:
    """Parse grid-template-columns/rows into list of track sizes."""
    # Handle repeat()
    template = re.sub(
        r"repeat\((\d+),\s*([^)]+)\)",
        lambda m: " ".join([m.group(2)] * int(m.group(1))),
        template,
    )

    # Split on whitespace
    parts = template.split()
    return [p for p in parts if p]


def css_dimension_to_proportion(dim: str, total: float = 100) -> Proportion | None:
    """Convert a CSS dimension to a Proportion.

    Handles:
    - Percentages: 25% → 0.25
    - Pixels: 200px → approximate based on total
    - fr units: 1fr, 2fr → proportional
    """
    if not dim:
        return None

    dim = dim.strip()

    # Percentage
    if dim.endswith("%"):
        try:
            pct = float(dim[:-1])
            return Proportion(value=pct / 100, char_count=int(pct))
        except ValueError:
            pass

    # Pixels (approximate)
    if dim.endswith("px"):
        try:
            px = float(dim[:-2])
            # Assume total is in pixels, convert to ratio
            ratio = px / total if total > 0 else 0
            return Proportion(value=ratio, char_count=int(px))
        except ValueError:
            pass

    # fr units
    if dim.endswith("fr"):
        try:
            fr = float(dim[:-2])
            # fr is relative, we'll normalize later
            return Proportion(value=fr, char_count=int(fr * 10))
        except ValueError:
            pass

    return None


def normalize_fr_proportions(proportions: list[Proportion]) -> list[Proportion]:
    """Normalize fr-based proportions to sum to 1.0."""
    total = sum(p.value for p in proportions)
    if total <= 0:
        return proportions

    return [
        Proportion(value=p.value / total, char_count=p.char_count)
        for p in proportions
    ]
