## CodeReviewer — Complete Build Plan

---

## Prerequisites — What You Need Before Writing Line 1


**Python & FastAPI:**
- Can you write a FastAPI route with Pydantic validation from scratch?
- Do you understand `async/await` in Python?
- Can you use `Depends()` for dependency injection?
- Do you understand Python virtual environments?

If any of these is no — spend 2 days on the FastAPI study plan from earlier in this conversation first. Don't start CodeReviewer with shaky foundations.

**JavaScript/Next.js:**
- App Router structure — you already know this
- `fetch` with auth headers — you know this
- WebSocket client in React — you probably don't, learn this specifically

**Git & GitHub:**
- Branching — one branch per feature, not everything on main
- Meaningful commit messages — "add JWT auth" not "fix stuff"
- This matters because CodeReviewer analyzes commit history — yours should be clean

**Tools to install before day 1:**
```bash
python 3.11+
node 18+
docker desktop
postgresql (local)
postman or bruno (API testing)
```

---

## The Full Stack — With Reasoning For Every Choice

### Backend
**FastAPI (Python)**
Why: You're learning it, it's in every AI engineering JD, native async, Pydantic built in. No alternative.

**PostgreSQL**
Why: Persistent storage for users, analysis history, cached reports. SQLite is fine locally but swap to PostgreSQL from day 1 — forces production habits.

**SQLAlchemy (async)**
Why: The ORM layer. Keeps raw SQL out of your routes. Maps directly to what you'd use at a real company.

**Alembic**
Why: Database migrations. Every schema change goes through a migration file. This is what real engineering looks like — not dropping and recreating tables.

**python-jose + passlib**
Why: JWT implementation. python-jose handles token creation/verification, passlib handles bcrypt password hashing.

**PyGithub**
Why: Clean Python wrapper over GitHub API. Handles auth, rate limiting, pagination. Don't hit the API raw.

**LangGraph**
Why: Agent orchestration. Industry standard right now. Your 5 analysis nodes are LangGraph nodes.

**HuggingFace Inference API**
Why: Free, no GPU required, access to Mistral-7B and other capable models. Abstracted behind a client so you can swap to OpenAI later.

**WebSockets (via FastAPI)**
Why: Streaming the review output token by token. FastAPI has native WebSocket support — no extra library needed.

**pytest + httpx**
Why: Testing your FastAPI endpoints. httpx is the async-compatible HTTP client for testing. Target 80%+ coverage.

### Frontend
**Next.js 14 (App Router)**
Why: You know it, it's on your resume, moving on.

**Tailwind CSS**
Why: Same reason. Fast, clean, no context switching.

**shadcn/ui**
Why: Component library built on Tailwind. Gives you professional-looking UI without designing from scratch. Saves 2 days.

**Zustand**
Why: Lightweight state management. Simpler than Redux for this scale. Auth state, current analysis state.

**React Query (TanStack Query)**
Why: Data fetching, caching, loading states handled properly. You'll stop writing useEffect for every API call.

**Jest + React Testing Library**
Why: Frontend tests. Even 5-10 component tests is enough to put on your resume legitimately.

### Infrastructure
**Docker**
Why: Backend runs in a container. Single `docker-compose.yml` spins up FastAPI + PostgreSQL locally.

**AWS EC2**
Why: This is specifically to close the "cloud claimed but not proven" gap. Free tier t2.micro is enough. One deployed URL on AWS changes your resume story.

**Nginx**
Why: Reverse proxy in front of FastAPI on EC2. Industry standard. Handles SSL, request routing.

**GitHub Actions**
Why: CI pipeline. On every push — run tests, lint, build Docker image. Shows you understand DevOps basics.

**Vercel**
Why: Frontend. Free, instant, you already know it.

---

## Full Architecture

```
Browser (Next.js on Vercel)
    │
    │  HTTPS
    ▼
Nginx (EC2)
    │
    ▼
FastAPI (Docker container on EC2)
    │
    ├── PostgreSQL (Docker container)
    │       Users, Sessions, Analysis history
    │
    ├── PyGithub
    │       Fetches repo file tree and contents
    │       Handles rate limiting + pagination
    │       Truncates at 50 files
    │
    └── LangGraph Orchestrator
            │
            ├── [Node 1] Fetcher
            │     Input:  repo_url
            │     Output: { path: content } map
            │
            ├── [Node 2] Structure Agent
            │     Input:  file map
            │     Checks: folder structure, naming,
            │             separation of concerns
            │     Output: architecture_findings{}
            │
            ├── [Node 3] Security Agent
            │     Input:  file map
            │     Checks: hardcoded secrets, unsafe
            │             inputs, exposed keys
            │     Output: security_findings{}
            │
            ├── [Node 4] Quality Agent
            │     Input:  file map
            │     Checks: function length, duplication,
            │             naming, complexity signals
            │     Output: quality_findings{}
            │
            ├── [Node 5] Test Agent
            │     Input:  file map
            │     Checks: test files present, CI config,
            │             coverage signals
            │     Output: testing_findings{}
            │
            └── [Node 6] Synthesizer
                  Input:  all findings
                  Calls:  HuggingFace Inference API
                  Output: structured JSON report
                  Stream: via WebSocket to frontend
```

