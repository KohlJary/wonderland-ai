"""IR data models for Ophanic parser."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Direction(str, Enum):
    """Layout direction for containers."""

    ROW = "row"
    COLUMN = "column"


class NodeType(str, Enum):
    """Type of layout node."""

    CONTAINER = "container"
    COMPONENT_REF = "component_ref"
    LABEL = "label"
    TABLE = "table"


@dataclass
class BoundingBox:
    """Character grid coordinates for a box."""

    top: int  # Line number (0-indexed)
    left: int  # Column number (0-indexed)
    bottom: int
    right: int

    @property
    def width(self) -> int:
        """Width in characters."""
        return self.right - self.left + 1

    @property
    def height(self) -> int:
        """Height in lines."""
        return self.bottom - self.top + 1

    @property
    def area(self) -> int:
        """Area in character cells."""
        return self.width * self.height

    def contains(self, other: BoundingBox) -> bool:
        """Check if this box fully contains another box."""
        return (
            self.top < other.top
            and self.left < other.left
            and self.bottom > other.bottom
            and self.right > other.right
        )

    def to_dict(self) -> dict[str, int]:
        return {
            "top": self.top,
            "left": self.left,
            "bottom": self.bottom,
            "right": self.right,
        }


@dataclass
class TableCell:
    """A cell in a table."""

    content: str
    is_header: bool = False
    colspan: int = 1
    rowspan: int = 1

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"content": self.content}
        if self.is_header:
            result["isHeader"] = True
        if self.colspan > 1:
            result["colspan"] = self.colspan
        if self.rowspan > 1:
            result["rowspan"] = self.rowspan
        return result


@dataclass
class TableRow:
    """A row in a table."""

    cells: list[TableCell] = field(default_factory=list)
    is_header_row: bool = False

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"cells": [c.to_dict() for c in self.cells]}
        if self.is_header_row:
            result["isHeaderRow"] = True
        return result


@dataclass
class TableData:
    """Table structure for data representation."""

    rows: list[TableRow] = field(default_factory=list)
    caption: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"rows": [r.to_dict() for r in self.rows]}
        if self.caption:
            result["caption"] = self.caption
        return result

    @property
    def headers(self) -> list[str]:
        """Get header row content."""
        if self.rows and self.rows[0].is_header_row:
            return [c.content for c in self.rows[0].cells]
        return []

    @property
    def data_rows(self) -> list[TableRow]:
        """Get non-header rows."""
        if self.rows and self.rows[0].is_header_row:
            return self.rows[1:]
        return self.rows


@dataclass
class Proportion:
    """Represents proportional sizing."""

    value: float  # e.g., 0.65 for 65%
    char_count: int  # Original character count (for debugging)

    def to_dict(self) -> dict[str, Any]:
        return {"value": self.value, "char_count": self.char_count}


@dataclass
class LayoutNode:
    """A node in the layout tree."""

    type: NodeType
    name: str | None = None  # Label text or component name
    direction: Direction | None = None  # For containers only
    width_proportion: Proportion | None = None
    height_proportion: Proportion | None = None
    children: list[LayoutNode] = field(default_factory=list)
    table_data: TableData | None = None  # For TABLE nodes
    source_bounds: BoundingBox | None = None  # For error messages/debugging

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"type": self.type.value}
        if self.name:
            result["name"] = self.name
        if self.direction:
            result["direction"] = self.direction.value
        if self.width_proportion:
            result["width"] = self.width_proportion.to_dict()
        if self.height_proportion:
            result["height"] = self.height_proportion.to_dict()
        if self.children:
            result["children"] = [c.to_dict() for c in self.children]
        if self.table_data:
            result["table"] = self.table_data.to_dict()
        return result


@dataclass
class BreakpointLayout:
    """Layout for a specific breakpoint."""

    breakpoint: str  # e.g., "desktop", "tablet", "mobile"
    root: LayoutNode

    def to_dict(self) -> dict[str, Any]:
        return {
            "breakpoint": self.breakpoint,
            "layout": self.root.to_dict(),
        }


@dataclass
class ComponentDefinition:
    """A reusable component with state variants."""

    name: str
    states: dict[str, LayoutNode] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "states": {k: v.to_dict() for k, v in self.states.items()},
        }


@dataclass
class ColorToken:
    """A color design token."""

    name: str
    hex: str  # #RRGGBB or #RRGGBBAA
    rgba: tuple[int, int, int, float] | None = None  # (r, g, b, a)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"name": self.name, "hex": self.hex}
        if self.rgba:
            result["rgba"] = self.rgba
        return result

    def to_css_var(self) -> str:
        """Output as CSS variable."""
        return f"--color-{self.name}: {self.hex};"

    def to_tailwind(self) -> tuple[str, str]:
        """Output as Tailwind config entry."""
        return (self.name, self.hex)


@dataclass
class TypographyToken:
    """A typography design token."""

    name: str
    font_family: str
    font_size: str  # e.g., "16px", "1rem"
    font_weight: int | str  # e.g., 400, "bold"
    line_height: str | None = None  # e.g., "1.5", "24px"
    letter_spacing: str | None = None  # e.g., "0.02em"

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "fontFamily": self.font_family,
            "fontSize": self.font_size,
            "fontWeight": self.font_weight,
        }
        if self.line_height:
            result["lineHeight"] = self.line_height
        if self.letter_spacing:
            result["letterSpacing"] = self.letter_spacing
        return result

    def to_oph_line(self) -> str:
        """Output as .oph token line."""
        parts = [self.font_family, self.font_size, str(self.font_weight)]
        if self.line_height:
            parts.append(self.line_height)
        return f"{self.name}: {' / '.join(parts)}"


@dataclass
class DesignTokens:
    """Collection of design tokens extracted from a design."""

    colors: list[ColorToken] = field(default_factory=list)
    typography: list[TypographyToken] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "colors": [c.to_dict() for c in self.colors],
            "typography": [t.to_dict() for t in self.typography],
        }

    def to_oph_section(self) -> str:
        """Output as @tokens section for .oph file."""
        lines = ["@tokens"]

        if self.colors:
            lines.append("# Colors")
            for color in self.colors:
                lines.append(f"{color.name}: {color.hex}")
            lines.append("")

        if self.typography:
            lines.append("# Typography")
            for typo in self.typography:
                lines.append(typo.to_oph_line())
            lines.append("")

        return "\n".join(lines)

    def to_css_vars(self) -> str:
        """Output as CSS custom properties."""
        lines = [":root {"]
        for color in self.colors:
            lines.append(f"  {color.to_css_var()}")
        for typo in self.typography:
            lines.append(f"  --font-{typo.name}-family: {typo.font_family};")
            lines.append(f"  --font-{typo.name}-size: {typo.font_size};")
            lines.append(f"  --font-{typo.name}-weight: {typo.font_weight};")
        lines.append("}")
        return "\n".join(lines)

    def to_tailwind_config(self) -> dict[str, Any]:
        """Output as Tailwind theme extension."""
        return {
            "colors": {c.name: c.hex for c in self.colors},
            "fontFamily": {
                t.name: [t.font_family] for t in self.typography
            },
            "fontSize": {
                t.name: t.font_size for t in self.typography
            },
        }


@dataclass
class OphanicDocument:
    """The complete parsed document."""

    title: str | None = None
    tokens: DesignTokens | None = None
    breakpoints: list[BreakpointLayout] = field(default_factory=list)
    components: list[ComponentDefinition] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "title": self.title,
            "breakpoints": [b.to_dict() for b in self.breakpoints],
            "components": [c.to_dict() for c in self.components],
        }
        if self.tokens:
            result["tokens"] = self.tokens.to_dict()
        return result

    def to_json(self, **kwargs: Any) -> str:
        import json

        return json.dumps(self.to_dict(), **kwargs)
