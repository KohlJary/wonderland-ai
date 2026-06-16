"""React/Tailwind adapter for Ophanic IR."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..models import (
    Direction,
    LayoutNode,
    NodeType,
    OphanicDocument,
    BreakpointLayout,
)


@dataclass
class ReactOptions:
    """Options for React code generation."""

    indent: int = 2
    component_style: Literal["function", "arrow"] = "function"
    include_imports: bool = True
    tailwind: bool = True
    breakpoint_strategy: Literal["separate", "responsive"] = "separate"


def generate_react(
    doc: OphanicDocument,
    options: ReactOptions | None = None,
) -> str:
    """Generate React/Tailwind code from an Ophanic document.

    Args:
        doc: Parsed Ophanic document
        options: Code generation options

    Returns:
        Generated React/JSX code as a string
    """
    if options is None:
        options = ReactOptions()

    generator = ReactGenerator(options)
    return generator.generate(doc)


class ReactGenerator:
    """Generates React code from Ophanic IR."""

    def __init__(self, options: ReactOptions):
        self.options = options
        self.indent_str = " " * options.indent

    def generate(self, doc: OphanicDocument) -> str:
        """Generate complete React code for the document."""
        parts: list[str] = []

        # Imports
        if self.options.include_imports:
            parts.append("import React from 'react';")
            parts.append("")

        # Main component (from first/primary breakpoint)
        if doc.breakpoints:
            main_bp = doc.breakpoints[0]
            component_name = self._to_component_name(doc.title or "Layout")
            parts.append(self._generate_component(component_name, main_bp))

        # Additional breakpoint components
        for bp in doc.breakpoints[1:]:
            bp_name = self._to_component_name(f"{doc.title or 'Layout'}_{bp.breakpoint}")
            parts.append("")
            parts.append(self._generate_component(bp_name, bp))

        # Component definitions
        for comp in doc.components:
            parts.append("")
            parts.append(self._generate_component_def(comp.name, comp.states.get("default")))

        # Export
        if doc.breakpoints:
            main_name = self._to_component_name(doc.title or "Layout")
            parts.append("")
            parts.append(f"export default {main_name};")

        return "\n".join(parts)

    def _generate_component(self, name: str, bp: BreakpointLayout) -> str:
        """Generate a React component from a breakpoint layout."""
        if self.options.component_style == "arrow":
            header = f"const {name} = () => {{"
        else:
            header = f"function {name}() {{"

        body = self._generate_jsx(bp.root, depth=1)

        return f"""{header}
{self.indent_str}return (
{body}
{self.indent_str});
}}"""

    def _generate_component_def(self, name: str, layout: LayoutNode | None) -> str:
        """Generate a component definition."""
        safe_name = self._to_component_name(name)

        if layout is None:
            # Empty placeholder
            return f"""function {safe_name}({{ ...props }}) {{
{self.indent_str}return <div {{...props}}>{name}</div>;
}}"""

        body = self._generate_jsx(layout, depth=1)

        return f"""function {safe_name}({{ ...props }}) {{
{self.indent_str}return (
{body}
{self.indent_str});
}}"""

    def _generate_jsx(self, node: LayoutNode, depth: int = 0) -> str:
        """Generate JSX for a layout node."""
        indent = self.indent_str * (depth + 1)

        if node.type == NodeType.COMPONENT_REF:
            return f"{indent}<{self._to_component_name(node.name or 'Unknown')} />"

        if node.type == NodeType.LABEL:
            # Simple label as a div
            content = self._escape_jsx(node.name or "")
            return f'{indent}<div className="p-4">{content}</div>'

        if node.type == NodeType.TABLE:
            return self._generate_table_jsx(node, depth)

        # Container
        classes = self._get_container_classes(node)
        class_str = f' className="{classes}"' if classes else ""

        if not node.children:
            return f"{indent}<div{class_str} />"

        children_jsx = "\n".join(
            self._generate_child_jsx(child, depth + 1, node.direction)
            for child in node.children
        )

        return f"{indent}<div{class_str}>\n{children_jsx}\n{indent}</div>"

    def _generate_child_jsx(
        self,
        node: LayoutNode,
        depth: int,
        parent_direction: Direction | None,
    ) -> str:
        """Generate JSX for a child node, including proportion styles."""
        indent = self.indent_str * (depth + 1)

        # Get proportion class
        proportion_class = self._get_proportion_class(node, parent_direction)

        if node.type == NodeType.COMPONENT_REF:
            safe_name = self._to_component_name(node.name or "Unknown")
            if proportion_class:
                return f'{indent}<div className="{proportion_class}"><{safe_name} /></div>'
            return f"{indent}<{safe_name} />"

        if node.type == NodeType.LABEL:
            content = self._escape_jsx(node.name or "")
            classes = f"p-4 {proportion_class}".strip()
            return f'{indent}<div className="{classes}">{content}</div>'

        # Container with children
        container_classes = self._get_container_classes(node)
        if proportion_class:
            container_classes = f"{proportion_class} {container_classes}".strip()

        class_str = f' className="{container_classes}"' if container_classes else ""

        if not node.children:
            return f"{indent}<div{class_str} />"

        children_jsx = "\n".join(
            self._generate_child_jsx(child, depth + 1, node.direction)
            for child in node.children
        )

        return f"{indent}<div{class_str}>\n{children_jsx}\n{indent}</div>"

    def _get_container_classes(self, node: LayoutNode) -> str:
        """Get Tailwind classes for a container node."""
        if not self.options.tailwind:
            return ""

        classes = ["flex"]

        if node.direction == Direction.COLUMN:
            classes.append("flex-col")

        return " ".join(classes)

    def _get_proportion_class(
        self,
        node: LayoutNode,
        parent_direction: Direction | None,
    ) -> str:
        """Get Tailwind proportion class for a node."""
        if not self.options.tailwind:
            return ""

        if parent_direction == Direction.ROW and node.width_proportion:
            pct = round(node.width_proportion.value * 100)
            return f"w-[{pct}%]"

        if parent_direction == Direction.COLUMN and node.height_proportion:
            pct = round(node.height_proportion.value * 100)
            return f"h-[{pct}%]"

        return ""

    def _to_component_name(self, name: str) -> str:
        """Convert a name to a valid React component name (PascalCase).

        Preserves existing PascalCase in the input (e.g., MetricCard stays MetricCard).
        """
        # If already PascalCase (starts with uppercase, no spaces), return as-is
        if name and name[0].isupper() and " " not in name and "_" not in name:
            # Just remove any non-alphanumeric chars
            cleaned = "".join(c for c in name if c.isalnum())
            if cleaned:
                return cleaned

        # Otherwise, convert to PascalCase
        words = "".join(c if c.isalnum() or c in " _" else " " for c in name).split()
        return "".join(word.capitalize() for word in words) or "Component"

    def _generate_table_jsx(self, node: LayoutNode, depth: int) -> str:
        """Generate JSX for a table node."""
        indent = self.indent_str * (depth + 1)
        inner_indent = self.indent_str * (depth + 2)
        cell_indent = self.indent_str * (depth + 3)

        if not node.table_data or not node.table_data.rows:
            return f"{indent}<table />"

        lines = [f'{indent}<table className="w-full border-collapse">']

        # Separate header and body rows
        header_rows = [r for r in node.table_data.rows if r.is_header_row]
        body_rows = [r for r in node.table_data.rows if not r.is_header_row]

        # Table head
        if header_rows:
            lines.append(f"{inner_indent}<thead>")
            for row in header_rows:
                lines.append(f"{cell_indent}<tr>")
                for cell in row.cells:
                    content = self._escape_jsx(cell.content)
                    classes = "border px-4 py-2 bg-gray-100 font-semibold text-left"
                    lines.append(f'{cell_indent}  <th className="{classes}">{content}</th>')
                lines.append(f"{cell_indent}</tr>")
            lines.append(f"{inner_indent}</thead>")

        # Table body
        if body_rows:
            lines.append(f"{inner_indent}<tbody>")
            for row in body_rows:
                lines.append(f"{cell_indent}<tr>")
                for cell in row.cells:
                    content = self._escape_jsx(cell.content)
                    classes = "border px-4 py-2"
                    lines.append(f'{cell_indent}  <td className="{classes}">{content}</td>')
                lines.append(f"{cell_indent}</tr>")
            lines.append(f"{inner_indent}</tbody>")

        lines.append(f"{indent}</table>")
        return "\n".join(lines)

    def _escape_jsx(self, text: str) -> str:
        """Escape text for JSX content."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("{", "&#123;")
            .replace("}", "&#125;")
        )
