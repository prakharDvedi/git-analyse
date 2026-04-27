Git Analyse

What It Actually Does
User pastes a GitHub repo URL → system fetches the code → multiple agents analyze different dimensions → LLM synthesizes a brutally honest review with specific, actionable suggestions.
Not a linter. Not a static analyzer. An opinionated engineering mentor that reads your code the way a senior engineer would.

The Output — What It Produces
json{
  "overall_score": 74,
  "summary": "Solid structure but auth logic is leaking 
               into routes. Tests are absent.",
  "dimensions": {
    "architecture": {
      "score": 80,
      "finding": "Good separation of concerns overall. 
                  Service layer exists but is inconsistent.",
      "specific_files": ["routes/auth.js", "services/user.js"],
      "suggestion": "Move token validation out of route 
                     handlers into a dedicated middleware"
    },
    "code_quality": { ... },
    "security": { ... },
    "testing": { ... },
    "documentation": { ... }
  },
  "top_3_fixes": [
    "Hardcoded JWT secret in config.py line 14",
    "No input validation on /upload endpoint",
    "Circular import between models/ and services/"
  ]
}

Architecture
User (Next.js)
    │
    │  POST /review  { repo_url, github_token? }
    ▼
FastAPI
    │
    ▼
LangGraph Orchestrator
    │
    ├── [Node 1] Fetcher Agent
    │       GitHub API → fetch file tree + contents
    │       Output: flat file map { path: content }
    │
    ├── [Node 2] Structure Agent  
    │       Analyzes: folder structure, naming, separation
    │       Output: architecture_findings
    │
    ├── [Node 3] Security Agent
    │       Scans: hardcoded secrets, exposed keys,
    │              unsafe inputs, SQL injection patterns
    │       Output: security_findings
    │
    ├── [Node 4] Quality Agent
    │       Checks: function length, complexity, 
    │               duplication, naming conventions
    │       Output: quality_findings
    │
    ├── [Node 5] Test Agent
    │       Looks for: test files, coverage signals,
    │                  CI config, test patterns
    │       Output: testing_findings
    │
    └── [Node 6] Synthesizer Agent
            Input: all upstream findings
            Output: final structured JSON report
    │
    ▼
Next.js renders report with scores,
findings per file, and top 3 priority fixes

Tech Stack With Reasoning
PieceToolWhyFrontendNext.js + TailwindYou know it, fast to buildBackendFastAPIWhat you're learningAuthJWT + bcryptForces proper implementationOrchestrationLangGraphIndustry standard agentic frameworkLLMHuggingFace Inference APIFree, no GPU, Mistral-7B works wellGitHub dataPyGithub libraryClean wrapper over GitHub APIDeployRailway + VercelBoth free tier

Scope Boundaries
In:

Public repos only (no token required)
Python and JavaScript/TypeScript repos
Max 50 files per analysis (prevent token overflow)
One analysis per request, results stored in memory

Out:

Private repo support (auth complexity, out of scope)
Real-time streaming (nice to have, not core)
Historical comparison between commits
IDE plugin


The 2-Week Build Plan
Week 1 — working backend:

Day 1-2: FastAPI + JWT auth complete
Day 3: GitHub fetcher working, file tree extraction
Day 4-5: LangGraph pipeline with all 5 agent nodes
Day 6-7: HuggingFace integration, full review JSON output

Week 2 — frontend + polish:

Day 8-9: Next.js UI — login, repo input, report display
Day 10-11: Connect frontend to backend end to end
Day 12: Docker + Railway deploy
Day 13: README + architecture diagram
Day 14: Eval — run 10 repos, note what breaks