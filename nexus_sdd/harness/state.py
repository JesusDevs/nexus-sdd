"""Shared state definitions for the Nexus-SDD Harness."""

from dataclasses import dataclass, field
from typing import TypedDict, Literal, Any

Phase = Literal["spec", "plan", "code", "test", "security", "done"]
AgentRole = Literal["spec_agent", "plan_agent", "code_agent", "test_agent", "security_agent"]


class TokenUsage(TypedDict):
    prompt: int
    completion: int
    total: int
    cost_usd: float


class HDUStatus(TypedDict):
    hdu_id: str
    title: str
    phase: Phase
    agent: AgentRole
    token_usage: list[TokenUsage]
    memory_ids: list[str]


class AgentState(TypedDict):
    phase: Phase
    hdu_id: str
    hdu_title: str
    spec_path: str
    memories: list[dict]
    profile: dict[str, Any]
    token_usage: list[TokenUsage]
    security_alerts: list[str]
    next_agent: AgentRole
    messages: list[dict]
    error: str


@dataclass
class DeveloperProfile:
    name: str
    role: str
    strengths: list[str]
    weaknesses: list[str]
    preferred_patterns: list[str]
    avoided_patterns: list[str]
    testing_level: str  # unit, integration, e2e, bdd
    stack: list[str]
    languages: list[str]


@dataclass
class TeamProfile:
    name: str
    conventions: dict[str, str]
    review_checklist: list[str]
    branch_strategy: str
    ci_cd: dict[str, str]


@dataclass
class ProjectProfile:
    name: str
    type: str  # web, mobile, backend, cli, library
    detected_stack: dict[str, list[str]]
    architecture: str
    testing_framework: str
