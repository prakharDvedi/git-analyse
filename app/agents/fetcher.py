from app.agents.state import ReviewState
from app.services.github_service import get_repo_tree, get_file_content, get_default_branch
from app.utils.repo_url import parse_github_repo_url

MAX_CONTENT_LENGTH = 3000


def fetcher_node(state: ReviewState) -> ReviewState:
    repo_url = state["repo_url"]

    owner, repo = parse_github_repo_url(repo_url)
    branch = get_default_branch(owner, repo)
    file_entries, _, _ = get_repo_tree(owner, repo, branch)

    file_map = {}
    for entry in file_entries:
        path = entry["path"]
        try:
            content = get_file_content(owner, repo, path)
            if len(content) > MAX_CONTENT_LENGTH:
                content = content[:MAX_CONTENT_LENGTH] + "\n\n[truncated...]"
            file_map[path] = content
        except Exception:
            file_map[path] = "[unable to read]"

    state["file_map"] = file_map
    return state