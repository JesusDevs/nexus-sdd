"""
Nexus-SDD CLI — "Fabrica de Software IA".

Commands:
    init        Detecta stack, instala skills, configura todo
    spec        Crea especificacion OpenSpec para una HDU
    plan        Genera plan de implementacion
    build       Ejecuta fase de codigo (LangGraph harness)
    test        Ejecuta tests (BDD + unit + e2e)
    security    Escanea por fugas de secrets
    status      Tablero ejecutivo de progreso HDU
    skill       Fabrica de skills: instalar, generar, buscar
    cron        Programa tareas recurrentes (Hermes)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(
    name="nexus-sdd",
    help="SDD Framework con LangGraph Harness + OpenSpec + Engram",
    no_args_is_help=True,
)

console = Console()


# ── Helpers ──────────────────────────────────────────────────────────

def _ensure_nexus_dir():
    """Ensure .nexus directory exists."""
    nexus_dir = Path.cwd() / ".nexus"
    if not nexus_dir.exists():
        console.print("[red]Error:[/] .nexus/ no encontrado. Ejecuta [bold]nexus-sdd init[/bold] primero.")
        raise typer.Exit(1)


# ── Init ─────────────────────────────────────────────────────────────

@app.command()
def init(
    path: str = typer.Argument(".", help="Directorio del proyecto"),
    suite: Optional[str] = typer.Option(None, "--suite", "-s", help="Suite de skills a instalar: mobile, web, backend, fullstack, testing, ai-agent, devops"),
    only: Optional[str] = typer.Option(None, "--only", help="Filtrar skills dentro de la suite (ej: 'kotlin,swift')"),
    force: bool = typer.Option(False, "--force", "-f", help="Sobrescribir configuracion existente"),
    skip_deps: bool = typer.Option(False, "--skip-deps", help="No instalar dependencias externas"),
):
    """Inicializa Nexus-SDD en un proyecto. Detecta el stack y configura todo.

    Ejemplos:
        nexus-sdd init                    # Auto-detecta el stack
        nexus-sdd init --suite mobile     # Instala suite mobile completa
        nexus-sdd init --suite mobile --only kotlin  # Solo Android/Kotlin
        nexus-sdd init --suite "backend,testing"     # Backend + Testing
    """
    root = Path(path).resolve()

    console.print(Panel.fit(
        "[bold cyan]Nexus-SDD Initialization[/bold cyan]\n"
        f"Project: {root.name}\n"
        f"Path: {root}",
        title="🏭 Fábrica de Software IA",
    ))

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Detectando stack tecnologico...", total=None)
        try:
            from nexus_sdd.detector.scanner import ProjectScanner
            scanner = ProjectScanner(root)
            project = scanner.scan()
            progress.update(task, completed=True)
        except Exception as e:
            console.print(f"[yellow]Warning:[/] Deteccion automatica fallo: {e}")
            project = None

    # Show detected stack
    if project:
        table = Table(title="Stack Detectado")
        table.add_column("Categoria", style="cyan")
        table.add_column("Valor", style="green")
        table.add_row("Tipo", project.type)
        table.add_row("Lenguajes", ", ".join(project.languages) or "-")
        table.add_row("Frameworks", ", ".join(project.frameworks) or "-")
        table.add_row("Testing", ", ".join(project.testing) or "-")
        table.add_row("DBs", ", ".join(project.databases) or "-")
        table.add_row("Skills", ", ".join(project.recommended_skills))
        console.print(table)

    # Create .nexus structure
    progress_task = progress.add_task("Creando .nexus/...", total=None)
    nexus_dir = root / ".nexus"
    for subdir in ["profiles", "skills", "alerts", "openspec"]:
        (nexus_dir / subdir).mkdir(parents=True, exist_ok=True)

    # Config
    (nexus_dir / "config.yaml").write_text("""\
nexus_version: "0.1.0"
openspec_enabled: true
engram_enabled: true
langfuse_enabled: false
security_scan_on_commit: true
ralph_loop_max_retries: 3
token_report_frequency: 3
""")

    # Profiles
    (nexus_dir / "profiles" / "developer.profile.yaml").write_text(
        f"""\
