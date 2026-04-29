# Benchmark Results

Dataset: 50 queries in `benchmarks/benchmark_queries.jsonl`.
Default run mode: deterministic proxy for reproducible CI and portfolio review.

## RAGAS-style Scores

| Metric | Mean | Median | Min | Max |
|---|---:|---:|---:|---:|
| relevancy | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| faithfulness | 0.9900 | 1.0000 | 0.5000 | 1.0000 |
| coherence | 0.9000 | 0.9000 | 0.9000 | 0.9000 |
| completeness | 0.8440 | 0.8500 | 0.7500 | 0.8500 |
| citation_accuracy | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| overall | 0.9541 | 0.9575 | 0.8325 | 0.9575 |

## Production Metrics

- Queries: 50
- Average latency: 0.1 ms
- Average estimated cost: $0.000799 per query
- Per-agent latency:
  - critic: 0.0 ms
  - evaluator: 0.04 ms
  - researcher: 0.0 ms
  - synthesizer: 0.01 ms

## Ablation: Multi-Agent vs Single-Agent

| Mode | Overall | Relevancy | Faithfulness | Completeness | Avg latency ms | Avg cost |
|---|---:|---:|---:|---:|---:|---:|
| multi_agent | 0.9541 | 1.0000 | 0.9900 | 0.8440 | 0.10 | $0.000799 |
| single_agent | 0.8678 | 1.0000 | 0.9306 | 0.6948 | 0.07 | $0.000603 |

Interpretation: the multi-agent path earns its quality lift from the critique and evaluation stages. The cost is extra latency and token usage.