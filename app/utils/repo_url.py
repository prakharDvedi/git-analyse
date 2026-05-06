from urllib.parse import urlparse


def parse_github_repo_url(repo_url: str) -> tuple[str, str]:
    """
    Returns (owner, repo) from URLs like:
    - https://github.com/owner/repo
    - https://github.com/owner/repo/
    - https://github.com/owner/repo.git
    """
    parsed = urlparse(repo_url.strip())
    if parsed.netloc not in {"github.com", "www.github.com"}:
        raise ValueError("Only github.com URLs are supported")

    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        raise ValueError("Invalid GitHub repository URL")

    owner = parts[0]
    repo = parts[1].removesuffix(".git")
    if not owner or not repo:
        raise ValueError("Invalid GitHub repository URL")

    return owner, repo
