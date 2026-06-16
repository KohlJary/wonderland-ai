"""Adapters for generating code from Ophanic IR."""

from .react import generate_react, ReactOptions
from .react_reverse import (
    parse_react,
    generate_diagram,
    react_to_ophanic,
    ReverseOptions,
)
from .figma import (
    figma_to_ophanic,
    figma_to_diagram,
    FigmaOptions,
    FigmaClient,
    FigmaAPIError,
    extract_file_key,
)

__all__ = [
    # Forward (IR → React)
    "generate_react",
    "ReactOptions",
    # Reverse (React → IR → Ophanic)
    "parse_react",
    "generate_diagram",
    "react_to_ophanic",
    "ReverseOptions",
    # Figma import
    "figma_to_ophanic",
    "figma_to_diagram",
    "FigmaOptions",
    "FigmaClient",
    "FigmaAPIError",
    "extract_file_key",
]
