from fastapi import Depends
from sqlalchemy.orm import Session

from chunker import chunk_repository
from models import RepositoryChunks
from services.embeddings import generate_embedding
from db import get_db


async def process_repository(
    repository_id: str,
    files_content: dict[str, str],
    db: Session = Depends(get_db),
):
    chunks = await chunk_repository(files_content)

    await process_chunks(
        repository_id,
        chunks,
        db,
    )


async def process_chunks(
    repository_id,
    chunks,
    db,
):
    for index, chunk in enumerate(chunks):
        embedding = await generate_embedding(
            chunk["chunk_content"]
        )

        db_chunk = RepositoryChunks(
            repository_id=repository_id,
            file_id=chunk["file_id"],
            file_path=chunk["file_path"],
            chunk_index=index,
            chunk_content=chunk["chunk_content"],
            embedding=str(embedding),
        )

        db.add(db_chunk)

    db.commit()