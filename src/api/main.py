"""
FastAPI Backend for Multi-Agent Research Assistant
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import json
import uuid
import re
from datetime import datetime

app = FastAPI(
    title="Multi-Agent Research API",
    description="AI-powered research using autonomous agents",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job storage (use Redis in production)
jobs = {}

class ResearchRequest(BaseModel):
    query: str
    max_iterations: int = 2
    citation_format: str = "apa"
    include_vector_search: bool = True

class ResearchResponse(BaseModel):
    job_id: str
    status: str
    message: str

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: float
    current_agent: Optional[str]
    result: Optional[dict]
    error: Optional[str] = None


def parse_llm_json(content: Optional[str]) -> dict:
    """Parse common LLM JSON response shapes, including fenced blocks."""
    if not content or not content.strip():
        raise ValueError("LLM returned an empty response")

    text = content.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


def fallback_findings(query: str, sources: List[dict]) -> dict:
    findings = []
    for source in sources[:5]:
        content = source.get("content") or source.get("snippet") or ""
        findings.append({
            "finding": f"{source.get('title', 'Source')} provides context for {query}.",
            "evidence": content[:500],
            "source": source.get("url", ""),
        })
    return {"findings": findings}


def fallback_synthesis(query: str, findings: List[dict], sources: List[dict]) -> dict:
    summary = " ".join(f.get("finding", "") for f in findings[:3]).strip()
    if not summary:
        summary = f"Research completed for {query}, but the model did not return structured synthesis."
    return {
        "title": f"Research Brief: {query}",
        "executive_summary": summary,
        "sections": [
            {
                "title": "Findings",
                "content": "\n".join(f"- {f.get('finding', '')}" for f in findings) or summary,
            },
            {
                "title": "Sources",
                "content": "\n".join(f"- {s.get('title', 'Source')}: {s.get('url', '')}" for s in sources[:5]),
            },
            {
                "title": "Limitations",
                "content": "This fallback report was generated because the model did not return valid JSON.",
            },
        ],
        "key_takeaways": [f.get("finding", "") for f in findings[:3] if f.get("finding")] or [summary],
        "limitations": ["Model response required fallback parsing."],
        "further_research": ["Re-run live benchmark and inspect raw model responses if fallbacks persist."],
        "word_count": len(summary.split()),
    }


def normalize_synthesis(query: str, synthesis: dict, findings: List[dict], sources: List[dict]) -> dict:
    """Coerce loose model JSON into the shape expected by exporters/evaluators."""
    if not isinstance(synthesis, dict):
        return fallback_synthesis(query, findings, sources)

    normalized = dict(synthesis)
    normalized.setdefault("title", f"Research Brief: {query}")

    executive_summary = normalized.get("executive_summary") or normalized.get("summary")
    if not isinstance(executive_summary, str) or not executive_summary.strip():
        executive_summary = " ".join(f.get("finding", "") for f in findings[:3] if isinstance(f, dict)).strip()
    normalized["executive_summary"] = executive_summary or f"Research summary for {query}."

    sections = normalized.get("sections", [])
    if isinstance(sections, dict):
        sections = [{"title": str(title), "content": str(content)} for title, content in sections.items()]
    elif isinstance(sections, list):
        coerced_sections = []
        for idx, section in enumerate(sections, start=1):
            if isinstance(section, dict):
                coerced_sections.append({
                    "title": str(section.get("title") or f"Section {idx}"),
                    "content": str(section.get("content") or section.get("text") or section.get("body") or ""),
                })
            else:
                coerced_sections.append({"title": f"Section {idx}", "content": str(section)})
        sections = coerced_sections
    else:
        sections = []
    if not sections:
        sections = fallback_synthesis(query, findings, sources)["sections"]
    normalized["sections"] = sections

    takeaways = normalized.get("key_takeaways", [])
    if isinstance(takeaways, str):
        takeaways = [takeaways]
    elif not isinstance(takeaways, list):
        takeaways = []
    normalized["key_takeaways"] = [str(item) for item in takeaways if str(item).strip()] or [
        f.get("finding", "") for f in findings[:3] if isinstance(f, dict) and f.get("finding")
    ]

    for key in ["limitations", "further_research"]:
        value = normalized.get(key, [])
        if isinstance(value, str):
            value = [value]
        elif not isinstance(value, list):
            value = []
        normalized[key] = [str(item) for item in value if str(item).strip()]

    word_count = normalized.get("word_count")
    if not isinstance(word_count, int):
        section_words = sum(len(section.get("content", "").split()) for section in normalized["sections"])
        normalized["word_count"] = section_words + len(normalized["executive_summary"].split())

    return normalized

@app.get("/")
async def root():
    return {
        "name": "Multi-Agent Research API",
        "version": "2.0.0",
        "endpoints": {
            "research": "/api/research",
            "status": "/api/research/{job_id}",
            "stream": "/api/research/{job_id}/stream",
            "export_pdf": "/api/research/{job_id}/export/pdf",
            "export_md": "/api/research/{job_id}/export/markdown"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/research", response_model=ResearchResponse)
async def create_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """Start a new research job."""
    job_id = str(uuid.uuid4())
    
    jobs[job_id] = {
        "status": "pending",
        "progress": 0.0,
        "current_agent": None,
        "query": request.query,
        "result": None,
        "created_at": datetime.now().isoformat()
    }
    
    # Add background task to run research
    background_tasks.add_task(run_research_job, job_id, request)
    
    return ResearchResponse(
        job_id=job_id,
        status="pending",
        message="Research job created. Poll /api/research/{job_id} for status."
    )

@app.get("/api/research/{job_id}", response_model=JobStatus)
async def get_research_status(job_id: str):
    """Get status of a research job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        current_agent=job["current_agent"],
        result=job["result"],
        error=job.get("error")
    )

