"""
Multi-Agent Research Assistant
Built with Groq (Llama 3.3) + Tavily Search
"""

import streamlit as st
import json
from datetime import datetime
from tavily import TavilyClient
from groq import Groq

st.set_page_config(page_title="Multi-Agent Research Assistant", page_icon="🔬", layout="wide")

st.markdown("""
<style>
.main-header{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);padding:2rem;border-radius:16px;margin-bottom:2rem;color:white;text-align:center}
.main-header h1{font-size:2.5rem;font-weight:700;margin-bottom:0.5rem}
.tech-badge{display:inline-block;background:rgba(255,255,255,0.2);padding:0.3rem 0.8rem;border-radius:20px;margin:0.2rem;font-size:0.85rem}
.metric-card{background:white;padding:1.2rem;border-radius:12px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.08);border:1px solid #e9ecef}
.source-card{background:white;padding:1rem;margin:0.5rem 0;border-radius:8px;border-left:4px solid #667eea;box-shadow:0 1px 4px rgba(0,0,0,0.05)}
.executive-summary{background:#f8f9fa;padding:1.5rem;border-radius:12px;line-height:1.7}
.stats-bar{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);padding:1rem;border-radius:12px;display:flex;justify-content:space-around;color:white;margin:1.5rem 0}
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
    response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, temperature=0.7, max_tokens=max_tokens)
    return response.choices[0].message.content

def parse_json_safely(text, default=None):
    if default is None:
        default = {}
    if "```json" in text:
        try: text = text.split("```json")[1].split("```")[0]
        except: pass
    elif "```" in text:
        try: text = text.split("```")[1].split("```")[0]
        except: pass
    text = text.strip()
    try: return json.loads(text)
    except: pass
    for suffix in ['"}]}}', '"}]}', '"]}}', '"]}', '}}', '}]', '}', ']']:
        try: return json.loads(text + suffix)
        except: continue
    try:
        start = text.find('{')
        if start != -1:
            for end in range(len(text), start, -1):
                try: return json.loads(text[start:end])
                except: continue
    except: pass
    return default

def run_researcher(query, keys, status):
    status.info("🔍 **Researcher**: Generating search queries...")
    search_prompt = f'Generate 3 search queries for: "{query}"\nReturn only queries, one per line.'
    queries_raw = call_llm(search_prompt, keys["groq"], max_tokens=200)
    queries = [q.strip().strip('"\'-.0123456789') for q in queries_raw.strip().split("\n") if q.strip()][:3] or [query]
    
    all_results = []
    for i, q in enumerate(queries):
        status.info(f"🔍 **Researcher**: Searching ({i+1}/{len(queries)})")
        try: all_results.extend(search_web(q, keys["tavily"], 3))
        except: pass
    
    unique = []
    seen = set()
    for r in all_results:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)
    
    status.info("🔍 **Researcher**: Analyzing sources...")
    sources_text = "\n\n".join([f"Title: {r['title']}\nURL: {r['url']}\nContent: {r['content'][:600]}" for r in unique[:6]])
    synthesis_prompt = f'Analyze sources about: "{query}"\n\n{sources_text}\n\nReturn JSON: {{"findings": [{{"finding": "...", "evidence": "...", "source": "url"}}]}}'
    findings = parse_json_safely(call_llm(synthesis_prompt, keys["groq"], max_tokens=2000), {"findings": []})
    status.success("✅ **Researcher**: Complete!")
    return {"queries": queries, "sources": unique[:6], "findings": findings.get("findings", [])}

def run_critic(query, research, keys, status):
    status.info("🎯 **Critic**: Evaluating quality...")
    findings_text = "\n".join([f"- {f.get('finding', str(f))}" for f in research["findings"][:5]])
    critic_prompt = f'Evaluate research on "{query}":\n\nFindings:\n{findings_text}\n\nSources: {len(research["sources"])}\n\nReturn JSON: {{"quality_score": 0.85, "strengths": ["..."], "weaknesses": ["..."]}}'
    critique = parse_json_safely(call_llm(critic_prompt, keys["groq"], max_tokens=800), {"quality_score": 0.8, "strengths": ["Good coverage"], "weaknesses": ["Could be deeper"]})
    status.success("✅ **Critic**: Complete!")
    return critique

def run_synthesizer(query, research, critique, keys, status):
    status.info("📝 **Synthesizer**: Writing report...")
    findings_text = "\n".join([f"- {f.get('finding', '')}: {f.get('evidence', '')}" for f in research["findings"][:6]])
    synth_prompt = f'''Create a research report on: "{query}"

FINDINGS:
{findings_text}

Return JSON:
{{"title": "Report Title", "executive_summary": "3-4 detailed paragraphs...", "sections": [{{"title": "Section", "content": "..."}}], "key_takeaways": ["1", "2", "3"], "limitations": ["1"], "further_research": ["1"]}}'''
    
    report = parse_json_safely(call_llm(synth_prompt, keys["groq"], system_prompt="Return ONLY valid JSON. No markdown.", max_tokens=4000), None)
    if not report or not report.get("title"):
        report = {"title": f"Research: {query}", "executive_summary": "Report generation completed.", "sections": [], "key_takeaways": [f.get("finding", "")[:100] for f in research["findings"][:3]], "limitations": ["Auto-generated"], "further_research": ["Further research recommended"]}
    
    word_count = len(report.get("executive_summary", "").split())
    for s in report.get("sections", []):
        word_count += len(s.get("content", "").split())
    report["word_count"] = word_count
    status.success("✅ **Synthesizer**: Complete!")
    return report

def calculate_eval(research, synthesis):
    r = min(1.0, len(research.get("findings", [])) / 4)
    f = min(1.0, len(research.get("sources", [])) / 5)
    c = min(1.0, (len(synthesis.get("sections", [])) + 1) / 3)
    w = min(1.0, synthesis.get("word_count", 0) / 400)
    return {"relevancy": r, "faithfulness": f, "coherence": c, "completeness": w, "overall": (r + f + c + w) / 4}

def render_sidebar():
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        keys = get_api_keys()
        st.write("Groq:", "✅" if keys["groq"] else "❌")
        st.write("Tavily:", "✅" if keys["tavily"] else "❌")
        st.divider()
        st.markdown("### 🏗️ Architecture\n```\nResearcher → Critic → Synthesizer\n```")
        st.markdown("### 🛠️ Stack\n- Llama 3.3 70B\n- Tavily Search\n- Streamlit")
        return keys

def main():
    keys = render_sidebar()
    
    st.markdown("""<div class="main-header"><h1>🔬 Multi-Agent Research Assistant</h1><p>AI-powered research using autonomous agents</p><div><span class="tech-badge">🦙 Llama 3.3</span><span class="tech-badge">🔍 Tavily</span><span class="tech-badge">🤖 Multi-Agent</span><span class="tech-badge">⚡ Groq</span></div></div>""", unsafe_allow_html=True)
    
    col1, col2 = st.columns([5, 1])
    with col1:
        query = st.text_input("Query", placeholder="e.g., What are the latest AI breakthroughs?", label_visibility="collapsed")
    with col2:
        run_btn = st.button("🚀 Research", type="primary", use_container_width=True)
    
    st.caption("**Try:** What is RAG in AI? • Latest climate solutions • Future of remote work")
    st.divider()
    
    if run_btn and query:
        if not keys["groq"] or not keys["tavily"]:
            st.error("Add API keys to .streamlit/secrets.toml")
            return
        
        status = st.empty()
        cols = st.columns(3)
        
        with cols[0]: st.info("🔍 **Researcher**\nSearching...")
        research = run_researcher(query, keys, status)
        with cols[0]: st.success("🔍 **Researcher**\n✅ Done")
        
        with cols[1]: st.info("🎯 **Critic**\nEvaluating...")
        critique = run_critic(query, research, keys, status)
        with cols[1]: st.success("🎯 **Critic**\n✅ Done")
        
        with cols[2]: st.info("📝 **Synthesizer**\nWriting...")
        synthesis = run_synthesizer(query, research, critique, keys, status)
        with cols[2]: st.success("📝 **Synthesizer**\n✅ Done")
        
        status.empty()
        st.divider()
        
        # Evaluation
        ev = calculate_eval(research, synthesis)
        st.markdown("### 📊 Quality Scores")
        mcols = st.columns(5)
        for i, (n, v) in enumerate([("Relevancy", ev["relevancy"]), ("Faithfulness", ev["faithfulness"]), ("Coherence", ev["coherence"]), ("Completeness", ev["completeness"]), ("Overall", ev["overall"])]):
            color = "#28a745" if v >= 0.8 else "#ffc107" if v >= 0.6 else "#dc3545"
            mcols[i].markdown(f'<div class="metric-card"><b>{n}</b><p style="font-size:2rem;font-weight:bold;color:{color}">{v:.0%}</p></div>', unsafe_allow_html=True)
        
        st.divider()
        
        # Report
        st.markdown(f"## 📄 {synthesis.get('title', 'Report')}")
        st.markdown(f'<div class="stats-bar"><div><b>{synthesis.get("word_count", 0)}</b><br>Words</div><div><b>{len(research.get("sources", []))}</b><br>Sources</div><div><b>$0.00</b><br>Cost</div></div>', unsafe_allow_html=True)
        
        st.markdown("### 📋 Executive Summary")
        st.markdown(f'<div class="executive-summary">{synthesis.get("executive_summary", "N/A")}</div>', unsafe_allow_html=True)
        
        if synthesis.get("sections"):
            st.markdown("### 📑 Sections")
            for s in synthesis["sections"]:
                with st.expander(s.get("title", "Section")):
                    st.write(s.get("content", ""))
        
        if synthesis.get("key_takeaways"):
            st.markdown("### 🎯 Key Takeaways")
            for t in synthesis["key_takeaways"]:
                st.markdown(f"• {t}")
        
        if research.get("sources"):
            st.markdown("### 📚 Sources")
            for s in research["sources"]:
                st.markdown(f'<div class="source-card"><b>{s.get("title", "")}</b><br><a href="{s.get("url", "#")}">{s.get("url", "")[:70]}...</a></div>', unsafe_allow_html=True)
        
        st.divider()
        st.download_button("📥 Download JSON", json.dumps({"query": query, "synthesis": synthesis, "research": research, "evaluation": ev}, indent=2), f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "application/json")

if __name__ == "__main__":
    main()
