"""
LangGraph State Machine for Multi-Agent Research Pipeline
"""
from typing import TypedDict, List, Optional, Annotated
from langgraph.graph import StateGraph, END
from enum import Enum

class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"

class ResearchState(TypedDict):
    """State that flows through the research pipeline."""
    query: str
    search_queries: List[str]
    sources: List[dict]
    findings: List[dict]
    critique: Optional[dict]
    synthesis: Optional[dict]
    citations: List[str]
    evaluation: Optional[dict]
    vector_ids: List[str]
    iteration: int
    max_iterations: int
    agent_status: dict
    error: Optional[str]

def create_initial_state(query: str, max_iterations: int = 2) -> ResearchState:
    """Create initial state for the pipeline."""
    return ResearchState(
        query=query,
        search_queries=[],
        sources=[],
        findings=[],
        critique=None,
        synthesis=None,
        citations=[],
        evaluation=None,
        vector_ids=[],
        iteration=0,
        max_iterations=max_iterations,
        agent_status={
            "researcher": AgentStatus.PENDING,
            "critic": AgentStatus.PENDING,
            "synthesizer": AgentStatus.PENDING,
            "evaluator": AgentStatus.PENDING
        },
        error=None
    )
