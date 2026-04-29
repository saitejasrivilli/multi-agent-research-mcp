# Evaluation Results

This benchmark evaluates the research pipeline on 50 queries from `benchmarks/benchmark_queries.jsonl`.

The default benchmark path is deterministic and offline-friendly. It exercises the same evaluation, reporting, ablation, and observability plumbing without requiring Groq or Tavily API keys. Use the live mode when measuring production retrieval/model quality.

## How to reproduce

```bash
PYTHONPATH=. python3 benchmarks/run_benchmark.py --limit 50
```

For a running FastAPI backend:

```bash
PYTHONPATH=. python3 benchmarks/run_benchmark.py --limit 50 --live --api-url http://localhost:8000
```

## Dataset

| Property | Value |
|---|---:|
| Query count | 50 |
| Query file | `benchmarks/benchmark_queries.jsonl` |
| Reference answers | Included per JSONL row |
| Default run mode | Deterministic benchmark proxy |
| Live run mode | FastAPI `/api/research` job execution |

## RAGAS-style score summary

| Metric | Mean | Median | Min | Max |
|---|---:|---:|---:|---:|
| Relevancy | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Faithfulness | 0.9900 | 1.0000 | 0.5000 | 1.0000 |
| Coherence | 0.9000 | 0.9000 | 0.9000 | 0.9000 |
| Completeness | 0.8440 | 0.8500 | 0.7500 | 0.8500 |
| Citation accuracy | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Overall | 0.9541 | 0.9575 | 0.8325 | 0.9575 |

## Metric definitions

| Metric | What it checks | Implementation |
|---|---|---|
| Relevancy | Query term overlap against findings and evidence | `RAGEvaluator.calculate_relevancy` |
| Faithfulness | Whether synthesis claims are supported by retrieved source text | `RAGEvaluator.calculate_faithfulness` |
| Coherence | Report structure, summary depth, sections, takeaways, and limitations | `RAGEvaluator.calculate_coherence` |
| Completeness | Word count, source count, section depth, and takeaway coverage | `RAGEvaluator.calculate_completeness` |
| Citation accuracy | Source coverage for citation reporting | `RAGEvaluator.calculate_citation_accuracy` |

## Interpretation

The deterministic run is best treated as a regression benchmark. It verifies that benchmark inputs, evaluation scoring, reporting, ablation comparison, and production metric collection are wired together.

The score profile shows strong relevancy and citation coverage in the controlled benchmark, with completeness as the most useful quality lever. Live runs should be saved separately when API keys, model versions, search settings, and timestamps are available.

## Generated artifacts

| File | Purpose |
|---|---|
| `results/benchmark_results.json` | Raw per-query benchmark rows, evaluations, and production metrics |
| `results/benchmark_report.md` | Human-readable benchmark summary |
| `results/ablation_results.json` | Aggregated multi-agent vs single-agent comparison |
