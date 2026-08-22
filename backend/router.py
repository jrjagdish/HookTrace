from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from auth import get_current_user
from services.processor import process_repository
from db import get_db
from models import ChatHistory, User, Repositories, RepositoryFiles
import schemas
from github_parser.tarfile import fetch_repo_tree_and_files
from fastapi import BackgroundTasks
from services.rag import answer_query

router = APIRouter()


@router.post("/repositories/create")
async def create_repository(
    payload: schemas.RepositoryCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repository = Repositories(**payload.dict())
    repository.user_id = current_user.id
    db.add(repository)
    db.commit()
    db.refresh(repository)
    payload_dict = payload.dict()
    branch = payload_dict.get("default_branch", "main")
    github_url = payload_dict.get("github_url", "")
    owner_repo = github_url.rstrip("/").split("/")[-2:]
    file_map = {}
    try:
        files_data = await fetch_repo_tree_and_files(
            owner_repo[0], owner_repo[1].removesuffix(".git"), branch
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch repository archive: {str(e)}"
        )

    for path, content in files_data["files_content"].items():
        repo_file = RepositoryFiles(
            repository_id=repository.id, file_path=path, file_content=content
        )
        db.add(repo_file)
        db.flush()
        file_map[path] = repo_file.id

    db.commit()
    background_tasks.add_task(
        process_repository, repository.id, files_data["files_content"],file_map
    )

    return {
        "repository_id": repository.id,
        "files_saved": len(files_data["files_content"]),
        "status" : "Processing"
    }

@router.get("/repositories")
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

@router.post("/repositories/{repository_id}/query")
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
    
    
    

    result = await answer_query(db, repository.id, payload.query, payload.top_k)
    chat = ChatHistory(
            repository_id=repository.id,
            user_id=current_user.id,
            query=payload.query,
            answer = result["answer"],
        )
    db.add(chat)
    db.commit()
    return result

@router.get("/chat_history")
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

@router.delete("/chat_history/{chat_id}")
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