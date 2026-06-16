"""Main parser orchestration for Ophanic files."""

from __future__ import annotations

from pathlib import Path

from .models import (
    BreakpointLayout,
    ComponentDefinition,
    LayoutNode,
    NodeType,
    OphanicDocument,
    DesignTokens,
    ColorToken,
    TypographyToken,
    TableData,
    TableRow,
    TableCell,
)
from .lexer import segment_document, DiagramSection, TableSection
from .box_detector import detect_boxes
from .hierarchy import build_hierarchy
from .proportion import calculate_proportions


def parse_diagram(section: DiagramSection) -> LayoutNode | None:
    """Parse a single diagram section into a layout tree.

    This is the core parsing pipeline:
    1. Get lines from section
    2. Detect boxes
    3. Build hierarchy
    4. Calculate proportions
    """
    lines = section.get_content()
    if not lines:
        return None

    # Detect all boxes
    boxes = detect_boxes(lines)
    if not boxes:
        return None

    # Build hierarchy from spatial containment
    root = build_hierarchy(boxes)
    if root is None:
        return None

    # Calculate proportions
    calculate_proportions(root)

    return root


def parse_table(table_section: TableSection) -> LayoutNode | None:
    """Parse a table section into a LayoutNode with TableData.

    Args:
        table_section: The lexed table section

    Returns:
        LayoutNode of type TABLE with table_data populated
    """
    if not table_section.rows:
        return None

    table_data = TableData()

    # Check if table has a header (separator row after first row)
    has_header = table_section.has_header()
    separator_idx = 1 if has_header else -1

    for i, row_cells in enumerate(table_section.rows):
        # Skip separator row
        if i == separator_idx and table_section.is_separator_row(row_cells):
            continue

        # Determine if this is a header row
        is_header_row = has_header and i == 0

        table_row = TableRow(is_header_row=is_header_row)
        for cell_text in row_cells:
            table_row.cells.append(TableCell(
                content=cell_text,
                is_header=is_header_row,
            ))

        table_data.rows.append(table_row)

    if not table_data.rows:
        return None

    return LayoutNode(
        type=NodeType.TABLE,
        name=table_section.name,
        table_data=table_data,
    )


def parse_tokens(tokens_section) -> DesignTokens | None:
    """Parse tokens section into DesignTokens model."""
    if not tokens_section:
        return None

    colors = []
    for name, hex_value in tokens_section.colors.items():
        colors.append(ColorToken(name=name, hex=hex_value))

    typography = []
    for name, spec in tokens_section.typography.items():
        # Parse "FontFamily / size / weight [/ lineHeight]"
        parts = [p.strip() for p in spec.split("/")]
        if len(parts) >= 3:
            typography.append(TypographyToken(
                name=name,
                font_family=parts[0],
                font_size=parts[1],
                font_weight=parts[2],
                line_height=parts[3] if len(parts) > 3 else None,
            ))
        elif len(parts) == 1:
            # Simple format: just store as-is
            typography.append(TypographyToken(
                name=name,
                font_family=parts[0],
                font_size="16px",
                font_weight=400,
            ))

    if not colors and not typography:
        return None

    return DesignTokens(colors=colors, typography=typography)


def parse(text: str) -> OphanicDocument:
    """Parse Ophanic text into a document.

    Args:
        text: The raw text content of an .ophanic file

    Returns:
        OphanicDocument with breakpoints and component definitions
    """
    # Segment document into sections
    segments = segment_document(text)

    doc = OphanicDocument(title=segments.title)

    # Parse tokens if present
    if segments.tokens:
        doc.tokens = parse_tokens(segments.tokens)

    # Parse each breakpoint
    for bp_section in segments.breakpoints:
        for diagram in bp_section.diagrams:
            root = parse_diagram(diagram)
            if root:
                layout = BreakpointLayout(
                    breakpoint=bp_section.name,
                    root=root,
                )
                doc.breakpoints.append(layout)

    # Parse each component
    for comp_section in segments.components:
        component = ComponentDefinition(name=comp_section.name)

        for state in comp_section.states:
            root = parse_diagram(state)
            if root:
                component.states[state.tag] = root

        if component.states:
            doc.components.append(component)

    # Parse tables (as separate breakpoints with table layouts)
    for table_section in segments.tables:
        table_node = parse_table(table_section)
        if table_node:
            # Add table as a named breakpoint
            bp_name = table_section.name.lower().replace(" ", "-")
            doc.breakpoints.append(
                BreakpointLayout(breakpoint=bp_name, root=table_node)
            )

    return doc


def parse_file(path: str | Path) -> OphanicDocument:
    """Parse an Ophanic file from disk.

    Args:
        path: Path to .ophanic or .oph file

    Returns:
        OphanicDocument with breakpoints and component definitions

    Raises:
        FileNotFoundError: If file doesn't exist
        OphanicError: If parsing fails
    """
    path = Path(path)

    # Validate extension
    if path.suffix not in (".ophanic", ".oph"):
        # Allow it anyway, just warn conceptually
        pass

    text = path.read_text(encoding="utf-8")
    return parse(text)
