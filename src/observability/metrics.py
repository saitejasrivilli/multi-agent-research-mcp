"""Lightweight production metrics for the research pipeline.

The app currently runs agents inline, so this module keeps instrumentation
simple: wrap each agent call with AgentTimer and estimate token/cost totals
from the returned payloads. It has no external service dependency.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from time import perf_counter
from typing import Any, Dict, Iterator, List, Optional


# Groq pricing changes over time. Keep these configurable in production.
DEFAULT_COST_PER_1K_INPUT_TOKENS = 0.00059
DEFAULT_COST_PER_1K_OUTPUT_TOKENS = 0.00079


@dataclass
class AgentMetric:
    agent: str
    latency_ms: float
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    success: bool = True
    error: Optional[str] = None


@dataclass
class QueryMetrics:
    query: str
    total_latency_ms: float = 0.0
    total_cost_usd: float = 0.0
    agents: List[AgentMetric] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "total_latency_ms": round(self.total_latency_ms, 2),
            "total_cost_usd": round(self.total_cost_usd, 6),
            "agents": [asdict(metric) for metric in self.agents],
        }


class MetricsCollector:
    """Collects per-agent latency and estimated cost for one research query."""

    def __init__(self, query: str):
        self.query = query
        self._start = perf_counter()
        self.metrics = QueryMetrics(query=query)

    @contextmanager
    def agent_timer(
        self,
        agent: str,
        *,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> Iterator[None]:
        start = perf_counter()
        success = True
        error = None
        try:
            yield
        except Exception as exc:  # pragma: no cover - preserves original exception
            success = False
            error = str(exc)
            raise
        finally:
            latency_ms = (perf_counter() - start) * 1000
            cost = estimate_llm_cost(input_tokens, output_tokens)
            self.metrics.agents.append(
                AgentMetric(
                    agent=agent,
                    latency_ms=round(latency_ms, 2),
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=round(cost, 6),
                    success=success,
                    error=error,
                )
            )

    def finalize(self) -> QueryMetrics:
        self.metrics.total_latency_ms = round((perf_counter() - self._start) * 1000, 2)
        self.metrics.total_cost_usd = round(sum(m.cost_usd for m in self.metrics.agents), 6)
        return self.metrics


def estimate_tokens(text: Any) -> int:
    """Cheap token estimate for cost reporting without adding tokenizer deps."""
    if text is None:
        return 0
    return max(1, int(len(str(text).split()) / 0.75))


def estimate_llm_cost(
    input_tokens: int,
    output_tokens: int,
    input_rate: float = DEFAULT_COST_PER_1K_INPUT_TOKENS,
    output_rate: float = DEFAULT_COST_PER_1K_OUTPUT_TOKENS,
) -> float:
    return (input_tokens / 1000 * input_rate) + (output_tokens / 1000 * output_rate)


def summarize_metrics(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize metrics emitted by benchmark or production runs."""
    if not rows:
        return {"queries": 0, "avg_latency_ms": 0, "avg_cost_usd": 0, "agent_latency_ms": {}}

    agent_buckets: Dict[str, List[float]] = {}
    for row in rows:
        for agent in row.get("agents", []):
            agent_buckets.setdefault(agent["agent"], []).append(agent.get("latency_ms", 0))

    return {
        "queries": len(rows),
        "avg_latency_ms": round(sum(r.get("total_latency_ms", 0) for r in rows) / len(rows), 2),
        "avg_cost_usd": round(sum(r.get("total_cost_usd", 0) for r in rows) / len(rows), 6),
        "agent_latency_ms": {
            agent: round(sum(values) / len(values), 2)
            for agent, values in sorted(agent_buckets.items())
        },
    }
