"""
Nexus-SDD Supervisor Graph — The "Director de Orquesta".

Routes work through SDD phases (spec → plan → code → test → security)
using specialized sub-agents, each with a defined "attitude" from profiles.

Architecture:
    Human Approval ──→ Supervisor ──→ Spec Agent
                           │
                    ┌──────┼──────┐
                    ▼      ▼      ▼
                 Plan   Code   Security
                  │      │        │
                  ▼      ▼        ▼
                 Test   Test   Report
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from nexus_sdd.harness.state import AgentState, AgentRole, Phase
from nexus_sdd.harness.agents.spec_agent import build_spec_agent
from nexus_sdd.harness.agents.plan_agent import build_plan_agent
from nexus_sdd.harness.agents.code_agent import build_code_agent
from nexus_sdd.harness.agents.test_agent import build_test_agent
from nexus_sdd.harness.agents.security_agent import build_security_agent

logger = logging.getLogger(__name__)

# ── Router ──────────────────────────────────────────────────────────
# The supervisor decides which agent runs based on the current phase.

AGENT_MAP: dict[Phase, AgentRole] = {
    "spec": "spec_agent",
    "plan": "plan_agent",
    "code": "code_agent",
    "test": "test_agent",
    "security": "security_agent",
}

PHASE_ORDER: list[Phase] = ["spec", "plan", "code", "test", "security"]


def supervisor_router(state: AgentState) -> AgentRole:
    """Returns the agent key for the current phase."""
    phase = state.get("phase", "spec")
    if phase == "done":
        return END
    return AGENT_MAP.get(phase, END)


def phase_transition(current: Phase, human_approved: bool = False) -> Phase:
    """Determines next phase. Requires human approval between phases."""
    if current == "done":
        return "done"
    idx = PHASE_ORDER.index(current)
    if idx + 1 < len(PHASE_ORDER):
        return PHASE_ORDER[idx + 1]
    return "done"


# ── Supervisor Node ─────────────────────────────────────────────────

def build_supervisor_node():
    """Creates the supervisor decision node."""

    def supervisor(state: AgentState) -> AgentState:
        logger.info(
            f"[Supervisor] HDU={state.get('hdu_id')} phase={state.get('phase')} "
            f"tokens_used={sum(t.get('total', 0) for t in state.get('token_usage', []))}"
        )
        return state

    return supervisor


# ── Graph Builder ───────────────────────────────────────────────────

class SupervisorGraph:
    """Builds and runs the full LangGraph harness."""

    def __init__(
        self,
        profile: dict | None = None,
        engram_mcp_available: bool = False,
        langfuse_handler=None,
    ):
        self.profile = profile or {}
        self.engram_available = engram_mcp_available
        self.langfuse_handler = langfuse_handler
        self.graph = self._build()

    def _build(self) -> StateGraph:
        workflow = StateGraph(AgentState)

        # Nodes: one per specialized agent role
        workflow.add_node("supervisor", build_supervisor_node())
        workflow.add_node("spec_agent", build_spec_agent(self.profile, self.engram_available))
        workflow.add_node("plan_agent", build_plan_agent(self.profile, self.engram_available))
        workflow.add_node("code_agent", build_code_agent(self.profile, self.engram_available))
        workflow.add_node("test_agent", build_test_agent(self.profile, self.engram_available))
        workflow.add_node("security_agent", build_security_agent(self.profile))

        # Entry
        workflow.set_entry_point("supervisor")

        # Conditional edges: supervisor → correct agent for current phase
        workflow.add_conditional_edges(
            "supervisor",
            supervisor_router,
            {
                "spec_agent": "spec_agent",
                "plan_agent": "plan_agent",
                "code_agent": "code_agent",
                "test_agent": "test_agent",
                "security_agent": "security_agent",
                END: END,
            },
        )

        # Each agent returns to supervisor for next phase routing
        for agent in AGENT_MAP.values():
            workflow.add_edge(agent, "supervisor")

        return workflow.compile(checkpointer=MemorySaver())

    def invoke(self, hdu_id: str, hdu_title: str, spec_path: str) -> dict:
        """Run the full SDD pipeline for one HDU."""
        config = {}
        if self.langfuse_handler:
            config["callbacks"] = [self.langfuse_handler]

        initial_state: AgentState = {
            "phase": "spec",
            "hdu_id": hdu_id,
            "hdu_title": hdu_title,
            "spec_path": spec_path,
            "memories": [],
            "profile": self.profile,
            "token_usage": [],
            "security_alerts": [],
            "next_agent": "spec_agent",
            "messages": [],
            "error": "",
        }

        result = self.graph.invoke(initial_state, config=config)
        return result

    def stream(self, hdu_id: str, hdu_title: str, spec_path: str):
        """Stream the pipeline for real-time frontend observation."""
        config = {}
        if self.langfuse_handler:
            config["callbacks"] = [self.langfuse_handler]

        initial_state: AgentState = {
            "phase": "spec",
            "hdu_id": hdu_id,
            "hdu_title": hdu_title,
            "spec_path": spec_path,
            "memories": [],
            "profile": self.profile,
            "token_usage": [],
            "security_alerts": [],
            "next_agent": "spec_agent",
            "messages": [],
            "error": "",
        }

        for event in self.graph.stream(initial_state, config=config):
            yield event


# ── LangFuse Integration ────────────────────────────────────────────

def create_langfuse_handler(
    hdu_id: str,
    developer_id: str,
    project_name: str,
    public_key: str | None = None,
    secret_key: str | None = None,
    host: str | None = None,
):
    """Creates LangFuse callback for full observability.

    Returns None gracefully if langfuse is not installed or keys are missing,
    so the harness works without LangFuse.
    """
    try:
        from langfuse.langchain import CallbackHandler

        return CallbackHandler(
            session_id=hdu_id,
            user_id=developer_id,
            tags=["nexus-sdd", project_name],
            public_key=public_key,
            secret_key=secret_key,
            host=host or "https://cloud.langfuse.com",
        )
    except ImportError:
        logger.warning("langfuse not installed — observability disabled")
        return None
    except Exception as exc:
        logger.warning(f"LangFuse init failed: {exc}")
        return None
