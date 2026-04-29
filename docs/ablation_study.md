# Ablation Study

This study compares the default multi-agent workflow against a single-agent baseline over the same 50-query benchmark set.

## Compared systems

| Mode | Pipeline |
|---|---|
| Multi-agent | Researcher -> Critic -> Synthesizer -> Evaluator |
| Single-agent baseline | Researcher -> Synthesizer with no independent critique stage |

The deterministic baseline intentionally keeps retrieval inputs comparable while reducing the critique/evaluation benefit. This makes the benchmark useful for regression testing and for showing the expected quality/latency tradeoff.

## Results

| Mode | Overall | Relevancy | Faithfulness | Completeness | Avg latency | Avg cost/query |
|---|---:|---:|---:|---:|---:|---:|
| Multi-agent | 0.9541 | 1.0000 | 0.9900 | 0.8440 | 0.10 ms | $0.000799 |
| Single-agent baseline | 0.8678 | 1.0000 | 0.9306 | 0.6948 | 0.07 ms | $0.000603 |

## Delta

| Metric | Multi-agent lift |
|---|---:|
| Overall | +0.0863 |
| Faithfulness | +0.0594 |
| Completeness | +0.1492 |
| Latency | +0.03 ms |
| Cost/query | +$0.000196 |

## Interpretation

The multi-agent pipeline improves answer quality mainly through faithfulness and completeness. The critic stage creates a quality check before synthesis, and the evaluator makes the score profile visible for later regression testing.

The single-agent baseline is faster and cheaper. It is a reasonable fallback for low-risk drafts, but the multi-agent path is a better default for research briefs where unsupported claims and missing coverage are more costly than small increases in latency and token spend.

## When to choose each mode

| Use case | Recommended mode | Reason |
|---|---|---|
| Portfolio demo and research briefs | Multi-agent | Shows source collection, critique, synthesis, and evaluation |
| Quick exploratory summaries | Single-agent baseline | Lower latency and cost |
| High-stakes domains | Multi-agent plus human review | Better structure, but still requires expert validation |
| Batch jobs with tight budget | Single-agent baseline or capped multi-agent | Cost predictability matters |

## Reproduction

```bash
PYTHONPATH=. python3 benchmarks/run_benchmark.py --limit 50
```

The ablation summary is written to `results/ablation_results.json` and included in `results/benchmark_report.md`.
