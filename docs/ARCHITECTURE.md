# Nexus-SDD Architecture

## Design Principles

1. **Zero-Friction.** One command installs everything. No external databases.
2. **Agent-Agnostic.** Works with Claude Code, OpenCode, Cursor, Windsurf, Codex.
3. **Spec-Driven.** No code without spec. No spec without BDD.
4. **Memory-First.** Every decision, bug, and pattern is persisted.
5. **Security by Default.** Secrets blocked at the harness level, not the model level.
6. **Community-Owned.** MIT license. Open standard. RFC-driven evolution.

## Layer Architecture

```
┌──────────────────────────────────────────────────────────┐
│  LAYER 1: CLI (nexus-sdd)                                │
│  Typer + Rich — 11 commands, auto-detection              │
├──────────────────────────────────────────────────────────┤
│  LAYER 2: LangGraph Harness (Supervisor)                 │
│  StateGraph with 5 specialized agents + router           │
├──────────────────────────────────────────────────────────┤
│  LAYER 3: Sub-Agents (Spec, Plan, Code, Test, Security)  │
│  Each with defined "attitude" from profiles              │
├──────────────────────────────────────────────────────────┤
│  LAYER 4: Tools & Integrations                           │
│  OpenSpec │ Engram │ LangFuse │ AST Scanner │ Hermes     │
├──────────────────────────────────────────────────────────┤
│  LAYER 5: Skills Protocol (.nexus/skills/)               │
│  YAML frontmatter + behavior rules + commands            │
└──────────────────────────────────────────────────────────┘
```

## Supervisor Pattern

The supervisor (`nexus_sdd/harness/supervisor.py`) implements a LangGraph StateGraph:

```
[START] → supervisor → spec_agent → supervisor
                          ↓
                      plan_agent → supervisor
                          ↓
                      code_agent → supervisor
                          ↓
                      test_agent → supervisor
                          ↓
                    security_agent → supervisor → [END]
```

Each agent returns to the supervisor after completing its phase. The supervisor:
1. Checks `state["phase"]` 
2. Routes to the correct agent
3. Transitions to the next phase
4. Tracks token usage across all phases

## State Machine

The `AgentState` flows through phases:

```
spec → plan → code → test → security → done
 ↑                                        │
 └────────── Ralph Loop (retry) ─────────┘
```

Ralph Loop triggers when the test agent finds failures not caused by test bugs:
- AgentState returns to `code` phase
- Code agent fixes the issue
- Re-runs tests
- Max 3 iterations, then escalates

## Project Detection

`nexus_sdd/detector/scanner.py` uses a signature-based system:

1. **File signatures** — `package.json`, `pyproject.toml`, `go.mod`, `build.gradle.kts`
2. **Deep scan** — Parse dependency files to extract frameworks, ORMs, test runners
3. **Directory patterns** — `android/`, `ios/` for mobile
4. **Recommendation** — Maps detected stack → matching skills

## Skill Protocol

Every skill is a `SKILL.md` with:

```yaml
---
name: skill-id
description: What this skill governs
category: web|mobile|backend|testing|language|infra
stack: [technologies, it, applies, to]
triggers: [keywords, that, trigger, this, skill]
---
# Skill Title

## Agent Attitude
[How the agent should think/behave]

## Rules
[Mandatory rules]

## Do's / Don'ts
[Encouraged and forbidden patterns]

## Recommended Commands
[CLI commands for linting, testing, type-checking]
```

## Security Middleware Flow

```
File written by code_agent
    ↓
Security middleware intercepts (pre-commit hook)
    ↓
AST + regex scan
    ├─ Clean → allow commit
    └─ Found → BLOCK commit
        ├─ Generate .nexus/alerts/security_leak_blocked.md
        └─ Notify developer with exact file:line
```

## Memory Flow (Engram)

```
Agent completes significant work
    ↓
engram save <title> <content> --type <type> --project <project>
    ↓
SQLite + FTS5 index
    ↓
Next session:
    agent calls engram search "<query>"
    ↓
Relevant memories injected into context
```

## Future: sqlite-vec Extension

Currently Engram uses FTS5 (lexical search). The roadmap includes:
- `sqlite-vec` extension for semantic search
- Local embedding model (no external API calls)
- Hybrid search: FTS5 + vector combined

This would unlock:
- "Find decisions similar to this one" (semantic, not keyword)
- "Has this bug pattern appeared before?" (across projects)
- Profile-based code generation (match developer style)
