"""
Test Agent — Fase 4: Testing Automatico (BDD + Unit + Integration).

Ejecuta tests en modo Ralph Loop: test → falla → corrige → test → pasa.
Soporta BDD (Gherkin/Behave/Cucumber) ademas de unit/integration/e2e.

Actitud: QA Engineer meticuloso. No acepta "funciona en mi maquina".
"""

from __future__ import annotations

from nexus_sdd.harness.state import AgentState


TEST_SYSTEM_PROMPT = """ERES un QA ENGINEER operando en fase TEST.

TU ACTITUD:
- Testea CONTRA el spec.md, no contra el codigo.
- Todo escenario BDD debe tener su test automatizado.
- Si un test falla, el code_agent debe corregirlo (Ralph Loop).
- No aceptes tests que pasan "de casualidad" (flaky tests).
- Si la cobertura baja del umbral, reportalo como bloqueante.

RALPH LOOP (Auto-correccion):
1. Ejecutar tests
2. Si fallan → notificar al code_agent con el error exacto
3. Esperar correccion
4. Re-ejecutar tests
5. Repetir hasta que pasen (max 3 iteraciones, luego escalar al humano)

TIPOS DE TESTING SEGUN PERFIL:
- unit: Testeo de funciones/clases aisladas
- integration: Testeo de modulos conectados
- e2e: Testeo de flujo completo (Playwright/Cypress)
- bdd: Testeo de comportamiento (Gherkin/Behave/Cucumber)

REPORTE DE TOKENS junto con resultados de tests.
"""


def build_test_agent(profile: dict, engram_available: bool = False):
    """Builds the Test Agent node."""

    def test_agent(state: AgentState) -> AgentState:
        hdu_id = state.get("hdu_id", "unknown")
        spec_path = state.get("spec_path", "")
        testing_level = profile.get("testing_level", "unit+integration")

        prompt = f"""{TEST_SYSTEM_PROMPT}

## HDU: {hdu_id}
## Spec Path: {spec_path}

## Nivel de Testing Requerido: {testing_level}

## Perfil del Proyecto
- Testing Framework: {profile.get('testing_framework', 'pytest')}
- Stack: {profile.get('stack', [])}
- Coverage Minima: {profile.get('coverage_min', '80%')}

## Instrucciones
1. Lee {spec_path}/specs/{hdu_id}.md para conocer los escenarios BDD
2. Lee {spec_path}/plan.md para entender la estructura esperada
3. Ejecuta el test runner del proyecto
4. Para cada fallo:
   a. Documenta el error exacto (mensaje + stack trace + archivo)
   b. Si es un error del codigo → notifica al code_agent (Ralph Loop)
   c. Si es un error del test → corrige el test
5. Si todos pasan → verifica cobertura
6. Genera reporte en {spec_path}/test-report.md
"""

        state["messages"] = state.get("messages", []) + [
            {"role": "system", "content": TEST_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        return state

    return test_agent
