"""
Plan Agent — Fase 2: Planificacion Tecnica.

Lee el spec.md y design.md de la fase anterior.
Desglosa en pasos tecnicos concretos con dependencias.
Consulta Engram para recuperar decisiones pasadas similares.

Actitud: Tech Lead. Pragmatico. Conoce los patrones del equipo.
"""

from __future__ import annotations

from nexus_sdd.harness.state import AgentState


PLAN_SYSTEM_PROMPT = """ERES un TECH LEAD operando en fase PLAN.

TU ACTITUD:
- Lee el spec.md y design.md ANTES de planificar.
- Busca en Engram: ¿como resolvimos esto antes? ¿que errores cometimos?
- Respeta los patrones preferidos del perfil del equipo.
- Si el perfil dice "evitar God Objects", NO los sugieras.
- Estima complejidad por tarea: low/medium/high.
- Marca dependencias entre tareas (task-A bloquea task-B).

ENTREGABLES:
1. Plan detallado con pasos tecnicos
2. Dependencias entre pasos
3. Estimacion de complejidad por paso
4. Referencias a memorias Engram relevantes (si existen)

REPORTE DE TOKENS al final.
"""


def build_plan_agent(profile: dict, engram_available: bool = False):
    """Builds the Plan Agent node."""

    def plan_agent(state: AgentState) -> AgentState:
        hdu_id = state.get("hdu_id", "unknown")
        spec_path = state.get("spec_path", "")
        memories = state.get("memories", [])

        # Build memory context from Engram
        memory_context = ""
        if memories:
            memory_context = "\n## Memorias Relevantes (Engram)\n"
            for mem in memories:
                memory_context += f"- [{mem.get('type', 'note')}] {mem.get('title', '')}: {mem.get('content', '')}\n"
        elif engram_available:
            memory_context = (
                "\n## Engram Disponible\n"
                "Usa mem_search para buscar decisiones pasadas relevantes "
                "antes de planificar.\n"
            )

        prompt = f"""{PLAN_SYSTEM_PROMPT}

## HDU: {hdu_id}
## Spec Path: {spec_path}

## Perfil del Equipo
- Convenciones: {profile.get('conventions', {})}
- Patrones Preferidos: {profile.get('preferred_patterns', [])}
- Patrones Evitados: {profile.get('avoided_patterns', [])}
- Estrategia de Branching: {profile.get('branch_strategy', 'trunk-based')}
{memory_context}

## Instrucciones
1. Lee {spec_path}/specs/{hdu_id}.md
2. Lee {spec_path}/design.md
3. Genera el plan de implementacion detallado
4. Escribe el plan en {spec_path}/plan.md
5. Marca dependencias entre tareas
6. Reporta tokens usados
"""

        state["messages"] = state.get("messages", []) + [
            {"role": "system", "content": PLAN_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        return state

    return plan_agent
