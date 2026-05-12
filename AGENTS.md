# Nexus-SDD Agent Instructions

## Your Role
You are an AI coding agent contributing to the **Nexus-SDD framework** itself.
Follow the same SDD methodology the framework enforces:

```
SPEC → PLAN → CODE → TEST → SECURITY
```

## Core Rules

1. **SPEC first.** Every change starts with OpenSpec. Use `/opsx:propose`.
2. **LangGraph patterns.** Use Supervisor + specialized agents. Don't build monoliths.
3. **Engram memory.** After every significant decision: `engram save`.
4. **Security.** The security middleware it's part of this framework. No hardcoded secrets.
5. **Skills are protocol.** Every skill file is a behavior contract for agents.

## Project Structure

```
nexus-sdd/
├── nexus_sdd/
│   ├── harness/          # LangGraph supervisor + agents
│   │   ├── supervisor.py # Director de Orquesta
│   │   └── agents/       # spec, plan, code, test, security
│   ├── detector/         # Project stack scanner
│   ├── skills/           # Skill registry + generator
│   └── security/         # Security middleware
├── skills/               # Technology-specific SKILL.md catalog
│   ├── web/              # React, Vue, Next.js, Svelte
│   ├── mobile/           # Kotlin KMP, Flutter, SwiftUI
│   ├── backend/          # FastAPI, Django, Go-Fiber
│   └── testing/          # BDD, Playwright, Vitest
├── templates/            # .nexus/ templates for new projects
├── install.sh            # Universal zero-friction installer
└── docs/                 # Architecture + quickstart
```

## When Adding a New Skill

1. Create `skills/<category>/<name>.md`
2. Frontmatter must include: `name`, `description`, `category`, `stack`, `triggers`
3. Body: Agent Attitude, Rules, Do's, Don'ts, Recommended Commands
4. Add detection signature in `nexus_sdd/detector/scanner.py`
5. Test: `nexus-sdd skill install <name>`

## When Adding a New Agent

1. Create `nexus_sdd/harness/agents/<role>_agent.py`
2. Must return a LangGraph node function: `(state: AgentState) -> AgentState`
3. Must include a SYSTEM_PROMPT defining the agent's "attitude"
4. Register in `supervisor.py` → `AGENT_MAP` and `PHASE_ORDER`
5. Test: `python -m pytest nexus_sdd/harness/tests/`

## Technology Stack (for this project)

- **Python 3.11+** — LangGraph harness, CLI (Typer), detector
- **Go** — Future CLI rewrite for single-binary distribution
- **TypeScript** — OpenSpec integration layer
- **Engram** — Memory backend (Go binary, MCP)
