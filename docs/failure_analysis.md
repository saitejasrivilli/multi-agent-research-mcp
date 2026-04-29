# Failure Analysis

This project is strongest as a portfolio-grade research assistant, not yet a hardened production research platform. The main risks are below.

| Failure mode | Likely cause | User impact | Detection signal | Mitigation |
|---|---|---|---|---|
| Irrelevant retrieval | Search query expansion is too broad or Tavily returns weak pages | Report answers the wrong question | Low relevancy score, low source overlap, user downvotes | Add hybrid retrieval, source reranking, and query-specific search constraints |
| Unsupported claims | Synthesizer writes beyond retrieved evidence | Hallucinated conclusions | Low faithfulness score, claims without source URLs | Force claim-source mapping before final answer |
| Citation mismatch | Current citation accuracy is mostly source-count based | Citations may look valid but not support the text | Manual spot checks fail | Add sentence-level citation validation |
| Revision loop cost spike | Critic quality threshold triggers repeated research | Higher latency and cost | High iteration count, high per-query cost | Cap loops and only revise specific missing evidence |
| Stale or low-quality web sources | Public search is the only default retrieval channel | Outdated or biased report | Source dates missing, conflicting sources | Add freshness filters and source quality scoring |
| JSON parsing failure | LLM returns malformed JSON | Empty findings or fallback report | Parse fallback path used | Use structured output / Pydantic validation and retries |
| API key or rate-limit failure | Missing or exhausted Groq/Tavily keys | Job errors | HTTP 401/429 or empty search results | Preflight key checks, retry/backoff, clearer UI errors |
| Vector DB optional path breaks | Chroma init or embedding model download fails | RAG context unavailable | Vector exception logs | Keep fallback to web-only mode and test Chroma separately |
| Prompt injection from web pages | Retrieved content contains malicious instructions | Rule bypass or corrupted synthesis | Suspicious instructions in source text | Treat source text as untrusted data and isolate it in prompts |
| Long-running request timeout | Sequential researcher → critic → synthesizer → evaluator calls | Poor UX and failed deployments | Timeout logs, abandoned sessions | Stream progress and add background job queue |

## Highest-priority fixes

1. Replace heuristic citation accuracy with claim-level source verification.
2. Add real live benchmark runs with saved raw outputs and model/search versions.
3. Add rate limiting and input limits before exposing the demo broadly.
4. Add durable job storage. The current API uses in-memory `jobs`, so restarts lose work.
5. Add tests for evaluator edge cases and JSON parsing failures.
