import asyncio

from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "BAAI/bge-small-en-v1.5"
)


async def generate_embedding(text: str) -> list[float]:
    return await asyncio.to_thread(lambda: model.encode(text).tolist())



async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return await asyncio.to_thread(lambda: model.encode(texts).tolist())