@app.get("/api/research/{job_id}/stream")
async def stream_research(job_id: str):
    """Stream research progress using SSE."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    async def event_generator():
        while True:
            job = jobs.get(job_id, {})
            data = {
                "status": job.get("status"),
                "progress": job.get("progress"),
                "current_agent": job.get("current_agent")
            }
            yield f"data: {json.dumps(data)}\n\n"
            
            if job.get("status") in ["completed", "error"]:
                break
            
            await asyncio.sleep(0.5)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

@app.get("/api/research/{job_id}/export/markdown")
async def export_markdown(job_id: str, citation_format: str = "apa"):
    """Export research as Markdown."""
    if job_id not in jobs or not jobs[job_id].get("result"):
        raise HTTPException(status_code=404, detail="Job not found or not completed")
    
    from src.export.exporters import MarkdownExporter
    
    result = jobs[job_id]["result"]
    md = MarkdownExporter.generate(
        result["synthesis"],
        result["research"],
        result["evaluation"],
        citation_format
    )
    
    return StreamingResponse(
        iter([md]),
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=research_{job_id[:8]}.md"}
    )

@app.get("/api/research/{job_id}/export/pdf")
async def export_pdf(job_id: str):
    """Export research as PDF."""
    if job_id not in jobs or not jobs[job_id].get("result"):
        raise HTTPException(status_code=404, detail="Job not found or not completed")
    
    from src.export.exporters import PDFExporter
    
    result = jobs[job_id]["result"]
    pdf_bytes = PDFExporter().generate(
        result["synthesis"],
        result["research"],
        result["evaluation"]
    )
    
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=research_{job_id[:8]}.pdf"}
    )

async def run_research_job(job_id: str, request: ResearchRequest):
    """Background task to run research pipeline."""
    try:
        jobs[job_id]["status"] = "running"
        
        # Import here to avoid circular imports
        from groq import Groq
        from tavily import TavilyClient
        from dotenv import load_dotenv
        import os

        load_dotenv()
        
        groq_key = os.getenv("GROQ_API_KEY")
        tavily_key = os.getenv("TAVILY_API_KEY")
        
        if not groq_key or not tavily_key:
            raise ValueError("API keys not configured")

        from src.observability.metrics import MetricsCollector, estimate_tokens
        collector = MetricsCollector(request.query)
        
        # Researcher
        jobs[job_id]["current_agent"] = "researcher"
        jobs[job_id]["progress"] = 0.25
        
        tavily = TavilyClient(api_key=tavily_key)
        groq = Groq(api_key=groq_key)
        
        with collector.agent_timer("researcher", input_tokens=estimate_tokens(request.query), output_tokens=2000):
            search_results = tavily.search(request.query, max_results=5)
            sources = search_results.get("results", [])
            
            sources_text = "\n".join([f"- {s['title']}: {s['content'][:300]}" for s in sources[:5]])
            findings_response = groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f"Extract 5 key findings from:\n{sources_text}\n\nReturn only valid JSON with this schema: {{\"findings\": [{{\"finding\": \"...\", \"evidence\": \"...\", \"source\": \"...\"}}]}}"}],
                max_tokens=2000
            )
            try:
                findings = parse_llm_json(findings_response.choices[0].message.content)
            except (json.JSONDecodeError, ValueError):
                findings = fallback_findings(request.query, sources)
        
        # Critic
        jobs[job_id]["current_agent"] = "critic"
        jobs[job_id]["progress"] = 0.50
        
        with collector.agent_timer("critic", input_tokens=estimate_tokens(findings), output_tokens=80):
            critique = {"quality_score": 0.85, "strengths": ["Good coverage"], "weaknesses": []}
        
        # Synthesizer
        jobs[job_id]["current_agent"] = "synthesizer"
        jobs[job_id]["progress"] = 0.75
        
        with collector.agent_timer("synthesizer", input_tokens=estimate_tokens(findings), output_tokens=4000):
            synth_response = groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f"Write research report on: {request.query}\n\nFindings: {json.dumps(findings)}\n\nReturn only valid JSON with title, executive_summary, sections, key_takeaways, limitations, further_research, and word_count."}],
                max_tokens=4000
            )
            try:
                synthesis = parse_llm_json(synth_response.choices[0].message.content)
            except (json.JSONDecodeError, ValueError):
                synthesis = fallback_synthesis(request.query, findings.get("findings", []), sources)
            synthesis = normalize_synthesis(request.query, synthesis, findings.get("findings", []), sources)
        
        # Evaluator
        jobs[job_id]["current_agent"] = "evaluator"
        jobs[job_id]["progress"] = 0.90
        
        from src.evaluation.metrics import RAGEvaluator
        with collector.agent_timer("evaluator", input_tokens=estimate_tokens(synthesis), output_tokens=80):
            evaluator = RAGEvaluator()
            evaluation = evaluator.evaluate(request.query, findings.get("findings", []), synthesis, sources)
        production_metrics = collector.finalize().to_dict()
        
        # Complete
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 1.0
        jobs[job_id]["current_agent"] = None
        jobs[job_id]["result"] = {
            "query": request.query,
            "synthesis": synthesis,
            "research": {"sources": sources, "findings": findings.get("findings", [])},
            "evaluation": evaluation,
            "production_metrics": production_metrics
        }
        
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
