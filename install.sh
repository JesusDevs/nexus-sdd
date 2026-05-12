#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════════════
# Nexus-SDD Universal Installer
# "One command to rule them all"
#
# Usage:
#   curl -fsSL https://nexus-sdd.dev/install.sh | bash
#   # or locally:
#   ./install.sh
#
# What it does:
#   1. Detects OS and installs prerequisites (Python, Node, Go)
#   2. Installs OpenSpec CLI (spec-driven development)
#   3. Installs Engram (agent memory)
#   4. Installs Engram-Vec (vector memory extension)
#   5. Installs Ollama + embedding model (local, zero-cost)
#   6. Sets up LangGraph harness + supervisor
#   7. Installs LangFuse for observability
#   8. Detects project tech stack
#   9. Installs matching skills
#   8. Configures Claude Code / Cursor / Windsurf / OpenCode
#   9. Creates .nexus/ directory structure
# ═══════════════════════════════════════════════════════════════════════

# ── Colors ───────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log()    { echo -e "${BLUE}[NEXUS]${NC} $1"; }
ok()     { echo -e "${GREEN}[✓]${NC} $1"; }
warn()   { echo -e "${YELLOW}[!]${NC} $1"; }
err()    { echo -e "${RED}[✗]${NC} $1"; }
header() { echo -e "\n${BOLD}${CYAN}═══ $1 ═══${NC}\n"; }

# ── Detect OS ────────────────────────────────────────────────────────
detect_os() {
    case "$(uname -s)" in
        Darwin)  OS="macos" ;;
        Linux)   OS="linux" ;;
        MINGW*|MSYS*|CYGWIN*) OS="windows" ;;
        *)       err "OS no soportado: $(uname -s)"; exit 1 ;;
    esac
    log "OS detectado: ${OS}"
}

# ── Check/Install Prerequisites ───────────────────────────────────────
install_python() {
    if command -v python3 &>/dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        if [[ "${PYTHON_VERSION%.*}" -ge 3 && "${PYTHON_VERSION#*.}" -ge 11 ]]; then
            ok "Python ${PYTHON_VERSION} encontrado"
            return
        fi
    fi
    warn "Python 3.11+ requerido. Instalando..."
    case "$OS" in
        macos)
            if command -v brew &>/dev/null; then
                brew install python@3.12
            else
                err "Instala Homebrew primero: https://brew.sh"
                exit 1
            fi
            ;;
        linux)
            sudo apt-get update -qq && sudo apt-get install -y python3.12 python3-pip python3.12-venv
            ;;
        windows)
            err "En Windows, instala Python desde https://python.org"
            exit 1
            ;;
    esac
    ok "Python instalado"
}

install_node() {
    if command -v node &>/dev/null; then
        NODE_VERSION=$(node -v | sed 's/v//' | cut -d. -f1)
        if [[ "$NODE_VERSION" -ge 20 ]]; then
            ok "Node.js $(node -v) encontrado"
            return
        fi
    fi
    warn "Node.js 20+ requerido para OpenSpec. Instalando..."
    case "$OS" in
        macos) brew install node@20 ;;
        linux)
            curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
            sudo apt-get install -y nodejs
            ;;
    esac
    ok "Node.js instalado"
}

install_go() {
    if command -v go &>/dev/null; then
        ok "Go $(go version | awk '{print $3}') encontrado"
        return
    fi
    warn "Go requerido para Engram. Instalando..."
    case "$OS" in
        macos) brew install go ;;
        linux)
            curl -fsSL https://go.dev/dl/go1.22.0.linux-amd64.tar.gz | sudo tar -C /usr/local -xz
            export PATH=$PATH:/usr/local/go/bin
            ;;
    esac
    ok "Go instalado"
}