---

## Database Schema

```sql
-- Users
CREATE TABLE users (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(255) UNIQUE NOT NULL,
    password    VARCHAR(255) NOT NULL,  -- bcrypt hash
    created_at  TIMESTAMP DEFAULT NOW()
);

-- Analyses
CREATE TABLE analyses (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER REFERENCES users(id),
    repo_url    VARCHAR(500) NOT NULL,
    status      VARCHAR(50),  -- pending/running/complete/failed
    report      JSONB,        -- full structured output
    created_at  TIMESTAMP DEFAULT NOW()
);
```

Simple. Two tables. Don't overcomplicate.

---

## API Endpoints

```
AUTH
POST   /auth/register     { email, password }
POST   /auth/login        { email, password } → JWT
GET    /auth/me           → current user (protected)

ANALYSIS
POST   /analyze           { repo_url } → analysis_id (protected)
GET    /analyze/{id}      → full report (protected)
GET    /analyze/history   → user's past analyses (protected)
WS     /ws/analyze/{id}   → stream review output tokens
```

---

## The Report Output Shape

```json
{
  "repo": "github.com/user/repo",
  "overall_score": 74,
  "files_analyzed": 34,
  "dimensions": {
    "architecture": {
      "score": 80,
      "findings": ["Good separation of concerns",
                   "Service layer inconsistent"],
      "flagged_files": ["routes/auth.js"]
    },
    "security": {
      "score": 55,
      "findings": ["Hardcoded secret in config.py:14",
                   "No input validation on /upload"],
      "flagged_files": ["config.py", "routes/upload.js"]
    },
    "quality": {
      "score": 70,
      "findings": ["Functions averaging 47 lines",
                   "Duplication in user handlers"]
    },
    "testing": {
      "score": 30,
      "findings": ["No test files found",
                   "No CI configuration"]
    }
  },
  "top_3_fixes": [
    "Move JWT_SECRET to environment variable (config.py:14)",
    "Add input validation middleware to /upload endpoint",
    "Extract duplicate user validation into shared utility"
  ],
  "summary": "Solid structure with clear separation. 
               Security hygiene needs immediate attention.
               Testing is the biggest gap before production."
}
```

---

## Build Order — Layer By Layer

### Layer 1 — Auth (Days 1-2)
**Goal:** JWT auth working end to end, tested in Swagger

```
project/
├── app/
│   ├── main.py
│   ├── database.py       ← SQLAlchemy engine + session
│   ├── deps.py           ← get_db, get_current_user
│   ├── models/
│   │   └── user.py       ← SQLAlchemy User model
│   ├── schemas/
│   │   └── auth.py       ← Pydantic register/login schemas
│   └── routers/
│       └── auth.py       ← /register /login /me
├── alembic/              ← migrations
├── tests/
│   └── test_auth.py      ← write these as you go
├── .env
├── requirements.txt
└── docker-compose.yml    ← FastAPI + PostgreSQL
```

**Done when:** Register a user, login, get token, hit /me with token, hit /me without token and get 401. All in Swagger UI.

---

### Layer 2 — GitHub Fetcher (Days 3-4)
**Goal:** Given any public repo URL, return file tree and contents

Key things to handle:
- Repos with 500+ files — truncate to 50 most relevant
- Binary files — skip them
- Large files — truncate content to 3000 chars
- Rate limiting — PyGithub handles this but you need to know it exists

**Done when:** Three different repos fetched cleanly, results logged to terminal.

---

### Layer 3 — LangGraph Pipeline (Days 5-7)
**Goal:** All 5 agent nodes running, state flowing between them

This is the hardest layer. Spend the most time here.

LangGraph state object:
```python
from typing import TypedDict, Optional

class ReviewState(TypedDict):
    repo_url: str
    file_map: dict          # { path: content }
    architecture: dict
    security: dict
    quality: dict
    testing: dict
    final_report: Optional[dict]
```

Each node is a function:
```python
def structure_agent(state: ReviewState) -> ReviewState:
    # analyze state["file_map"]
    # return state with state["architecture"] populated
    ...
```

**Done when:** Full pipeline runs on a small repo, all 5 node outputs visible in terminal.

---

### Layer 4 — HuggingFace + WebSocket Streaming (Days 8-9)
**Goal:** Synthesizer calls HF API, streams tokens to frontend

