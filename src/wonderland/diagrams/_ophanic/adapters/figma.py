"""Figma adapter: Import Figma designs to Ophanic IR and diagrams.

This module handles:
- Figma REST API authentication and file fetching
- Converting Figma auto-layout frames to Ophanic IR
- Extracting proportions from FILL sizing and layoutGrow
- Component instance detection
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from ..models import (
    Direction,
    LayoutNode,
    NodeType,
    OphanicDocument,
    BreakpointLayout,
    Proportion,
    DesignTokens,
    ColorToken,
    TypographyToken,
    TableData,
    TableRow,
    TableCell,
)
from .react_reverse import DiagramGenerator, ReverseOptions


FIGMA_API_BASE = "https://api.figma.com/v1"
FIGMA_CACHE_DIR = Path.home() / ".cache" / "ophanic" / "figma"


@dataclass
class FigmaOptions:
    """Options for Figma import."""

    token: str | None = None  # Personal access token (or from FIGMA_TOKEN env)
    depth: int | None = None  # Limit traversal depth (None = full tree)
    node_ids: list[str] = field(default_factory=list)  # Specific nodes to fetch
    include_pages: list[str] = field(default_factory=list)  # Filter by page names
    diagram_width: int = 80
    use_cache: bool = True  # Use cached responses when available
    cache_ttl: int = 3600  # Cache TTL in seconds (default: 1 hour)


class FigmaAPIError(Exception):
    """Error from Figma API."""

    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(f"Figma API error ({status}): {message}")


class FigmaClient:
    """Client for Figma REST API with caching."""

    def __init__(self, token: str | None = None, use_cache: bool = True, cache_ttl: int = 3600):
        self.token = token or os.environ.get("FIGMA_TOKEN")
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl
        if not self.token:
            raise ValueError(
                "Figma token required. Set FIGMA_TOKEN env var or pass token parameter."
            )

    def get_file(
        self,
        file_key: str,
        depth: int | None = None,
        node_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Fetch a Figma file.

        Args:
            file_key: The file key from the Figma URL
            depth: Limit traversal depth (1=pages only, 2=pages+top-level, etc.)
            node_ids: Specific node IDs to fetch (comma-separated in API)

        Returns:
            Figma file JSON response
        """
        url = f"{FIGMA_API_BASE}/files/{file_key}"

        params = []
        if depth is not None:
            params.append(f"depth={depth}")
        if node_ids:
            params.append(f"ids={','.join(node_ids)}")

        if params:
            url += "?" + "&".join(params)

        # Check cache first
        cache_key = self._cache_key(file_key, depth, node_ids)
        if self.use_cache:
            cached = self._load_cache(cache_key)
            if cached:
                print(f"Using cached Figma data ({cache_key[:8]}...)")
                return cached

        # Fetch from API
        data = self._request(url)

        # Save to cache
        if self.use_cache:
            self._save_cache(cache_key, data)

        return data

    def _cache_key(self, file_key: str, depth: int | None, node_ids: list[str] | None) -> str:
        """Generate a cache key for this request."""
        parts = [file_key, str(depth or "full")]
        if node_ids:
            parts.extend(sorted(node_ids))
        key_str = ":".join(parts)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _cache_path(self, cache_key: str) -> Path:
        """Get the cache file path for a key."""
        return FIGMA_CACHE_DIR / f"{cache_key}.json"

    def _load_cache(self, cache_key: str) -> dict[str, Any] | None:
        """Load data from cache if valid."""
        import time

        cache_file = self._cache_path(cache_key)
        if not cache_file.exists():
            return None

        # Check TTL
        age = time.time() - cache_file.stat().st_mtime
        if age > self.cache_ttl:
            return None

        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            return None

    def _save_cache(self, cache_key: str, data: dict[str, Any]) -> None:
        """Save data to cache."""
        cache_file = self._cache_path(cache_key)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(data), encoding="utf-8")

    def get_node(self, file_key: str, node_id: str) -> dict[str, Any]:
        """Fetch a specific node from a Figma file.

        Args:
            file_key: The file key from the Figma URL
            node_id: The node ID to fetch

        Returns:
            Node data from the nodes endpoint
        """
        url = f"{FIGMA_API_BASE}/files/{file_key}/nodes?ids={node_id}"
        return self._request(url)

    def _request(self, url: str, retries: int = 3) -> dict[str, Any]:
        """Make an authenticated request to the Figma API with retry on rate limit."""
        import time

        req = Request(url)
        req.add_header("X-Figma-Token", self.token or "")

        last_error = None
        for attempt in range(retries):
            try:
                with urlopen(req, timeout=30) as response:
                    return json.loads(response.read().decode("utf-8"))
            except HTTPError as e:
                body = e.read().decode("utf-8") if e.fp else str(e)
                last_error = FigmaAPIError(e.code, body)

                # Retry on rate limit (429) with exponential backoff
                if e.code == 429 and attempt < retries - 1:
                    wait_time = (2 ** attempt) * 10  # 10s, 20s, 40s
                    print(f"Rate limited, waiting {wait_time}s... (attempt {attempt + 1}/{retries})")
                    time.sleep(wait_time)
                    continue

                raise last_error from e

        raise last_error  # type: ignore


