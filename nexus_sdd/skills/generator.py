"""
Skill Generator — "Fabrica de Skills" automatizada.

Toma un prompt descriptivo ("Reglas de Testing en React Testing Library")
y genera un archivo SKILL.md perfectamente formateado con:
  - YAML frontmatter (name, triggers, category, stack)
  - Reglas de comportamiento
  - Do's y Don'ts
  - Comandos Bash/MCP recomendados
  - Integracion con OpenSpec y Engram
"""

from __future__ import annotations

from pathlib import Path

SKILL_TEMPLATE = """---
name: {name}
description: {description}
category: {category}
stack: [{stack}]
triggers: [{triggers}]
---

# {title}

{description}

## Agent Attitude
{attitude}

## Rules
{rules}

## Do's
{dos}

## Don'ts
{donts}

## Recommended Commands
{commands}

## OpenSpec Integration
When working on a spec that involves {domain}, the agent MUST:
1. Reference this skill's rules during the PLAN phase
2. Apply Do's during the CODE phase
3. Verify Don'ts during the SECURITY phase

## Engram Memory Hints
After applying this skill, save to Engram:
```bash
engram save "Applied {name} to {domain} module" \\
  "Used {name} patterns. Key decisions: ..." \\
  --type pattern --project $PROJECT
```
"""


class SkillGenerator:
    """Generates SKILL.md files from prompts and internal knowledge."""

    def __init__(self, output_dir: Path | None = None):
        self.output_dir = output_dir or Path(".nexus/skills/generated")

    def generate(
        self,
        name: str,
        description: str,
        category: str,
        stack: str,
        triggers: str,
        attitude: str,
        rules: str,
        dos: str,
        donts: str,
        domain: str,
        title: str | None = None,
    ) -> Path:
        """Generate a SKILL.md file from parameters."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        content = SKILL_TEMPLATE.format(
            name=name,
            description=description,
            category=category,
            stack=stack,
            triggers=triggers,
            title=title or f"{name} Skill",
            attitude=attitude,
            rules=rules,
            dos=dos,
            donts=donts,
            commands="- `npm test -- --coverage` — Run tests with coverage",
            domain=domain,
        )

        filepath = self.output_dir / f"{name}.md"
        filepath.write_text(content)
        return filepath

    def generate_from_prompt(self, prompt: str, model_knowledge: str = "") -> Path:
        """Generate a skill from a natural language prompt.

        This is the "magic" function that would use an LLM sub-agent
        to research the topic and fill in the template. In the CLI,
        this triggers a sub-agent with web access.

        Args:
            prompt: e.g., "Reglas de Testing en React Testing Library"
            model_knowledge: Optional knowledge injected from the model
        """
        # In the CLI, this spawns a LangGraph sub-agent that:
        # 1. Searches the web for best practices on the topic
        # 2. Extracts rules, do's, don'ts
        # 3. Fills the SKILL_TEMPLATE
        # 4. Saves to .nexus/skills/generated/

        slug = prompt.lower().replace(" ", "-")[:60]
        # Placeholder — the real implementation uses LLM
        return self.generate(
            name=slug,
            description=prompt,
            category="generated",
            stack="auto-detected",
            triggers=prompt.lower(),
            attitude=f"Apply best practices for: {prompt}",
            rules=f"- Follow community standards for {prompt}\n- Write tests before implementation",
            dos=f"- Do follow {prompt} conventions\n- Do write readable assertions",
            donts=f"- Don't ignore {prompt} best practices\n- Don't test implementation details",
            domain=prompt,
        )
