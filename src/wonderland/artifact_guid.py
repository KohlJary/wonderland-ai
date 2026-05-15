"""Artifact identity primitives (P18 GUID-everywhere).

Every artifact registry (Story/Feature/Ticket/ADR/Ruling/Review/
ContractNote/Milestone/Requirement/TestScenario/Implementation)
stamps a stable GUID at creation. The GUID is the identity; slug
is cosmetic.

ULID is the chosen format:
  - 26-char Crockford-base32; lexically sortable by creation time
  - Compact enough to embed in filenames without ugliness
  - Already used elsewhere in the substrate (utterance ids)
  - Short form (first 8 chars) is collision-resistant within a
    project and human-distinguishable

Slug-as-identity failure modes this primitive eliminates:
  - Phantom citations (agent invents a slug that doesn't resolve):
    cite by GUID; any GUID that doesn't resolve becomes a substrate-
    level error rather than silent drift
  - Slug drift across rotations (same concept, near-duplicate
    slugs hashed differently): GUID is sticky; agent re-emits with
    the existing GUID to amend, slug can change freely
  - Near-duplicate features at M2 (validation4: 9 features for 3
    concepts because Rabbit tried to revise but his retitled slug
    produced a new file): re-emit with the same GUID updates in
    place

The slug field stays load-bearing for human browsing: filenames
embed the slug so operators can scan a directory; markdown headers
display slug-derived titles. But the substrate routes on GUID.
"""

from __future__ import annotations

from ulid import ULID


def new_artifact_guid() -> str:
    """Generate a fresh ULID for an artifact. ULIDs are 26-char
    Crockford-base32 strings, lexically sortable by creation time
    (~ms resolution). Collision probability is astronomically low
    within a single project's artifact set."""
    return str(ULID())


def short_guid(guid: str) -> str:
    """First 8 chars of a ULID — short enough to embed in a
    filename without uglifying it, long enough to disambiguate
    every artifact a single project will ever produce.

    Used in filenames as ``<kind>-<short_guid>-<slug>.md``. The
    full GUID lives in the markdown body's ``**GUID:**`` line so
    nothing important depends on the short form's uniqueness; the
    short form is purely for human-glance disambiguation."""
    return guid[:8] if guid else ""
