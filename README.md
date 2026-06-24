# CodeReviewer

Paste a GitHub repository URL and get a structured engineering review across architecture, security, code quality, and testing.

## What It Does

CodeReviewer fetches a public GitHub repository, samples and filters files, then runs a LangGraph-based review pipeline that scores the repo and produces prioritized fixes.

The current pipeline is partially agentic:
- it fetches repository contents with PyGithub
- routes analysis based on repo structure
- runs independent analysis nodes in parallel
- uses a tool-using security agent with a small investigate loop
- synthesizes the final verdict into a structured JSON report

## Current Architecture

```txt
Browser (Next.js)
    |
    |  HTTP / WebSocket
    v
FastAPI (Python)
    |
    +-- Auth + review API
    |
    +-- GitHub fetch layer (PyGithub)
    |     - fetch default branch
    |     - fetch recursive tree
    |     - fetch file contents
    |     - skip binaries / large files
    |
    +-- LangGraph review pipeline
          |
          +-- Fetcher
          +-- Router
          |     decides which agents to run
          |
          +-- Structure Agent   \
          +-- Security Agent     > runs in parallel after fetch
          +-- Quality Agent     /
          +-- Testing Agent
          |
          +-- Synthesizer
                produces final report
```

## Why It Is More Than A Prompt Wrapper

This project is not just a single prompt over a repo dump.

It currently includes:
- a graph-based workflow
- repo-local tool use (`list_files`, `get_file`, `search_code`)
- routing decisions after fetch
- a security investigate loop (`think -> choose tool -> observe -> continue/finish`)
- validated structured outputs for agent findings

It is still early-stage agentic, not fully autonomous.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI |
| Graph Orchestration | LangGraph |
| GitHub Fetch | PyGithub |
| LLM | Hugging Face Router API or Ollama |
| Frontend | Next.js 16 |
| Styling | Tailwind CSS |
| Database | SQLite (dev) |
| Auth | JWT |
| Observability | Structured JSON logging |
| DevOps | Docker Compose + GitHub Actions |

## Report Shape

Each analysis returns a structured report like:

```json
{
  "overall_score": 76,
  "files_analyzed": 50,
  "mega_verdict": "Promising codebase with clear improvement paths.",
  "dimensions": {
    "structure": {
      "score": 85,
      "findings": [
        {
          "file": "backend/src/api/main.py",
          "reason": "Potential lack of separation between API routes and business logic",
          "evidence_snippet": "main.py appears to mix route and application logic",
          "severity": "medium",
          "confidence": 0.7
        }
      ],
      "flagged_files": ["backend/src/api/main.py"],
      "recommendations": ["Split route handlers from service logic"]
    }
  },
  "top_3_fixes": [
    "Refactor route handlers to reduce cross-layer coupling",
    "Add higher-value tests for critical flows",
    "Improve secrets/config handling"
  ],
  "summary": "Good foundation but several areas need attention."
}
```

## Backend Features Implemented

- JWT register/login/me flow
- structured JSON logging with correlation IDs
- CORS for local frontend
- PyGithub repository fetching
- binary and oversized file skipping
- parallel post-fetch analysis nodes
- persisted analysis history in SQLite
- WebSocket analysis streaming endpoint
- validated evidence-based findings schema
- Dockerized backend and frontend
- GitHub Actions CI for backend, frontend, and image builds
- Langfuse tracing on the live analysis pipeline

## Local Setup

### Prerequisites

- Python 3.10+
- Node 18+

### Backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `.env` at repo root and set at minimum:

```env
JWT_SECRET=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXP_MINUTES=60
DATABASE_URL=sqlite:///./codereviewer.db
APP_NAME=CodeReviewer

GITHUB_TOKEN=your_github_token

LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com

LLM_PROVIDER=huggingface
LLM_MODEL=deepseek-ai/DeepSeek-V3-0324:novita
HF_TOKEN=your_huggingface_token
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=1024
```

Run backend:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open:

- `http://localhost:3000`

## Docker Setup

Copy the example environment file and fill in your real tokens:

```powershell
Copy-Item .env.example .env
```

Then run the full stack:

```powershell
docker compose up --build
```

Services:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

Notes:

- backend data is persisted in the `backend_data` Docker volume
- Compose overrides SQLite to use `sqlite:///./data/gitanalyse.db`
- frontend is built with `NEXT_PUBLIC_API_URL=http://localhost:8000`

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register a user |
| POST | `/auth/login` | Login and get JWT |
| GET | `/auth/me` | Current authenticated user |
| POST | `/review/tree` | Fetch repo tree preview |
| POST | `/review/file` | Fetch one file content |
| POST | `/analyze` | Run full analysis and persist report |
| GET | `/analyze` | List current user's analysis history |
| GET | `/analyze/{id}` | Get one persisted analysis report |
| WS | `/analyze/ws` | Stream analysis result chunks |

## Project Structure

```txt
git-analyse/
|-- app/
|   |-- main.py
|   |-- api/
|   |-- agents/
|   |   |-- pipeline.py
|   |   |-- router.py
|   |   |-- tools.py
|   |   |-- fetcher.py
|   |   |-- structure.py
|   |   |-- security.py
|   |   |-- quality.py
|   |   |-- testing.py
|   |   `-- synthesizer.py
|   |-- core/
|   |-- models/
|   |-- repositories/
|   |-- schemas/
|   `-- services/
|-- frontend/
|-- requirements.txt
|-- PROJECT_DOCUMENTATION.md
`-- README.md
```

## Known Limitations

- capped at 50 files per analysis
- large text files and binaries are skipped
- analysis is still slower than ideal for frontend UX
- findings are better grounded now, but still partly LLM-dependent
- SQLite is still dev-only

## CI

GitHub Actions runs three checks on push / pull request:

- backend dependency install + Python compile/import validation
- frontend dependency install + production build
- Docker image builds for backend and frontend

