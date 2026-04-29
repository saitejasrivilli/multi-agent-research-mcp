from src.evaluation.metrics import RAGEvaluator
from src.observability.metrics import estimate_llm_cost, summarize_metrics


def test_evaluator_returns_overall_score():
    evaluator = RAGEvaluator()
    scores = evaluator.evaluate(
        "RAG evaluation",
        [{"finding": "RAG evaluation measures faithfulness", "evidence": "faithfulness and relevancy"}],
        {
            "title": "RAG evaluation",
            "executive_summary": "RAG evaluation measures whether generated answers are relevant and faithful to source evidence.",
            "sections": [{"title": "Metrics", "content": "Faithfulness and relevancy are core metrics."}],
            "key_takeaways": ["Faithfulness matters"],
            "word_count": 120,
        },
        [{"title": "Source", "url": "https://example.com/rag", "content": "RAG evaluation measures faithfulness and relevancy."}],
    )
    assert 0 <= scores["overall"] <= 1
    assert "grade" in scores


def test_cost_estimation_is_positive():
    assert estimate_llm_cost(1000, 1000) > 0


def test_metrics_summary_groups_agents():
    summary = summarize_metrics([
        {"total_latency_ms": 100, "total_cost_usd": 0.01, "agents": [{"agent": "researcher", "latency_ms": 40}]},
        {"total_latency_ms": 200, "total_cost_usd": 0.03, "agents": [{"agent": "researcher", "latency_ms": 60}]},
    ])
    assert summary["queries"] == 2
    assert summary["avg_latency_ms"] == 150
    assert summary["agent_latency_ms"]["researcher"] == 50
