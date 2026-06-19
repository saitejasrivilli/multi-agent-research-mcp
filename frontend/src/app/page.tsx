'use client';

import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, Loader, Download, Search } from 'lucide-react';

interface Finding {
  finding: string;
  evidence: string;
  source: string;
}

interface ResearchJob {
  job_id: string;
  status: string;
  progress: number;
  current_agent?: string;
  error?: string;
  result?: {
    query: string;
    synthesis: {
      title: string;
      executive_summary: string;
      sections: Array<{ title: string; content: string }>;
      key_takeaways: string[];
      limitations: string[];
      further_research: string[];
      word_count: number;
    };
    research: {
      sources: Array<any>;
      findings: Finding[];
    };
    evaluation: any;
    production_metrics: any;
  };
}

export default function Home() {
  const [query, setQuery] = useState('');
  const [job, setJob] = useState<ResearchJob | null>(null);
  const [loading, setLoading] = useState(false);
  const [apiUrl] = useState('http://localhost:8000');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [job]);

  const startResearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      const response = await fetch(`${apiUrl}/api/research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          max_iterations: 2,
          citation_format: 'apa',
          include_vector_search: true,
        }),
      });

      if (!response.ok) throw new Error('Failed to start research');
      const data = await response.json();
      setJob({ job_id: data.job_id, status: 'pending', progress: 0 });

      // Poll for status updates
      pollJobStatus(data.job_id);
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to start research');
      setLoading(false);
    }
  };

  const pollJobStatus = async (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${apiUrl}/api/research/${jobId}`);
        if (!response.ok) throw new Error('Failed to fetch status');
        const status = await response.json();

        setJob(status);

        if (status.status === 'completed' || status.status === 'error') {
          clearInterval(interval);
          setLoading(false);
        }
      } catch (error) {
        console.error('Polling error:', error);
        clearInterval(interval);
        setLoading(false);
      }
    }, 500);
  };

  const exportToPDF = async () => {
    if (!job?.job_id) return;
    try {
      const response = await fetch(
        `${apiUrl}/api/research/${job.job_id}/export/pdf`
      );
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `research_${job.job_id.slice(0, 8)}.pdf`;
      a.click();
    } catch (error) {
      console.error('Export error:', error);
    }
  };

  const exportToMarkdown = async () => {
    if (!job?.job_id) return;
    try {
      const response = await fetch(
        `${apiUrl}/api/research/${job.job_id}/export/markdown`
      );
      const text = await response.text();
      const blob = new Blob([text], { type: 'text/markdown' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `research_${job.job_id.slice(0, 8)}.md`;
      a.click();
    } catch (error) {
      console.error('Export error:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <div className="border-b border-slate-700 bg-slate-800/50 backdrop-blur">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <div className="flex items-center gap-3 mb-2">
            <MessageCircle className="w-8 h-8 text-indigo-400" />
            <h1 className="text-3xl font-bold text-white">Research Assistant</h1>
          </div>
          <p className="text-slate-300">Multi-agent RAG with Groq + Tavily</p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 py-8">
        {!job ? (
          // Initial State
          <div className="space-y-8">
            {/* Search Form */}
            <div className="bg-slate-800 rounded-lg border border-slate-700 p-8 shadow-lg">
              <form onSubmit={startResearch} className="space-y-4">
                <div className="relative">
                  <Search className="absolute left-3 top-3 w-5 h-5 text-slate-400" />
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="What would you like to research?"
                    className="w-full bg-slate-700 border border-slate-600 rounded-lg pl-10 pr-4 py-3 text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
                <button
                  type="submit"
                  disabled={!query.trim() || loading}
                  className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-600 text-white font-medium py-3 rounded-lg transition"
                >
                  {loading ? 'Starting Research...' : 'Start Research'}
                </button>
              </form>
            </div>

            {/* Info Cards */}
            <div className="grid md:grid-cols-3 gap-4">
              {[
                {
                  title: 'Multi-Agent',
                  desc: 'Researcher, Critic, Synthesizer agents',
                },
                { title: 'Web Search', desc: 'Real-time Tavily AI search' },
                { title: 'Evaluation', desc: 'RAGAS-style quality metrics' },
              ].map((card) => (
                <div
                  key={card.title}
                  className="bg-slate-800 rounded-lg border border-slate-700 p-6"
                >
                  <h3 className="font-semibold text-white mb-2">{card.title}</h3>
                  <p className="text-slate-400 text-sm">{card.desc}</p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          // Research State
          <div className="space-y-6">
            {/* Progress Bar */}
            <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-white font-medium">{job.current_agent || 'Preparing'}</span>
                  <span className="text-slate-400 text-sm">{Math.round(job.progress * 100)}%</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div
                    className="bg-indigo-500 h-2 rounded-full transition-all"
                    style={{ width: `${job.progress * 100}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Status */}
            {job.status === 'running' && (
              <div className="flex items-center gap-3 bg-slate-800 rounded-lg border border-slate-700 p-4">
                <Loader className="w-5 h-5 text-indigo-400 animate-spin" />
                <span className="text-slate-300">
                  {job.current_agent && `Running ${job.current_agent}...`}
                </span>
              </div>
            )}

            {/* Results */}
            {job.status === 'completed' && job.result && (
              <div className="space-y-6">
                {/* Summary */}
                <div className="bg-slate-800 rounded-lg border border-slate-700 p-8">
                  <h2 className="text-2xl font-bold text-white mb-4">
                    {job.result.synthesis.title}
                  </h2>
                  <p className="text-slate-300 leading-relaxed">
                    {job.result.synthesis.executive_summary}
                  </p>
                </div>

                {/* Sections */}
                {job.result.synthesis.sections.map((section, i) => (
                  <div
                    key={i}
                    className="bg-slate-800 rounded-lg border border-slate-700 p-6"
                  >
                    <h3 className="text-lg font-semibold text-white mb-3">
                      {section.title}
                    </h3>
                    <div className="text-slate-300 whitespace-pre-wrap">
                      {section.content}
                    </div>
                  </div>
                ))}

                {/* Key Takeaways */}
                <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
                  <h3 className="text-lg font-semibold text-white mb-3">
                    Key Takeaways
                  </h3>
                  <ul className="space-y-2">
                    {job.result.synthesis.key_takeaways.map((item, i) => (
                      <li key={i} className="text-slate-300 flex gap-2">
                        <span className="text-indigo-400">•</span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Sources & Findings */}
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
                    <h3 className="text-lg font-semibold text-white mb-3">
                      Sources
                    </h3>
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {job.result.research.sources.slice(0, 5).map((source, i) => (
                        <a
                          key={i}
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-indigo-400 hover:text-indigo-300 text-sm break-all"
                        >
                          {source.title}
                        </a>
                      ))}
                    </div>
                  </div>

                  <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
                    <h3 className="text-lg font-semibold text-white mb-3">
                      Findings
                    </h3>
                    <div className="space-y-3 max-h-96 overflow-y-auto">
                      {job.result.research.findings.slice(0, 5).map((finding, i) => (
                        <div key={i} className="text-sm">
                          <p className="text-indigo-400 font-medium">
                            {finding.finding}
                          </p>
                          <p className="text-slate-400 text-xs mt-1">
                            {finding.evidence.slice(0, 100)}...
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Export Buttons */}
                <div className="flex gap-4 justify-center">
                  <button
                    onClick={exportToPDF}
                    className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-lg transition"
                  >
                    <Download className="w-4 h-4" />
                    PDF
                  </button>
                  <button
                    onClick={exportToMarkdown}
                    className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-lg transition"
                  >
                    <Download className="w-4 h-4" />
                    Markdown
                  </button>
                </div>

                {/* Metrics */}
                {job.result.evaluation && (
                  <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">
                      Quality Metrics
                    </h3>
                    <div className="grid md:grid-cols-5 gap-4">
                      {Object.entries(job.result.evaluation).map(
                        ([key, value]: [string, any]) => (
                          <div key={key} className="text-center">
                            <p className="text-slate-400 text-sm capitalize">
                              {key.replace(/_/g, ' ')}
                            </p>
                            <p className="text-white text-lg font-bold mt-1">
                              {typeof value === 'number'
                                ? value.toFixed(2)
                                : value}
                            </p>
                          </div>
                        )
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {job.status === 'error' && (
              <div className="bg-red-900/20 border border-red-700 rounded-lg p-4">
                <p className="text-red-300">
                  Error: {job.error || 'Unknown error'}
                </p>
              </div>
            )}

            {/* Back Button */}
            <button
              onClick={() => {
                setJob(null);
                setQuery('');
              }}
              className="w-full bg-slate-700 hover:bg-slate-600 text-white font-medium py-3 rounded-lg transition"
            >
              Start New Research
            </button>
          </div>
        )}
      </div>

      <div ref={messagesEndRef} />
    </div>
  );
}
