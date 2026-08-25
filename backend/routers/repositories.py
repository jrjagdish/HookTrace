import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

import schemas
from auth import get_current_user
from db import get_db
from github_parser.tarfile import parse_github_url
from models import ChatHistory, Repositories, User
from services.processor import ingest_repository
from services.rag import answer_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.post("/create", response_model=schemas.RepositoryOut, status_code=status.HTTP_201_CREATED)
async def create_repository(
    payload: schemas.RepositoryCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
 
    try:
        parse_github_url(payload.github_url)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    repository = Repositories(**payload.model_dump())
    repository.user_id = current_user.id
    db.add(repository)
    db.commit()
    db.refresh(repository)

   
    background_tasks.add_task(
        ingest_repository, repository.id, payload.github_url, payload.default_branch
    )

    return repository


@router.get("", response_model=list[schemas.RepositoryOut])
async def get_repositories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repositories = (
        db.query(Repositories)
        .filter(Repositories.user_id == current_user.id)
        .all()
    )
    return repositories


@router.post("/{repository_id}/query", response_model=schemas.QueryResponse)
async def query_repository(
    repository_id: UUID,
    payload: schemas.QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repository = (
        db.query(Repositories)
        .filter(Repositories.id == repository_id, Repositories.user_id == current_user.id)
        .first()
    )
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found or access denied",
        )

    if repository.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Repository is not ready yet (status: {repository.status})",
        )

    try:
        result = await answer_query(db, repository.id, payload.query, payload.top_k)
    except Exception:
       
        logger.exception("Query failed for repository %s", repository_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate an answer. Please try again.",
        )

    chat = ChatHistory(
        repository_id=repository.id,
        user_id=current_user.id,
        query=payload.query,
        answer=result["answer"],
    )
    db.add(chat)
    db.commit()
    return result