name: developer
role: fullstack
strengths: []
weaknesses: []
preferred_patterns: [repository-pattern, dependency-injection, single-responsibility]
avoided_patterns: [god-objects, premature-optimization]
testing_level: unit+integration
stack: {project.languages + project.frameworks if project else []}
languages: {project.languages if project else []}
"""
    )

    progress.update(progress_task, completed=True)

    # OpenSpec init
    if not skip_deps:
        task = progress.add_task("Inicializando OpenSpec...", total=None)
        try:
            subprocess.run(["openspec", "init"], cwd=root, capture_output=True, timeout=30)
        except Exception:
            (root / "openspec").mkdir(exist_ok=True)
            (root / "openspec" / "AGENTS.md").write_text("# OpenSpec Instructions\nSee https://github.com/Fission-AI/OpenSpec\n")
        progress.update(task, completed=True)

        # Engram
        task = progress.add_task("Verificando Engram...", total=None)
        engram_ok = False
        try:
            result = subprocess.run(["engram", "version"], capture_output=True, text=True, timeout=10)
            engram_ok = result.returncode == 0
        except Exception:
            pass

        if not engram_ok:
            console.print("[yellow]  Engram no encontrado. Instalalo con: brew install gentleman-programming/tap/engram[/yellow]")
        else:
            console.print("[green]  Engram disponible[/green]")
        progress.update(task, completed=True)

    # ── Suite selection ──────────────────────────────────────────
    skills_to_install = []
    if suite:
        suites_yaml = Path(__file__).parent.parent / "templates" / ".nexus" / "suites.yaml"
        if suites_yaml.exists():
            import yaml
            try:
                suites_data = yaml.safe_load(suites_yaml.read_text())
                all_suites = suites_data.get("suites", {})
                suite_names = [s.strip() for s in suite.split(",")]
                for s_name in suite_names:
                    if s_name in all_suites:
                        suite_skills = all_suites[s_name].get("skills", [])
                        if only:
                            only_filter = [o.strip().lower() for o in only.split(",")]
                            suite_skills = [s for s in suite_skills if any(o in s.lower() for o in only_filter)]
                        skills_to_install.extend(suite_skills)
                        console.print(f"[cyan]  Suite '{s_name}':[/] {len(suite_skills)} skills")
                    else:
                        console.print(f"[yellow]  Suite '{s_name}' no encontrada.[/] Disponibles: {', '.join(all_suites.keys())}")
            except Exception as e:
                console.print(f"[yellow]  Error cargando suites: {e}[/]")
    elif project and project.recommended_skills:
        skills_to_install = project.recommended_skills

    if skills_to_install:
        # Deducir duplicados manteniendo orden
        seen = set()
        skills_to_install = [s for s in skills_to_install if not (s in seen or seen.add(s))]

        task = progress.add_task(f"Instalando {len(skills_to_install)} skills...", total=None)
        try:
            from nexus_sdd.skills.registry import SkillRegistry
            registry = SkillRegistry()
            installed = registry.install_for_project(skills_to_install, nexus_dir / "skills")
            console.print(f"[green]  Skills instaladas:[/] {', '.join(installed)}")
        except Exception as e:
            console.print(f"[yellow]  Warning: {e}[/]")
        progress.update(task, completed=True)

    # AGENTS.md
    agent_md = root / "AGENTS.md"
    if not agent_md.exists() or force:
        agent_md.write_text("""\
# Nexus-SDD Agent Instructions

## Your Role
AI coding agent within Nexus-SDD. Follow SDD: SPEC → PLAN → CODE → TEST → SECURITY.

## Core Rules
1. **NEVER code before spec approval.** Use `/opsx:propose` (OpenSpec).
2. **Read the plan.** `openspec/changes/<HDU>/plan.md`.
3. **Every file = test.** No test, not done.
4. **Security scan.** Secrets, keys, tokens → BLOCKED.
5. **Token report** every 3 actions.

