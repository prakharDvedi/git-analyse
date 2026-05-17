from __future__ import annotations

from app.agents.state import ReviewState


def router_node(state: ReviewState) -> ReviewState:
    file_map = state["file_map"]
    paths = list(file_map.keys())
    lower_paths = [path.lower() for path in paths]

    selected = {"structure", "security", "quality"}
    notes: dict[str, str] = {}

    has_tests = any(
        "test" in path or "__tests__" in path or path.endswith(".spec.ts") or path.endswith(".test.ts")
        for path in lower_paths
    )
    if has_tests:
        selected.add("testing")
        notes["testing"] = "Test-like files detected."
    else:
        # Keep testing agent for absence detection too, but note why.
        selected.add("testing")
        notes["testing"] = "No obvious tests detected; run testing agent to report coverage gap."

    has_sensitive_surface = any(
        any(token in path for token in ("auth", "config", "secret", "env", "docker", "api", "middleware"))
        for path in lower_paths
    )
    if has_sensitive_surface:
        notes["security"] = "Sensitive files/config surfaces detected."
    else:
        notes["security"] = "No obvious sensitive path names; security agent still runs on sampled files."

    state["selected_agents"] = sorted(selected)
    state["router_notes"] = notes
    return state


def route_selected_agents(state: ReviewState) -> list[str]:
    selected = state.get("selected_agents") or []
    # Always route at least one analysis node so the graph progresses.
    return selected or ["quality"]