HuggingFace setup:
```python
from huggingface_hub import InferenceClient

client = InferenceClient(
    model="mistralai/Mistral-7B-Instruct-v0.3",
    token=HF_TOKEN
)

# Streaming
for token in client.text_generation(prompt, stream=True):
    yield token
```

WebSocket in FastAPI:
```python
@app.websocket("/ws/analyze/{analysis_id}")
async def stream_analysis(ws: WebSocket, analysis_id: int):
    await ws.accept()
    async for token in run_pipeline(analysis_id):
        await ws.send_text(token)
    await ws.close()
```

**Done when:** Full review streams token by token in the terminal, then in the browser.

---

### Layer 5 — Next.js Frontend (Days 10-11)
**Four pages only:**

```
/              → landing, repo URL input (no auth required)
/auth          → login + register tabs
/dashboard     → list of past analyses
/report/[id]   → full rendered report
```

WebSocket client in React:
```javascript
const ws = new WebSocket(`wss://api.yourdomain.com/ws/analyze/${id}`)
ws.onmessage = (e) => setStreamedText(prev => prev + e.data)
```

**Done when:** Full flow works browser to backend. Login, paste URL, see streaming report.

---

### Layer 6 — Tests (Day 12)
**Backend — pytest:**
```
tests/
├── test_auth.py        ← register, login, protected routes
├── test_github.py      ← fetcher with mock API responses
├── test_pipeline.py    ← each agent node with sample input
└── test_report.py      ← synthesizer output structure
```

**Frontend — Jest:**
```
__tests__/
├── ReportCard.test.tsx    ← renders scores correctly
├── AuthForm.test.tsx      ← form validation
└── StreamOutput.test.tsx  ← WebSocket mock
```

Target: 80% backend coverage, at least 5 frontend component tests.

---

### Layer 7 — Deploy (Days 13-14)
**Step by step:**

1. `docker-compose.yml` works locally — FastAPI + PostgreSQL
2. Push image to Docker Hub
3. Spin up AWS EC2 t2.micro (free tier)
4. Pull image, run container
5. Install Nginx, configure reverse proxy
6. Point domain or use EC2 public IP
7. Add GitHub Actions CI — runs tests on every push
8. Frontend to Vercel as always

---

## The Eval Harness — Don't Skip This

After deploy, run this:

```python
# eval/run_eval.py
REPOS = [
    "https://github.com/your/panditai",
    "https://github.com/your/evakeel",
    # 8 more diverse repos
]

for repo in REPOS:
    report = call_api(repo)
    # manually score each dimension 1-5
    # log to eval/results.csv
```

| Repo | Architecture | Security | Quality | Testing | Notes |
|---|---|---|---|---|---|
| PanditAI | 4/5 ✅ | 3/5 ⚠️ | 4/5 ✅ | 1/5 ❌ | Correctly flagged no tests |
| eVakeel | 3/5 ✅ | 4/5 ✅ | 3/5 ✅ | 1/5 ❌ | - |

This table goes in your README. It's the thing that makes interviewers say "oh this person actually thinks about AI quality."

---

## README Structure

```
# CodeReviewer

> Agentic code analysis tool — paste a GitHub repo, 
  get a structured engineering review.

## Architecture Diagram
[image]

## Tech Stack
[table]

## How It Works
[4 sentences, plain English]

## Evaluation Results
[your 10-repo table]

## Challenges
- Non-deterministic LLM output — solved with structured 
  prompts and output validation
- GitHub rate limiting — handled with PyGithub's built-in 
  retry logic
- Token overflow on large repos — solved with 50-file cap 
  and content truncation

## Local Setup
[5 commands that actually work]

## Live Demo
[URL]
```

---

## What This Looks Like On Your Resume When Done

```latex
\noindent\textbf{CodeReviewer | Agentic Code Analysis | 
\normalfont Next.js · FastAPI · LangGraph · HuggingFace · 
AWS · PostgreSQL}
\hfill{\href{https://github.com}{GitHub} | 
\href{https://live.com}{Live}}
\begin{itemize}
    \item \textbf{Architected} a \textbf{5-node LangGraph 
    pipeline} analyzing GitHub repositories across 
    architecture, security, quality, and test coverage — 
    streaming structured reviews via \textbf{WebSockets}
    \item \textbf{Implemented} full \textbf{JWT auth}, 
    \textbf{async PostgreSQL} with Alembic migrations, and 
    \textbf{pytest suites} achieving \textbf{80\%+ branch 
    coverage}
    \item \textbf{Deployed} on \textbf{AWS EC2} with Docker 
    and Nginx reverse proxy; \textbf{CI/CD} via GitHub 
    Actions — evaluated against \textbf{10 real repos} with 
    documented output quality scoring
\end{itemize}
```

---

**Start with Layer 1. Auth first. Nothing else until auth works cold.**

Come back here when it does.