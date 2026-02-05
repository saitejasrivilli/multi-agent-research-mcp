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
│   ├── evaluation/       # RAGAS metrics
│   ├── export/           # PDF/Markdown exporters
│   └── api/              # FastAPI backend
├── tests/                # Test suite
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/    # CI/CD
```

## 📜 License

MIT
