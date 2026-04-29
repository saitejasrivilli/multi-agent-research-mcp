"""
LangGraph Workflow with Conditional Routing and Revision Loops
"""
from langgraph.graph import StateGraph, END
from .state import ResearchState, AgentStatus

def should_revise(state: ResearchState) -> str:
    """Determine if research needs revision based on critic feedback."""
    if state.get("error"):
        return "end"
    
    critique = state.get("critique", {})
    quality_score = critique.get("quality_score", 1.0)
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 2)
    
    if quality_score < 0.7 and iteration < max_iterations:
        return "revise"
    return "synthesize"

def create_research_workflow(researcher_fn, critic_fn, synthesizer_fn, evaluator_fn):
    """Create the LangGraph workflow with conditional edges."""
    
    workflow = StateGraph(ResearchState)
    
    # Add nodes
    workflow.add_node("researcher", researcher_fn)
    workflow.add_node("critic", critic_fn)
    workflow.add_node("synthesizer", synthesizer_fn)
    workflow.add_node("evaluator", evaluator_fn)
    
    # Set entry point
    workflow.set_entry_point("researcher")
    
    # Add edges
    workflow.add_edge("researcher", "critic")
    
    # Conditional edge: revise or synthesize
    workflow.add_conditional_edges(
        "critic",
        should_revise,
        {
            "revise": "researcher",
            "synthesize": "synthesizer",
            "end": END
        }
    )
    
    workflow.add_edge("synthesizer", "evaluator")
    workflow.add_edge("evaluator", END)
    
    return workflow.compile()
