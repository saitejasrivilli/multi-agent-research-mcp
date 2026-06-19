# Multi-Agent Research Assistant Frontend

Next.js + TypeScript frontend for the multi-agent research system.

## Features

- **Real-time progress tracking** — See which agent is running (Researcher → Critic → Synthesizer → Evaluator)
- **Live job polling** — Stream updates from FastAPI backend
- **Rich result display** — Synthesis, sections, key takeaways, sources, findings
- **Quality metrics** — RAGAS evaluation scores (Relevancy, Faithfulness, Coherence, etc.)
- **Export options** — Download as PDF or Markdown with citations
- **Dark theme** — Modern Tailwind UI with Slate + Indigo colors

## Local Development

```bash
# Install
npm install

# Setup environment
cp .env.local.example .env.local
# Edit .env.local if backend is on different port

# Run dev server
npm run dev

# Open http://localhost:3000
```

## Building

```bash
npm run build
npm start
```

## Deployment to Vercel

### Option 1: CLI Deploy

```bash
npm install -g vercel
vercel login
vercel --prod
```

### Option 2: Git Auto-Deploy

1. Push to GitHub:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/multi-agent-research-mcp.git
   git push -u origin main
   ```

2. In [Vercel Dashboard](https://vercel.com/dashboard):
   - Click "New Project"
   - Import GitHub repo
   - Set root directory: `frontend`
   - Environment: `NEXT_PUBLIC_API_URL=<your-api-url>`
   - Deploy

### Environment Variables

- **`NEXT_PUBLIC_API_URL`** — Backend API URL (e.g., `https://api.example.com` or `http://localhost:8000`)
  - Must be public (used from browser)
  - Default: `http://localhost:8000`

## API Endpoints Used

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/research` | Start a new research job |
| GET | `/api/research/{job_id}` | Get job status & result |
| GET | `/api/research/{job_id}/export/pdf` | Download as PDF |
| GET | `/api/research/{job_id}/export/markdown` | Download as Markdown |

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Hosting**: Vercel
