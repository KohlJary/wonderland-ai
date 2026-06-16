"""Reverse adapter: Parse React/JSX to Ophanic IR and diagrams."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from ..models import (
    Direction,
    LayoutNode,
    NodeType,
    OphanicDocument,
    BreakpointLayout,
    Proportion,
    BoundingBox,
)


@dataclass
class ReverseOptions:
    """Options for reverse parsing."""

    diagram_width: int = 80  # Total width for generated diagrams
    min_box_width: int = 24  # Minimum box width in characters
    collapse_empty: bool = True  # Collapse empty containers
    max_nesting_depth: int = 2  # Maximum nesting depth before flattening
    include_comments: bool = True


def parse_react(jsx_code: str, options: ReverseOptions | None = None) -> OphanicDocument:
    """Parse React/JSX code into an Ophanic document.

    Extracts layout structure from Tailwind classes and JSX hierarchy.

    Args:
        jsx_code: React/JSX source code
        options: Parsing options

    Returns:
        OphanicDocument with extracted layout
    """
    if options is None:
        options = ReverseOptions()

    parser = ReactParser(options)
    return parser.parse(jsx_code)


def generate_diagram(doc: OphanicDocument, options: ReverseOptions | None = None) -> str:
    """Generate .ophanic diagram text from a document.

    Args:
        doc: Ophanic document (can be from parser or reverse adapter)
        options: Generation options

    Returns:
        .ophanic file content with box-drawing diagrams
    """
    if options is None:
        options = ReverseOptions()

    generator = DiagramGenerator(options)
    return generator.generate(doc)


def react_to_ophanic(jsx_code: str, options: ReverseOptions | None = None) -> str:
    """Convert React/JSX code directly to .ophanic diagram format.

    Convenience function combining parse_react and generate_diagram.
    """
    if options is None:
        options = ReverseOptions()

    doc = parse_react(jsx_code, options)
    return generate_diagram(doc, options)


# =============================================================================
# React Parser
# =============================================================================


class ReactParser:
    """Parses React/JSX code into Ophanic IR."""

    # Patterns for extracting JSX structure
    COMPONENT_PATTERN = re.compile(
        r"function\s+(\w+)\s*\([^)]*\)\s*\{[\s\S]*?return\s*\(([\s\S]*?)\n\s*\);?\s*\}",
        re.MULTILINE,
    )

    ARROW_COMPONENT_PATTERN = re.compile(
        r"const\s+(\w+)\s*=\s*\([^)]*\)\s*=>\s*\{[\s\S]*?return\s*\(([\s\S]*?)\n\s*\);?\s*\}",
        re.MULTILINE,
    )

    # JSX element patterns
    JSX_ELEMENT_PATTERN = re.compile(
        r"<(\w+)([^>]*)(?:/>|>([\s\S]*?)</\1>)",
        re.MULTILINE,
    )

    # Tailwind class patterns
    FLEX_PATTERN = re.compile(r"\bflex\b")
    FLEX_COL_PATTERN = re.compile(r"\bflex-col\b")
    WIDTH_PATTERN = re.compile(r"\bw-\[(\d+)%\]")
    HEIGHT_PATTERN = re.compile(r"\bh-\[(\d+)%\]")
    GRID_PATTERN = re.compile(r"\bgrid\b")
    GRID_COLS_PATTERN = re.compile(r"\bgrid-cols-(\d+)\b")

    def __init__(self, options: ReverseOptions):
        self.options = options

    def parse(self, jsx_code: str) -> OphanicDocument:
        """Parse JSX code into an Ophanic document."""
        doc = OphanicDocument()

        # Find all component definitions
        components = self._find_components(jsx_code)

        for name, jsx_body in components:
            # Parse the JSX body into a layout tree
            root = self._parse_jsx_element(jsx_body)
            if root:
                # First component becomes main layout
                if not doc.breakpoints:
                    doc.title = name
                    doc.breakpoints.append(
                        BreakpointLayout(breakpoint="default", root=root)
                    )
                else:
                    # Additional components could be breakpoints or component defs
                    # For now, treat as additional breakpoints
                    doc.breakpoints.append(
                        BreakpointLayout(breakpoint=name.lower(), root=root)
                    )

        return doc

    def _find_components(self, jsx_code: str) -> list[tuple[str, str]]:
        """Find all React component definitions."""
        components = []

        # Function components
        for match in self.COMPONENT_PATTERN.finditer(jsx_code):
            name, body = match.groups()
            components.append((name, body))

        # Arrow function components
        for match in self.ARROW_COMPONENT_PATTERN.finditer(jsx_code):
            name, body = match.groups()
            components.append((name, body))

        return components

    def _parse_jsx_element(self, jsx: str) -> LayoutNode | None:
        """Parse a JSX element string into a LayoutNode."""
        jsx = jsx.strip()
        if not jsx:
            return None

        # Find the opening tag
        open_match = re.match(r"<(\w+)([^>]*?)(/?)>", jsx)
        if not open_match:
            # Might be text content
            text = jsx.strip()
            if text and not text.startswith("<"):
                return LayoutNode(type=NodeType.LABEL, name=self._clean_text(text[:50]))
            return None

        tag_name, attrs, self_closing = open_match.groups()
        attrs = attrs or ""

        # Check if it's a component reference (PascalCase)
        if tag_name[0].isupper() and tag_name not in ("React",):
            return LayoutNode(type=NodeType.COMPONENT_REF, name=tag_name)

        # Parse as container
        node = LayoutNode(type=NodeType.CONTAINER)

        # Extract direction from Tailwind classes
        class_match = re.search(r'className=["\']([^"\']*)["\']', attrs)
        if class_match:
            classes = class_match.group(1)
            node.direction = self._extract_direction(classes)

            # Extract width/height proportions
            width_match = self.WIDTH_PATTERN.search(classes)
            if width_match:
                pct = int(width_match.group(1))
                node.width_proportion = Proportion(value=pct / 100, char_count=pct)

            height_match = self.HEIGHT_PATTERN.search(classes)
            if height_match:
                pct = int(height_match.group(1))
                node.height_proportion = Proportion(value=pct / 100, char_count=pct)

        # Self-closing tag - no children
        if self_closing == "/":
            return node

        # Find matching closing tag (handle nested same-tags)
        children_jsx = self._extract_element_content(jsx, tag_name)

        # Parse children
        if children_jsx and children_jsx.strip():
            children = self._parse_children(children_jsx)
            node.children = children

            # If no explicit direction and has children, infer from context
            if node.direction is None and children:
                node.direction = Direction.ROW  # Default to row

        # Check if this is effectively a label (no layout children, just text)
        if not node.children:
            text = self._extract_text_content(children_jsx or "")
            if text:
                # Keep proportions when converting to label
                return LayoutNode(
                    type=NodeType.LABEL,
                    name=self._clean_text(text[:50]),
                    width_proportion=node.width_proportion,
                    height_proportion=node.height_proportion,
                )

        return node

    def _extract_element_content(self, jsx: str, tag_name: str) -> str | None:
        """Extract content between opening and closing tags, handling nesting."""
        # Find end of opening tag
        open_match = re.match(r"<" + tag_name + r"[^>]*>", jsx)
        if not open_match:
            return None

        start_pos = open_match.end()
        depth = 1
        pos = start_pos

        open_pattern = re.compile(r"<" + tag_name + r"(?:\s|>|/>)")
        close_pattern = re.compile(r"</" + tag_name + r"\s*>")

        while pos < len(jsx) and depth > 0:
            # Find next open or close tag
            open_m = open_pattern.search(jsx, pos)
            close_m = close_pattern.search(jsx, pos)

            if close_m is None:
                break

            if open_m and open_m.start() < close_m.start():
                # Check if self-closing
                tag_end = jsx.find(">", open_m.start())
                if tag_end != -1 and jsx[tag_end - 1] != "/":
                    depth += 1
                pos = tag_end + 1 if tag_end != -1 else open_m.end()
            else:
                depth -= 1
                if depth == 0:
                    return jsx[start_pos:close_m.start()]
                pos = close_m.end()

        return None

    def _clean_text(self, text: str) -> str:
        """Clean text content, removing JSX expressions and excess whitespace."""
        # Remove JSX expressions {foo}
        text = re.sub(r"\{[^}]*\}", "", text)
        # Remove HTML comments
        text = re.sub(r"", "", text)
        # Clean whitespace
        return " ".join(text.split())

    def _extract_direction(self, classes: str) -> Direction | None:
        """Extract flex direction from Tailwind classes."""
        if self.FLEX_COL_PATTERN.search(classes):
            return Direction.COLUMN
        if self.FLEX_PATTERN.search(classes):
            return Direction.ROW
        if self.GRID_PATTERN.search(classes):
            return Direction.ROW  # Treat grid as row for now
        return None

    def _parse_children(self, jsx: str) -> list[LayoutNode]:
        """Parse child JSX elements."""
        children = []

        # Find all top-level JSX elements
        depth = 0
        current_start = None
        i = 0

        while i < len(jsx):
            if jsx[i:i+1] == "<":
                if jsx[i:i+2] == "</":
                    # Closing tag
                    depth -= 1
                    if depth == 0 and current_start is not None:
                        # Find end of closing tag
                        end = jsx.find(">", i)
                        if end != -1:
                            element_jsx = jsx[current_start:end+1]
                            child = self._parse_jsx_element(element_jsx)
                            if child:
                                children.append(child)
                            current_start = None
                            i = end + 1
                            continue
                elif jsx[i:i+4] == "<!--":
                    # Comment, skip
                    end = jsx.find("-->", i)
                    if end != -1:
                        i = end + 3
                        continue
                else:
                    # Opening tag
                    if depth == 0:
                        current_start = i
                    depth += 1

                    # Check for self-closing
                    tag_end = jsx.find(">", i)
                    if tag_end != -1 and jsx[tag_end-1:tag_end] == "/":
                        depth -= 1
                        if depth == 0 and current_start is not None:
                            element_jsx = jsx[current_start:tag_end+1]
                            child = self._parse_jsx_element(element_jsx)
                            if child:
                                children.append(child)
                            current_start = None
                            i = tag_end + 1
                            continue
            i += 1

        return children

    def _extract_text_content(self, jsx: str) -> str:
        """Extract plain text content from JSX, ignoring tags."""
        # Remove all JSX tags
        text = re.sub(r"<[^>]+>", " ", jsx)
        # Clean up whitespace
        text = " ".join(text.split())
        return text.strip()


# =============================================================================
# Diagram Generator
# =============================================================================


class DiagramGenerator:
    """Generates .ophanic diagram text from Ophanic IR."""

    def __init__(self, options: ReverseOptions):
        self.options = options

    def generate(self, doc: OphanicDocument) -> str:
        """Generate complete .ophanic file content."""
        parts = []

        # Title
        if doc.title:
            parts.append(f"# {doc.title}")
            parts.append("")

        # Design tokens (if present)
        if doc.tokens:
            parts.append(doc.tokens.to_oph_section())

        # Breakpoints
        for bp in doc.breakpoints:
            parts.append(f"@{bp.breakpoint}")
            diagram = self._generate_box(bp.root, self.options.diagram_width - 2)
            parts.append(diagram)
            parts.append("")

        # Component definitions
        for comp in doc.components:
            parts.append(f"## ◆{comp.name}")
            parts.append("")
            for state_name, layout in comp.states.items():
                parts.append(f"@{state_name}")
                diagram = self._generate_box(layout, self.options.diagram_width - 2)
                parts.append(diagram)
                parts.append("")

        return "\n".join(parts)

    def _generate_box(self, node: LayoutNode, width: int, depth: int = 0) -> str:
        """Generate a box diagram for a layout node."""
        width = max(width, self.options.min_box_width)

        if node.type == NodeType.COMPONENT_REF:
            return self._draw_box(f"◆{node.name}", width)

        if node.type == NodeType.LABEL:
            label = node.name or ""
            # Collapse empty labels if option enabled
            if not label and self.options.collapse_empty:
                return ""
            return self._draw_box(label, width)

        # Container with children
        if not node.children:
            # Collapse empty containers if option enabled
            if self.options.collapse_empty:
                return ""
            return self._draw_box("", width)

        # Filter out empty children when collapse_empty is enabled
        children = node.children
        if self.options.collapse_empty:
            children = [c for c in children if not self._is_empty_node(c)]
            if not children:
                return ""

        # Flatten if we've hit max nesting depth
        if depth >= self.options.max_nesting_depth:
            # Summarize children as a simple label
            summary = self._summarize_children(children)
            return self._draw_box(summary, width)

        if node.direction == Direction.ROW:
            return self._generate_row(children, width, depth + 1)
        else:
            return self._generate_column(children, width, depth + 1)

    def _summarize_children(self, children: list[LayoutNode]) -> str:
        """Create a summary label for flattened children."""
        parts = []
        for child in children[:3]:  # Max 3 items in summary
            if child.type == NodeType.COMPONENT_REF:
                parts.append(f"◆{child.name}")
            elif child.type == NodeType.LABEL and child.name:
                parts.append(child.name)
            elif child.children:
                # Recursively summarize
                sub = self._summarize_children(child.children)
                if sub:
                    parts.append(sub)
        if len(children) > 3:
            parts.append("...")
        return " | ".join(parts) if parts else ""

    def _is_empty_node(self, node: LayoutNode) -> bool:
        """Check if a node is empty (no content, no meaningful children)."""
        if node.type == NodeType.COMPONENT_REF:
            return False  # Component refs are never empty
        if node.type == NodeType.LABEL:
            return not (node.name and node.name.strip())
        # Container - check children recursively
        if not node.children:
            return True
        return all(self._is_empty_node(c) for c in node.children)

    def _generate_row(self, children: list[LayoutNode], width: int, depth: int = 0) -> str:
        """Generate horizontally arranged boxes."""
        if not children:
            return self._draw_box("", width)

        # Calculate widths for each child
        # Account for: outer borders (2) + spaces between children (n-1)
        n = len(children)
        available = width - 2 - (n - 1)  # Inner space minus separators
        child_widths = self._distribute_widths(children, available)

        # Generate each child box
        child_boxes = []
        actual_widths = []
        for child, w in zip(children, child_widths):
            box = self._generate_box(child, w, depth)
            if not box:  # Skip empty boxes
                continue
            child_boxes.append(box.split("\n"))
            actual_widths.append(w)

        if not child_boxes:
            return self._draw_box("", width)

        # Combine boxes horizontally
        max_height = max(len(box) for box in child_boxes)

        # Pad boxes to same height
        for i, box in enumerate(child_boxes):
            w = actual_widths[i]
            while len(box) < max_height:
                box.append("│" + " " * (w - 2) + "│")

        # Merge horizontally
        lines = []
        inner_width = width - 2  # Space inside outer box borders
        for row in range(max_height):
            line_parts = [box[row] for box in child_boxes]
            line = " ".join(line_parts)
            # Pad line to fill inner width exactly
            if len(line) < inner_width:
                line = line + " " * (inner_width - len(line))
            lines.append(line)

        # Wrap in outer container
        return self._wrap_in_box(lines, width)

    def _generate_column(self, children: list[LayoutNode], width: int, depth: int = 0) -> str:
        """Generate vertically stacked boxes."""
        if not children:
            return self._draw_box("", width)

        inner_width = width - 4  # Account for padding

        # Generate each child
        child_lines = []
        for child in children:
            box = self._generate_box(child, inner_width, depth)
            if not box:  # Skip empty boxes
                continue
            for line in box.split("\n"):
                child_lines.append("│ " + line.ljust(inner_width) + " │")

        if not child_lines:
            return self._draw_box("", width)

        # Wrap in outer container
        return self._wrap_in_box_raw(child_lines, width)

    def _distribute_widths(self, children: list[LayoutNode], total_width: int) -> list[int]:
        """Distribute width among children based on proportions."""
        n = len(children)
        if n == 0:
            return []

        min_w = self.options.min_box_width

        # Check if we have enough space for all children at minimum width
        min_total = n * min_w
        if total_width < min_total:
            # Not enough space - give each child equal share, even if below minimum
            # This prevents broken boxes
            base = max(4, total_width // n)  # Minimum 4 chars for a box to render
            widths = [base] * n
            diff = total_width - sum(widths)
            if diff > 0:
                widths[-1] += diff
            return widths

        # Check if children have explicit proportions
        proportions = []
        for child in children:
            if child.width_proportion:
                proportions.append(child.width_proportion.value)
            else:
                proportions.append(None)

        # If all have proportions, use them
        if all(p is not None for p in proportions):
            total_prop = sum(p for p in proportions if p)
            widths = [
                max(min_w, int((p / total_prop) * total_width))
                for p in proportions
            ]
        else:
            # Equal distribution
            base_width = total_width // n
            widths = [max(min_w, base_width) for _ in children]

        # Adjust to match total
        diff = total_width - sum(widths)
        if diff > 0 and widths:
            widths[-1] += diff
        elif diff < 0 and widths:
            # Over budget - reduce largest boxes first
            while diff < 0:
                max_idx = widths.index(max(widths))
                if widths[max_idx] > min_w:
                    widths[max_idx] -= 1
                    diff += 1
                else:
                    break  # Can't reduce further

        return widths

    def _draw_box(self, content: str, width: int) -> str:
        """Draw a simple box with content."""
        width = max(width, len(content) + 4, self.options.min_box_width)
        inner_width = width - 2

        top = "┌" + "─" * inner_width + "┐"
        bottom = "└" + "─" * inner_width + "┘"

        # Truncate at word boundary if needed
        max_content_len = inner_width - 2
        if len(content) > max_content_len:
            content = self._truncate_at_word(content, max_content_len)
        content_line = "│ " + content.ljust(inner_width - 2) + " │"

        return f"{top}\n{content_line}\n{bottom}"

    def _truncate_at_word(self, text: str, max_len: int) -> str:
        """Truncate text at word boundary with ellipsis."""
        if len(text) <= max_len:
            return text
        # Leave room for "..."
        truncate_at = max_len - 3
        if truncate_at <= 0:
            return text[:max_len]
        # Find last space before truncate point
        last_space = text[:truncate_at].rfind(" ")
        if last_space > truncate_at // 2:
            return text[:last_space] + "..."
        # No good word boundary, just truncate
        return text[:truncate_at] + "..."

    def _wrap_in_box(self, content_lines: list[str], width: int) -> str:
        """Wrap content lines in an outer box."""
        inner_width = width - 2

        top = "┌" + "─" * inner_width + "┐"
        bottom = "└" + "─" * inner_width + "┘"

        wrapped = [top]
        for line in content_lines:
            line_len = len(line)
            if line_len < inner_width:
                # Pad line to fit
                padding = inner_width - line_len
                line = "│" + line + " " * padding + "│"
            elif line_len > inner_width:
                # Line is too wide - this shouldn't happen with proper width calculation
                # but if it does, just wrap it (don't truncate box characters)
                line = "│" + line[:inner_width] + "│"
            else:
                # Exact fit
                line = "│" + line + "│"
            wrapped.append(line)
        wrapped.append(bottom)

        return "\n".join(wrapped)

    def _wrap_in_box_raw(self, content_lines: list[str], width: int) -> str:
        """Wrap pre-formatted content lines in an outer box."""
        inner_width = width - 2

        top = "┌" + "─" * inner_width + "┐"
        bottom = "└" + "─" * inner_width + "┘"

        return "\n".join([top] + content_lines + [bottom])
