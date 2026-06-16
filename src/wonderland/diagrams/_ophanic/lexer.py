"""Document segmentation for Ophanic files."""

from __future__ import annotations

from dataclasses import dataclass, field

# Box-drawing characters used in diagrams
BOX_CHARS = set("┌┐└┘─│├┤┬┴┼")


def has_box_chars(line: str) -> bool:
    """Check if a line contains box-drawing characters."""
    return any(c in BOX_CHARS for c in line)


@dataclass
class DiagramSection:
    """A section of diagram content."""

    tag: str  # e.g., "desktop", "default", "hover"
    lines: list[tuple[int, str]] = field(default_factory=list)  # (line_num, content)
    start_line: int = 0

    def add_line(self, line_num: int, content: str) -> None:
        if not self.lines:
            self.start_line = line_num
        self.lines.append((line_num, content))

    def get_content(self) -> list[str]:
        """Get just the line content without line numbers."""
        return [content for _, content in self.lines]


@dataclass
class BreakpointSection:
    """A top-level breakpoint section."""

    name: str  # e.g., "desktop", "tablet", "mobile"
    diagrams: list[DiagramSection] = field(default_factory=list)

    def add_diagram(self, tag: str) -> DiagramSection:
        diagram = DiagramSection(tag=tag)
        self.diagrams.append(diagram)
        return diagram


@dataclass
class ComponentSection:
    """A component definition section."""

    name: str  # e.g., "MetricCard", "ActivityFeed"
    states: list[DiagramSection] = field(default_factory=list)

    def add_state(self, tag: str) -> DiagramSection:
        state = DiagramSection(tag=tag)
        self.states.append(state)
        return state


@dataclass
class TableSection:
    """A table section with markdown-style rows."""

    name: str
    rows: list[list[str]] = field(default_factory=list)  # List of rows, each row is list of cells
    start_line: int = 0

    def has_header(self) -> bool:
        """Check if table has a separator row (indicating header)."""
        if len(self.rows) < 2:
            return False
        # Check if second row is a separator (all dashes)
        second_row = self.rows[1]
        return all(cell.strip().replace('-', '').replace(':', '') == '' for cell in second_row)

    def is_separator_row(self, row: list[str]) -> bool:
        """Check if a row is a markdown table separator."""
        return all(cell.strip().replace('-', '').replace(':', '') == '' for cell in row)


def is_table_row(line: str) -> bool:
    """Check if a line is a markdown-style table row."""
    stripped = line.strip()
    return stripped.startswith('|') and stripped.endswith('|') and stripped.count('|') >= 2


def parse_table_row(line: str) -> list[str]:
    """Parse a markdown table row into cells."""
    stripped = line.strip()
    # Remove leading/trailing pipes and split
    if stripped.startswith('|'):
        stripped = stripped[1:]
    if stripped.endswith('|'):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split('|')]


@dataclass
class TokensSection:
    """Design tokens section."""

    colors: dict[str, str] = field(default_factory=dict)  # name -> hex
    typography: dict[str, str] = field(default_factory=dict)  # name -> spec


@dataclass
class DocumentSegments:
    """Segmented document ready for parsing."""

    title: str | None = None
    tokens: TokensSection | None = None
    breakpoints: list[BreakpointSection] = field(default_factory=list)
    components: list[ComponentSection] = field(default_factory=list)
    tables: list[TableSection] = field(default_factory=list)
    _has_content: bool = field(default=False, repr=False)

    @property
    def has_content(self) -> bool:
        return self._has_content


def segment_document(text: str) -> DocumentSegments:
    """Split document into sections by markers.

    Markers:
    - `# Title` at start = document title
    - `@tokens` = design tokens section
    - `@breakpoint` = top-level breakpoint section
    - `## ◆ComponentName` = component definition
    - `@state` within component = state variant
    - `@table TableName` = table section
    - `# comment` = ignored (after content starts)
    """
    segments = DocumentSegments()
    lines = text.split("\n")

    current_breakpoint: BreakpointSection | None = None
    current_component: ComponentSection | None = None
    current_diagram: DiagramSection | None = None
    current_table: TableSection | None = None
    in_tokens_section = False
    current_token_type: str | None = None  # "colors" or "typography"

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Title detection (only at very start, before any content)
        if not segments._has_content and stripped.startswith("# ") and not stripped.startswith("## "):
            # Make sure it's not a comment after content
            potential_title = stripped[2:].strip()
            # Check if this looks like a title (no @, no box chars)
            if not potential_title.startswith("@") and not has_box_chars(potential_title):
                segments.title = potential_title
                continue

        # Component definition: ## ◆ComponentName
        if stripped.startswith("## ◆"):
            component_name = stripped[4:].strip()
            current_component = ComponentSection(name=component_name)
            segments.components.append(current_component)
            current_breakpoint = None  # Exit breakpoint context
            current_diagram = None
            current_table = None
            in_tokens_section = False
            segments._has_content = True
            continue

        # Tokens section: @tokens
        if stripped == "@tokens":
            in_tokens_section = True
            current_table = None
            segments.tokens = TokensSection()
            segments._has_content = True
            continue

        # Table section: @table TableName
        if stripped.startswith("@table "):
            table_name = stripped[7:].strip()
            current_table = TableSection(name=table_name, start_line=i)
            segments.tables.append(current_table)
            current_diagram = None  # Exit diagram context
            in_tokens_section = False
            segments._has_content = True
            continue

        # Breakpoint/state tag: @tag (but not @tokens or @table)
        if stripped.startswith("@"):
            tag = stripped[1:].split()[0]  # Handle @hover [transition: ...]
            segments._has_content = True
            in_tokens_section = False  # Exit tokens section
            current_table = None  # Exit table context

            if current_component is not None:
                # State within component
                current_diagram = current_component.add_state(tag)
            else:
                # Top-level breakpoint
                current_breakpoint = BreakpointSection(name=tag)
                segments.breakpoints.append(current_breakpoint)
                current_diagram = current_breakpoint.add_diagram(tag)
            continue

        # Token section parsing
        if in_tokens_section and segments.tokens:
            # Section headers within tokens
            if stripped.lower() == "# colors":
                current_token_type = "colors"
                continue
            elif stripped.lower() == "# typography":
                current_token_type = "typography"
                continue
            elif stripped.startswith("#"):
                continue  # Other comments in tokens section

            # Parse key: value lines
            if ":" in stripped:
                key, _, value = stripped.partition(":")
                key = key.strip()
                value = value.strip()
                if key and value:
                    if current_token_type == "colors" or value.startswith("#"):
                        segments.tokens.colors[key] = value
                    elif current_token_type == "typography" or "/" in value:
                        segments.tokens.typography[key] = value
                    elif not current_token_type:
                        # Guess based on value format
                        if value.startswith("#") or len(value) in (4, 7, 9):
                            segments.tokens.colors[key] = value
                        else:
                            segments.tokens.typography[key] = value
            continue

        # Table row parsing (within @table section)
        if current_table is not None:
            if is_table_row(line):
                row = parse_table_row(line)
                current_table.rows.append(row)
                segments._has_content = True
                continue
            # Non-table line ends table context (unless empty)
            if stripped:
                current_table = None

        # Comment line (after content has started)
        if stripped.startswith("#"):
            continue  # Skip comments

        # Empty line
        if not stripped:
            continue

        # Diagram content (lines with box chars or content within a diagram)
        if current_diagram is not None:
            if has_box_chars(line) or line.strip():
                current_diagram.add_line(i, line)
                segments._has_content = True

    return segments
