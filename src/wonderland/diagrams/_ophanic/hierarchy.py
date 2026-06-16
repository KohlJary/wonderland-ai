"""Hierarchy building and direction inference for Ophanic."""

from __future__ import annotations

from .models import BoundingBox, Direction, LayoutNode, NodeType
from .box_detector import DetectedBox


def has_vertical_overlap(a: BoundingBox, b: BoundingBox) -> bool:
    """Check if two boxes share vertical space (overlap in rows)."""
    return not (a.bottom <= b.top or b.bottom <= a.top)


def has_horizontal_overlap(a: BoundingBox, b: BoundingBox) -> bool:
    """Check if two boxes share horizontal space (overlap in columns)."""
    return not (a.right <= b.left or b.right <= a.left)


def classify_content(content: str) -> tuple[NodeType, str | None]:
    """Determine the type and name from box content.

    Returns (type, name) where name is extracted label or component name.
    """
    stripped = content.strip()

    # Component reference: ◆ComponentName
    if "◆" in stripped:
        # Find the component name after ◆
        idx = stripped.index("◆")
        # Extract word after ◆
        rest = stripped[idx + 1 :]
        # Take first word (alphanumeric)
        name_chars = []
        for c in rest:
            if c.isalnum() or c == "_":
                name_chars.append(c)
            else:
                break
        if name_chars:
            return (NodeType.COMPONENT_REF, "".join(name_chars))

    # Empty content = container
    if not stripped:
        return (NodeType.CONTAINER, None)

    # Has meaningful text = label
    # Extract first significant word/phrase as name
    lines = stripped.split("\n")
    first_line = lines[0].strip() if lines else ""

    # Clean up the label (remove box chars, extra spaces)
    label = first_line.strip()
    if label:
        return (NodeType.LABEL, label)

    return (NodeType.CONTAINER, None)


def find_parent(
    box: DetectedBox,
    all_boxes: list[DetectedBox],
    box_to_node: dict[int, LayoutNode],
) -> DetectedBox | None:
    """Find the smallest box that fully contains this box."""
    candidates = []

    for other in all_boxes:
        if other is box:
            continue
        if id(other) not in box_to_node:
            continue
        if other.bounds.contains(box.bounds):
            candidates.append(other)

    if not candidates:
        return None

    # Return smallest containing box
    return min(candidates, key=lambda b: b.bounds.area)


def infer_direction(children: list[LayoutNode]) -> Direction:
    """Determine if children are arranged horizontally or vertically.

    - If ALL children share vertical space (same row range) = ROW
    - If any children are stacked vertically (no overlap) = COLUMN

    This handles mixed arrangements by defaulting to COLUMN when
    children span multiple visual "rows".
    """
    if len(children) < 2:
        return Direction.COLUMN  # Default for 0-1 children

    bounds = [c.source_bounds for c in children if c.source_bounds]
    if len(bounds) < 2:
        return Direction.COLUMN

    # Check if ALL pairs of children share vertical space
    # If any pair doesn't overlap, we have vertical stacking
    for i, a in enumerate(bounds):
        for b in bounds[i + 1 :]:
            if not has_vertical_overlap(a, b):
                return Direction.COLUMN

    # All children share vertical space = horizontal row
    return Direction.ROW


def sort_children(children: list[LayoutNode], direction: Direction) -> list[LayoutNode]:
    """Sort children by position based on direction.

    ROW: sort left-to-right by left edge
    COLUMN: sort top-to-bottom by top edge
    """
    if not children:
        return children

    if direction == Direction.ROW:
        return sorted(
            children,
            key=lambda c: c.source_bounds.left if c.source_bounds else 0,
        )
    else:
        return sorted(
            children,
            key=lambda c: c.source_bounds.top if c.source_bounds else 0,
        )


def build_hierarchy(boxes: list[DetectedBox]) -> LayoutNode | None:
    """Build a layout tree from detected boxes.

    Uses spatial containment to determine parent-child relationships.
    Boxes are processed largest-first (already sorted by detect_boxes).
    """
    if not boxes:
        return None

    box_to_node: dict[int, LayoutNode] = {}
    root: LayoutNode | None = None

    for box in boxes:
        # Classify content
        node_type, name = classify_content(box.content)

        # Create node
        node = LayoutNode(
            type=node_type,
            name=name,
            source_bounds=box.bounds,
        )
        box_to_node[id(box)] = node

        # Find parent
        parent_box = find_parent(box, boxes, box_to_node)

        if parent_box is None:
            # This is the root (or a new root if we find multiple top-level boxes)
            if root is None:
                root = node
            else:
                # Multiple top-level boxes - create implicit root container
                if root.type != NodeType.CONTAINER or root.source_bounds is not None:
                    # Wrap existing root
                    new_root = LayoutNode(type=NodeType.CONTAINER)
                    new_root.children.append(root)
                    root = new_root
                root.children.append(node)
        else:
            # Add as child of parent
            parent_node = box_to_node[id(parent_box)]
            parent_node.children.append(node)
            # Parent becomes a container if it has children
            if parent_node.type == NodeType.LABEL:
                parent_node.type = NodeType.CONTAINER

    # Now infer directions and sort children
    if root:
        _finalize_node(root)

    return root


def _finalize_node(node: LayoutNode) -> None:
    """Recursively set direction and sort children."""
    if not node.children:
        return

    # Nodes with children are always containers
    # (their content includes nested boxes which shouldn't be classified)
    node.type = NodeType.CONTAINER
    node.name = None  # Clear any name from nested content

    # Infer direction from child arrangement
    node.direction = infer_direction(node.children)

    # Sort children by position
    node.children = sort_children(node.children, node.direction)

    # Recurse
    for child in node.children:
        _finalize_node(child)
