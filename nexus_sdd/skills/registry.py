"""
Skill Registry — Catalogo de skills disponibles.

Cada skill es un archivo SKILL.md con:
  - YAML frontmatter (name, triggers, category, stack)
  - Reglas de comportamiento para el agente
  - Comandos y herramientas recomendadas

El registry detecta que skills estan instaladas y cuales
faltan segun el stack del proyecto.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Skill:
    name: str
    category: str  # web, mobile, backend, testing, language, infra
    stack: list[str] = field(default_factory=list)
    triggers: list[str] = field(default_factory=list)
    path: Path | None = None
    installed: bool = False

    @classmethod
    def from_markdown(cls, filepath: Path) -> "Skill | None":
        """Parse a SKILL.md file into a Skill object."""
        content = filepath.read_text()
        frontmatter = _parse_frontmatter(content)

        if not frontmatter:
            return None

        return cls(
            name=frontmatter.get("name", filepath.stem),
            category=frontmatter.get("category", "unknown"),
            stack=frontmatter.get("stack", []),
            triggers=frontmatter.get("triggers", []),
            path=filepath,
            installed=True,
        )


def _parse_frontmatter(content: str) -> dict | None:
    """Extract YAML frontmatter from markdown."""
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return None

    end_idx = -1
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx == -1:
        return None

    try:
        import yaml
        return yaml.safe_load("\n".join(lines[1:end_idx]))
    except ImportError:
        # Minimal YAML parser fallback
        result = {}
        for line in lines[1:end_idx]:
            line = line.strip()
            if ":" in line and not line.startswith("#"):
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if value.startswith("[") and value.endswith("]"):
                    value = [v.strip().strip('"').strip("'") for v in value[1:-1].split(",") if v.strip()]
                result[key] = value
        return result


class SkillRegistry:
    """Manages the catalog of available and installed skills."""

    def __init__(self, skills_dir: Path | None = None):
        self.skills_dir = skills_dir or Path(__file__).parent.parent.parent / "skills"
        self.catalog: dict[str, Skill] = {}
        self._load_catalog()

    def _load_catalog(self):
        """Scan the skills directory for all SKILL.md files."""
        if not self.skills_dir.exists():
            return

        for skill_file in self.skills_dir.rglob("**/SKILL.md"):
            skill = Skill.from_markdown(skill_file)
            if skill:
                self.catalog[skill.name] = skill

    def list_available(self) -> list[Skill]:
        return list(self.catalog.values())

    def list_by_category(self, category: str) -> list[Skill]:
        return [s for s in self.catalog.values() if s.category == category]

    def get(self, name: str) -> Skill | None:
        return self.catalog.get(name)

    def recommend_for_stack(self, detected_stack: list[str]) -> list[Skill]:
        """Recommend skills matching a detected tech stack."""
        recommended = []
        stack_lower = [s.lower() for s in detected_stack]
        for skill in self.catalog.values():
            skill_stack = [s.lower() for s in skill.stack]
            if any(s in stack_lower for s in skill_stack):
                recommended.append(skill)
        return recommended

    def install_skill(self, skill_name: str, target_dir: Path) -> bool:
        """Copy a skill from catalog to project .nexus/skills/."""
        skill = self.catalog.get(skill_name)
        if not skill or not skill.path:
            return False

        target = target_dir / f"{skill_name}.md"
        target.write_text(skill.path.read_text())
        return True

    def install_for_project(self, recommended: list[str], target_dir: Path) -> list[str]:
        """Install all recommended skills. Returns list of installed names."""
        installed = []
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in recommended:
            if self.install_skill(name, target_dir):
                installed.append(name)
        return installed
