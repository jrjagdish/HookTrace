from uuid import UUID
from sqlalchemy.orm import Session

from models import RepositoryChunks
from services.embeddings import generate_embedding



async def retrieve_relevent_chunks(
    db: Session, repository_id: UUID, query: str, top_k: int = 5
):
    query_embedding = await generate_embedding(query)
    chunks = (
        db.query(RepositoryChunks)
        .filter(RepositoryChunks.repository_id == repository_id)
        .order_by(RepositoryChunks.embedding.cosine_distance(query_embedding))
        .limit(top_k)
        .all()
    )
    return chunks
