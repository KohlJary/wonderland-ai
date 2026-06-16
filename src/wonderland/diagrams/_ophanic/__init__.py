"""Ophanic - Parse visual layout diagrams into structured IR."""

from .models import (
    Direction,
    NodeType,
    BoundingBox,
    Proportion,
    LayoutNode,
    BreakpointLayout,
    ComponentDefinition,
    OphanicDocument,
)
from .parser import parse, parse_file
from .errors import OphanicError, UnclosedBoxError, InvalidNestingError
from .adapters.react import generate_react, ReactOptions
from .adapters.react_reverse import (
    parse_react,
    generate_diagram,
    react_to_ophanic,
    ReverseOptions,
)

__version__ = "0.1.0"
__all__ = [
    # Models
    "Direction",
    "NodeType",
    "BoundingBox",
    "Proportion",
    "LayoutNode",
    "BreakpointLayout",
    "ComponentDefinition",
    "OphanicDocument",
    # Parser
    "parse",
    "parse_file",
    # Errors
    "OphanicError",
    "UnclosedBoxError",
    "InvalidNestingError",
    # Forward Adapter (IR → React)
    "generate_react",
    "ReactOptions",
    # Reverse Adapter (React → IR → Ophanic)
    "parse_react",
    "generate_diagram",
    "react_to_ophanic",
    "ReverseOptions",
]
