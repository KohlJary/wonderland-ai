"""Analyze React components with CSS Modules to generate Ophanic diagrams.

This module handles:
- React/TSX components with CSS Modules
- CSS Grid and Flexbox layouts
- Multiple breakpoints from media queries
- Component hierarchy
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..models import (
    Direction,
    LayoutNode,
    NodeType,
    OphanicDocument,
    BreakpointLayout,
    ComponentDefinition,
    Proportion,
)
from .css_parser import (
    parse_css_file,
    parse_css,
    extract_layout_info,
    CSSRule,
    LayoutInfo,
    css_dimension_to_proportion,
    normalize_fr_proportions,
)
from .react_reverse import DiagramGenerator, ReverseOptions


@dataclass
class ComponentAnalysis:
    """Analysis result for a React component."""

    name: str
    jsx_path: Path
    css_path: Path | None
    root_layout: LayoutNode | None = None
    breakpoints: dict[str, LayoutNode] = field(default_factory=dict)
    sub_components: list[str] = field(default_factory=list)


def analyze_component(
    jsx_path: str | Path,
    css_path: str | Path | None = None,
) -> ComponentAnalysis:
    """Analyze a React component and its CSS to extract layout structure.

    Args:
        jsx_path: Path to .tsx/.jsx file
        css_path: Path to .css file (auto-detected if not provided)

    Returns:
        ComponentAnalysis with layout information
    """
    jsx_path = Path(jsx_path)

    # Auto-detect CSS file
    if css_path is None:
        # Try same name with .css extension
        potential_css = jsx_path.with_suffix(".css")
        if potential_css.exists():
            css_path = potential_css
        else:
            # Try in same directory with component name
            potential_css = jsx_path.parent / f"{jsx_path.stem}.css"
            if potential_css.exists():
                css_path = potential_css
    else:
        css_path = Path(css_path)

    # Read JSX
    jsx_content = jsx_path.read_text(encoding="utf-8")

    # Parse CSS if available
    css_rules: dict[str, CSSRule] = {}
    if css_path and css_path.exists():
        css_rules = parse_css_file(css_path)

    # Extract component name
    name = _extract_component_name(jsx_content) or jsx_path.stem

    # Analyze JSX structure with CSS context
    analyzer = ComponentLayoutAnalyzer(jsx_content, css_rules)
    root = analyzer.analyze(component_name=name)

    # Extract breakpoint variants
    breakpoints = analyzer.extract_breakpoints()

    # Find sub-component references
    sub_components = analyzer.find_sub_components()

    return ComponentAnalysis(
        name=name,
        jsx_path=jsx_path,
        css_path=css_path,
        root_layout=root,
        breakpoints=breakpoints,
        sub_components=sub_components,
    )


def component_to_ophanic(
    jsx_path: str | Path,
    css_path: str | Path | None = None,
    options: ReverseOptions | None = None,
) -> str:
    """Convert a React component to Ophanic diagram format.

    Args:
        jsx_path: Path to .tsx/.jsx file
        css_path: Path to .css file (auto-detected if not provided)
        options: Diagram generation options

    Returns:
        .ophanic file content
    """
    if options is None:
        options = ReverseOptions()

    analysis = analyze_component(jsx_path, css_path)

    # Build document
    doc = OphanicDocument(title=analysis.name)

    # Default/desktop layout
    if analysis.root_layout:
        doc.breakpoints.append(
            BreakpointLayout(breakpoint="desktop", root=analysis.root_layout)
        )

    # Responsive breakpoints
    for bp_name, layout in analysis.breakpoints.items():
        doc.breakpoints.append(
            BreakpointLayout(breakpoint=bp_name, root=layout)
        )

    # Generate diagram
    generator = DiagramGenerator(options)
    return generator.generate(doc)


def _extract_component_name(jsx_content: str) -> str | None:
    """Extract the main component name from JSX content.

    Prioritizes:
    1. Exported function components
    2. Default export
    3. First function component
    """
    # Try exported function component first (most reliable)
    match = re.search(r"export\s+(?:default\s+)?function\s+(\w+)\s*\(", jsx_content)
    if match:
        return match.group(1)

    # Try arrow function with export
    match = re.search(r"export\s+(?:default\s+)?(?:const|let|var)\s+(\w+)\s*=", jsx_content)
    if match:
        return match.group(1)

    # Try default export reference
    match = re.search(r"export\s+default\s+(\w+)\s*;", jsx_content)
    if match:
        return match.group(1)

    # Fallback to first function component
    match = re.search(r"function\s+(\w+)\s*\(", jsx_content)
    if match:
        return match.group(1)

    return None


def _extract_return_jsx(content: str, return_start: int) -> str | None:
    """Extract JSX from a return statement by tracking parentheses depth.

    Args:
        content: The source code
        return_start: Position of the 'return' keyword

    Returns:
        The JSX content inside return (...), or None if not found
    """
    # Find the opening paren after 'return'
    pos = return_start + 6  # Skip 'return'
    while pos < len(content) and content[pos] in ' \t\n':
        pos += 1

    if pos >= len(content) or content[pos] != '(':
        return None

    # Track paren depth to find matching close
    start = pos + 1
    depth = 1
    pos = start

    while pos < len(content) and depth > 0:
        char = content[pos]
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        elif char == '"' or char == "'" or char == '`':
            # Skip string literals
            quote = char
            pos += 1
            while pos < len(content):
                if content[pos] == '\\':
                    pos += 2
                    continue
                if content[pos] == quote:
                    break
                if quote == '`' and content[pos] == '$' and pos + 1 < len(content) and content[pos + 1] == '{':
                    # Template literal interpolation - track braces
                    pos += 2
                    brace_depth = 1
                    while pos < len(content) and brace_depth > 0:
                        if content[pos] == '{':
                            brace_depth += 1
                        elif content[pos] == '}':
                            brace_depth -= 1
                        pos += 1
                    continue
                pos += 1
        pos += 1

    if depth == 0:
        # Found matching paren
        jsx = content[start:pos - 1].strip()
        return jsx

    return None


def _find_top_level_returns(content: str) -> list[int]:
    """Find return statements at brace depth 0 (not inside callbacks/nested functions).

    Returns list of positions of 'return' keywords at depth 0.
    """
    returns = []
    depth = 0
    i = 0

    while i < len(content):
        char = content[i]

        # Track brace depth
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
        # Skip string literals
        elif char in '"\'`':
            quote = char
            i += 1
            while i < len(content):
                if content[i] == '\\':
                    i += 2
                    continue
                if content[i] == quote:
                    break
                i += 1
        # Check for 'return' keyword at depth 0
        elif depth == 0 and content[i:i + 6] == 'return':
            # Make sure it's the keyword (not part of identifier)
            before = content[i - 1] if i > 0 else ' '
            after = content[i + 6] if i + 6 < len(content) else ' '
            if not before.isalnum() and before != '_' and not after.isalnum() and after != '_':
                returns.append(i)
                i += 6
                continue

        i += 1

    return returns


def _find_main_component_jsx(jsx_content: str, component_name: str | None) -> str | None:
    """Find the JSX return statement for the main component.

    For components with conditional returns (loading/error states),
    we want the LAST top-level return in the component (at brace depth 0),
    which is typically the main render.
    """
    if component_name:
        # Find the function body for the named component
        # Match: export function Name() { ... }
        func_pattern = rf"(?:export\s+(?:default\s+)?)?function\s+{component_name}\s*\([^)]*\)\s*\{{"
        func_match = re.search(func_pattern, jsx_content)

        if func_match:
            # Find the function body by tracking braces
            start = func_match.end()
            depth = 1
            pos = start

            while pos < len(jsx_content) and depth > 0:
                if jsx_content[pos] == "{":
                    depth += 1
                elif jsx_content[pos] == "}":
                    depth -= 1
                pos += 1

            func_body = jsx_content[start:pos - 1]

            # Find top-level return statements in the function body
            return_positions = _find_top_level_returns(func_body)

            if return_positions:
                # Use the LAST top-level return (main render, not loading/error states)
                last_return_pos = return_positions[-1]
                jsx = _extract_return_jsx(func_body, last_return_pos)
                if jsx:
                    return jsx

    # Fallback: find last return statement in entire file using simple regex
    return_positions = [m.start() for m in re.finditer(r'\breturn\s*\(', jsx_content)]

    if return_positions:
        last_return_pos = return_positions[-1]
        jsx = _extract_return_jsx(jsx_content, last_return_pos)
        if jsx:
            return jsx

    return None


class ComponentLayoutAnalyzer:
    """Analyzes a React component's layout structure."""

    # Patterns for className extraction
    CLASSNAME_PATTERN = re.compile(
        r'className\s*=\s*[{"\']([^}"\']+)[}"\']',
    )

    # Pattern for styles.xxx (CSS Modules)
    STYLES_PATTERN = re.compile(
        r"styles\.(\w+)",
    )

    # JSX element pattern
    JSX_OPEN_PATTERN = re.compile(
        r"<(\w+)([^>]*?)(/?)>",
    )

    def __init__(self, jsx_content: str, css_rules: dict[str, CSSRule]):
        self.jsx = jsx_content
        self.css_rules = css_rules
        self.class_to_layout: dict[str, LayoutInfo] = {}

        # Pre-compute layout info for each CSS class
        for selector, rule in css_rules.items():
            # Handle direct class selectors only (not descendant combinators)
            # Skip selectors with spaces, >, +, ~ (combinators)
            if selector.startswith(".") and not any(c in selector for c in " >+~"):
                # Extract class name, handling pseudo-classes
                class_name = selector[1:].split(":")[0].split("@")[0]
                self.class_to_layout[class_name] = extract_layout_info(rule)

    def analyze(self, component_name: str | None = None) -> LayoutNode | None:
        """Analyze the component and return the root layout node."""
        # Find the main component's JSX
        jsx_body = _find_main_component_jsx(self.jsx, component_name)

        if not jsx_body:
            # Fallback: find any return statement
            return_match = re.search(
                r"return\s*\(\s*([\s\S]*?)\n\s*\);",
                self.jsx,
                re.MULTILINE,
            )
            if return_match:
                jsx_body = return_match.group(1)

        if not jsx_body:
            return None

        return self._parse_jsx_element(jsx_body)

    def _parse_jsx_element(self, jsx: str) -> LayoutNode | None:
        """Parse a JSX element into a LayoutNode."""
        jsx = jsx.strip()
        if not jsx:
            return None

        # Find opening tag
        open_match = self.JSX_OPEN_PATTERN.match(jsx)
        if not open_match:
            # Might be text content
            text = jsx.strip()
            if text and not text.startswith("<") and not text.startswith("{"):
                clean = self._clean_text(text)
                if clean:
                    return LayoutNode(type=NodeType.LABEL, name=self._truncate_label(clean))
            return None

        tag_name, attrs, self_closing = open_match.groups()

        # Component reference (PascalCase)
        if tag_name[0].isupper() and tag_name not in ("React", "Fragment"):
            return LayoutNode(type=NodeType.COMPONENT_REF, name=tag_name)

        # Skip content-focused elements (they're not structural layout)
        content_tags = {"p", "span", "label", "h1", "h2", "h3", "h4", "h5", "h6", "a", "strong", "em", "code", "pre"}
        if tag_name.lower() in content_tags:
            # Extract just the text as a simple label
            content = self._extract_element_content(jsx, tag_name)
            if content:
                text = self._extract_text_content(content)
                if text:
                    return LayoutNode(type=NodeType.LABEL, name=self._truncate_label(text))
            return None

        # Create container node
        node = LayoutNode(type=NodeType.CONTAINER)

        # Extract layout info from CSS classes
        layout_info = self._get_layout_info(attrs)
        if layout_info:
            node.direction = layout_info.direction
            if layout_info.width:
                prop = css_dimension_to_proportion(layout_info.width)
                if prop:
                    node.width_proportion = prop
            if layout_info.height:
                prop = css_dimension_to_proportion(layout_info.height)
                if prop:
                    node.height_proportion = prop

        # Self-closing tag
        if self_closing == "/":
            return node

        # Extract children
        children_jsx = self._extract_element_content(jsx, tag_name)
        if children_jsx:
            children = self._parse_children(children_jsx)
            node.children = children

            # Infer direction if not set
            if node.direction is None and children:
                node.direction = Direction.ROW

            # Apply grid proportions to children if applicable
            if layout_info and layout_info.grid_columns and len(children) == len(layout_info.grid_columns):
                proportions = [
                    css_dimension_to_proportion(col)
                    for col in layout_info.grid_columns
                ]
                proportions = [p for p in proportions if p]
                if proportions:
                    proportions = normalize_fr_proportions(proportions)
                    for child, prop in zip(children, proportions):
                        child.width_proportion = prop

        # Convert to label if no layout children
        if not node.children:
            text = self._extract_text_content(children_jsx or "")
            if text:
                label = self._truncate_label(text)
                if label:
                    return LayoutNode(
                        type=NodeType.LABEL,
                        name=label,
                        width_proportion=node.width_proportion,
                        height_proportion=node.height_proportion,
                    )

        return node

    def _get_layout_info(self, attrs: str) -> LayoutInfo | None:
        """Extract layout info from element attributes."""
        # Look for className
        class_match = self.CLASSNAME_PATTERN.search(attrs)
        if not class_match:
            return None

        class_value = class_match.group(1)

        # Handle CSS Modules: styles.className or styles['className']
        styles_matches = self.STYLES_PATTERN.findall(class_value)
        if styles_matches:
            # Combine layout info from all matched classes
            combined = LayoutInfo()
            for class_name in styles_matches:
                if class_name in self.class_to_layout:
                    info = self.class_to_layout[class_name]
                    if info.is_flex or info.is_grid:
                        combined.is_flex = combined.is_flex or info.is_flex
                        combined.is_grid = combined.is_grid or info.is_grid
                        combined.direction = info.direction or combined.direction
                        combined.grid_columns = info.grid_columns or combined.grid_columns
                        combined.grid_rows = info.grid_rows or combined.grid_rows
                        combined.width = info.width or combined.width
                        combined.height = info.height or combined.height
            return combined

        # Handle regular class names (space-separated)
        class_names = class_value.split()
        for class_name in class_names:
            if class_name in self.class_to_layout:
                return self.class_to_layout[class_name]

        return None

    def _extract_element_content(self, jsx: str, tag_name: str) -> str | None:
        """Extract content between opening and closing tags."""
        open_pattern = re.compile(r"<" + tag_name + r"[^>]*>")
        open_match = open_pattern.match(jsx)
        if not open_match:
            return None

        start_pos = open_match.end()
        depth = 1
        pos = start_pos

        open_re = re.compile(r"<" + tag_name + r"(?:\s|>|/>)")
        close_re = re.compile(r"</" + tag_name + r"\s*>")

        while pos < len(jsx) and depth > 0:
            open_m = open_re.search(jsx, pos)
            close_m = close_re.search(jsx, pos)

            if close_m is None:
                break

            if open_m and open_m.start() < close_m.start():
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

    def _parse_children(self, jsx: str) -> list[LayoutNode]:
        """Parse top-level child elements from JSX.

        Uses a simpler approach: find top-level tags by matching opening tags
        with their corresponding closing tags at the same name-specific depth.
        """
        children = []
        i = 0

        while i < len(jsx):
            char = jsx[i]

            # Skip JSX comments {/* ... */}
            if jsx[i:i + 3] == "{/*":
                end = jsx.find("*/}", i)
                if end != -1:
                    i = end + 3
                    continue

            # Skip JSX expressions {...} - they're self-contained units
            if char == "{":
                brace_depth = 1
                i += 1
                while i < len(jsx) and brace_depth > 0:
                    if jsx[i] == "{":
                        brace_depth += 1
                    elif jsx[i] == "}":
                        brace_depth -= 1
                    elif jsx[i] in '"\'`':
                        quote = jsx[i]
                        i += 1
                        while i < len(jsx):
                            if jsx[i] == "\\":
                                i += 2
                                continue
                            if jsx[i] == quote:
                                break
                            i += 1
                    i += 1
                continue

            # Skip HTML comments
            if jsx[i:i + 4] == "<!--":
                end = jsx.find("-->", i)
                if end != -1:
                    i = end + 3
                    continue

            # Handle tags
            if char == "<" and i + 1 < len(jsx) and jsx[i + 1] not in "/!":
                # Opening tag - extract tag name
                tag_match = re.match(r"<(\w+)", jsx[i:])
                if tag_match:
                    tag_name = tag_match.group(1)
                    element_start = i

                    # Find the closing > of this opening tag
                    tag_end = jsx.find(">", i)
                    if tag_end == -1:
                        i += 1
                        continue

                    # Check if self-closing
                    if jsx[tag_end - 1] == "/":
                        # Self-closing element
                        element_jsx = jsx[element_start:tag_end + 1]
                        child = self._parse_jsx_element(element_jsx)
                        if child:
                            children.append(child)
                        i = tag_end + 1
                        continue

                    # Not self-closing - find matching close tag by tracking depth
                    depth = 1
                    pos = tag_end + 1
                    open_re = re.compile(r"<" + tag_name + r"(?:\s|>|/>)")
                    close_re = re.compile(r"</" + tag_name + r"\s*>")

                    while pos < len(jsx) and depth > 0:
                        # Find next opening or closing tag of same name
                        open_m = open_re.search(jsx, pos)
                        close_m = close_re.search(jsx, pos)

                        if close_m is None:
                            break

                        if open_m and open_m.start() < close_m.start():
                            # Found another opening tag
                            nested_end = jsx.find(">", open_m.start())
                            if nested_end != -1 and jsx[nested_end - 1] != "/":
                                depth += 1
                            pos = nested_end + 1 if nested_end != -1 else open_m.end()
                        else:
                            # Found closing tag
                            depth -= 1
                            if depth == 0:
                                element_end = close_m.end()
                                element_jsx = jsx[element_start:element_end]
                                child = self._parse_jsx_element(element_jsx)
                                if child:
                                    children.append(child)
                                i = element_end
                                break
                            pos = close_m.end()

                    if depth != 0:
                        i = tag_end + 1
                    continue

            i += 1

        return children

    def _extract_text_content(self, jsx: str) -> str:
        """Extract plain text from JSX, stripping all JSX expressions."""
        # First, strip all JSX expressions (handling nested braces)
        text = self._strip_jsx_expressions(jsx)
        # Remove all HTML/JSX tags (including attributes)
        text = re.sub(r"<[^>]+>", " ", text)
        # Remove common JS noise patterns that might leak through
        text = re.sub(r"\b(const|let|var|return|function|=>|\.map|\.filter)\b", "", text)
        # Remove HTML attribute fragments (e.g., .click, disabled, className=, etc.)
        text = re.sub(r"\.\w+", " ", text)  # .click, .target, etc.
        text = re.sub(r"\b(disabled|readonly|checked|selected|required|hidden|async|defer)\b", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(className|onClick|onChange|onSubmit|onKeyDown|href|src|alt|title|type|value|name|id|style|ref|key)\b", "", text, flags=re.IGNORECASE)
        text = re.sub(r"[()[\]{}=><|&!?:;,\"\']", " ", text)
        # Clean up whitespace
        text = " ".join(text.split())
        # Filter out short noise fragments and camelCase variables
        words = text.split()
        words = [w for w in words if len(w) > 1 or w.isalpha()]
        words = [w for w in words if not self._is_js_variable(w)]
        return " ".join(words)

    def _strip_jsx_expressions(self, text: str) -> str:
        """Strip JSX expressions {...} handling nested braces."""
        result = []
        i = 0
        while i < len(text):
            if text[i] == "{":
                # Skip the entire expression
                depth = 1
                i += 1
                while i < len(text) and depth > 0:
                    if text[i] == "{":
                        depth += 1
                    elif text[i] == "}":
                        depth -= 1
                    elif text[i] in '"\'`':
                        # Skip string literals
                        quote = text[i]
                        i += 1
                        while i < len(text):
                            if text[i] == "\\":
                                i += 2
                                continue
                            if text[i] == quote:
                                break
                            i += 1
                    i += 1
            else:
                result.append(text[i])
                i += 1
        return "".join(result)

    def _clean_text(self, text: str) -> str:
        """Clean text content for labels."""
        # Strip JSX expressions
        text = self._strip_jsx_expressions(text)
        # Remove JS noise
        text = re.sub(r"\b(const|let|var|return|function|=>)\b", "", text)
        text = re.sub(r"[()[\]{}=><|&!?:;,]", " ", text)
        text = " ".join(text.split())
        # Filter noise
        if any(kw in text.lower() for kw in ["target.value", "settimeout", "usestate", "useeffect"]):
            return ""
        # Filter camelCase variable names (e.g., fileInputRef, setSearchQuery)
        text = self._filter_camelcase_vars(text)
        return text

    def _filter_camelcase_vars(self, text: str) -> str:
        """Filter out camelCase identifiers that look like JS variable names."""
        words = text.split()
        filtered = []
        for word in words:
            # Skip if it looks like a camelCase variable name:
            # - starts with lowercase
            # - contains uppercase letters in the middle
            # - no spaces
            # - common patterns: xxxRef, setXxx, useXxx, handleXxx, onXxx
            if self._is_js_variable(word):
                continue
            filtered.append(word)
        return " ".join(filtered)

    def _is_js_variable(self, word: str) -> bool:
        """Check if a word looks like a JavaScript variable name."""
        if not word or len(word) < 2:
            return False
        # Must start with lowercase letter
        if not word[0].islower():
            return False
        # Common JS variable patterns
        js_patterns = [
            r"^(set|get|use|handle|on|is|has|can|should)[A-Z]",  # setFoo, useFoo, handleFoo
            r"Ref$",  # fooRef
            r"Id$",  # fooId
            r"State$",  # fooState
            r"Props$",  # fooProps
            r"Context$",  # fooContext
            r"Handler$",  # fooHandler
            r"Callback$",  # fooCallback
        ]
        for pattern in js_patterns:
            if re.search(pattern, word):
                return True
        # Generic camelCase with multiple humps (e.g., fileInputRef, searchQuery)
        # Count uppercase letters - if multiple humps, likely a variable
        uppercase_count = sum(1 for c in word if c.isupper())
        if uppercase_count >= 2:
            return True
        # Single hump camelCase that's long (likely variable, not a word)
        if uppercase_count == 1 and len(word) > 12:
            return True
        return False

    def _truncate_label(self, text: str, max_len: int = 30) -> str:
        """Truncate label at word boundary with ellipsis."""
        text = self._clean_text(text)
        if not text:
            return ""
        if len(text) <= max_len:
            return text
        # Find last space before max_len
        truncated = text[:max_len]
        last_space = truncated.rfind(" ")
        if last_space > max_len // 2:
            # Truncate at word boundary
            return truncated[:last_space] + "..."
        # No good word boundary, just truncate
        return truncated + "..."

    def extract_breakpoints(self) -> dict[str, LayoutNode]:
        """Extract layout variants for different breakpoints."""
        breakpoints: dict[str, LayoutNode] = {}

        # Find all breakpoint-specific rules
        for selector, rule in self.css_rules.items():
            if "@" in selector:
                # This is a breakpoint-specific rule
                bp_match = re.search(r"@(max|min)-(\d+)", selector)
                if bp_match:
                    bp_name = f"{bp_match.group(1)}-{bp_match.group(2)}"
                    # For now, we'd need to re-analyze with these rules applied
                    # This is a simplified version
                    pass

        return breakpoints

    def find_sub_components(self) -> list[str]:
        """Find references to other components."""
        components = set()
        for match in re.finditer(r"<([A-Z]\w+)", self.jsx):
            name = match.group(1)
            if name not in ("React", "Fragment"):
                components.add(name)
        return sorted(components)
