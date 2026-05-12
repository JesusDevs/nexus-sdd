"""
Spec Agent — Fase 1: Especificacion (OpenSpec).

NO escribe codigo. Solo genera artefactos de especificacion:
  - proposal.md (por que, que cambia)
  - specs/*.md (requisitos y escenarios BDD)
  - design.md (enfoque tecnico)
  - tasks.md (checklist de implementacion)

Actitud: Arquitecto. Documenta antes de actuar. Cada decision
tiene un rationale explicito.
"""

from __future__ import annotations

from nexus_sdd.harness.state import AgentState


SPEC_SYSTEM_PROMPT = """ERES un ARQUITECTO DE SOFTWARE operando en fase SPEC.

TU ACTITUD:
- NO escribas codigo. Solo artefactos de especificacion.
- Cada requisito funcional debe tener su escenario BDD (Given/When/Then).
- Cada decision de arquitectura requiere un rationale documentado.
- Si detectas ambiguedad, NO la resuelvas solo — documentala como pregunta para el humano.
- Consulta la memoria del proyecto (Engram) antes de decidir: ¿ya se intento esto antes?

ENTREGABLES OBLIGATORIOS:
1. proposal.md — ¿Por que hacemos esto? ¿Que cambia? ¿Que NO cambia?
2. specs/{hdu_id}.md — Requisitos funcionales con escenarios BDD
3. design.md — Enfoque tecnico, trade-offs, alternativas consideradas
4. tasks.md — Checklist ordenado de implementacion

REPORTE DE TOKENS:
Al final de tu respuesta, incluye un bloque:
```
---
tokens_usados: {prompt}/{completion}
costo_estimado_usd: {costo}
---
```
"""


def build_spec_agent(profile: dict, engram_available: bool = False):
    """Builds the Spec Agent node for the LangGraph harness."""

    def spec_agent(state: AgentState) -> AgentState:
        import os
        from pathlib import Path

        hdu_id = state.get("hdu_id", "unknown")
        hdu_title = state.get("hdu_title", "")
        spec_path = state.get("spec_path", f"openspec/changes/{hdu_id}")

        # Ensure OpenSpec directory structure
        Path(spec_path).mkdir(parents=True, exist_ok=True)
        Path(f"{spec_path}/specs").mkdir(parents=True, exist_ok=True)

        # Build the spec prompt
        prompt = f"""{SPEC_SYSTEM_PROMPT}

## HDU Actual: {hdu_id}
**Titulo**: {hdu_title}

## Perfil del Proyecto
- Stack: {profile.get('stack', [])}
- Patrones Preferidos: {profile.get('preferred_patterns', [])}
- Patrones Evitados: {profile.get('avoided_patterns', [])}
- Nivel de Testing: {profile.get('testing_level', 'unit+integration')}

## Instrucciones
Genera los 4 artefactos para esta HDU usando OpenSpec format.
Escribe cada archivo en `{spec_path}/`.

**IMPORTANTE**:
- proposal.md primero (para aprobacion humana)
- specs/{hdu_id}.md con escenarios BDD en formato Gherkin
- design.md con alternativas consideradas y trade-offs
- tasks.md con checklist ordenado y dependencias entre tareas
"""

        # Store the prompt for the LLM to process
        state["messages"] = state.get("messages", []) + [
            {"role": "system", "content": SPEC_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        # The actual LLM call is handled by the LangGraph agent executor
        # This node prepares the context; the model generates the specs
        return state

    return spec_agent
