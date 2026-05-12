"""
Code Agent — Fase 3: Generacion de Codigo.

SIGUE el plan al pie de la letra. No improvisa.
Ejecuta en contenedor aislado si esta configurado.
Cada archivo generado pasa por el security middleware.

Actitud: Desarrollador Senior disciplinado. Sin "vibe coding".
"""

from __future__ import annotations

from nexus_sdd.harness.state import AgentState


CODE_SYSTEM_PROMPT = """ERES un DESARROLLADOR SENIOR operando en fase CODE.

TU ACTITUD:
- SIGUE el plan.md. NO improvises features no especificadas.
- Aplica los patrones del perfil del equipo.
- Cada archivo que generes debe tener su test correspondiente.
- NO hardcodees configuracion, secrets, ni URLs.
- Usa las herramientas del proyecto (linter, formatter, type checker).
- Antes de escribir, verifica que el security middleware no detecte riesgos.

REGLAS ESTRICTAS:
1. Lee el plan.md completo antes de tocar codigo.
2. Un archivo a la vez. Escribe → test → siguiente.
3. Si el test falla, corrijelo ANTES de continuar (Ralph Loop).
4. Nunca borres tests existentes.
5. Si encuentras un bug en codigo existente, reportalo. No lo arregles en esta fase.

ANTIPATRONES PROHIBIDOS:
- God objects / clases de +500 lineas
- Funciones con +5 parametros
- Magia numbers sin nombre
- Comentarios que dicen LO QUE hace el codigo (el codigo ya lo dice)
- Early returns sin manejo de errores

REPORTE DE TOKENS cada 3 acciones significativas.
"""


def build_code_agent(profile: dict, engram_available: bool = False):
    """Builds the Code Agent node."""

    def code_agent(state: AgentState) -> AgentState:
        hdu_id = state.get("hdu_id", "unknown")
        spec_path = state.get("spec_path", "")
        memories = state.get("memories", [])

        # Build context from plan and memory
        memory_hint = ""
        if memories:
            bugs = [m for m in memories if m.get("type") == "bug"]
            if bugs:
                memory_hint = "\n## Bugs Pasados (Engram) — NO repitas estos errores\n"
                for b in bugs:
                    memory_hint += f"- {b.get('title')}: {b.get('content')}\n"

        prompt = f"""{CODE_SYSTEM_PROMPT}

## HDU: {hdu_id}
## Spec Path: {spec_path}

## Perfil del Desarrollador
- Fortalezas: {profile.get('strengths', [])}
- Debilidades: {profile.get('weaknesses', [])} (presta mas atencion aqui)
- Patrones Preferidos: {profile.get('preferred_patterns', [])}
- Patrones Evitados: {profile.get('avoided_patterns', [])}
- Nivel de Testing: {profile.get('testing_level', 'unit+integration')}
{memory_hint}

## Instrucciones
1. Lee {spec_path}/plan.md
2. Implementa las tareas en orden, una por una
3. Cada archivo → su test → verificar → siguiente
4. Reporta tokens regularmente
"""

        state["messages"] = state.get("messages", []) + [
            {"role": "system", "content": CODE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        return state

    return code_agent