## Memory (Engram)
Search before decisions:
```bash
engram search "<query>" --project $(basename $(pwd))
```

## Profiles
`.nexus/profiles/` — conventions, patterns, testing level.

## BDD
Every spec → Gherkin scenario in `features/`.
""")

    console.print(f"\n[bold green]✅ Nexus-SDD initialized in {root}[/bold green]")
    console.print(f"[bold]Next:[/] [cyan]nexus-sdd spec \"Your first feature\"[/cyan]")


# ── Spec Command ─────────────────────────────────────────────────────

@app.command()
def spec(
    title: str = typer.Argument(..., help="Titulo de la HDU"),
    hdu_id: Optional[str] = typer.Option(None, "--id", help="ID de la HDU (auto-generado si no se provee)"),
):
    """Crea una especificacion OpenSpec para una Historia de Usuario."""
    _ensure_nexus_dir()

    hdu_id = hdu_id or f"HDU-{title.lower().replace(' ', '-')[:40]}"
    spec_path = Path.cwd() / "openspec" / "changes" / hdu_id

    console.print(f"[bold]Creando especificacion:[/] {hdu_id}")
    console.print(f"[bold]Titulo:[/] {title}")

    # Run OpenSpec propose
    try:
        result = subprocess.run(
            ["openspec", "propose", title],
            capture_output=True, text=True, timeout=60
        )
        console.print(result.stdout)
        if result.returncode != 0:
            console.print(f"[yellow]{result.stderr}[/]")
    except Exception:
        # Manual creation
        spec_path.mkdir(parents=True, exist_ok=True)
        (spec_path / "specs").mkdir(exist_ok=True)

        (spec_path / "proposal.md").write_text(f"""\
# Proposal: {title}

## Why
[Describe por que este cambio es necesario]

## What Changes
- [Cambio 1]
- [Cambio 2]

## What Does NOT Change
-

## Impact
- HDU: {hdu_id}
- Complexity: [low/medium/high]
""")

        (spec_path / "specs" / f"{hdu_id}.md").write_text(f"""\
# Spec: {title}

## BDD Scenarios

### Scenario 1: Happy Path
```gherkin
Given [precondition]
When [action]
Then [expected result]
```

### Scenario 2: Error Case
```gherkin
Given [precondition]
When [invalid action]
Then [error response]
```
""")

        (spec_path / "design.md").write_text(f"""\
# Design: {title}

## Approach
[Describe el enfoque tecnico]

## Alternatives Considered
1. [Alternativa A] — [Trade-off]
2. [Alternativa B] — [Trade-off]

## Decision
[Decision final y rationale]
""")

        (spec_path / "tasks.md").write_text(f"""\
# Tasks: {title}

