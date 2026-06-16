"""Box boundary detection for Ophanic diagrams."""

from __future__ import annotations

from dataclasses import dataclass

from .models import BoundingBox

# Character sets for box detection
TOP_LEFT_CORNERS = set("┌├")  # Can start a box
TOP_RIGHT_CORNERS = set("┐┬┤")  # Can end top edge
BOTTOM_LEFT_CORNERS = set("└├")  # Can end left edge
BOTTOM_RIGHT_CORNERS = set("┘┴┤")  # Can close a box
HORIZONTAL = set("─┬┴┼")
VERTICAL = set("│├┤┼")


@dataclass
class DetectedBox:
    """A detected box with its bounds and content."""

    bounds: BoundingBox
    content: str  # Text content inside the box (excluding borders)
    content_lines: list[str]  # Individual lines of content


def char_at(lines: list[str], row: int, col: int) -> str:
    """Safely get character at position, returning empty string if out of bounds."""
    if row < 0 or row >= len(lines):
        return ""
    line = lines[row]
    if col < 0 or col >= len(line):
        return ""
    return line[col]


def trace_horizontal_right(lines: list[str], row: int, start_col: int) -> int | None:
    """Follow horizontal edge right until we find a corner.

    Returns the column of the closing corner, or None if not found.
    """
    col = start_col + 1
    max_col = len(lines[row]) if row < len(lines) else 0

    while col < max_col:
        char = lines[row][col]
        if char in TOP_RIGHT_CORNERS:
            return col
        if char in HORIZONTAL or char in TOP_LEFT_CORNERS:
            col += 1
        else:
            # Not a valid box edge character
            break

    return None


def trace_vertical_down(lines: list[str], start_row: int, col: int) -> int | None:
    """Follow vertical edge down until we find a corner.

    Returns the row of the closing corner, or None if not found.
    """
    row = start_row + 1

    while row < len(lines):
        char = char_at(lines, row, col)
        if char in BOTTOM_LEFT_CORNERS:
            return row
        if char in VERTICAL:
            row += 1
        else:
            break

    return None


def verify_bottom_edge(lines: list[str], row: int, left_col: int, right_col: int) -> bool:
    """Verify that a valid bottom edge exists between corners."""
    for col in range(left_col + 1, right_col):
        char = char_at(lines, row, col)
        if char not in HORIZONTAL and char not in BOTTOM_LEFT_CORNERS:
            return False

    # Check bottom-right corner
    char = char_at(lines, row, right_col)
    return char in BOTTOM_RIGHT_CORNERS


def verify_right_edge(lines: list[str], top_row: int, bottom_row: int, col: int) -> bool:
    """Verify that a valid right edge exists between corners.

    Handles lines shorter than expected (e.g., due to emoji display width).
    Searches within a small tolerance window for the edge character.
    """
    tolerance = 3  # Characters of tolerance for emoji/unicode width

    for row in range(top_row + 1, bottom_row):
        if row >= len(lines):
            return False

        line = lines[row]
        found = False

        # Search in a window around the expected column
        for check_col in range(max(0, col - tolerance), min(len(line), col + tolerance + 1)):
            if check_col < len(line) and line[check_col] in VERTICAL:
                found = True
                break

        if not found:
            # Also check if line ends with edge char (for short lines)
            if line and line[-1] in VERTICAL:
                found = True

        if not found:
            return False

    return True


def extract_content(lines: list[str], bounds: BoundingBox) -> tuple[str, list[str]]:
    """Extract text content from inside a box (excluding borders)."""
    content_lines = []

    for row in range(bounds.top + 1, bounds.bottom):
        if row >= len(lines):
            content_lines.append("")
            continue

        line = lines[row]
        # Extract content between left and right borders
        start = bounds.left + 1
        end = bounds.right

        if start < len(line):
            # Find actual content bounds (skip border chars)
            content = line[start:end] if end <= len(line) else line[start:]
            # Strip the border character if present at start/end
            if content and content[0] in VERTICAL:
                content = content[1:]
            if content and content[-1] in VERTICAL:
                content = content[:-1]
            content_lines.append(content)
        else:
            content_lines.append("")

    # Join and strip for single content string
    full_content = "\n".join(content_lines).strip()

    return full_content, content_lines


def detect_boxes(lines: list[str]) -> list[DetectedBox]:
    """Detect all rectangular boxes in the diagram.

    Scans for top-left corners and traces edges to find complete boxes.
    Returns boxes sorted by area (largest first).
    """
    boxes: list[DetectedBox] = []

    for row, line in enumerate(lines):
        for col, char in enumerate(line):
            # Look for top-left corner
            if char != "┌":
                continue

            # Try to trace a complete box
            # 1. Trace right to find top-right corner
            right_col = trace_horizontal_right(lines, row, col)
            if right_col is None:
                continue

            # 2. Trace down from top-left to find bottom-left corner
            bottom_row = trace_vertical_down(lines, row, col)
            if bottom_row is None:
                continue

            # 3. Verify bottom edge exists
            if not verify_bottom_edge(lines, bottom_row, col, right_col):
                continue

            # 4. Verify right edge exists
            if not verify_right_edge(lines, row, bottom_row, right_col):
                continue

            # Valid box found!
            bounds = BoundingBox(
                top=row,
                left=col,
                bottom=bottom_row,
                right=right_col,
            )

            content, content_lines = extract_content(lines, bounds)

            boxes.append(
                DetectedBox(
                    bounds=bounds,
                    content=content,
                    content_lines=content_lines,
                )
            )

    # Sort by area (largest first) for hierarchy building
    boxes.sort(key=lambda b: b.bounds.area, reverse=True)

    return boxes
