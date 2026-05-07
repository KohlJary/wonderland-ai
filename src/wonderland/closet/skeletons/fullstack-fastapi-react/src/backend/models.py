"""SQLAlchemy models. Just `Base` + an example `HelloMessage` showing
the pattern. Replace HelloMessage with the actual feature models.

============================================================================
SKELETON TEMPLATE — HelloMessage is a placeholder; DELETE OR REPLACE.

If you delete this class, you MUST also:
  - Delete src/backend/api/messages.py (it imports HelloMessage)
  - Remove the `messages_router` line in src/backend/api/__init__.py
  - Delete tests/test_messages.py

Half-replacement (removing HelloMessage but leaving the references
in messages.py / __init__.py) breaks the import chain — pytest will
fail to collect ANY tests because conftest.py imports the broken
chain. Always run `run_tests` after a batch of changes to verify
the build still loads.

If you replace HelloMessage with new classes (Session, Break, etc.),
that's fine — but apply the same cleanup to its referencers above.
============================================================================
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


# === TEMPLATE: HelloMessage is a placeholder. Delete or replace. ===
class HelloMessage(Base):
    """Placeholder model demonstrating the SQLAlchemy pattern.

    The team should DELETE this when shipping real features — it
    exists only so the seed has a working end-to-end flow (DB row →
    API response → frontend render) for the human verifying the
    seed."""

    __tablename__ = "hello_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String(280), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "created_at": (
                self.created_at.isoformat() if self.created_at else datetime.now(timezone.utc).isoformat()
            ),
        }
