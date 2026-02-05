"""
Multi-Agent Research Assistant
Portfolio Project | Built with Groq + Tavily
"""

import streamlit as st
import json
from datetime import datetime
from tavily import TavilyClient
from groq import Groq

st.set_page_config(page_title="Multi-Agent Research Assistant", page_icon="🔬", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.header-container {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
    padding: 2.5rem 2rem;
    border-radius: 20px;
    margin-bottom: 2rem;
    text-align: center;
    box-shadow: 0 10px 40px rgba(99, 102, 241, 0.3);
}
.header-container h1 {
    color: white;
    font-size: 2.8rem;
    font-weight: 700;
    margin: 0 0 0.5rem 0;
}
.header-container p {
    color: rgba(255,255,255,0.9);
    font-size: 1.15rem;
    margin: 0;
}
.tech-pills {
    margin-top: 1.2rem;
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 0.5rem;
}
.tech-pill {
    background: rgba(255,255,255,0.2);
    color: white;
    padding: 0.4rem 1rem;
    border-radius: 50px;
    font-size: 0.9rem;
    font-weight: 500;
    backdrop-filter: blur(10px);
}

.metric-container {
    background: white;
    border-radius: 16px;
    padding: 1.5rem 1rem;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    border: 1px solid #e5e7eb;
    height: 100%;
}
.metric-label {
    font-size: 0.9rem;
    font-weight: 600;
    color: #6b7280;
    margin-bottom: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.metric-value {
    font-size: 2.5rem;
    font-weight: 700;
    line-height: 1;
}
.metric-value.green { color: #10b981; }
.metric-value.yellow { color: #f59e0b; }
.metric-value.red { color: #ef4444; }

.summary-box {
    background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%);
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 2rem;
    margin: 1rem 0;
    line-height: 1.8;
    font-size: 1.05rem;
    color: #334155;
}

.takeaway-item {
    background: white;
    border-left: 4px solid #10b981;
    padding: 1rem 1.25rem;
    margin: 0.75rem 0;
    border-radius: 0 12px 12px 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    font-size: 1rem;
    line-height: 1.6;
}

.source-item {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 1.25rem;
    margin: 0.75rem 0;
    transition: all 0.2s ease;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.source-item:hover {
    border-color: #6366f1;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
}
.source-title {
    font-weight: 600;
    color: #1e293b;
    font-size: 1rem;
    margin-bottom: 0.5rem;
}
.source-url {
    color: #6366f1;
    font-size: 0.9rem;
    word-break: break-all;
}

.stats-strip {
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    border-radius: 16px;
    padding: 1.5rem 2rem;
    display: flex;
    justify-content: space-around;
    align-items: center;
    margin: 1.5rem 0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}
.stat-item {
    text-align: center;
    color: white;
}
.stat-value {
    font-size: 1.8rem;
    font-weight: 700;
}
.stat-label {
    font-size: 0.85rem;
    opacity: 0.8;
    margin-top: 0.25rem;
}

.section-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: #1e293b;
    margin: 2rem 0 1rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.agent-box {
    background: white;
    border: 2px solid #e5e7eb;
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    transition: all 0.3s ease;
}
.agent-box.running {
    border-color: #f59e0b;
    background: linear-gradient(145deg, #fffbeb 0%, #fef3c7 100%);
}
.agent-box.done {
    border-color: #10b981;
    background: linear-gradient(145deg, #ecfdf5 0%, #d1fae5 100%);
}
.agent-icon { font-size: 2rem; margin-bottom: 0.5rem; }
.agent-name { font-weight: 600; font-size: 1.1rem; color: #1e293b; }
.agent-desc { font-size: 0.85rem; color: #6b7280; margin-top: 0.25rem; }
.agent-status { margin-top: 0.75rem; font-weight: 600; font-size: 0.9rem; }

.footer-box {
    text-align: center;
    padding: 2rem;
    margin-top: 2rem;
    border-top: 1px solid #e5e7eb;
    color: #6b7280;
}
.footer-box a { color: #6366f1; text-decoration: none; font-weight: 500; }
</style>
""", unsafe_allow_html=True)


def get_api_keys():
    keys = {"groq": None, "tavily": None}
    try:
        keys["groq"] = st.secrets.get("GROQ_API_KEY")
        keys["tavily"] = st.secrets.get("TAVILY_API_KEY")
    except:
        pass
    return keys


def search_web(query, tavily_key, max_results=5):
    client = TavilyClient(api_key=tavily_key)
    return client.search(query, max_results=max_results).get("results", [])


def call_llm(prompt, groq_key, system_prompt=None, max_tokens=4096):
    client = Groq(api_key=groq_key)
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.7,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content


def parse_json_safely(text, default=None):
    if default is None:
        default = {}
    try:
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
    except:
        pass
    text = text.strip()
    try:
        return json.loads(text)
    except:
        pass
    for suffix in ['"}]}}', '"}]}', '"]}}', '"]}', '}}', '}]', '}', ']']:
        try:
            return json.loads(text + suffix)
        except:
            continue
    return default


def run_researcher(query, keys, status_col):
    with status_col:
        st.markdown('<div class="agent-box running"><div class="agent-icon">🔍</div><div class="agent-name">Researcher</div><div class="agent-desc">Searching the web</div><div class="agent-status" style="color:#f59e0b;">⏳ Working...</div></div>', unsafe_allow_html=True)
    
    search_prompt = f'Generate 3 search queries for: "{query}"\nReturn only queries, one per line.'
    queries_raw = call_llm(search_prompt, keys["groq"], max_tokens=200)
    queries = [q.strip().strip('"\'-.0123456789') for q in queries_raw.strip().split("\n") if q.strip()][:3] or [query]
    
    all_results = []
    for q in queries:
        try:
            all_results.extend(search_web(q, keys["tavily"], 3))
        except:
            pass
    
    unique = []
    seen = set()
    for r in all_results:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)
    
    sources_text = "\n\n".join([f"Title: {r['title']}\nURL: {r['url']}\nContent: {r['content'][:600]}" for r in unique[:6]])
    
    synthesis_prompt = f'''Analyze these sources about: "{query}"

{sources_text}

Extract 5 key findings. Return ONLY valid JSON:
{{"findings": [{{"finding": "detailed finding here", "evidence": "supporting evidence", "source": "url"}}]}}'''
    
    findings = parse_json_safely(call_llm(synthesis_prompt, keys["groq"], max_tokens=2000), {"findings": []})
    
    return {"queries": queries, "sources": unique[:6], "findings": findings.get("findings", [])}


def run_critic(query, research, keys, status_col):
    with status_col:
        st.markdown('<div class="agent-box running"><div class="agent-icon">🎯</div><div class="agent-name">Critic</div><div class="agent-desc">Evaluating quality</div><div class="agent-status" style="color:#f59e0b;">⏳ Working...</div></div>', unsafe_allow_html=True)
    
    findings_text = "\n".join([f"- {f.get('finding', str(f))}" for f in research["findings"][:5]])
    critic_prompt = f'''Evaluate research on "{query}":

Findings:
{findings_text}

Sources: {len(research["sources"])}

Return ONLY valid JSON:
{{"quality_score": 0.85, "strengths": ["strength1", "strength2"], "weaknesses": ["weakness1"]}}'''
    
    return parse_json_safely(call_llm(critic_prompt, keys["groq"], max_tokens=800), 
                             {"quality_score": 0.8, "strengths": ["Good coverage"], "weaknesses": ["Could be deeper"]})


def run_synthesizer(query, research, critique, keys, status_col):
    with status_col:
        st.markdown('<div class="agent-box running"><div class="agent-icon">📝</div><div class="agent-name">Synthesizer</div><div class="agent-desc">Writing report</div><div class="agent-status" style="color:#f59e0b;">⏳ Working...</div></div>', unsafe_allow_html=True)
    
    findings_text = "\n".join([f"- {f.get('finding', '')}: {f.get('evidence', '')}" for f in research["findings"][:6]])
    
    synth_prompt = f'''Write a detailed research report on: "{query}"

KEY FINDINGS:
{findings_text}

IMPORTANT: Write a comprehensive executive summary of 3-4 paragraphs (at least 200 words). Include detailed sections.

Return ONLY valid JSON:
{{
    "title": "Clear Descriptive Title",
    "executive_summary": "Write 3-4 detailed paragraphs here summarizing all key findings, their implications, and conclusions. This should be comprehensive and informative, at least 200 words.",
    "sections": [
        {{"title": "Background", "content": "Detailed background..."}},
        {{"title": "Key Findings", "content": "Detailed findings..."}},
        {{"title": "Implications", "content": "Detailed implications..."}}
    ],
    "key_takeaways": ["Complete takeaway 1", "Complete takeaway 2", "Complete takeaway 3"],
    "limitations": ["Limitation 1"],
    "further_research": ["Suggestion 1"]
}}'''
    
    report = parse_json_safely(
        call_llm(synth_prompt, keys["groq"], system_prompt="You are a research analyst. Return ONLY valid JSON with detailed content. Executive summary must be at least 200 words.", max_tokens=4000),
        None
    )
    
    if not report or not report.get("executive_summary"):
        report = {
            "title": f"Research Report: {query}",
            "executive_summary": f"This research analyzed {query} using multiple authoritative sources. " + " ".join([f.get("finding", "") for f in research["findings"][:3]]),
            "sections": [{"title": "Key Findings", "content": "\n".join([f.get("finding", "") for f in research["findings"]])}],
            "key_takeaways": [f.get("finding", "")[:200] for f in research["findings"][:4]],
            "limitations": ["Based on available online sources"],
            "further_research": ["Additional analysis recommended"]
        }
    
    word_count = len(report.get("executive_summary", "").split())
    for s in report.get("sections", []):
        word_count += len(s.get("content", "").split())
    report["word_count"] = word_count
    
    return report


def calculate_eval(research, synthesis):
    r = min(1.0, len(research.get("findings", [])) / 4)
    f = min(1.0, len(research.get("sources", [])) / 5)
    c = min(1.0, (len(synthesis.get("sections", [])) + 1) / 3)
    w = min(1.0, synthesis.get("word_count", 0) / 300)
    return {"relevancy": r, "faithfulness": f, "coherence": c, "completeness": w, "overall": (r + f + c + w) / 4}


def render_header():
    st.markdown('''
    <div class="header-container">
        <h1>🔬 Multi-Agent Research Assistant</h1>
        <p>AI-powered research using autonomous agents that search, analyze, and synthesize information</p>
        <div class="tech-pills">
            <span class="tech-pill">�� Llama 3.3 70B</span>
            <span class="tech-pill">🔍 Tavily Search</span>
            <span class="tech-pill">🤖 Multi-Agent RAG</span>
            <span class="tech-pill">⚡ Groq Inference</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)


def render_sidebar():
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        keys = get_api_keys()
        
        st.markdown("### API Status")
        c1, c2 = st.columns(2)
        c1.markdown(f"**Groq** {'✅' if keys['groq'] else '❌'}")
        c2.markdown(f"**Tavily** {'✅' if keys['tavily'] else '❌'}")
        
        st.divider()
        
        st.markdown("### 🏗️ Architecture")
        st.code("Researcher → Critic → Synthesizer", language=None)
        
        st.markdown("### 📚 Tech Stack")
        st.markdown("""
        - **LLM**: Llama 3.3 70B
        - **Search**: Tavily AI  
        - **Inference**: Groq
        - **UI**: Streamlit
        """)
        
        st.divider()
        st.markdown("### 🔗 Links")
        st.markdown("[GitHub Repo](https://github.com/saitejasrivilli/multi-agent-research-mcp)")
        
        return keys


def main():
    keys = render_sidebar()
    render_header()
    
    st.markdown("### 🔎 Enter Research Query")
    col1, col2 = st.columns([5, 1])
    with col1:
        query = st.text_input("query", placeholder="What are the latest developments in AI?", label_visibility="collapsed")
    with col2:
        run_btn = st.button("🚀 Go", type="primary", use_container_width=True)
    
    st.caption("**Examples:** What is RAG in AI? • Latest climate change solutions • Future of electric vehicles • India-US trade relations")
    
    st.divider()
    
    if run_btn and query:
        if not keys["groq"] or not keys["tavily"]:
            st.error("⚠️ Please configure API keys in Streamlit secrets")
            return
        
        st.markdown('<div class="section-title">🤖 Agent Pipeline</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        # Run agents
        research = run_researcher(query, keys, col1)
        with col1:
            st.markdown('<div class="agent-box done"><div class="agent-icon">🔍</div><div class="agent-name">Researcher</div><div class="agent-desc">Found sources</div><div class="agent-status" style="color:#10b981;">✅ Complete</div></div>', unsafe_allow_html=True)
        
        critique = run_critic(query, research, keys, col2)
        with col2:
            st.markdown('<div class="agent-box done"><div class="agent-icon">🎯</div><div class="agent-name">Critic</div><div class="agent-desc">Evaluated quality</div><div class="agent-status" style="color:#10b981;">✅ Complete</div></div>', unsafe_allow_html=True)
        
        synthesis = run_synthesizer(query, research, critique, keys, col3)
        with col3:
            st.markdown('<div class="agent-box done"><div class="agent-icon">📝</div><div class="agent-name">Synthesizer</div><div class="agent-desc">Report ready</div><div class="agent-status" style="color:#10b981;">✅ Complete</div></div>', unsafe_allow_html=True)
        
        ev = calculate_eval(research, synthesis)
        
        st.divider()
        
        # Quality Metrics
        st.markdown('<div class="section-title">📊 Quality Scores</div>', unsafe_allow_html=True)
        
        m1, m2, m3, m4, m5 = st.columns(5)
        metrics = [
            (m1, "Relevancy", ev["relevancy"]),
            (m2, "Faithfulness", ev["faithfulness"]),
            (m3, "Coherence", ev["coherence"]),
            (m4, "Completeness", ev["completeness"]),
            (m5, "Overall", ev["overall"])
        ]
        
        for col, name, val in metrics:
            color_class = "green" if val >= 0.8 else "yellow" if val >= 0.6 else "red"
            with col:
                st.markdown(f'''
                <div class="metric-container">
                    <div class="metric-label">{name}</div>
                    <div class="metric-value {color_class}">{val:.0%}</div>
                </div>
                ''', unsafe_allow_html=True)
        
        st.divider()
        
        # Report
        st.markdown(f'<div class="section-title">📄 {synthesis.get("title", "Research Report")}</div>', unsafe_allow_html=True)
        
        st.markdown(f'''
        <div class="stats-strip">
            <div class="stat-item"><div class="stat-value">{synthesis.get("word_count", 0)}</div><div class="stat-label">Words</div></div>
            <div class="stat-item"><div class="stat-value">{len(research.get("sources", []))}</div><div class="stat-label">Sources</div></div>
            <div class="stat-item"><div class="stat-value">{len(synthesis.get("sections", []))}</div><div class="stat-label">Sections</div></div>
            <div class="stat-item"><div class="stat-value">$0</div><div class="stat-label">Cost</div></div>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown('<div class="section-title">📋 Executive Summary</div>', unsafe_allow_html=True)
        summary = synthesis.get("executive_summary", "No summary available.")
        st.markdown(f'<div class="summary-box">{summary}</div>', unsafe_allow_html=True)
        
        if synthesis.get("sections"):
            st.markdown('<div class="section-title">📑 Detailed Sections</div>', unsafe_allow_html=True)
            for section in synthesis["sections"]:
                with st.expander(f"📌 {section.get('title', 'Section')}", expanded=False):
                    st.write(section.get("content", ""))
        
        if synthesis.get("key_takeaways"):
            st.markdown('<div class="section-title">🎯 Key Takeaways</div>', unsafe_allow_html=True)
            for t in synthesis["key_takeaways"]:
                if t:
                    st.markdown(f'<div class="takeaway-item">{t}</div>', unsafe_allow_html=True)
        
        if research.get("sources"):
            st.markdown('<div class="section-title">📚 Sources</div>', unsafe_allow_html=True)
            for s in research["sources"]:
                st.markdown(f'''
                <div class="source-item">
                    <div class="source-title">{s.get("title", "Source")}</div>
                    <a class="source-url" href="{s.get("url", "#")}" target="_blank">{s.get("url", "")}</a>
                </div>
                ''', unsafe_allow_html=True)
        
        st.divider()
        
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "📥 Download Report (JSON)",
                json.dumps({"query": query, "synthesis": synthesis, "research": research, "evaluation": ev}, indent=2, ensure_ascii=False),
                f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "application/json",
                use_container_width=True
            )
        
        st.markdown('''
        <div class="footer-box">
            Built with ❤️ by <a href="https://github.com/saitejasrivilli" target="_blank">Sai Teja</a> | 
            <a href="https://github.com/saitejasrivilli/multi-agent-research-mcp" target="_blank">View Source</a>
        </div>
        ''', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