# ── Install OpenSpec ──────────────────────────────────────────────────
install_openspec() {
    header "Instalando OpenSpec (Spec-Driven Development)"
    if command -v openspec &>/dev/null; then
        ok "OpenSpec ya instalado: $(openspec version 2>/dev/null || echo 'ok')"
    else
        npm install -g @fission-ai/openspec
        ok "OpenSpec instalado globalmente"
    fi
}

# ── Install Engram ────────────────────────────────────────────────────
install_engram() {
    header "Instalando Engram (Agent Memory)"
    if command -v engram &>/dev/null; then
        ok "Engram ya instalado"
        engram version 2>/dev/null || true
    else
        case "$OS" in
            macos)
                brew install gentleman-programming/tap/engram
                ;;
            linux)
                curl -fsSL https://github.com/Gentleman-Programming/engram/releases/latest/download/engram_linux_amd64.tar.gz | sudo tar -C /usr/local/bin -xz engram
                ;;
        esac
        ok "Engram instalado"
    fi
}

# ── Install Ollama + Embedding Model ──────────────────────────────────
install_ollama() {
    header "Instalando Ollama (Embeddings Locales)"

    if command -v ollama &>/dev/null; then
        ok "Ollama CLI encontrado"
    else
        warn "Instalando Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh
        ok "Ollama instalado"
    fi

    # Verificar que el servicio corre
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        ok "Ollama servicio corriendo"
    else
        warn "Iniciando Ollama en background..."
        ollama serve &>/dev/null &
        sleep 3
    fi

    # Descargar modelo
    MODEL="bge-large-en-v1.5"
    if ollama list 2>/dev/null | grep -q "$MODEL"; then
        ok "Modelo $MODEL descargado"
    else
        warn "Descargando $MODEL (~600MB, una sola vez)..."
        ollama pull "$MODEL"
        ok "Modelo $MODEL listo"
    fi
}

# ── Install Engram-Vec ─────────────────────────────────────────────────
install_engram_vec() {
    header "Instalando Engram-Vec (Extensión Vectorial)"

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    ENGRAM_VEC_DIR="$SCRIPT_DIR/../engram-vec"

    if [[ -f "$ENGRAM_VEC_DIR/main.go" ]]; then
        cd "$ENGRAM_VEC_DIR"
        go build -o engram-vec . 2>/dev/null || {
            warn "Compilación de engram-vec falló. Bajando binario..."
        }
        if [[ -f "./engram-vec" ]]; then
            cp engram-vec /usr/local/bin/ 2>/dev/null || sudo cp engram-vec /usr/local/bin/
            ok "engram-vec instalado desde fuente"
        fi
    elif command -v engram-vec &>/dev/null; then
        ok "engram-vec ya instalado"
    else
        warn "engram-vec no encontrado. Instálalo desde:"
        warn "  https://github.com/nexus-sdd/engram-vec"
    fi
}

# ── Install Nexus-SDD Python Package ──────────────────────────────────
install_nexus() {
    header "Instalando Nexus-SDD (LangGraph Harness)"

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$SCRIPT_DIR"

    if [[ -f "pyproject.toml" ]]; then
        pip3 install -e ".[dev]" 2>/dev/null || pip3 install -e .
        ok "Nexus-SDD instalado en modo desarrollo"
    else
        warn "pyproject.toml no encontrado. Instalando desde pip..."
        pip3 install nexus-sdd
        ok "Nexus-SDD instalado desde PyPI"
    fi
}

# ── Detect Project Stack ──────────────────────────────────────────────
detect_stack() {
    header "Detectando Stack Tecnologico del Proyecto"

    # Run the Python detector
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$SCRIPT_DIR"

    python3 -c "
import sys
sys.path.insert(0, '.')
from nexus_sdd.detector.scanner import detect_project_type

project = detect_project_type()
print(f'TIPO: {project.type}')
print(f'LENGUAJES: {\", \".join(project.languages) or \"desconocido\"}')
print(f'FRAMEWORKS: {\", \".join(project.frameworks) or \"ninguno\"}')
print(f'TESTING: {\", \".join(project.testing) or \"ninguno\"}')
print(f'DB: {\", \".join(project.databases) or \"ninguna\"}')
print(f'SKILLS: {\", \".join(project.recommended_skills)}')
" 2>/dev/null || warn "Detector no disponible. Usando deteccion basica..."

    log "Stack detectado (ver arriba)"
}

