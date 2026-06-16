"""Proportion calculation for Ophanic layouts."""

from __future__ import annotations

from .models import Direction, LayoutNode, Proportion


def calculate_proportions(node: LayoutNode) -> None:
    """Calculate width/height proportions for all children recursively.

    For ROW direction: calculate width proportions
    For COLUMN direction: calculate height proportions

    Proportions are stored as ratios (0.0-1.0).
    """
    if not node.children:
        return

    if node.direction == Direction.ROW:
        _calculate_width_proportions(node.children)
    elif node.direction == Direction.COLUMN:
        _calculate_height_proportions(node.children)

    # Recurse into children
    for child in node.children:
        calculate_proportions(child)


def _calculate_width_proportions(children: list[LayoutNode]) -> None:
    """Calculate width proportions for horizontally-arranged children."""
    # Get widths from bounds
    widths = []
    for child in children:
        if child.source_bounds:
            widths.append(child.source_bounds.width)
        else:
            widths.append(1)  # Default width if no bounds

    total = sum(widths)
    if total == 0:
        return

    for child, width in zip(children, widths):
        ratio = width / total
        child.width_proportion = Proportion(
            value=round(ratio, 4),
            char_count=width,
        )


def _calculate_height_proportions(children: list[LayoutNode]) -> None:
    """Calculate height proportions for vertically-arranged children."""
    # Get heights from bounds
    heights = []
    for child in children:
        if child.source_bounds:
            heights.append(child.source_bounds.height)
        else:
            heights.append(1)  # Default height if no bounds

    total = sum(heights)
    if total == 0:
        return

    for child, height in zip(children, heights):
        ratio = height / total
        child.height_proportion = Proportion(
            value=round(ratio, 4),
            char_count=height,
        )
