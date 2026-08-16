from sqlalchemy.orm import Session
from services.retrieval import retrieve_relevent_chunks
from uuid import UUID
from services.llm import generate_answer


async def answer_query(db: Session, repository_id: UUID, query: str, top_k: int = 5):

    chunks = await retrieve_relevent_chunks(db, repository_id, query, top_k)
    context = "\n\n".join(f"""
FILE: {chunk.file_path}

{chunk.chunk_content}
""" for chunk in chunks)
    answer = await generate_answer(query, context)

    return {
        "answer": answer,
        "sources": [
            {
                "file_path": chunk.file_path,
                "chunk_id": chunk.id,
            }
            for chunk in chunks
        ],
    }
