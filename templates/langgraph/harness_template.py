"""
Template for new LangGraph projects using Nexus-SDD harness.

Copy this to your project and customize for your domain.
"""

from nexus_sdd.harness import SupervisorGraph
from nexus_sdd.harness.supervisor import create_langfuse_handler

# ── Configuration ───────────────────────────────────────────────────

PROFILE = {
    "name": "my-team",
    "role": "fullstack",
    "stack": ["python", "fastapi", "react"],
    "languages": ["python", "typescript"],
    "preferred_patterns": ["repository-pattern", "tdd", "dependency-injection"],
    "avoided_patterns": ["god-objects", "premature-optimization"],
    "testing_level": "bdd+unit+integration",
    "testing_framework": "pytest",
    "coverage_min": "80%",
    "branch_strategy": "trunk-based",
    "conventions": {
        "naming": "snake_case",
        "formatting": "ruff",
        "imports": "isort",
    },
}

# ── LangFuse (optional) ──────────────────────────────────────────────

# langfuse_handler = create_langfuse_handler(
#     hdu_id="HDU-01",
#     developer_id="dev-1",
#     project_name="my-project",
#     public_key="pk-lf-...",
#     secret_key="sk-lf-...",
# )

# ── Run Pipeline ─────────────────────────────────────────────────────

if __name__ == "__main__":
    graph = SupervisorGraph(
        profile=PROFILE,
        engram_mcp_available=True,
        # langfuse_handler=langfuse_handler,
    )

    # Run complete pipeline
    result = graph.invoke(
        hdu_id="HDU-01",
        hdu_title="User Authentication",
        spec_path="openspec/changes/HDU-01",
    )

    print(f"Pipeline completed: {result.get('phase')}")
    print(f"Token usage: {result.get('token_usage')}")
    print(f"Security alerts: {len(result.get('security_alerts', []))}")
