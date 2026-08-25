import logging
from uuid import UUID

from chunker import chunk_repository
from db import get_db_session
from github_parser.tarfile import fetch_repo_tree_and_files, parse_github_url
from models import Repositories, RepositoryChunks, RepositoryFiles
from services.embeddings import generate_embeddings

logger = logging.getLogger(__name__)


# CHANGED: this is the whole ingestion pipeline now (fetch + save files + chunk + embed),
# run as a single background task. Previously `routers`/`router.py` awaited the GitHub
# fetch inline in the `POST /repositories/create` handler — the request stayed open for
# as long as the download took, and only the chunk/embed step ran in the background.
# It also never updated `repository.status` past "processing" on either success or
# failure, so the frontend's polling loop (Dashboard.jsx) would spin forever. This
# function now owns the full lifecycle and always leaves the repository in "ready" or
# "failed".
async def ingest_repository(repository_id: UUID, github_url: str, branch: str) -> None:
    with get_db_session() as db:
        repository = db.get(Repositories, repository_id)
        if repository is None:
            logger.error("Repository %s was deleted before ingestion started", repository_id)
            return

        try:
            owner, repo = parse_github_url(github_url)
            files_data = await fetch_repo_tree_and_files(owner, repo, branch)

            file_map: dict[str, UUID] = {}
            for path, content in files_data["files_content"].items():
                repo_file = RepositoryFiles(
                    repository_id=repository.id, file_path=path, file_content=content
                )
                db.add(repo_file)
                db.flush()
                file_map[path] = repo_file.id

            chunks = await chunk_repository(files_data["files_content"])
            await process_chunks(repository.id, chunks, file_map, db)

            repository.status = "ready"
            db.commit()
        except Exception:
            # CHANGED: previously an exception here (network error, bad URL, embedding
            # failure) just propagated out of the background task, got swallowed by
            # BackgroundTasks' default handling, and left the repository stuck on
            # "processing" with no record of what went wrong.
            logger.exception("Ingestion failed for repository %s", repository_id)
            db.rollback()
            repository.status = "failed"
            db.commit()


async def process_chunks(
    repository_id: UUID,
    chunks: list[dict],
    file_map: dict[str, UUID],
    db,
) -> None:
    if not chunks:
        return

    
    contents = [chunk["content"] for chunk in chunks]
    embeddings = await generate_embeddings(contents)

    for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        db.add(
            RepositoryChunks(
                repository_id=repository_id,
                file_id=file_map[chunk["file_path"]],
                file_path=chunk["file_path"],
                chunk_index=index,
                chunk_content=chunk["content"],
                embedding=embedding,
            )
        )
