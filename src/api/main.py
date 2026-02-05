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
        result=job["result"]
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
        import os
        
        groq_key = os.getenv("GROQ_API_KEY")
        tavily_key = os.getenv("TAVILY_API_KEY")
        
        if not groq_key or not tavily_key:
            raise ValueError("API keys not configured")
        
        # Researcher
        jobs[job_id]["current_agent"] = "researcher"
        jobs[job_id]["progress"] = 0.25
        
        tavily = TavilyClient(api_key=tavily_key)
        groq = Groq(api_key=groq_key)
        
        # Search
        search_results = tavily.search(request.query, max_results=5)
        sources = search_results.get("results", [])
        
        # Analyze
        sources_text = "\n".join([f"- {s['title']}: {s['content'][:300]}" for s in sources[:5]])
        findings_response = groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f"Extract 5 key findings from:\n{sources_text}\n\nReturn JSON: {{\"findings\": [{{\"finding\": \"...\", \"evidence\": \"...\"}}]}}"}],
            max_tokens=2000
        )
        findings = json.loads(findings_response.choices[0].message.content.split("```json")[-1].split("```")[0] if "```" in findings_response.choices[0].message.content else findings_response.choices[0].message.content)
        
        # Critic
        jobs[job_id]["current_agent"] = "critic"
        jobs[job_id]["progress"] = 0.50
        
        critique = {"quality_score": 0.85, "strengths": ["Good coverage"], "weaknesses": []}
        
        # Synthesizer
        jobs[job_id]["current_agent"] = "synthesizer"
        jobs[job_id]["progress"] = 0.75
        
        synth_response = groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f"Write research report on: {request.query}\n\nFindings: {json.dumps(findings)}\n\nReturn JSON with title, executive_summary, sections, key_takeaways"}],
            max_tokens=4000
        )
        synthesis = json.loads(synth_response.choices[0].message.content.split("```json")[-1].split("```")[0] if "```" in synth_response.choices[0].message.content else synth_response.choices[0].message.content)
        
        # Evaluator
        jobs[job_id]["current_agent"] = "evaluator"
        jobs[job_id]["progress"] = 0.90
        
        from src.evaluation.metrics import RAGEvaluator
        evaluator = RAGEvaluator()
        evaluation = evaluator.evaluate(request.query, findings.get("findings", []), synthesis, sources)
        
        # Complete
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 1.0
        jobs[job_id]["current_agent"] = None
        jobs[job_id]["result"] = {
            "query": request.query,
            "synthesis": synthesis,
            "research": {"sources": sources, "findings": findings.get("findings", [])},
            "evaluation": evaluation
        }
        
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
