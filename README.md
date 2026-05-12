# 🏭 Nexus-SDD — Fábrica de Software IA

**Zero-Friction Spec-Driven Development Framework.**

Una CLI auto-instalable que transforma la IA de "chatbot avanzado" a Fábrica de Software Industrial.

```bash
nexus-sdd init && nexus-sdd spec "Mi primer feature"
```

## El Problema

Los agentes de IA programan "por vibra" (vibe coding). Generan código a velocidad increíble... pero también generan **deuda técnica gigante** a velocidad increíble.

Nexus-SDD es la **capa de control** que le falta a la IA:

- ✅ Obliga a **planificar** antes de escribir código (OpenSpec)
- ✅ Divide el trabajo en **fases estrictas** (SDD)
- ✅ **Memoria institucional** que sobrevive a sesiones (Engram)
- ✅ **Seguridad automática** — bloquea leaks de API keys antes del commit
- ✅ **Auto-corrección** — Ralph Loop: test → falla → corrige → test → pasa
- ✅ **BDD nativo** — cada especificación es un test ejecutable
- ✅ **Zero-Friction** — un comando. Sin bases de datos externas.

## Quick Start

```bash
# 1. Clona Nexus-SDD
git clone https://github.com/nexus-sdd/nexus-sdd.git
cd nexus-sdd

# 2. Instala TODO (auto-detecta tu stack)
./install.sh

# 3. Crea tu primera especificación
nexus-sdd spec "Login con OAuth2"

# 4. Revisa el progreso
nexus-sdd status
```

## Arquitectura

```
┌──────────────────────────────────────────────────────────────┐
│                    NEXUS-SDD (Orquestador)                    │
│  CLI │ Security Middleware │ Skill Factory │ Hermes Cron     │
├──────────────────────────────────────────────────────────────┤
│              LANGGRAPH HARNESS (Supervisor)                   │
│  spec_agent → plan_agent → code_agent → test_agent → sec     │
├──────────────────────────────────────────────────────────────┤
│              OPENSPEC (Spec-Driven Development)               │
│  proposal.md │ specs/*.md │ design.md │ tasks.md             │
├──────────────────────────────────────────────────────────────┤
│              ENGRAM (Memoria Persistente)                     │
│  SQLite + FTS5 │ MCP (19 tools) │ Sync │ Cloud │ TUI        │
├──────────────────────────────────────────────────────────────┤
│              LANGGRAPH HARNESS (Supervisor)                   │
│  spec_agent → plan_agent → code_agent → test_agent → sec     │
├──────────────────────────────────────────────────────────────┤
│              OPENSPEC (Spec-Driven Development)               │
│  proposal.md │ specs/*.md │ design.md │ tasks.md             │
├──────────────────────────────────────────────────────────────┤
│              ENGRAM (Memoria Persistente)                     │
│  SQLite + FTS5 │ MCP (19 tools) │ Sync │ Cloud │ TUI        │
└──────────────────────────────────────────────────────────────┘
```

## Flujo de Desarrollo (SDD + BDD)

```
nexus-sdd spec "Feature X"
    └─→ OpenSpec: proposal.md + specs/*.md + design.md + tasks.md
        └─→ BDD: escenarios Gherkin (Given/When/Then) en specs/

nexus-sdd plan --hdu-id HDU-01
    └─→ LangGraph Plan Agent + consulta Engram (¿ya hicimos esto antes?)
        └─→ plan.md con dependencias y estimaciones

nexus-sdd build --hdu-id HDU-01
    └─→ LangGraph Code Agent + Security Middleware activo
        └─→ Cada archivo escaneado por API keys/secrets
            └─→ Si detecta leak: BLOQUEA + genera alerta en .nexus/alerts/

nexus-sdd test --hdu-id HDU-01
    └─→ Ralph Loop: test → falla → corrige → test → pasa (max 3 ciclos)
        └─→ BDD + Unit + Integration + E2E

nexus-sdd security
    └─→ Escaneo completo del proyecto
        └─→ Reporte en .nexus/alerts/security_leak_blocked.md (si hay hallazgos)

nexus-sdd status
    └─→ Tablero ejecutivo: HDUs, fases, progreso, costo en tokens
```

## Stack Detection (Automático)

Nexus-SDD detecta automáticamente el stack de tu proyecto y te instala las skills que necesitas:

| Detecta | Skills Instaladas |
|---------|-------------------|
| `package.json` + `next.config.js` + `tailwind.config.ts` | `react`, `nextjs`, `typescript-strict`, `vitest` |
| `pubspec.yaml` + `lib/main.dart` | `flutter`, `dart-effective`, `flutter-test` |
| `build.gradle.kts` + `shared/` | `kotlin-kmp`, `kotlin-idiomatic`, `detekt` |
| `pyproject.toml` + `fastapi` | `fastapi`, `python-best-practices`, `pytest`, `bdd-behave` |
| `go.mod` + `gin` | `go-idiomatic`, `go-fiber` (o gin) |