def extract_file_key(url_or_key: str) -> str:
    """Extract file key from a Figma URL or return as-is if already a key.

    Handles URLs like:
    - https://www.figma.com/file/abc123XYZ/MyDesign
    - https://www.figma.com/design/abc123XYZ/MyDesign
    - abc123XYZ (already a key)
    """
    # Check if it's a URL
    match = re.search(r"figma\.com/(?:file|design)/([a-zA-Z0-9]+)", url_or_key)
    if match:
        return match.group(1)

    # Assume it's already a file key
    return url_or_key


def figma_to_ophanic(
    file_key_or_url: str,
    options: FigmaOptions | None = None,
) -> OphanicDocument:
    """Convert a Figma file to an Ophanic document.

    Args:
        file_key_or_url: Figma file key or URL
        options: Import options

    Returns:
        OphanicDocument with layout structure
    """
    if options is None:
        options = FigmaOptions()

    file_key = extract_file_key(file_key_or_url)
    client = FigmaClient(
        token=options.token,
        use_cache=options.use_cache,
        cache_ttl=options.cache_ttl,
    )

    # Fetch the file
    file_data = client.get_file(
        file_key,
        depth=options.depth,
        node_ids=options.node_ids if options.node_ids else None,
    )

    # Convert to Ophanic
    converter = FigmaConverter(options)
    return converter.convert(file_data)


def figma_to_diagram(
    file_key_or_url: str,
    options: FigmaOptions | None = None,
) -> str:
    """Convert a Figma file directly to an Ophanic diagram.

    Args:
        file_key_or_url: Figma file key or URL
        options: Import options

    Returns:
        .ophanic file content
    """
    if options is None:
        options = FigmaOptions()

    doc = figma_to_ophanic(file_key_or_url, options)

    # Use depth for diagram nesting limit (default to 4 for deeper structure)
    max_depth = options.depth if options.depth else 4
    reverse_options = ReverseOptions(
        diagram_width=options.diagram_width,
        max_nesting_depth=max_depth,
    )
    generator = DiagramGenerator(reverse_options)
    return generator.generate(doc)


