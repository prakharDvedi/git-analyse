from __future__ import annotations

from typing import Any


SNIPPET_LIMIT = 2000


def list_files(file_map: dict[str, str], contains: str | None = None, limit: int = 50) -> list[str]:
    files = list(file_map.keys())
    if contains:
        needle = contains.lower()
        files = [path for path in files if needle in path.lower()]
    return files[:limit]


def get_file(file_map: dict[str, str], path: str) -> dict[str, Any]:
    content = file_map.get(path)
    if content is None:
        return {"path": path, "found": False, "content": ""}
    return {
        "path": path,
        "found": True,
        "content": content[:SNIPPET_LIMIT],
    }


def search_code(file_map: dict[str, str], query: str, limit: int = 10) -> list[dict[str, Any]]:
    query_lower = query.lower()
    matches: list[dict[str, Any]] = []
    for path, content in file_map.items():
        if query_lower not in content.lower() and query_lower not in path.lower():
            continue
        index = content.lower().find(query_lower)
        if index < 0:
            snippet = content[:SNIPPET_LIMIT]
        else:
            start = max(index - 120, 0)
            end = min(index + 240, len(content))
            snippet = content[start:end]
        matches.append({"path": path, "snippet": snippet})
        if len(matches) >= limit:
            break
    return matches


def run_tool(file_map: dict[str, str], tool_name: str, args: dict[str, Any]) -> Any:
    if tool_name == "list_files":
        return list_files(
            file_map=file_map,
            contains=args.get("contains"),
            limit=int(args.get("limit", 50)),
        )
    if tool_name == "get_file":
        return get_file(file_map=file_map, path=str(args["path"]))
    if tool_name == "search_code":
        return search_code(
            file_map=file_map,
            query=str(args["query"]),
            limit=int(args.get("limit", 10)),
        )
    raise ValueError(f"Unknown tool: {tool_name}")


def tool_registry_description() -> str:
    return """Available tools:
- list_files(contains?: string, limit?: int): list repo file paths, optionally filtered by path substring
- get_file(path: string): fetch one file and return a truncated content snippet
- search_code(query: string, limit?: int): search repo contents/paths and return matching snippets"""

