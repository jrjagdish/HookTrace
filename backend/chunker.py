import asyncio
from pathlib import Path

from tree_sitter_language_pack import get_parser

EXTENSION_LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".cs": "c_sharp",
}


async def get_language(path: str) -> str | None:
    ext = Path(path).suffix.lower()
    return EXTENSION_LANGUAGE_MAP.get(ext)


async def chunk_file(
    file_path: str,
    content: str,
) -> list[dict]:

    language = await get_language(file_path)

    if not language:
        return []

    parser = get_parser(language)

    
    tree = await asyncio.to_thread(parser.parse, content.encode("utf-8"))

    chunks = []

    root = tree.root_node

    for node in root.children:

        chunk = content[
            node.start_byte : node.end_byte
        ]

        chunks.append(
            {
                "file_path": file_path,
                "node_type": node.type,
                "content": chunk,
            }
        )

    return chunks


async def chunk_repository(
    files_content: dict[str, str],
) -> list[dict]:

    all_chunks = []

    for file_path, content in files_content.items():

        chunks = await chunk_file(
            file_path=file_path,
            content=content,
        )

        all_chunks.extend(chunks)

    return all_chunks