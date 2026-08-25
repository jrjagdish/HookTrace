from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import schemas
from auth import get_current_user
from db import get_db
from models import ChatHistory, User

router = APIRouter(prefix="/chat_history", tags=["chat_history"])


@router.get("", response_model=list[schemas.ChatHistoryOut])
async def get_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat_history = (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == current_user.id)
        .all()
    )
    return chat_history


@router.delete("/{chat_id}")
async def delete_chat_history(
    chat_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat_entry = (
        db.query(ChatHistory)
        .filter(ChatHistory.id == chat_id, ChatHistory.user_id == current_user.id)
        .first()
    )
    if not chat_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat entry not found or access denied",
        )
    db.delete(chat_entry)
    db.commit()
    return {"detail": "Chat entry deleted successfully"}
