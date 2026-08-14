from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from auth import get_current_user
from services.processor import process_repository
from db import get_db
from models import User, Repositories, RepositoryFiles
import schemas
from github_parser.tarfile import fetch_repo_tree_and_files
from fastapi import BackgroundTasks

router = APIRouter()


@router.post("/repositories")
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

    db.commit()
    background_tasks.add_task(
        process_repository, repository.id, files_data["files_content"]
    )

    return {
        "repository_id": repository.id,
        "files_saved": len(files_data["files_content"]),
        "status" : "Processing"
    }
