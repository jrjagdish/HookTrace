from uuid import UUID
from fastapi import Depends
from sqlalchemy.orm import Session

from chunker import chunk_repository
from models import RepositoryChunks
from services.embeddings import generate_embedding
from db import get_db


async def process_repository(
    repository_id: str,
    files_content: dict[str, str],
    file_map: dict[str, UUID],
):
    db = next(get_db())
    chunks = await chunk_repository(files_content)

    await process_chunks(
        repository_id,
        chunks,
        file_map,
        db,
    )


async def process_chunks(
    repository_id,
    chunks,
    file_map,
    db,
):
    for index, chunk in enumerate(chunks):
        embedding = await generate_embedding(
            chunk["content"]
        )

        db_chunk = RepositoryChunks(
            repository_id=repository_id,
            file_id=file_map[chunk["file_path"]],
            file_path=chunk["file_path"],
            chunk_index=index,
            chunk_content=chunk["content"],
            embedding=embedding,
        )

        db.add(db_chunk)

    db.commit()