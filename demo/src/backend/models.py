"""SQLAlchemy models for the note-taking application.

Exports: Note, Tag (primary feature models).
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import hashlib

from sqlalchemy import Column, DateTime, Integer, String, Text, ForeignKey, Table, func, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def compute_revision_id(title: str, body: str, sorted_tag_ids: list[int], updated_at: str) -> str:
    """Compute deterministic revision_id as SHA256 hash of note state.
    
    Semantics: revision_id is cryptographically opaque, deterministic, and unforgeable.
    Used for optimistic locking: client caches revision_id after save, sends it as If-Match
    header on next PUT. If the header doesn't match the current revision, the server returns
    409 Conflict to prevent silent overwrites in multi-tab scenarios.
    
    Inputs:
    - title: note title string
    - body: note body string
    - sorted_tag_ids: sorted list of tag IDs (order-independent, reduces redundant hash mismatches)
    - updated_at: ISO8601 timestamp of the last update (string from the database)
    
    Returns:
    - revision_id: hex string (64 chars), SHA256 digest
    
    Invariant: identical inputs always produce identical revision_id (deterministic).
    This allows idempotent saves: if the client retries the same save, the server
    recognizes it by matching revision_id and doesn't double-write.
    
    TODO (ticket-081): Cache revision_id as a database column (computed on every write, cached on reads).
    Currently recomputed on every GET request (100 notes × 100 hash calls for a list is acceptable
    for MVP single-user scope, but adds O(n) CPU per list operation). For post-MVP optimization:
    add `revision_id` column to Note model, compute on POST/PUT, return from cache on GET.
    Revisit after performance testing confirms this is a bottleneck.
    
    Contract reference: contract-note-01KRY0B8 (backend impact section, revision-id computation)
    """
    # Canonicalize inputs for deterministic hashing
    canonical_state = json.dumps(
        {
            "title": title,
            "body": body,
            "tag_ids": sorted(sorted_tag_ids),  # Sort to be order-independent
            "updated_at": updated_at,
        },
        sort_keys=True,  # JSON keys in alphabetical order
        separators=(",", ":"),  # Compact representation (no spaces)
    )
    
    digest = hashlib.sha256(canonical_state.encode("utf-8")).hexdigest()
    return digest

# Association table for Note-Tag many-to-many relationship
# note_id has CASCADE delete: when a note is deleted, its associations are deleted
# tag_id does NOT have CASCADE delete: when an association is deleted, the tag persists
#   (tags can be shared across multiple notes, so we don't cascade-delete them)
note_tags = Table(
    "note_tags",
    Base.metadata,
    Column("note_id", Integer, ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)


class Note(Base):
    """A note with title, body, optional tags, and audit timestamps.
    
    Invariants:
    - id: auto-assigned primary key
    - title: text, required, non-empty
    - body: text, required, always a string (empty string is default, never NULL)
    - tags: relationship to Tag objects (many-to-many via note_tags)
    - created_at: ISO8601 timestamp, set on insert, immutable
    - updated_at: ISO8601 timestamp, set on insert, updated on each change
    """

    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False, default="")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationship to tags via association table
    # Note: cascade="all, delete" is NOT used here because tags can be shared
    # across multiple notes. The database foreign key (ondelete="CASCADE")
    # handles deleting the association; we don't cascade-delete the tag itself.
    tags = relationship("Tag", secondary=note_tags, back_populates="notes")

    def to_dict(self) -> dict:
        """Serialize to JSON-safe dict with ISO8601 timestamps (UTC).
        
        Ensures timestamps are timezone-aware (UTC) even if SQLAlchemy
        returns naive datetimes from SQLite. Tags returned with both
        names and IDs per contract-note-004 response shape.
        
        Note: revision_id is NOT computed here — it must be computed by the endpoint
        after this method returns, using compute_revision_id(). This separation
        ensures revision_id is always fresh and consistent with the current state.
        
        Invariant: all timestamps in JSON responses must be ISO8601 with
        explicit timezone (ending in 'Z' for UTC).
        """
        def ensure_tz_aware(dt: datetime | None) -> str:
            """Convert datetime to UTC ISO8601 string with Z suffix.
            
            If dt is naive (no tzinfo), assume UTC.
            If dt is aware, convert to UTC.
            Always returns ISO8601 with explicit Z suffix for UTC.
            """
            if not dt:
                dt = datetime.now(timezone.utc)
            elif dt.tzinfo is None:
                # Naive datetime: assume UTC (SQLite doesn't track tz)
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                # Timezone-aware: convert to UTC
                dt = dt.astimezone(timezone.utc)
            
            # Return ISO8601 with Z suffix for UTC (replaces +00:00)
            return dt.isoformat(timespec='microseconds').replace('+00:00', 'Z')
        
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "tag_names": [tag.name for tag in self.tags],
            "tag_ids": [tag.id for tag in self.tags],
            "created_at": ensure_tz_aware(self.created_at),
            "updated_at": ensure_tz_aware(self.updated_at),
        }


class Tag(Base):
    """A tag that can be associated with multiple notes.
    
    Invariants:
    - id: auto-assigned primary key
    - name: text, required, non-empty, globally unique
    - name is case-sensitive: 'research', 'Research', 'RESEARCH' are three distinct tags
    - notes: relationship to Note objects (many-to-many via note_tags)
    
    Contract reference: contract-note-tag-case-sensitivity (agreed: case-sensitive, v1)
    """

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    
    # Relationship back to notes
    # No cascade here either; the association table's foreign key constraints handle cleanup.
    notes = relationship("Note", secondary=note_tags, back_populates="tags")

    def to_dict(self) -> dict:
        """Serialize to JSON-safe dict."""
        return {
            "id": self.id,
            "name": self.name,
        }


class AuditLog(Base):
    """Immutable append-only audit trail of note saves.
    
    Each save attempt (POST or PUT, success or collision) creates an audit_log entry with:
    - note_id: FK to the note that was saved
    - timestamp: server-side timestamp of the save
    - user_id: user who saved (v1: always NULL, single-user scope)
    - saved_state_json: complete snapshot of note state at save time {title, body, tag_ids}
    - revision_id: opaque hash of the saved state (SHA256), returned to client for collision detection
    - state_hash: hash of entire log entry (tamper detection), computed as SHA256(note_id + timestamp + saved_state_json)
    - collision_detected: bool, true if save was rejected due to If-Match mismatch (409 Conflict)
    - conflicting_revision_id: if collision_detected=true, the server's current revision_id at conflict time
    
    Invariants:
    - Immutable: rows are never updated or deleted, only appended
    - Forensic completeness: every field required (no NULLs except user_id and conflicting_revision_id in v1)
    - Full-state snapshots: not deltas, to eliminate reconstruction-logic bugs
    - On collision (409): saved_state_json records the attempted save (from request payload), collision_detected=true, conflicting_revision_id=server's current revision
    
    Contract reference: ADR-01KRXX85 (audit-trail-schema-full-state-snapshots-with-timestamped-revisions)
                        contract-note-01KRY0B8 (revision-id-computation-and-collision-detection-contract-backend-side)
                        ticket-063 (audit-trail-logging-on-every-save-with-immutable-records)
    """

    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    user_id = Column(Integer, nullable=True)  # v1: NULL (single-user); future: FK to User
    saved_state_json = Column(Text, nullable=False)  # JSON snapshot of {title, body, tag_ids} at save time (or attempted save on collision)
    revision_id = Column(String(64), nullable=False)  # SHA256 hex digest (opaque hash returned to client)
    state_hash = Column(String(64), nullable=False)  # SHA256 hex digest (tamper detection)
    collision_detected = Column(Boolean, nullable=False, default=False)  # True if 409 Conflict was returned
    conflicting_revision_id = Column(String(64), nullable=True)  # Server's revision_id at time of conflict (if collision_detected=true)

    def to_dict(self) -> dict:
        """Serialize to JSON-safe dict with ISO8601 timestamp."""
        def ensure_tz_aware(dt: datetime | None) -> str:
            if not dt:
                dt = datetime.now(timezone.utc)
            elif dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt.isoformat(timespec='microseconds').replace('+00:00', 'Z')
        
        return {
            "id": self.id,
            "note_id": self.note_id,
            "timestamp": ensure_tz_aware(self.timestamp),
            "user_id": self.user_id,
            "saved_state_json": json.loads(self.saved_state_json),
            "revision_id": self.revision_id,
            "state_hash": self.state_hash,
        }
