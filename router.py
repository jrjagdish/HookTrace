from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from auth import get_current_user
from db import get_db
from models import User, Repositories, RepositoryFiles
import schemas

router = APIRouter()


@router.post("/repositories")
def create_repository(
    payload: schemas.RepositoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repository = Repositories(**payload.dict())
    repository.user_id = current_user.id
    db.add(repository)
    db.commit()
    db.refresh(repository)
    return repository
