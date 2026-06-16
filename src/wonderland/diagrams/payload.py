"""Emission payload for diagram decisions (P21 chunk 2).

What an agent ships when it authors a layout diagram during a workflow
(e.g. milestone_plan sketching the app's top-level structure). The
substrate writes it through ``DiagramRegistry``.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from wonderland.diagrams.models import DEFAULT_LAYER


class DiagramPayload(BaseModel):
    """A diagram an agent authored, as an Ophanic ``.oph`` body."""

    name: str = Field(min_length=1)
    oph: str = Field(min_length=1, description="The .oph diagram body")
    layer: str = Field(
        default=DEFAULT_LAYER,
        description="Structural layer: 'ui' (front-end tree), 'db', …",
    )


__all__ = ["DiagramPayload"]