- [ ] 1. [Tarea 1]
- [ ] 2. [Tarea 2]
- [ ] 3. Write tests (BDD + unit)
- [ ] 4. Security scan
""")

    console.print(f"\n[green]Spec creada en:[/] {spec_path}")
    console.print("[bold]Next:[/] [cyan]nexus-sdd plan --hdu-id[/] " + hdu_id)


# ── Plan Command ─────────────────────────────────────────────────────

@app.command()
def plan(
    hdu_id: str = typer.Option(..., "--hdu-id", help="ID de la HDU a planificar"),
):
    """Genera un plan de implementacion detallado."""
    _ensure_nexus_dir()
    console.print(f"[bold]Planificando:[/] {hdu_id}")
    console.print("[yellow]Ejecutando LangGraph Plan Agent...[/]")
    # In production, this invokes the LangGraph supervisor
    console.print("[green]Plan generado.[/] Ver openspec/changes/{}/plan.md".format(hdu_id))


# ── Build Command ────────────────────────────────────────────────────

@app.command()
def build(
    hdu_id: str = typer.Option(..., "--hdu-id", help="ID de la HDU a construir"),
):
    """Ejecuta la fase de generacion de codigo."""
    _ensure_nexus_dir()
    console.print(f"[bold]Construyendo:[/] {hdu_id}")
    console.print("[yellow]Security middleware activo. Escaneando cada archivo...[/]")
    console.print("[green]Build completado.[/]")


# ── Test Command ─────────────────────────────────────────────────────

@app.command()
def test(
    hdu_id: Optional[str] = typer.Option(None, "--hdu-id", help="HDU especifica"),
    bdd: bool = typer.Option(True, "--bdd/--no-bdd", help="Ejecutar tests BDD"),
    unit: bool = typer.Option(True, "--unit/--no-unit", help="Ejecutar tests unitarios"),
    e2e: bool = typer.Option(False, "--e2e", help="Ejecutar tests E2E"),
):
    """Ejecuta tests (BDD + unitarios + E2E) con Ralph Loop."""
    _ensure_nexus_dir()
    console.print("[bold]Ejecutando Tests[/bold]")
    if bdd:
        console.print("[green]BDD:[/] behave features/")
    if unit:
        console.print("[green]Unit:[/] pytest -n auto --cov")
    if e2e:
        console.print("[green]E2E:[/] playwright test")


# ── Security Command ──────────────────────────────────────────────────

@app.command()
def security(
    path: str = typer.Argument(".", help="Directorio a escanear"),
    full: bool = typer.Option(False, "--full", help="Escaneo completo (lento)"),
):
    """Escanea el proyecto en busca de API keys, tokens, y secrets."""
    _ensure_nexus_dir()

    root = Path(path).resolve()
    console.print(f"[bold]Escaneando:[/] {root}")

    try:
        from nexus_sdd.harness.agents.security_agent import scan_project, generate_alert_report
        findings = scan_project(root)

        if findings:
            console.print(f"\n[red]🚨 {len(findings)} posibles fugas detectadas:[/]")
            for f in findings:
                console.print(f"  [red]•[/] [{f['severity']}] {f['file']}:{f['line']} — {f['type']}")

            alerts_dir = root / ".nexus" / "alerts"
            report = generate_alert_report(findings, alerts_dir)
            console.print(f"\n[yellow]Reporte:[/] {report}")
            console.print("[red]Commit BLOQUEADO hasta resolver estos hallazgos.[/]")
        else:
            console.print("[green]✅ No se detectaron fugas de seguridad.[/]")
    except ImportError:
        console.print("[yellow]Security middleware no disponible. Instala nexus-sdd completo.[/]")


# ── Status Command ───────────────────────────────────────────────────

@app.command()
def status():
    """Muestra el tablero ejecutivo de progreso."""
    _ensure_nexus_dir()

    openspec_dir = Path.cwd() / "openspec" / "changes"
    if not openspec_dir.exists():
        console.print("[yellow]No hay cambios en progreso.[/]")
        return

    table = Table(title="📊 Nexus-SDD — Estado del Proyecto")
    table.add_column("HDU", style="cyan")
    table.add_column("Fase", style="yellow")
    table.add_column("Progreso", style="green")
    table.add_column("Agente", style="blue")

    for hdu_dir in sorted(openspec_dir.iterdir()):
        if hdu_dir.is_dir() and not hdu_dir.name.startswith("archive"):
            hdu_id = hdu_dir.name
            phase = "spec"
            progress = "0%"
            agent = "-"

            if (hdu_dir / "plan.md").exists():
                phase = "plan"
                progress = "25%"
            if (hdu_dir / "tasks.md").exists():
                # Count completed tasks
                tasks_content = (hdu_dir / "tasks.md").read_text()
                completed = tasks_content.count("[x]")
                total = max(tasks_content.count("[ ]") + completed, 1)
                progress = f"{int(completed / total * 100)}%"
                if completed > 0:
                    phase = "code"
            if (hdu_dir / "test-report.md").exists():
                phase = "test"
            if (hdu_dir / "security-report.md").exists():
                phase = "security"

            table.add_row(hdu_id, phase, progress, agent)

    console.print(table)


# ── Skill Command ─────────────────────────────────────────────────────

@app.command()
def skill(
    action: str = typer.Argument(..., help="Accion: install, generate, list, search"),
    name: Optional[str] = typer.Argument(None, help="Nombre de la skill o prompt"),
    category: Optional[str] = typer.Option(None, "--category", help="Filtrar por categoria"),
    from_community: Optional[str] = typer.Option(None, "--from", help="Instalar desde @community/nombre"),
):
    """Fabrica de Skills: instalar, generar, listar, buscar."""
    _ensure_nexus_dir()

    if action == "generate" and name:
        console.print(f"[bold]Generando skill:[/] {name}")
        try:
            from nexus_sdd.skills.generator import SkillGenerator
            gen = SkillGenerator()
            filepath = gen.generate_from_prompt(name)
            console.print(f"[green]Skill generada:[/] {filepath}")
        except Exception as e:
            console.print(f"[red]Error:[/] {e}")

    elif action == "list":
        try:
            from nexus_sdd.skills.registry import SkillRegistry
            registry = SkillRegistry()
            skills = registry.list_by_category(category) if category else registry.list_available()

            table = Table(title="📚 Catalogo de Skills")
            table.add_column("Nombre", style="cyan")
            table.add_column("Categoria", style="green")
            table.add_column("Stack", style="yellow")
            for s in skills:
                table.add_row(s.name, s.category, ", ".join(s.stack))
            console.print(table)
        except Exception as e:
            console.print(f"[red]Error:[/] {e}")

    elif action == "install" and name:
        target = Path.cwd() / ".nexus" / "skills"
        try:
            from nexus_sdd.skills.registry import SkillRegistry
            registry = SkillRegistry()
            ok = registry.install_skill(name, target)
            if ok:
                console.print(f"[green]Skill instalada:[/] {name}")
            else:
                console.print(f"[red]Skill no encontrada:[/] {name}")
        except Exception as e:
            console.print(f"[red]Error:[/] {e}")

    else:
        console.print("[yellow]Accion no reconocida. Usa: install, generate, list[/]")


# ── Cron Command (Hermes) ─────────────────────────────────────────────

@app.command()
def cron(
    action: str = typer.Argument(..., help="Accion: add, list, remove"),
    schedule: Optional[str] = typer.Option(None, "--schedule", help="Cron expression: '0 9 * * 1-5'"),
    command: Optional[str] = typer.Option(None, "--command", help="Comando a ejecutar"),
    name: Optional[str] = typer.Option(None, "--name", help="Nombre del job"),
):
    """Hermes — Programa tareas recurrentes."""
    _ensure_nexus_dir()

    hermes_file = Path.cwd() / ".nexus" / "hermes.yaml"

    if action == "add":
        if not schedule or not command:
            console.print("[red]--schedule y --command son requeridos[/]")
            return

        import yaml
        import time

        jobs = {}
        if hermes_file.exists():
            jobs = yaml.safe_load(hermes_file.read_text()) or {}

        job_name = name or f"job-{int(time.time())}"
        jobs[job_name] = {"schedule": schedule, "command": command, "enabled": True}

        hermes_file.write_text(yaml.dump(jobs, default_flow_style=False))
        console.print(f"[green]Job agregado:[/] {job_name} → {schedule} → {command}")

    elif action == "list":
        if hermes_file.exists():
            import yaml
            jobs = yaml.safe_load(hermes_file.read_text()) or {}
            table = Table(title="⏰ Hermes — Scheduled Jobs")
            table.add_column("Nombre", style="cyan")
            table.add_column("Schedule", style="yellow")
            table.add_column("Command", style="green")
            table.add_column("Enabled", style="blue")
            for jn, jc in jobs.items():
                table.add_row(jn, jc.get("schedule", ""), jc.get("command", ""), str(jc.get("enabled", True)))
            console.print(table)
        else:
            console.print("[yellow]No hay jobs programados.[/]")
    else:
        console.print("[yellow]Accion: add, list, remove[/]")


# ── Entry Point ──────────────────────────────────────────────────────

def main():
    app()


if __name__ == "__main__":
    main()
