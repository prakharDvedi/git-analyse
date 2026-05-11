# CodeReviewer

> Paste a GitHub repository URL. Get a structured engineering review across architecture, security, code quality, and test coverage — streamed live to your browser.

---

## What It Does

Most code review tools run static analysis — they flag syntax and style. CodeReviewer reasons about your code the way a senior engineer would: does the folder structure make sense, are secrets exposed, are functions too complex, is there any test coverage at all?

Four specialized agents analyze the repository in parallel. A synthesizer compiles their findings into a scored report with prioritized fixes. The entire report streams token-by-token to the frontend via WebSocket.

---

## Architecture

```
Browser (Next.js)
    │
    │  HTTPS / WebSocket
    ▼
FastAPI (Python)
    │
    ├── GitHub Fetcher (PyGithub)
    │     Fetches file tree + contents
    │     Truncates at 50 files, skips binaries
    │
    └── LangGraph Pipeline
            │
            ├── [Node 1] Structure Agent
            │     Folder layout, naming, separation of concerns
            │
            ├── [Node 2] Security Agent
            │     Hardcoded secrets, unsafe inputs, exposed keys
            │
            ├── [Node 3] Quality Agent
            │     Function length, duplication, complexity signals
            │
            ├── [Node 4] Testing Agent
            │     Test files, CI config, coverage signals
            │
            └── [Node 5] Synthesizer
                    Compiles findings → overall score → streams to client
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| AI Orchestration | LangGraph |
| LLM | HuggingFace Inference API |
| Streaming | WebSockets |
| Frontend | Next.js 14 (TypeScript) |
| Styling | Tailwind CSS + shadcn/ui |
| Database | SQLite (dev) |

---

## Report Output

Each analysis produces a structured report:

```json
{
  "overall_score": 74,
  "files_analyzed": 34,
  "mega_verdict": "Promising codebase. Prioritize security and testing.",
  "dimensions": {
    "structure": { "score": 80, "findings": [...], "flagged_files": [...] },
    "security":  { "score": 55, "findings": [...], "flagged_files": [...] },
    "quality":   { "score": 70, "findings": [...], "flagged_files": [...] },
    "testing":   { "score": 30, "findings": [...], "flagged_files": [...] }
  },
  "top_3_fixes": [
    "Move secrets to environment variables",
    "Add baseline tests for authentication and critical flows",
    "Refactor long functions in flagged files"
  ],
  "summary": "Solid structure. Security hygiene needs immediate attention. Testing is a major gap."
}
```

---

## Local Setup

**Prerequisites:** Python 3.11+, Node 18+

```bash
# 1. Clone the repo
git clone https://github.com/prakharDvedi/CodeReviewer
cd git-analyse

# 2. Backend
cd app
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Environment variables
cp .env.example .env
# Add your GITHUB_TOKEN and HF_TOKEN

# 4. Run backend
uvicorn main:app --reload

# 5. Frontend (separate terminal)
cd ../frontend
npm install
npm run dev
```

Or run both with the PowerShell script:

```powershell
.\start-dev.ps1
```

Open [http://localhost:3000](http://localhost:3000)

---

## Environment Variables

Create a `.env` file inside `app/`:

```env
GITHUB_TOKEN=your_github_personal_access_token
HF_TOKEN=your_huggingface_api_token
```

- **GITHUB_TOKEN** — needed for private repos and higher rate limits. [Get one here](https://github.com/settings/tokens)
- **HF_TOKEN** — needed for LLM inference. [Get one here](https://huggingface.co/settings/tokens)

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/repositories/analyze` | Start analysis for a repo URL |
| GET | `/api/repositories/{id}` | Fetch completed report |
| GET | `/api/repositories/` | List past analyses |
| WS | `/ws/analyze/{id}` | Stream report tokens live |

---

## Project Structure

```
git-analyse/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── api/                 # Route handlers
│   ├── agents/              # LangGraph agent nodes
│   │   ├── state.py         # Shared ReviewState TypedDict
│   │   ├── structure.py
│   │   ├── security.py
│   │   ├── quality.py
│   │   ├── testing.py
│   │   └── synthesizer.py
│   ├── core/                # Config, settings
│   ├── models/              # Database models
│   ├── schemas/             # Pydantic schemas
│   └── services/            # GitHub fetcher, pipeline runner
├── frontend/
│   ├── app/                 # Next.js App Router pages
│   ├── components/          # React components
│   └── lib/                 # Utilities, API client
├── start-dev.ps1            # Dev startup script
└── README.md
```

---

## Known Limitations

- Public repositories only (no auth flow for private repos yet)
- Capped at 50 files per analysis to stay within LLM context limits
- SQLite in development — swap to PostgreSQL before any production deploy
- LLM output is non-deterministic; scores may vary slightly between runs on the same repo
