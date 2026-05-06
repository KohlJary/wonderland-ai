"""POST /api/messages — placeholder echo endpoint demonstrating the
DB → API → response flow. The team should replace this with the
actual feature endpoints (delete or repurpose this file)."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.backend.db import get_db
from src.backend.models import HelloMessage

router = APIRouter()


class MessageCreate(BaseModel):
    text: str = Field(min_length=1, max_length=280)


class MessageResponse(BaseModel):
    id: int
    text: str
    created_at: str


@router.post("/messages", response_model=MessageResponse)
def create_message(
    payload: MessageCreate, db: Session = Depends(get_db)
) -> MessageResponse:
    """Echo a message into the DB and return it. Replace with real
    feature work."""
    msg = HelloMessage(text=payload.text)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return MessageResponse(**msg.to_dict())


@router.get("/messages", response_model=list[MessageResponse])
def list_messages(db: Session = Depends(get_db)) -> list[MessageResponse]:
    """List all messages (newest last). For development convenience."""
    rows = db.query(HelloMessage).order_by(HelloMessage.id).all()
    return [MessageResponse(**r.to_dict()) for r in rows]