class FigmaConverter:
    """Converts Figma file data to Ophanic IR."""

    # Node types that represent layout containers
    CONTAINER_TYPES = {"FRAME", "COMPONENT", "COMPONENT_SET", "SECTION", "GROUP"}

    # Node types to skip (non-layout elements)
    SKIP_TYPES = {"VECTOR", "BOOLEAN_OPERATION", "STAR", "LINE", "ELLIPSE", "POLYGON", "SLICE"}

    def __init__(self, options: FigmaOptions):
        self.options = options
        self.components: dict[str, dict] = {}  # componentId -> component node
        # Token extraction
        self._colors: dict[str, ColorToken] = {}  # hex -> ColorToken
        self._typography: dict[str, TypographyToken] = {}  # key -> TypographyToken
        self._color_counter = 0
        self._typo_counter = 0

    def convert(self, file_data: dict[str, Any]) -> OphanicDocument:
        """Convert Figma file data to OphanicDocument."""
        doc = OphanicDocument()
        doc.title = file_data.get("name", "Untitled")

        # Store component definitions for instance resolution
        if "components" in file_data:
            self.components = file_data["components"]

        # Process document
        document = file_data.get("document", {})
        pages = document.get("children", [])

        # Filter pages if specified
        if self.options.include_pages:
            pages = [
                p for p in pages
                if p.get("name") in self.options.include_pages
            ]

        # Process each page
        for page in pages:
            # Extract design tokens from this page
            self._extract_tokens(page)

            # Get top-level frames from the page
            for child in page.get("children", []):
                if child.get("type") in self.CONTAINER_TYPES:
                    layout = self._convert_node(child)
                    if layout:
                        # Use frame name as breakpoint identifier
                        bp_name = self._to_breakpoint_name(child.get("name", "default"))
                        doc.breakpoints.append(
                            BreakpointLayout(breakpoint=bp_name, root=layout)
                        )

        # Attach extracted tokens
        doc.tokens = self._build_tokens()

        return doc

    def _convert_node(self, node: dict[str, Any]) -> LayoutNode | None:
        """Convert a Figma node to a LayoutNode."""
        node_type = node.get("type", "")

        # Skip non-layout nodes
        if node_type in self.SKIP_TYPES:
            return None

        # Handle component instances - drill into their children for structure
        if node_type == "INSTANCE":
            component_id = node.get("componentId")
            component_name = self._get_component_name(component_id, node)

            # If instance has children, process them for actual content
            children = node.get("children", [])
            if children:
                # Treat instance like a container but with component name prefix
                container = self._convert_container(node)
                if container.children:
                    # Add component name as context
                    container.name = component_name
                    return container

            # No children - just reference the component
            return LayoutNode(
                type=NodeType.COMPONENT_REF,
                name=component_name,
            )

        # Handle text nodes as labels
        if node_type == "TEXT":
            characters = node.get("characters", "")
            if characters.strip():
                return LayoutNode(
                    type=NodeType.LABEL,
                    name=self._truncate(characters, 30),
                )
            return None

        # Handle rectangles and other shapes as simple containers
        if node_type == "RECTANGLE":
            name = node.get("name", "")
            if name and not name.startswith("Rectangle"):
                return LayoutNode(type=NodeType.LABEL, name=self._truncate(name, 30))
            return None

        # Handle containers (FRAME, COMPONENT, GROUP, etc.)
        if node_type in self.CONTAINER_TYPES:
            return self._convert_container(node)

        return None

    def _convert_container(self, node: dict[str, Any]) -> LayoutNode:
        """Convert a container node (FRAME, COMPONENT, etc.) to a LayoutNode."""
        layout_mode = node.get("layoutMode", "NONE")

        # Determine direction
        if layout_mode == "HORIZONTAL":
            direction = Direction.ROW
        elif layout_mode == "VERTICAL":
            direction = Direction.COLUMN
        else:
            # No auto-layout - try to infer from children positions
            direction = self._infer_direction(node)

        # Create container node
        container = LayoutNode(
            type=NodeType.CONTAINER,
            direction=direction,
        )

        # Process children
        children = node.get("children", [])
        if children:
            child_nodes = []
            for child in children:
                # Skip absolutely positioned children in auto-layout
                if child.get("layoutPositioning") == "ABSOLUTE":
                    continue

                child_node = self._convert_node(child)
                if child_node:
                    # Calculate proportion for FILL children
                    self._apply_proportions(child, child_node, direction)
                    child_nodes.append(child_node)

            container.children = child_nodes

            # Normalize FILL proportions among siblings
            self._normalize_fill_proportions(container)

        # If container has no children and has a meaningful name, make it a label
        if not container.children:
            name = node.get("name", "")
            if name and not self._is_generic_name(name):
                return LayoutNode(
                    type=NodeType.LABEL,
                    name=self._truncate(name, 30),
                )

        # Check if this container is actually a table
        table_node = self._detect_table(node, container)
        if table_node:
            return table_node

        return container

    def _apply_proportions(
        self,
        figma_node: dict[str, Any],
        layout_node: LayoutNode,
        parent_direction: Direction | None,
    ) -> None:
        """Apply width/height proportions based on Figma sizing."""
        h_sizing = figma_node.get("layoutSizingHorizontal", "FIXED")
        v_sizing = figma_node.get("layoutSizingVertical", "FIXED")
        layout_grow = figma_node.get("layoutGrow", 0)

        # For row layouts, horizontal sizing matters
        if parent_direction == Direction.ROW:
            if h_sizing == "FILL":
                # Use layoutGrow as relative weight (default to 1 if FILL but no grow)
                grow = layout_grow if layout_grow > 0 else 1
                layout_node.width_proportion = Proportion(
                    value=grow,  # Will be normalized later
                    char_count=int(grow),
                )
            elif h_sizing == "FIXED":
                # Could use absolute width, but for now just mark as fixed
                width = figma_node.get("absoluteBoundingBox", {}).get("width", 0)
                if width > 0:
                    layout_node.width_proportion = Proportion(
                        value=width,
                        char_count=int(width),
                    )

        # For column layouts, vertical sizing matters
        if parent_direction == Direction.COLUMN:
            if v_sizing == "FILL":
                grow = layout_grow if layout_grow > 0 else 1
                layout_node.height_proportion = Proportion(
                    value=grow,
                    char_count=int(grow),
                )

    def _normalize_fill_proportions(self, container: LayoutNode) -> None:
        """Normalize FILL proportions among siblings to sum to 1.0."""
        if not container.children:
            return

        if container.direction == Direction.ROW:
            # Normalize width proportions
            fill_children = [
                c for c in container.children
                if c.width_proportion is not None
            ]
            if fill_children:
                total = sum(c.width_proportion.value for c in fill_children if c.width_proportion)
                if total > 0:
                    for child in fill_children:
                        if child.width_proportion:
                            child.width_proportion = Proportion(
                                value=child.width_proportion.value / total,
                                char_count=int(child.width_proportion.value),
                            )

        elif container.direction == Direction.COLUMN:
            # Normalize height proportions
            fill_children = [
                c for c in container.children
                if c.height_proportion is not None
            ]
            if fill_children:
                total = sum(c.height_proportion.value for c in fill_children if c.height_proportion)
                if total > 0:
                    for child in fill_children:
                        if child.height_proportion:
                            child.height_proportion = Proportion(
                                value=child.height_proportion.value / total,
                                char_count=int(child.height_proportion.value),
                            )

    def _detect_table(
        self,
        node: dict[str, Any],
        container: LayoutNode,
    ) -> LayoutNode | None:
        """Detect if a container is a table and convert it.

        A container is considered a table if:
        - It's a column layout with multiple row children
        - Each row has similar structure (same number of children)
        - The name contains 'table', 'grid', or 'list'
        """
        name = node.get("name", "").lower()
        children = node.get("children", [])

        # Quick heuristic checks
        is_table_name = any(
            keyword in name
            for keyword in ("table", "grid", "list", "data", "schedule", "pricing")
        )

        # Must be a column layout with at least 2 rows
        if container.direction != Direction.COLUMN or len(children) < 2:
            if not is_table_name:
                return None

        # Check if children have consistent structure (same number of grandchildren)
        row_widths = []
        row_data: list[list[str]] = []

        for child in children:
            grandchildren = child.get("children", [])

            # Row must have children (cells)
            if not grandchildren:
                # Check if it's a single-cell row (text content)
                if child.get("type") == "TEXT":
                    row_data.append([child.get("characters", "").strip()])
                    row_widths.append(1)
                    continue
                # Skip rows with no content
                continue

            # Check for horizontal layout (row)
            row_layout = child.get("layoutMode", "")
            if row_layout != "HORIZONTAL" and not is_table_name:
                # Not a row layout and not explicitly named as table
                return None

            # Extract cell content
            cells = []
            for cell in grandchildren:
                cell_text = self._extract_cell_text(cell)
                cells.append(cell_text)

            row_data.append(cells)
            row_widths.append(len(cells))

        # Need at least 2 rows with consistent column count
        if len(row_data) < 2:
            return None

        # Check if column counts are consistent (allow some variance for merged cells)
        if row_widths:
            most_common_width = max(set(row_widths), key=row_widths.count)
            consistent_rows = sum(1 for w in row_widths if w == most_common_width)
            if consistent_rows < len(row_widths) * 0.6:  # At least 60% consistent
                if not is_table_name:
                    return None

        # Build table data
        table_data = TableData()

        # First row is header if it has different styling (we assume yes for now)
        for i, cells in enumerate(row_data):
            is_header = i == 0
            table_row = TableRow(is_header_row=is_header)
            for cell_text in cells:
                table_row.cells.append(TableCell(
                    content=cell_text,
                    is_header=is_header,
                ))
            table_data.rows.append(table_row)

        return LayoutNode(
            type=NodeType.TABLE,
            name=node.get("name", "Table"),
            table_data=table_data,
        )

    def _extract_cell_text(self, cell: dict[str, Any]) -> str:
        """Extract text content from a table cell node."""
        # If it's a text node, get characters directly
        if cell.get("type") == "TEXT":
            return cell.get("characters", "").strip()

        # If it's a container, look for text children
        for child in cell.get("children", []):
            if child.get("type") == "TEXT":
                return child.get("characters", "").strip()
            # Recurse one level
            for grandchild in child.get("children", []):
                if grandchild.get("type") == "TEXT":
                    return grandchild.get("characters", "").strip()

        # Fall back to node name
        name = cell.get("name", "")
        if name and not self._is_generic_name(name):
            return name

        return ""

    def _infer_direction(self, node: dict[str, Any]) -> Direction | None:
        """Infer layout direction from children positions when no auto-layout."""
        children = node.get("children", [])
        if len(children) < 2:
            return Direction.ROW  # Default

        # Get bounding boxes
        boxes = []
        for child in children[:4]:  # Check first few children
            bbox = child.get("absoluteBoundingBox")
            if bbox:
                boxes.append(bbox)

        if len(boxes) < 2:
            return Direction.ROW

        # Check if children are arranged horizontally or vertically
        # by comparing position variance
        x_positions = [b["x"] for b in boxes]
        y_positions = [b["y"] for b in boxes]

        x_variance = max(x_positions) - min(x_positions)
        y_variance = max(y_positions) - min(y_positions)

        # If more horizontal spread, it's a row; otherwise column
        if x_variance > y_variance:
            return Direction.ROW
        else:
            return Direction.COLUMN

    def _get_component_name(
        self,
        component_id: str | None,
        instance_node: dict[str, Any],
    ) -> str:
        """Get the name for a component instance."""
        # First try the instance's own name
        instance_name = instance_node.get("name", "")

        # Try to get from components map
        if component_id and component_id in self.components:
            comp = self.components[component_id]
            return comp.get("name", instance_name or "Component")

        # Fall back to instance name or generic
        return instance_name or "Component"

    def _to_breakpoint_name(self, name: str) -> str:
        """Convert a frame name to a breakpoint identifier."""
        # Common patterns
        name_lower = name.lower()

        if any(k in name_lower for k in ["mobile", "phone", "sm", "small"]):
            return "mobile"
        if any(k in name_lower for k in ["tablet", "md", "medium", "ipad"]):
            return "tablet"
        if any(k in name_lower for k in ["desktop", "lg", "large", "web"]):
            return "desktop"

        # Clean up the name for use as breakpoint
        clean = re.sub(r"[^a-zA-Z0-9]+", "-", name.lower()).strip("-")
        return clean or "default"

    def _is_generic_name(self, name: str) -> bool:
        """Check if a name is generic (auto-generated by Figma)."""
        generic_patterns = [
            r"^Frame\s*\d*$",
            r"^Group\s*\d*$",
            r"^Rectangle\s*\d*$",
            r"^Component\s*\d*$",
            r"^Instance\s*\d*$",
        ]
        return any(re.match(p, name) for p in generic_patterns)

    def _truncate(self, text: str, max_len: int) -> str:
        """Truncate text at word boundary."""
        text = " ".join(text.split())  # Normalize whitespace
        if len(text) <= max_len:
            return text
        truncate_at = max_len - 3
        last_space = text[:truncate_at].rfind(" ")
        if last_space > truncate_at // 2:
            return text[:last_space] + "..."
        return text[:truncate_at] + "..."

    # ========== Token Extraction ==========

    def _extract_tokens(self, node: dict[str, Any]) -> None:
        """Extract color and typography tokens from a node recursively."""
        # Extract colors from fills
        fills = node.get("fills", [])
        for fill in fills:
            if fill.get("type") == "SOLID" and fill.get("visible", True):
                self._extract_color(fill.get("color", {}), fill.get("opacity", 1.0))

        # Extract colors from strokes
        strokes = node.get("strokes", [])
        for stroke in strokes:
            if stroke.get("type") == "SOLID" and stroke.get("visible", True):
                self._extract_color(stroke.get("color", {}), stroke.get("opacity", 1.0))

        # Extract typography from TEXT nodes
        if node.get("type") == "TEXT":
            self._extract_typography(node)

        # Extract from background color
        bg = node.get("backgroundColor")
        if bg:
            self._extract_color(bg, bg.get("a", 1.0))

        # Recurse into children
        for child in node.get("children", []):
            self._extract_tokens(child)

    def _extract_color(self, color: dict[str, Any], opacity: float = 1.0) -> None:
        """Extract a color token from Figma color object."""
        if not color:
            return

        r = int(color.get("r", 0) * 255)
        g = int(color.get("g", 0) * 255)
        b = int(color.get("b", 0) * 255)
        a = color.get("a", 1.0) * opacity

        # Generate hex
        if a < 1.0:
            hex_color = f"#{r:02x}{g:02x}{b:02x}{int(a * 255):02x}"
        else:
            hex_color = f"#{r:02x}{g:02x}{b:02x}"

        # Skip if already seen
        hex_key = hex_color.lower()
        if hex_key in self._colors:
            return

        # Generate a name based on color characteristics
        name = self._generate_color_name(r, g, b, a)

        self._colors[hex_key] = ColorToken(
            name=name,
            hex=hex_color,
            rgba=(r, g, b, a),
        )

    def _generate_color_name(self, r: int, g: int, b: int, a: float) -> str:
        """Generate a semantic name for a color."""
        # Check for common colors
        if r == g == b:
            if r < 30:
                return "black" if "black" not in self._colors else f"gray-{self._color_counter}"
            if r > 225:
                return "white" if "white" not in self._colors else f"gray-light-{self._color_counter}"
            # Gray scale
            level = r // 25  # 0-10 scale
            name = f"gray-{level * 100}"
            if name in [c.name for c in self._colors.values()]:
                self._color_counter += 1
                name = f"gray-{self._color_counter}"
            return name

        # Determine dominant color
        max_channel = max(r, g, b)
        if r == max_channel and r > g + 30 and r > b + 30:
            base = "red"
        elif g == max_channel and g > r + 30 and g > b + 30:
            base = "green"
        elif b == max_channel and b > r + 30 and b > g + 30:
            base = "blue"
        elif r > 200 and g > 200 and b < 100:
            base = "yellow"
        elif r > 200 and g < 150 and b > 200:
            base = "purple"
        elif r < 100 and g > 200 and b > 200:
            base = "cyan"
        elif r > 200 and g > 100 and b < 100:
            base = "orange"
        else:
            self._color_counter += 1
            return f"color-{self._color_counter}"

        # Check if base name exists
        if base in [c.name for c in self._colors.values()]:
            self._color_counter += 1
            return f"{base}-{self._color_counter}"
        return base

    def _extract_typography(self, node: dict[str, Any]) -> None:
        """Extract typography token from a TEXT node."""
        style = node.get("style", {})
        if not style:
            return

        font_family = style.get("fontFamily", "Inter")
        font_size = style.get("fontSize", 16)
        font_weight = style.get("fontWeight", 400)
        line_height_px = style.get("lineHeightPx")
        letter_spacing = style.get("letterSpacing", 0)

        # Create a key for deduplication
        key = f"{font_family}-{font_size}-{font_weight}"
        if key in self._typography:
            return

        # Generate name based on size
        if font_size >= 32:
            name = "display"
        elif font_size >= 24:
            name = "heading"
        elif font_size >= 20:
            name = "title"
        elif font_size >= 16:
            name = "body"
        elif font_size >= 14:
            name = "label"
        else:
            name = "caption"

        # Make unique if needed
        if name in [t.name for t in self._typography.values()]:
            self._typo_counter += 1
            name = f"{name}-{self._typo_counter}"

        # Format line height
        line_height = None
        if line_height_px and font_size > 0:
            ratio = line_height_px / font_size
            line_height = f"{ratio:.2f}".rstrip("0").rstrip(".")

        # Format letter spacing
        letter_spacing_str = None
        if letter_spacing and letter_spacing != 0:
            letter_spacing_str = f"{letter_spacing / font_size:.3f}em"

        self._typography[key] = TypographyToken(
            name=name,
            font_family=font_family,
            font_size=f"{int(font_size)}px",
            font_weight=font_weight,
            line_height=line_height,
            letter_spacing=letter_spacing_str,
        )

    def _build_tokens(self) -> DesignTokens | None:
        """Build DesignTokens from extracted data."""
        if not self._colors and not self._typography:
            return None

        return DesignTokens(
            colors=list(self._colors.values()),
            typography=list(self._typography.values()),
        )
