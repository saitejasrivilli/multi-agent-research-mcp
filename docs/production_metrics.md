# Production Metrics

The metrics layer lives in `src/observability/metrics.py`. It tracks latency, token estimates, cost estimates, success state, and errors per agent.

## Metrics to report

| Metric | Why it matters | Source |
|---|---|---|
| End-to-end latency | User waits for this total time | `QueryMetrics.total_latency_ms` |
| Per-agent latency | Shows bottlenecks by researcher, critic, synthesizer, evaluator | `AgentMetric.latency_ms` |
| Estimated cost per query | Needed for pricing and rate limiting decisions | `AgentMetric.cost_usd` |
| Failure rate by agent | Finds fragile stages | `AgentMetric.success` and `error` |
| Quality score | Guards against cheap but bad outputs | `evaluation.overall` |
| Citation accuracy | Guards against fake trust signals | `evaluation.citation_accuracy` |

## Expected use cases

| Use case | Fit | Reason |
|---|---|---|
| Market scan | Strong | Benefits from source collection, synthesis, and limitations |
| Literature or technical overview | Strong | Multi-agent critique improves coverage and structure |
| Competitive intelligence brief | Medium | Needs freshness and source quality checks |
| Legal or medical advice | Weak | Requires expert review and stronger verification |
| Real-time news answer | Medium | Works only when search freshness and source dates are enforced |

## Instrumentation example

```python
from src.observability.metrics import MetricsCollector, estimate_tokens

collector = MetricsCollector(query)
with collector.agent_timer("researcher", input_tokens=estimate_tokens(query)):
    research = run_researcher(query, keys, status_col)

metrics = collector.finalize().to_dict()
```

## Cost caveat

The module uses configurable token-cost estimates. Do not treat these as billing truth. For production, replace estimates with provider-returned usage fields where available.
