# 🔬 Multi-Agent Research Assistant

AI-powered research using autonomous agents with LangGraph, RAG, and real-time evaluation.
Live Demo: https://multi-agent-research-mcp-pr.streamlit.app/

![Quality Score](https://img.shields.io/badge/Quality-85%25-green)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🏗️ Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph State Machine                   │
├─────────────┬─────────────┬─────────────┬─────────────────────┤
│ Researcher  │   Critic    │ Synthesizer │     Evaluator      │
│   Agent     │   Agent     │   Agent     │   (RAGAS/DeepEval) │
├─────────────┴─────────────┴─────────────┴─────────────────────┤
│                    ChromaDB Vector Store                      │
├───────────────────────────────────────────────────────────────┤
│              Tavily Search    │    Groq (Llama 3.3)          │
└───────────────────────────────────────────────────────────────┘
```

## ✨ Features

- **LangGraph State Machine**: Conditional routing, revision loops
- **Vector Database**: ChromaDB for semantic search & RAG
- **Multi-Agent Pipeline**: Researcher → Critic → Synthesizer → Evaluator
- **Real-time Streaming**: Async SSE for live updates
- **Export Options**: PDF, Markdown with APA/MLA/Chicago citations
- **RAG Evaluation**: RAGAS-inspired metrics (relevancy, faithfulness, coherence)
- **FastAPI Backend**: REST API with async job processing
- **Docker + CI/CD**: GitHub Actions, containerized deployment

## 🚀 Quick Start

### Local Development
```bash
# Clone
git clone https://github.com/saitejasrivilli/multi-agent-research-mcp
cd multi-agent-research-mcp

# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Add your GROQ_API_KEY and TAVILY_API_KEY

# Run Streamlit
streamlit run app.py

# Run API (separate terminal)
uvicorn src.api.main:app --reload
```

### Docker
```bash
docker-compose up
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/research` | Start research job |
| GET | `/api/research/{id}` | Get job status |
| GET | `/api/research/{id}/stream` | Stream progress (SSE) |
| GET | `/api/research/{id}/export/pdf` | Export as PDF |
| GET | `/api/research/{id}/export/markdown` | Export as Markdown |

## 📊 Evaluation Metrics

| Metric | Description |
|--------|-------------|
| Relevancy | Query-finding alignment |
| Faithfulness | Source accuracy |
| Coherence | Structure & flow |
| Completeness | Coverage depth |
| Citation Accuracy | Source attribution |


## 📈 Benchmark & Results

Run the reproducible 50-query benchmark:

```bash
PYTHONPATH=. python3 benchmarks/run_benchmark.py --limit 50
```

Artifacts:

| File | Purpose |
|------|---------|
| `benchmarks/benchmark_queries.jsonl` | 50 benchmark queries with reference answers |
| `results/benchmark_results.json` | Raw per-query outputs, scores, and production metrics |
| `results/ablation_results.json` | Multi-agent vs single-agent comparison |
| `results/benchmark_report.md` | Human-readable benchmark report |
| `docs/evaluation_results.md` | Evaluation methodology and 50-query RAGAS-style score summary |
| `docs/ablation_study.md` | Multi-agent vs single-agent baseline analysis |
| `docs/failure_analysis.md` | Failure modes, detection signals, and mitigations |
| `docs/production_metrics.md` | Latency, cost, agent metrics, and use-case fit |

### 50-query RAGAS-style benchmark

Detailed methodology is in `docs/evaluation_results.md`.

| Metric | Mean | Median | Min | Max |
|--------|-----:|-------:|----:|----:|
| Relevancy | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Faithfulness | 0.9900 | 1.0000 | 0.5000 | 1.0000 |
| Coherence | 0.9000 | 0.9000 | 0.9000 | 0.9000 |
| Completeness | 0.8440 | 0.8500 | 0.7500 | 0.8500 |
| Citation Accuracy | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Overall | 0.9541 | 0.9575 | 0.8325 | 0.9575 |

Caveat: the default benchmark is a deterministic proxy so reviewers can run it without API keys. Treat it as a regression and wiring test, not proof of live web-search quality. For live evaluation:

```bash
PYTHONPATH=. python3 benchmarks/run_benchmark.py --live --api-url http://127.0.0.1:8000
```

Recommended live workflow:

```bash
PYTHONPATH=. uvicorn src.api.main:app --host 127.0.0.1 --port 8000
PYTHONPATH=. python3 benchmarks/run_benchmark.py --limit 1 --live --api-url http://127.0.0.1:8000
PYTHONPATH=. python3 benchmarks/run_benchmark.py --limit 50 --live --api-url http://127.0.0.1:8000 --delay-seconds 5
```

Do not run the API with `--reload` during live benchmarks. Jobs are stored in memory, so a reload can remove a pending job before the benchmark polls it.

### Live benchmark sample

A live run completed 28 of 50 benchmark queries before the Groq on-demand daily token limit stopped the remaining requests. The completed live subset produced:

| Metric | Mean | Median | Min | Max |
|--------|-----:|-------:|----:|----:|
| Relevancy | 0.7000 | 0.8000 | 0.0000 | 1.0000 |
| Faithfulness | 0.6667 | 0.5833 | 0.0000 | 1.0000 |
| Coherence | 0.9964 | 1.0000 | 0.9000 | 1.0000 |
| Completeness | 0.7679 | 0.8000 | 0.6500 | 0.9000 |
| Citation Accuracy | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Overall | 0.8061 | 0.8150 | 0.5950 | 0.9700 |

Live production metrics from the completed subset:

| Metric | Value |
|--------|------:|
| Completed queries | 28 |
| Failed queries | 22 |
| Average latency | 7087.4 ms |
| Average estimated cost/query | $0.005454 |
| Researcher latency | 3462.59 ms |
| Synthesizer latency | 3614.8 ms |
| Evaluator latency | 0.31 ms |

The failed live queries were caused by provider token limits, not benchmark logic. Resume a partial live run with:

```bash
PYTHONPATH=. python3 benchmarks/run_benchmark.py --start 30 --limit 21 --live --api-url http://127.0.0.1:8000 --delay-seconds 5
```

### Ablation study: multi-agent vs single-agent

Detailed ablation notes are in `docs/ablation_study.md`.

| Mode | Overall | Relevancy | Faithfulness | Completeness | Avg latency | Avg cost/query |
|------|--------:|----------:|-------------:|-------------:|------------:|---------------:|
| Multi-agent | 0.9541 | 1.0000 | 0.9900 | 0.8440 | 0.10 ms | $0.000799 |
| Single-agent baseline | 0.8678 | 1.0000 | 0.9306 | 0.6948 | 0.07 ms | $0.000603 |

The critic/evaluator stages improve faithfulness and completeness. The single-agent baseline is faster and cheaper. That tradeoff should stay visible.

## 🔎 Failure Analysis

Detailed failure analysis is in `docs/failure_analysis.md`.

Highest-risk failure modes:

| Failure mode | Impact | Mitigation |
|--------------|--------|------------|
| Irrelevant retrieval | Report answers the wrong question | Add reranking and tighter query generation |
| Unsupported claims | Hallucinated conclusions | Add sentence-level claim-source verification |
| Citation mismatch | False trust signal | Validate citations against nearby claims |
| Revision loop cost spike | Higher latency and cost | Cap loops and revise only missing evidence |
| Prompt injection from web pages | Corrupted synthesis | Treat retrieved content as untrusted data |

## 📡 Production Metrics

Production metrics are implemented in `src/observability/metrics.py`.

| Metric | Why it matters |
|--------|----------------|
| End-to-end latency | User-visible wait time |
| Per-agent latency | Shows bottlenecks across researcher, critic, synthesizer, evaluator |
| Estimated cost/query | Needed for pricing, rate limits, and budget control |
| Agent success/failure | Identifies fragile pipeline stages |
| Evaluation scores | Prevents cost optimization from degrading quality |

High-fit use cases: market scans, technical overviews, literature-style summaries, competitive intelligence drafts, and due-diligence briefs.

Poor-fit use cases without expert review: legal advice, medical advice, financial decisions, and real-time breaking-news claims.

## 🛠️ Tech Stack

- **LLM**: Llama 3.3 70B (Groq)
- **Search**: Tavily AI
- **Orchestration**: LangGraph
- **Vector DB**: ChromaDB
- **Evaluation**: RAGAS/DeepEval
- **Backend**: FastAPI
- **Frontend**: Streamlit
- **Deployment**: Docker, GitHub Actions

## 📁 Project Structure
```
├── app.py                 # Streamlit UI
├── src/
│   ├── graph/            # LangGraph state machine
│   ├── agents/           # Agent implementations
│   ├── vectordb/         # ChromaDB integration
│   ├── evaluation/       # RAGAS-style metrics
│   ├── observability/    # Production latency and cost metrics
│   ├── export/           # PDF/Markdown exporters
│   └── api/              # FastAPI backend
├── benchmarks/           # 50-query benchmark runner and query set
├── results/              # Saved benchmark and ablation outputs
├── docs/                 # Evaluation, ablation, failure analysis, and production metrics notes
├── tests/                # Test suite
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/    # CI/CD
```

## 📜 License

MIT
