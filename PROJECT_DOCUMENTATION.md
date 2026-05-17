# GitAnalyse (CodeReviewer) - Complete Technical Documentation

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Technology Stack](#technology-stack)
4. [Frontend (Next.js)](#frontend-nextjs)
5. [Backend (FastAPI)](#backend-fastapi)
6. [Database Layer](#database-layer)
7. [AI/LLM Pipeline](#aillm-pipeline)
8. [Data Flow & Request Lifecycle](#data-flow--request-lifecycle)
9. [API Endpoints](#api-endpoints)
10. [Configuration & Environment](#configuration--environment)
11. [Project Structure](#project-structure)
12. [Key Components Deep Dive](#key-components-deep-dive)
13. [Known Limitations](#known-limitations)

---

## Project Overview

**GitAnalyse** (also known as CodeReviewer) is a web application that analyzes GitHub repositories and provides structured engineering reviews across four dimensions:

- **Structure**: Folder organization, separation of concerns, naming conventions
- **Security**: Hardcoded secrets, SQL injection, XSS, auth bypass, command injection
- **Quality**: Function complexity, code duplication, readability, error handling
- **Testing**: Test files, CI/CD configuration, coverage signals

The system uses multiple specialized AI agents running in parallel, orchestrated via a LangGraph pipeline. Each agent analyzes the codebase and returns structured findings with scores. A final synthesizer agent compiles everything into a scored report with prioritized fixes.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (Next.js)                             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌──────────────┐    │
│  │   Landing   │   │   Auth      │   │  Dashboard  │   │ Report View  │    │
│  │   Page     │   │   Page      │   │   Page      │   │   Page       │    │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘   └──────┬───────┘    │
│         │                 │                 │                  │            │
│         └─────────────────┴────────┬────────┴──────────────────┘            │
│                                    │                                         │
│                           ┌────────▼────────┐                                │
│                           │   lib/api.ts    │                                │
│                           │  (API Client)   │                                │
│                           └────────┬────────┘                                │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
                                     │ HTTPS/REST
                                     │
┌────────────────────────────────────┼────────────────────────────────────────┐
│                            BACKEND (FastAPI)                                │
│                                    │                                         │
│  ┌─────────────────────────────────▼──────────────────────────────────────┐  │
│  │                         Routes Layer                                  │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌───────────┐   │  │
│  │  │ Health  │  │  Auth   │  │  Users  │  │ Review  │  │ Analyze   │   │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └───────────┘   │  │
│  └─────────────────────────────────┬──────────────────────────────────────┘  │
│                                    │                                         │
│  ┌─────────────────────────────────▼──────────────────────────────────────┐  │
│  │                      Services Layer                                   │  │
│  │  ┌─────────────────┐  ┌──────────────────────────┐                   │  │
│  │  │ GitHub Service  │  │  Auth Service            │                   │  │
│  │  │ (fetch repo)   │  │  (register/login/jwt)   │                   │  │
│  │  └────────┬────────┘  └────────────┬─────────────┘                   │  │
│  └───────────┼─────────────────────────┼───────────────────────────────────┘  │
│              │                         │                                    │
│  ┌───────────▼─────────────────────────▼───────────────────────────────────┐ │
│  │                      Agents Layer (LangGraph)                         │ │
│  │                                                                         │ │
│  │    ┌─────────┐                                                         │ │
│  │    │ Fetcher │────► ┌────────────┐                                     │ │
│  │    │  Node   │      │ Structure  │                                     │ │
│  │    └─────────┘      │   Agent    │────►                                │ │
│  │                     └────────────┘      ┌────────────┐                 │ │
│  │                                   ┌────►│ Security  │────►             │ │
│  │                                   │     │   Agent   │                  │ │
│  │                                   │     └────────────┘                 │ │
│  │                                   │            ┌────────────┐          │ │
│  │                                   └──────────►│  Quality   │────►      │ │
│  │                                   │            │   Agent    │           │ │
│  │                                   │            └────────────┘          │ │
│  │                                   │                 ┌────────────┐      │ │
│  │                                   └───────────────►│  Testing   │────┐  │ │
│  │                                   │                 │   Agent    │    │  │ │
│  │                                   │                 └────────────┘    │  │ │
│  │                                   │                     ┌──────────▼──┘  │  │ │
│  │                                   └────────────────────►│ Synthesizer │  │ │
│  │                                                        │   Agent     │  │ │
│  │                                                        └─────────────┘  │ │
│  └─────────────────────────────────┬───────────────────────────────────────┘  │
│                                    │                                          │
│  ┌─────────────────────────────────▼───────────────────────────────────────┐  │
│  │                         LLM Layer                                       │  │
│  │  ┌─────────────────┐  ┌────────────────────────────────────────────┐   │  │
│  │  │   call_llm()    │  │  run_validated_agent_call()                 │   │  │
│  │  │ (HF/Ollama)    │  │  (JSON parsing + validation + retry)       │   │  │
│  │  └─────────────────┘  └────────────────────────────────────────────┘   │  │
│  └─────────────────────────────────┬───────────────────────────────────────┘  │
│                                    │                                          │
│  ┌─────────────────────────────────▼───────────────────────────────────────┐  │
│  │                      Database Layer (SQLAlchemy)                      │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────────────┐    │  │
│  │  │  User Model │  │   Base      │  │    User Repository          │    │  │
│  │  └─────────────┘  └─────────────┘  └──────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
                              ┌─────────────┐
                              │  SQLite DB  │
                              │  (dev)      │
                              └─────────────┘
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Next.js 14 (TypeScript) | React-based web UI with App Router |
| **Frontend Styling** | Tailwind CSS + shadcn/ui | Utility-first CSS with component library |
| **Frontend State** | React hooks (useState, useEffect) | Local component state management |
| **Backend** | FastAPI (Python 3.10+) | REST API framework with async support |
| **AI Orchestration** | LangGraph | Graph-based workflow for multi-agent pipeline |
| **LLM Provider** | Ollama / HuggingFace Inference | Local or cloud LLM inference |
| **Database** | SQLite (dev) / PostgreSQL (prod) | SQLAlchemy ORM for data persistence |
| **Auth** | JWT (Python-Jose) + Argon2 | Token-based authentication with secure password hashing |
| **HTTP Client** | requests + huggingface_hub | GitHub API and LLM API calls |
| **Logging** | Python logging + custom telemetry | Structured logging with correlation IDs |

---

## Frontend (Next.js)

### Project Structure

```
frontend/
├── app/
│   ├── page.tsx              # Landing page (repo URL input)
│   ├── layout.tsx            # Root layout with metadata
│   ├── globals.css           # Global styles (Tailwind)
│   ├── auth/
│   │   └── page.tsx          # Login/Register page
│   ├── dashboard/
│   │   └── page.tsx          # User dashboard
│   └── report/
│       └── [id]/
│           └── page.tsx      # Report display page
├── components/
│   └── ui/
│       ├── button.tsx        # Reusable Button component
│       └── input.tsx         # Reusable Input component
├── lib/
│   └── api.ts                # API client wrapper
├── package.json              # Dependencies
├── tailwind.config.js        # Tailwind configuration
├── tsconfig.json             # TypeScript config
└── next.config.ts            # Next.js configuration
```

### Frontend Pages

1. **Landing Page** (`/`) - `app/page.tsx`
   - Input field for GitHub repository URL
   - "Analyze Repository" button
   - Checks for authentication token, redirects to `/auth` if not logged in
   - On submit: calls API, stores result in localStorage, navigates to report page

2. **Authentication Page** (`/auth`) - `app/auth/page.tsx`
   - Toggle between "Login" and "Register" modes
   - Register: Email, Username, Password fields
   - Login: Email, Password fields
   - On success: stores JWT token in localStorage, redirects to dashboard

3. **Dashboard Page** (`/dashboard`) - `app/dashboard/page.tsx`
   - User's past analyses and account info
   - (Implementation appears minimal currently)

4. **Report Page** (`/report/[id]`) - `app/report/[id]/page.tsx`
   - Displays the final analysis report
   - Shows overall score, dimension scores, findings, recommendations

### API Client (`lib/api.ts`)

The API client wraps `fetch` and handles:

- Base URL configuration (`NEXT_PUBLIC_API_URL` defaults to `http://127.0.0.1:8000`)
- Automatic JWT token inclusion from localStorage
- Error handling with detailed validation error messages
- Organized into namespaces: `api.auth`, `api.review`, `api.analyze`

```typescript
// Key functions
api.auth.login({ email, password })     // Returns { access_token }
api.auth.register({ email, username, password })
api.auth.me()                           // Returns current user
api.auth.logout()                       // Clears token

api.review.tree(repoUrl)                // Fetches repo file tree
api.review.file(repoUrl, path)          // Fetches specific file content

api.analyze.create(repoUrl)             // Triggers analysis
```

### Components

- **Button**: Reusable button with loading state support
- **Input**: Reusable input with label, error, and type support

---

## Backend (FastAPI)

### Entry Point: `app/main.py`

The FastAPI application initialization:

1. **CORS Middleware**: Allows requests from `localhost:3000` and `127.0.0.1:3000`
2. **Request Logging Middleware**: Adds correlation IDs, logs all requests with timing
3. **Database Tables**: Creates all tables on startup using SQLAlchemy
4. **Router Registration**: Includes health, auth, users, review, and analysis routers

### Routes Overview

| Route File | Prefix | Description |
|------------|--------|-------------|
| `health.py` | `/` | Health check endpoint |
| `auth.py` | `/auth` | Register, login, get current user |
| `users.py` | `/users` | User management (placeholder) |
| `review.py` | `/review` | GitHub repo tree and file fetching |
| `analysis.py` | `/analyze` | Trigger repository analysis |

### Core Services

#### 1. GitHub Service (`app/services/github_service.py`)

Fetches repository data from GitHub API:

- **`get_default_branch(owner, repo)`**: Fetches default branch name
- **`get_repo_tree(owner, repo, branch)`**: Gets recursive file tree, returns up to 50 files
- **`get_file_content(owner, repo, path)`**: Fetches file content, decodes from base64, limits to 200KB

Key constraints:
- Max 50 files per analysis (to stay within LLM context limits)
- Max 200KB per file
- Requires `GITHUB_TOKEN` for private repos and higher rate limits

#### 2. Auth Service (`app/services/auth_service.py`)

Handles user authentication:

- **`register_user(db, email, username, password)`**: Creates new user with hashed password
- **`login_user(db, email, password)`**: Verifies credentials, returns JWT token
- Uses Argon2 for password hashing
- Uses JWT for token generation with configurable expiration

### API Routes Detail

#### Authentication Routes (`/auth`)

```
POST /auth/register
  Body: { "email": "...", "username": "...", "password": "..." }
  Response: { "id": 1, "email": "...", "username": "...", "is_active": true }

POST /auth/login
  Body: { "email": "...", "password": "..." }
  Response: { "access_token": "eyJ...", "token_type": "bearer" }

GET /auth/me
  Header: Authorization: Bearer <token>
  Response: { "id": 1, "email": "...", "username": "...", "is_active": true }
```

#### Review Routes (`/review`)

```
POST /review/tree
  Body: { "repo_url": "https://github.com/owner/repo" }
  Response: {
    "owner": "owner",
    "repo": "repo",
    "total_discovered": 45,
    "total_returned": 45,
    "truncated": false,
    "files": [{ "path": "src/main.py", "type": "file", "size": 1234 }]
  }

POST /review/file
  Query: ?path=src/main.py
  Body: { "repo_url": "https://github.com/owner/repo" }
  Response: { "path": "src/main.py", "content": "..." }
```

#### Analysis Routes (`/analyze`)

```
POST /analyze
  Header: Authorization: Bearer <token>
  Body: { "repo_url": "https://github.com/owner/repo" }
  Response: {
    "id": 1,
    "repo_url": "https://github.com/owner/repo",
    "status": "complete",
    "report": {
      "overall_score": 74,
      "mega_verdict": "Promising codebase...",
      "dimensions": {
        "structure": { "score": 80, "findings": [...], ... },
        "security": { "score": 55, "findings": [...], ... },
        "quality": { "score": 70, "findings": [...], ... },
        "testing": { "score": 30, "findings": [...], ... }
      },
      "top_3_fixes": [...],
      "all_recommendations": [...],
      "flagged_files": [...],
      "summary": "..."
    }
  }
```

### Dependency Injection (`app/api/deps.py`)

- **`get_current_user`**: OAuth2 dependency that:
  - Extracts JWT from `Authorization: Bearer <token>` header
  - Decodes token using JWT secret
  - Looks up user in database
  - Returns User object or raises 401

---

## Database Layer

### Database Configuration (`app/db.py`)

- Uses SQLAlchemy with SQLite for development
- `DATABASE_URL` from settings (defaults to `sqlite:///./codereviewer.db`)
- Creates `SessionLocal` for database sessions
- `get_db()` is a generator that provides sessions to route handlers

### Models

#### Base Model (`app/models/base.py`)
```python
Base = declarative_base()  # SQLAlchemy declarative base
```

#### User Model (`app/models/user.py`)
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
```

### Repositories (`app/repositories/user_repo.py`)

- **`get_user_by_email(db, email)`**: Find user by email
- **`get_user_by_username(db, username)`**: Find user by username
- **`create_user(db, email, username, hashed_password)`**: Create new user

---

## AI/LLM Pipeline

### LangGraph Workflow (`app/agents/pipeline.py`)

The analysis pipeline uses LangGraph to orchestrate multiple agents:

```
START → fetcher → structure → security → quality → testing → synthesizer → END
```

Each node is a function that:
- Takes `ReviewState` (TypedDict) as input
- Returns updated `ReviewState`

### ReviewState Schema (`app/agents/state.py`)

```python
class ReviewState(TypedDict):
    repo_url: str                          # GitHub repository URL
    file_map: dict                         # {file_path: file_content}
    structure_findings: Optional[dict]     # Structure agent results
    security_findings: Optional[dict]       # Security agent results
    quality_findings: Optional[dict]        # Quality agent results
    testing_findings: Optional[dict]       # Testing agent results
    final_report: Optional[dict]            # Final synthesized report
```

### Agent Nodes

#### 1. Fetcher Node (`app/agents/fetcher.py`)

**Purpose**: Fetch repository files from GitHub

**Process**:
1. Parse repo URL to get owner/repo
2. Get default branch
3. Fetch file tree (up to 50 files)
4. Fetch content for each file (truncate to 3000 chars if too long)
5. Store in `file_map`

**Output**: `state["file_map"] = {path: content, ...}`

#### 2. Structure Agent (`app/agents/structure.py`)

**Purpose**: Analyze project architecture and organization

**Evaluation Criteria**:
- Folder organization (src/, lib/, app/, services/)
- Separation of concerns
- File naming conventions
- Module organization
- API/routes pattern
- Database/access layer separation
- Signs of tight coupling or cross-layer leakage

**Score Guidelines**:
- 90-100: Excellent architecture, clear separation
- 70-89: Good structure, some inconsistencies
- 50-69: Needs organizational improvement
- 0-49: Poor organization, hard to navigate

**Output**: JSON with score (0-100), findings, flagged_files, recommendations

#### 3. Security Agent (`app/agents/security.py`)

**Purpose**: Find security vulnerabilities

**Looks For**:
- Hardcoded secrets: API keys, tokens, passwords, AWS credentials
- SQL injection: string concatenation in queries
- XSS: unsanitized user input in HTML/JS
- Auth bypass: missing checks, weak validation
- Command injection: os.system, subprocess with user input
- Path traversal: unsafe file access

**Output**: JSON with score (0-100), findings, flagged_files, recommendations

#### 4. Quality Agent (`app/agents/quality.py`)

**Purpose**: Analyze code quality and maintainability

**Checks**:
- Function complexity (too long, nested)
- Code duplication
- Poor naming conventions
- Missing documentation
- Magic numbers/strings
- Error handling issues
- Readability risks

**Score Guidelines**:
- 90-100: Excellent, production-ready code
- 70-89: Good, minor improvements possible
- 50-69: Needs refactoring
- 0-49: Significant issues, hard to maintain

**Output**: JSON with score (0-100), findings, flagged_files, recommendations

#### 5. Testing Agent (`app/agents/testing.py`)

**Purpose**: Analyze testing coverage and CI/CD

**Checks**:
- Test files (test_*.py, *_test.py, spec_*.js, *.test.js)
- Test directories (__tests__/, tests/, test/)
- CI/CD configuration (.github/workflows/, .gitlab-ci.yml)
- Test coverage tools
- Testing frameworks used
- Mock/fixture patterns
- Critical untested risk areas

**Score Guidelines**:
- 90-100: Comprehensive tests, good coverage
- 70-89: Some tests present, CI configured
- 50-69: Limited tests, CI missing
- 0-49: No tests found, no CI

**Output**: JSON with score (0-100), findings, flagged_files, recommendations

#### 6. Synthesizer Node (`app/agents/synthesizer.py`)

**Purpose**: Compile all agent findings into final report

**Process**:
1. Calls LLM with all agent findings to generate structured report
2. Falls back to deterministic report generation if LLM fails

**Output**: Comprehensive report with:
- overall_score (0-100)
- mega_verdict (1-2 sentence executive summary)
- summary
- files_analyzed
- dimensions (structure, security, quality, testing with scores, findings, flagged_files, recommendations)
- top_3_fixes
- all_recommendations
- flagged_files

### LLM Integration (`app/agents/llm.py`)

**call_llm()**: Unified LLM interface supporting:
- **Ollama** (local): Default at `http://127.0.0.1:11434`
- **HuggingFace** (cloud): Uses Inference API

**Settings**:
```python
llm_provider: str = "ollama"           # or "huggingface"
llm_model: str = "qwen2.5-coder:14b"   # default model
llm_temperature: float = 0.2
llm_max_tokens: int = 1024
```

**Per-Agent Model Overrides** (optional):
```python
llm_model_structure: Optional[str]    # Override for structure agent
llm_model_security: Optional[str]      # Override for security agent
llm_model_quality: Optional[str]       # Override for quality agent
llm_model_testing: Optional[str]       # Override for testing agent
llm_model_synthesizer: Optional[str]   # Override for synthesizer
```

**call_llm_json()**: Wrapper that forces JSON output with regex extraction

### Validation (`app/agents/validation.py`)

**run_validated_agent_call()**: Ensures agent outputs are valid:
1. Calls LLM with prompt
2. Extracts JSON using regex `{[\s\S]*}` pattern
3. Validates against Pydantic `AgentOutput` schema
4. Retries up to 2 times if validation fails
5. Returns fallback on complete failure

**AgentOutput Schema** (`app/agents/schemas.py`):
```python
class AgentOutput(BaseModel):
    score: int = Field(ge=0, le=100)
    findings: list[FindingItem] = Field(default_factory=list)
    flagged_files: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)

class FindingItem(BaseModel):
    file: str = Field(min_length=1)
    reason: str = Field(min_length=5)
    evidence_snippet: str = Field(min_length=3)
    severity: str = Field(pattern="^(low|medium|high|critical)$")
    confidence: float = Field(ge=0.0, le=1.0)
```

---

## Data Flow & Request Lifecycle

### Full Analysis Flow

```
1. User enters repo URL on landing page
   │
2. Frontend checks for auth token
   │  - If no token → redirect to /auth
   │
3. Frontend calls POST /api/analyze with repo_url
   │
4. FastAPI calls get_current_user dependency (validates JWT)
   │
5. Analysis route calls run_review(repo_url)
   │
6. LangGraph pipeline executes:
   │
   ├─► Fetcher Node
   │   ├─► parse_github_repo_url() → (owner, repo)
   │   ├─► get_default_branch()
   │   ├─► get_repo_tree() → file list (max 50)
   │   ├─► get_file_content() for each file
   │   └─► state["file_map"] = {...}
   │
   ├─► Structure Agent
   │   ├─► run_validated_agent_call(prompt, system_prompt)
   │   ├─► call_llm() → LLM response
   │   ├─► Validate JSON output
   │   └─► state["structure_findings"] = {...}
   │
   ├─► Security Agent
   │   ├─► Similar flow to Structure Agent
   │   └─► state["security_findings"] = {...}
   │
   ├─► Quality Agent
   │   ├─► Similar flow
   │   └─► state["quality_findings"] = {...}
   │
   ├─► Testing Agent
   │   ├─► Similar flow
   │   └─► state["testing_findings"] = {...}
   │
   └─► Synthesizer
       ├─► _synthesize_with_llm()
       │   └─► call_llm_json() → final report
       └─► state["final_report"] = {...}

7. Route returns ReviewResponse with report

8. Frontend navigates to /report/[id]

9. Report page displays:
   - Overall score (0-100)
   - Dimension scores (structure, security, quality, testing)
   - Findings by category
   - Flagged files
   - Top 3 recommended fixes
   - All recommendations
   - Executive summary (mega_verdict)
```

### Authentication Flow

```
1. User visits /auth
2. User fills form (login or register)
3. Frontend calls appropriate API:
   - POST /auth/login → returns access_token
   - POST /auth/register → creates user
4. Frontend stores token in localStorage
5. Subsequent API calls include:
   Authorization: Bearer <token>
6. FastAPI deps.get_current_user extracts and validates token
7. User object is available in route handlers
```

---

## Configuration & Environment

### Environment Variables (`.env`)

```env
# JWT Configuration
JWT_SECRET=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database
DATABASE_URL=sqlite:///./codereviewer.db

# App Settings
APP_NAME=CodeReviewer

# LLM Settings
HF_TOKEN=your_huggingface_token

# GitHub
GITHUB_TOKEN=your_github_pat

# LLM Configuration
LLM_PROVIDER=ollama                    # or "huggingface"
LLM_MODEL=qwen2.5-coder:14b           # model name
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=1024

# Optional per-agent overrides
LLM_MODEL_STRUCTURE=
LLM_MODEL_SECURITY=
LLM_MODEL_QUALITY=
LLM_MODEL_TESTING=
LLM_MODEL_SYNTHESIZER=

# Ollama (when using local provider)
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

### Settings (`app/core/settings.py`)

Pydantic-based settings with:
- Environment variable loading from `.env`
- LRU cache for singleton access
- Validation for production JWT secret

---

## Project Structure

```
git-analyse/
├── .env                          # Environment variables
├── .gitignore
├── README.md                      # Project overview
├── codereviewer.db               # SQLite database (dev)
│
├── app/                          # Backend source
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point
│   ├── db.py                     # Database connection & session
│   │
│   ├── api/                      # Route handlers
│   │   ├── __init__.py
│   │   ├── deps.py               # Dependency injection (auth)
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py          # Health check
│   │       ├── auth.py            # Auth endpoints
│   │       ├── users.py           # User endpoints
│   │       ├── review.py          # GitHub review endpoints
│   │       └── analysis.py        # Analysis endpoints
│   │
│   ├── agents/                   # AI agents (LangGraph nodes)
│   │   ├── __init__.py
│   │   ├── state.py              # ReviewState TypedDict
│   │   ├── pipeline.py            # LangGraph workflow definition
│   │   ├── fetcher.py            # GitHub file fetcher node
│   │   ├── llm.py                # LLM interface (Ollama/HF)
│   │   ├── validation.py          # Agent output validation
│   │   ├── schemas.py            # Pydantic output schemas
│   │   ├── structure.py          # Structure agent
│   │   ├── security.py           # Security agent
│   │   ├── quality.py            # Quality agent
│   │   ├── testing.py            # Testing agent
│   │   └── synthesizer.py        # Final report generator
│   │
│   ├── core/                     # Core utilities
│   │   ├── __init__.py
│   │   ├── settings.py           # Configuration (Pydantic)
│   │   ├── security.py           # JWT & password hashing
│   │   └── telemetry.py          # Logging utilities
│   │
│   ├── models/                   # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py              # Declarative base
│   │   └── user.py              # User model
│   │
│   ├── repositories/             # Data access layer
│   │   ├── __init__.py
│   │   └── user_repo.py         # User CRUD operations
│   │
│   ├── schemas/                 # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── auth.py              # Auth request/response schemas
│   │   ├── analysis.py          # Analysis request schemas
│   │   └── review.py            # Review request/response schemas
│   │
│   ├── services/                 # Business logic
│   │   ├── __init__.py
│   │   ├── github_service.py   # GitHub API client
│   │   └── auth_service.py      # Auth business logic
│   │
│   └── utils/                    # Utilities
│       ├── __init__.py
│       └── repo_url.py          # GitHub URL parser
│
└── frontend/                    # Frontend source (Next.js)
    ├── package.json
    ├── tsconfig.json
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── next.config.ts
    ├── app/
    │   ├── page.tsx             # Landing page
    │   ├── layout.tsx           # Root layout
    │   ├── globals.css          # Global styles
    │   ├── auth/
    │   │   └── page.tsx         # Auth page
    │   ├── dashboard/
    │   │   └── page.tsx         # Dashboard page
    │   └── report/
    │       └── [id]/
    │           └── page.tsx     # Report view page
    ├── components/
    │   └── ui/
    │       ├── button.tsx       # Button component
    │       └── input.tsx        # Input component
    └── lib/
        └── api.ts              # API client
```

---

## Key Components Deep Dive

### 1. JWT Authentication Flow

```
User Login:
1. POST /auth/login with {email, password}
2. auth_service.login_user():
   - Find user by email
   - verify_password(password, hashed)
   - create_access_token(user_id) → JWT
3. Return {access_token: "eyJ..."}
4. Frontend stores in localStorage

Subsequent Requests:
1. Frontend adds header: Authorization: Bearer <token>
2. FastAPI deps.get_current_user():
   - OAuth2PasswordBearer extracts token
   - decode_access_token() verifies JWT
   - Query User by ID from token payload
   - Return User object to route
```

### 2. GitHub API Integration

```
1. parse_github_repo_url(url) → (owner, repo)
   - Validates github.com domain
   - Extracts owner and repo from path

2. get_default_branch(owner, repo)
   - GET https://api.github.com/repos/{owner}/{repo}
   - Returns resp.json()["default_branch"]

3. get_repo_tree(owner, repo, branch)
   - GET https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1
   - Filter tree entries to only "blob" type (files)
   - Limit to MAX_FILES (50)
   - Return (file_entries, total, truncated)

4. get_file_content(owner, repo, path)
   - GET https://api.github.com/repos/{owner}/{repo}/contents/{path}
   - Check file size (max 200KB)
   - Decode base64 content
   - Return string
```

### 3. Agent Prompt Engineering

Each agent has:
- **System prompt**: Defines role and output format
- **Task prompt**: Specific analysis instructions with placeholders

Example (Structure Agent):
```python
SYSTEM_PROMPT = """You are a software architecture expert analyzing code.
Respond with JSON containing:
- score: integer 0-100
- findings: array of strings (specific observations)
- flagged_files: array of files with issues"""

STRUCTURE_PROMPT = """Analyze the project structure:

{file_list}

Score against these engineering principles:
- Correctness, Readability, Maintainability, Security by design, Operational simplicity
- Layered architecture (Controller -> Service -> Repository -> Data)
...

Return ONLY valid JSON."""
```

### 4. Fallback Mechanisms

**LLM Output Failure**:
- If JSON parsing fails: retry with repair suffix
- If Pydantic validation fails: retry with repair suffix
- If all retries fail: return deterministic fallback with score=40

**Synthesizer Fallback**:
- If LLM fails: calculate average of agent scores
- Concatenate all findings
- Generate verdict based on score thresholds

---

## Known Limitations

1. **Public repositories only** - No auth flow for private repos yet
2. **50 file cap** - To stay within LLM context limits
3. **SQLite in development** - Needs PostgreSQL for production
4. **Non-deterministic LLM** - Scores may vary slightly between runs
5. **200KB file size limit** - Large files are truncated

---

## Summary

This is a complete full-stack application with:

- **Frontend**: Next.js 14 with TypeScript, Tailwind CSS, App Router
- **Backend**: FastAPI with async support, SQLAlchemy ORM
- **Database**: SQLite (dev) with User model
- **Auth**: JWT tokens with Argon2 password hashing
- **AI**: Multi-agent LangGraph pipeline with LLM integration
- **GitHub**: REST API integration via requests library
- **Observability**: Structured logging with correlation IDs

The system analyzes GitHub repositories using specialized AI agents and produces comprehensive code review reports with scores, findings, and actionable recommendations.