## Comandos

| Comando | Descripción |
|---------|-------------|
| `nexus-sdd init` | Detecta stack, instala skills, configura agentes |
| `nexus-sdd spec "Titulo"` | Crea especificación OpenSpec + BDD |
| `nexus-sdd plan --hdu-id ID` | Plan de implementación (LangGraph Plan Agent) |
| `nexus-sdd build --hdu-id ID` | Generación de código (Code Agent + Security) |
| `nexus-sdd test --hdu-id ID` | Tests BDD + Unit + Integration + Ralph Loop |
| `nexus-sdd security` | Escaneo de API keys, secrets, vulnerabilidades |
| `nexus-sdd status` | Tablero ejecutivo de progreso |
| `nexus-sdd skill generate "..."` | Genera una skill desde un prompt |
| `nexus-sdd skill list` | Lista el catálogo de skills disponibles |
| `nexus-sdd skill install <name>` | Instala una skill en el proyecto |
| `nexus-sdd cron add --schedule "0 9 * * 1-5" --command "..."` | Programa tareas (Hermes) |

## Skills Catalog

### Web
- **react** — React 18+ con Server Components, hooks, Tailwind
- **vue** — Vue 3 Composition API, Pinia, TypeScript
- **nextjs** — Next.js App Router, Server Actions, ISR, streaming
- **svelte** — Svelte 5 runes, SvelteKit

### Mobile
- **kotlin-kmp** — Kotlin Multiplatform con Compose Multiplatform
- **flutter** — Flutter + Dart 3, Riverpod, arquitectura limpia
- **swiftui** — SwiftUI moderno con MVVM

### Backend
- **fastapi** — FastAPI async, Pydantic v2, SQLAlchemy 2.0
- **django** — Django 5.0+ DRF, service layer, N+1 prevention
- **go-fiber** — Go + Fiber, GORM, clean architecture

### Testing
- **bdd-behave** — BDD con Gherkin/Behave + pytest-bdd
- **playwright** — E2E cross-browser, fixtures, tracing
- **vitest** — Unit + integration testing rápido

## Seguridad (Middleware)

Nexus-SDD incluye un **Security Middleware** que escanea cada archivo antes del commit:

```
Patrones detectados:
├─ API Keys: sk-ant-api..., sk-or..., sk-..., pk_live..., ghp_..., glpat-...
├─ Secrets: password=, secret=, private_key=
├─ Conexiones: mongodb://user:pass@..., postgres://user:pass@...
├─ Tokens: Bearer ... , xox[bpras]-...
└─ Private Keys: -----BEGIN PRIVATE KEY-----

Si detecta algo:
├─ BLOQUEA el commit
├─ Revierte el archivo
└─ Genera .nexus/alerts/security_leak_blocked.md
```

## Ralph Loop (Auto-Corrección)

El agente de testing implementa el **Ralph Loop**:

```
1. Ejecutar todos los tests
2. Si pasan → ✅ Continuar
3. Si fallan → Enviar error exacto al code_agent
4. code_agent corrige → Vuelve a 1
5. Máximo 3 iteraciones → Si sigue fallando, escala al humano
```

## Perfiles

Cada proyecto tiene perfiles que definen la "actitud" del agente:

```yaml
# .nexus/profiles/developer.profile.yaml
name: developer
strengths: [backend, Rust, testing]
weaknesses: [CSS, accessibility]
preferred_patterns: [repository-pattern, TDD]
avoided_patterns: [god-objects, premature-optimization]
testing_level: bdd+unit+integration
```

El agente adapta su comportamiento:
- **Fortalezas**: Asume que el código en estas áreas es correcto, no sobre-explica
- **Debilidades**: Presta más atención, explica decisiones, sugiere buenas prácticas
- **Patrones preferidos**: Aplica por defecto
- **Patrones evitados**: Nunca los sugiere

## Engram — Memoria Institucional

```bash
# El agente recuerda entre sesiones
engram save "Patron de autenticacion usado en HDU-01" \
  "Implementamos OAuth2 con PKCE. Clean Architecture + Repository Pattern." \
  --type architecture --project banking-app

# Semanas después, en otro feature...
engram search "autenticacion OAuth2"
# → Recupera la decisión, el patrón, y el resultado
```

## Transportabilidad

Todo vive en `.nexus/` y en `AGENTS.md`. Si compartes el repo:

```
otro-dev/ $ git clone proyecto
otro-dev/ $ cd proyecto
# Claude Code/Cursor lee AGENTS.md → se auto-configura
# .nexus/skills/ están listas
# .nexus/profiles/ definen el comportamiento
# Engram recuerda el historial del proyecto
```

## Licencia

MIT — Open Source. La comunidad es dueña del estándar.