# ── Install Skills ────────────────────────────────────────────────────
install_skills() {
    header "Instalando Skills para el Stack Detectado"

    TARGET_DIR="$(pwd)/.nexus/skills"
    mkdir -p "$TARGET_DIR"

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    # Copy language/framework skills based on detection
    python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from nexus_sdd.detector.scanner import detect_project_type
from nexus_sdd.skills.registry import SkillRegistry

project = detect_project_type()
registry = SkillRegistry()
installed = registry.install_for_project(project.recommended_skills, Path('$TARGET_DIR'))

print(f'Skills instaladas ({len(installed)}):')
for s in installed:
    print(f'  ✓ {s}')

if not installed:
    print('  (skills base: openspec, engram, sdd-methodology)')
" 2>/dev/null || {
        warn "Instalacion automatica fallo. Copiando skills manualmente..."
        if [[ -d "$SCRIPT_DIR/skills" ]]; then
            cp -r "$SCRIPT_DIR/skills"/* "$TARGET_DIR/"
            ok "Skills copiadas manualmente"
        fi
    }
}

# ── Create .nexus Directory ───────────────────────────────────────────
create_nexus_dir() {
    header "Creando estructura .nexus/"

    mkdir -p .nexus/{profiles,skills,alerts,openspec}
    mkdir -p openspec/changes

    # Default developer profile
    cat > .nexus/profiles/developer.profile.yaml << 'PROFILE'
name: developer
role: fullstack
strengths: []
weaknesses: []
preferred_patterns:
  - repository-pattern
  - dependency-injection
  - single-responsibility
avoided_patterns:
  - god-objects
  - premature-optimization
testing_level: unit+integration
stack: []
languages: []
PROFILE

    # Default team profile
    cat > .nexus/profiles/team.profile.yaml << 'TEAM'
name: team
conventions:
  naming: snake_case
  formatting: ruff
  imports: isort
review_checklist:
  - tests_present
  - no_hardcoded_secrets
  - no_dead_code
branch_strategy: trunk-based
ci_cd:
  provider: github-actions
  auto_deploy: false
TEAM

    # Config
    cat > .nexus/config.yaml << 'CONFIG'
nexus_version: "0.1.0"
openspec_enabled: true
engram_enabled: true
langfuse_enabled: false
security_scan_on_commit: true
ralph_loop_max_retries: 3
token_report_frequency: 3
CONFIG

    ok "Estructura .nexus/ creada"
}

# ── Configure AI Agents ───────────────────────────────────────────────
configure_agents() {
    header "Configurando Agentes de IA"

    # Claude Code
    if [[ -d ".claude" ]] || command -v claude &>/dev/null; then
        mkdir -p .claude

        # Registrar engram-vec como MCP server
        claude mcp add engram-vec -- engram-vec mcp 2>/dev/null || warn "No se pudo agregar engram-vec a Claude Code"

        # AGENTS.md for Claude Code
        cat > AGENTS.md << 'AGENTS'
# Nexus-SDD Agent Instructions

## Your Role
You are an AI coding agent working within the Nexus-SDD framework.
You follow Spec-Driven Development (SDD): SPEC → PLAN → CODE → TEST → SECURITY.

## Core Rules
1. **NEVER write code before a spec is approved.** Use OpenSpec (`/opsx:propose`).
2. **Read the plan before coding.** The plan is in `openspec/changes/<HDU>/plan.md`.
3. **Every file gets its test.** No test = not done.
4. **Security scan before commit.** Secrets, keys, tokens → BLOCKED.
5. **Report token usage** every 3 significant actions.

## Memory (Engram)
Before making architectural decisions, search Engram:
```bash
engram search "<your query>" --project $(basename $(pwd))
```

## Profiles
Read `.nexus/profiles/` for team conventions, preferred patterns, and testing level.

## BDD
Every spec requirement must have a Gherkin scenario in `features/`.
AGENTS

        ok "Claude Code configurado (AGENTS.md)"
    fi

    # OpenCode
    if command -v opencode &>/dev/null; then
        engram setup opencode 2>/dev/null || warn "Engram setup para OpenCode fallo"
        ok "OpenCode configurado"
    fi

    # Cursor/Windsurf
    if [[ -d ".cursor" ]]; then
        cat > .cursor/rules/nexus-sdd.md << 'CURSOR'
# Nexus-SDD Rules
- Follow SDD: spec → plan → code → test → security
- Use .nexus/profiles/ for conventions
- Security scan before commit
- BDD scenarios for every feature
CURSOR
        ok "Cursor configurado"
    fi
}

# ── Init OpenSpec ─────────────────────────────────────────────────────
init_openspec() {
    header "Inicializando OpenSpec"

    if command -v openspec &>/dev/null; then
        openspec init 2>/dev/null || {
            warn "openspec init manual requerido. Ejecuta: openspec init"
        }
        ok "OpenSpec inicializado"
    else
        # Create basic OpenSpec structure even without CLI
        mkdir -p openspec/{changes,specs}
        cat > openspec/AGENTS.md << 'OPENSPEC'
# OpenSpec Instructions

Slash commands for AI coding tools:
- `/opsx:propose` — Create a new change (proposal + specs + design + tasks)
- `/opsx:apply` — Implement the tasks
- `/opsx:archive` — Archive a completed change

Nexus-SDD extends this with:
- BDD scenarios in every spec
- Security scan before archive
- Engram memory after every applied change
OPENSPEC
        ok "OpenSpec base creado (instala @fission-ai/openspec para commands completos)"
    fi
}

# ── Interactive Wizard ────────────────────────────────────────────────
print_summary() {
    header "Nexus-SDD Instalacion Completa"

    echo -e "${GREEN}${BOLD}  ✅ Nexus-SDD esta listo!${NC}\n"

    echo -e "  ${BOLD}¿Qué querés hacer ahora?${NC}\n"

    echo -e "  ${CYAN}[1]${NC} ${BOLD}Iniciar un proyecto desde cero${NC}"
    echo -e "      Elijo mi stack (web, mobile, backend, AI...) y Nexus-SDD"
    echo -e "      configura todo: skills, perfiles, seguridad, OpenSpec."
    echo -e "      ${GREEN}nexus-sdd init${NC}\n"

    echo -e "  ${CYAN}[2]${NC} ${BOLD}Agregar Nexus-SDD a un proyecto existente${NC}"
    echo -e "      Detecta el stack automáticamente e instala solo lo necesario."
    echo -e "      ${GREEN}nexus-sdd init${NC} (en el directorio del proyecto)\n"

    echo -e "  ${CYAN}[3]${NC} ${BOLD}Explorar las skills disponibles${NC}"
    echo -e "      Ver el catálogo de 14 skills y 12 suites."
    echo -e "      ${GREEN}nexus-sdd skill list${NC}\n"

    echo -e "  ${CYAN}[4]${NC} ${BOLD}Probar la seguridad${NC}"
    echo -e "      Escanear mi proyecto actual en busca de API keys y secrets."
    echo -e "      ${GREEN}nexus-sdd security${NC}\n"

    echo -e "  ${CYAN}[5]${NC} ${BOLD}Instalar skills específicas${NC}"
    echo -e "      ${GREEN}nexus-sdd skill install <nombre>${NC}"
    echo -e "      Ej: ${GREEN}nexus-sdd skill install langgraph-python${NC}\n"

    echo -e "  ${BOLD}Suites disponibles para init:${NC}"
    echo -e "  mobile mobile-android mobile-ios mobile-flutter"
    echo -e "  web web-react web-vue"
    echo -e "  backend backend-python backend-go"
    echo -e "  fullstack ai-agent ai-agent-local"
    echo -e "  testing devops\n"

    echo -e "  ${BOLD}Ejemplos rápidos:${NC}"
    echo -e "  ${GREEN}nexus-sdd init --suite mobile${NC}              # Android + iOS + Flutter"
    echo -e "  ${GREEN}nexus-sdd init --suite backend-python${NC}     # FastAPI + Django"
    echo -e "  ${GREEN}nexus-sdd init --suite ai-agent${NC}          # LangGraph + AWS + Bedrock"
    echo -e "  ${GREEN}nexus-sdd init --suite fullstack${NC}         # React + FastAPI + Testing\n"

    # Ask the user
    echo -e "  ${BOLD}¿Qué suite querés probar?${NC} Escribí el número o nombre de suite (o Enter para salir):"
    read -r USER_CHOICE

    case "$USER_CHOICE" in
        1|"mobile")
            echo -e "\n${GREEN}Ejecutando: nexus-sdd init --suite mobile${NC}"
            nexus-sdd init --suite mobile
            ;;
        2|"web")
            echo -e "\n${GREEN}Ejecutando: nexus-sdd init --suite web${NC}"
            nexus-sdd init --suite web
            ;;
        3|"backend")
            echo -e "\n${GREEN}Ejecutando: nexus-sdd init --suite backend${NC}"
            nexus-sdd init --suite backend
            ;;
        4|"ai-agent"|"ai")
            echo -e "\n${GREEN}Ejecutando: nexus-sdd init --suite ai-agent${NC}"
            nexus-sdd init --suite ai-agent
            ;;
        5|"fullstack")
            echo -e "\n${GREEN}Ejecutando: nexus-sdd init --suite fullstack${NC}"
            nexus-sdd init --suite fullstack
            ;;
        ""|"skip"|"no")
            echo -e "\n${YELLOW}Ok. Cuando quieras: nexus-sdd init${NC}"
            ;;
        *)
            # Try as suite name
            echo -e "\n${GREEN}Ejecutando: nexus-sdd init --suite $USER_CHOICE${NC}"
            nexus-sdd init --suite "$USER_CHOICE" 2>/dev/null || {
                echo -e "\n${YELLOW}Suite '$USER_CHOICE' no reconocida.${NC}"
                echo -e "${YELLOW}Ejecutá manualmente: nexus-sdd init --suite <nombre>${NC}"
                echo -e "${YELLOW}Suites disponibles: mobile, web, backend, ai-agent, fullstack, testing${NC}"
            }
            ;;
    esac

    echo -e "\n${GREEN}${BOLD}Listo. Ahora el agente IA va a leer AGENTS.md + skills + perfiles.${NC}"
    echo -e "${CYAN}Probá: nexus-sdd spec \"Tu primer feature\"${NC}"
    echo -e "${CYAN}Estado: nexus-sdd status${NC}"
}

# ── Main ──────────────────────────────────────────────────────────────
main() {
    echo -e "\n${BOLD}${CYAN}"
    echo "╔══════════════════════════════════════════════╗"
    echo "║   🏭  NEXUS-SDD  —  Fábrica de Software IA  ║"
    echo "║       Zero-Friction Installer                ║"
    echo "╚══════════════════════════════════════════════╝"
    echo -e "${NC}\n"

    detect_os
    install_python
    install_node
    install_go
    install_openspec
    install_engram
    install_ollama
    install_engram_vec
    install_nexus
    detect_stack
    install_skills
    create_nexus_dir
    configure_agents
    init_openspec
    print_summary
}

main "$@"
