from langgraph.graph import StateGraph, START, END
from app.agents.state import ReviewState
from app.agents.fetcher import fetcher_node
from app.agents.router import route_selected_agents, router_node
from app.agents.structure import structure_agent
from app.agents.security import security_agent
from app.agents.quality import quality_agent
from app.agents.testing import testing_agent
from app.agents.synthesizer import synthesizer_node


def create_review_graph():
    workflow = StateGraph(ReviewState)

    workflow.add_node("fetcher", fetcher_node)
    workflow.add_node("router", router_node)
    workflow.add_node("structure", structure_agent)
    workflow.add_node("security", security_agent)
    workflow.add_node("quality", quality_agent)
    workflow.add_node("testing", testing_agent)
    workflow.add_node("synthesizer", synthesizer_node)

    workflow.add_edge(START, "fetcher")
    workflow.add_edge("fetcher", "router")
    workflow.add_conditional_edges(
        "router",
        route_selected_agents,
        ["structure", "security", "quality", "testing"],
    )
    workflow.add_edge("structure", "synthesizer")
    workflow.add_edge("security", "synthesizer")
    workflow.add_edge("quality", "synthesizer")
    workflow.add_edge("testing", "synthesizer")
    workflow.add_edge("synthesizer", END)

    return workflow.compile()


def run_review(repo_url: str) -> dict:
    graph = create_review_graph()
    result = graph.invoke({"repo_url": repo_url})
    return result["final_report"]
