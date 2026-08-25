import io
import logging
import re
import tarfile
from typing import Any, Dict, List, Tuple

import httpx



logger = logging.getLogger(__name__)

_GITHUB_URL_RE = re.compile(
    r"^https?://github\.com/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+?)(\.git)?/?$"
)



def parse_github_url(github_url: str) -> Tuple[str, str]:
    match = _GITHUB_URL_RE.match((github_url or "").strip())
    if not match:
        raise ValueError("github_url must look like https://github.com/<owner>/<repo>")
    return match.group("owner"), match.group("repo")


async def fetch_repo_tree_and_files(
    owner: str, repo: str, branch: str = "main", github_token: str = None
) -> Dict[str, Any]:
    headers = {"User-Agent": "FastAPI-App"}
    logger.debug("Fetching repo tree: owner=%s repo=%s branch=%s", owner, repo, branch)

    if github_token:
      
        url = f"https://api.github.com/repos/{owner}/{repo}/tarball/{branch}"
        headers["Authorization"] = f"Bearer {github_token}"
    else:
       
        url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.tar.gz"

    file_tree: List[str] = []
    files_content: Dict[str, str] = {}

    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url, headers=headers)
        except httpx.RequestError as e:
            raise Exception(f"Failed to fetch repository archive: {e}")
        
        if response.status_code == 404:
            raise Exception(
                "Repository not found or private. Please log in with GitHub."
            )
        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch repository archive: HTTP {response.status_code}"
            )

        buffer = io.BytesIO(response.content)

        with tarfile.open(fileobj=buffer, mode="r:gz") as tar:
            members = tar.getmembers()
            if not members:
                return {"file_tree": file_tree, "files_content": files_content}

            prefix = members[0].name.split("/")[0] + "/" if members[0].name else ""

            for member in members:
                if not member.isfile():
                    continue

                clean_path = member.name.removeprefix(prefix)

                if any(
                    clean_path.startswith(ignored) or clean_path.endswith(ignored)
                    for ignored in [
                        ".git/",
                        "node_modules/",
                        ".png",
                        ".jpg",
                        ".pdf",
                        "package-lock.json",
                        "poetry.lock",
                        ".mp4",
                        ".mov",
                        ".avi",
                        ".mkv",
                        ".flv",
                        ".wmv",
                        ".webm",
                        ".m4v",
                        ".3gp",
                        ".3g2",
                        ".ogg",
                        ".ogv",
                        ".ts",
                        ".vob",
                        ".rm",
                        ".rmvb",
                        ".asf",
                        ".divx",
                        ".xvid",
                        "venv/",
                        "__pycache__/",
                        ".pyc",
                        ".ipynb_checkpoints/",
                        
                    ]
                ):
                    continue

                file_tree.append(clean_path)

             
                if member.size < 500 * 1024:
                    file_obj = tar.extractfile(member)
                    if file_obj:
                        try:
                            files_content[clean_path] = file_obj.read().decode("utf-8")
                        except UnicodeDecodeError:
                            pass
    return {"file_tree": file_tree, "files_content": files_content}
