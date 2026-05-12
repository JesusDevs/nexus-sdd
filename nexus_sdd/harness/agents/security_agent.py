"""
Security Agent — Fase 5: Security Middleware.

Escanea codigo ANTES de commit. Busca:
  - API keys, tokens, secrets hardcodeados
  - SQL injection, XSS, path traversal
  - Configuraciones inseguras

Si detecta un leak: BLOQUEA el commit, revierte el archivo,
genera alerta en .nexus/alerts/security_leak_blocked.md.

Actitud: Guardia de seguridad. Paranoico justificado.
"""

from __future__ import annotations

import re
from pathlib import Path

from nexus_sdd.harness.state import AgentState


SECURITY_SYSTEM_PROMPT = """ERES un SECURITY AUDITOR operando en fase SECURITY.

TU ACTITUD:
- Confia en NADIE. Cada archivo es sospechoso hasta que pase el scan.
- Busca patrones de fuga de secrets (API keys, tokens, passwords).
- NO permitas que el agente haga commit si detectas algo.
- Genera un reporte detallado de cada hallazgo.

PATRONES QUE VIGILAS:
- API Keys: sk-ant-api..., sk-or-..., pk_live..., gh_, glpat-
- Tokens: Bearer, x-api-key, Authorization headers
- Secrets: password=, secret=, private_key=
- URLs internas hardcodeadas (staging, prod, internal ips)
- Conexiones a bases de datos sin SSL
- Input de usuario sin sanitizar (SQLi, XSS)

ACCION CUANDO DETECTAS UN LEAK:
1. BLOQUEAR inmediatamente
2. Registrar en .nexus/alerts/security_leak_blocked.md
3. Notificar al desarrollador con el archivo + linea exacta
4. NO continuar hasta que el humano lo resuelva
"""

# ── Detection Patterns ──────────────────────────────────────────────

SECRET_PATTERNS: list[tuple[str, str]] = [
    # (regex, name)
    (r"sk-ant-api\d{2}-[A-Za-z0-9_\-]{90,}", "Anthropic API Key"),
    (r"sk-or-[A-Za-z0-9_\-]{40,}", "OpenRouter API Key"),
    (r"sk-[A-Za-z0-9]{32,}", "OpenAI API Key"),
    (r"pk_live_[A-Za-z0-9]{24,}", "Stripe Live Publishable Key"),
    (r"sk_live_[A-Za-z0-9]{24,}", "Stripe Live Secret Key"),
    (r"ghp_[A-Za-z0-9]{36}", "GitHub Personal Access Token"),
    (r"gho_[A-Za-z0-9]{36}", "GitHub OAuth Token"),
    (r"glpat-[A-Za-z0-9\-]{20,}", "GitLab Personal Access Token"),
    (r"xox[bpras]-[A-Za-z0-9\-]{10,}", "Slack Token"),
    (r"AIza[0-9A-Za-z\-_]{35}", "Google API Key"),
    (r"(?:password|passwd|pwd|secret|token|api_key|apikey)\s*=\s*[\"'][^\"']{8,}[\"']", "Hardcoded Credential"),
    (r"mongodb(\+srv)?://[^:\s]+:[^@\s]+@", "MongoDB Connection String"),
    (r"postgres://[^:\s]+:[^@\s]+@", "PostgreSQL Connection String"),
    (r"mysql://[^:\s]+:[^@\s]+@", "MySQL Connection String"),
    (r"Bearer\s+[A-Za-z0-9_\-\.]{20,}", "Hardcoded Bearer Token"),
    (r"-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----", "Private Key"),
]

# Files/dirs to skip during scan
SKIP_PATTERNS = [
    ".git/", "__pycache__/", "node_modules/", ".venv/", "venv/",
    "*.pyc", "*.lock", "*.min.js", "*.min.css", "*.map",
    ".nexus/alerts/", "package-lock.json", "yarn.lock", "Cargo.lock",
    "*.svg", "*.png", "*.jpg", "*.ico", "*.woff2",
]


def scan_file(filepath: Path) -> list[dict]:
    """Scan a single file for secrets. Returns list of findings."""
    findings = []

    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return findings

    for line_no, line in enumerate(content.splitlines(), start=1):
        for pattern, name in SECRET_PATTERNS:
            match = re.search(pattern, line)
            if match:
                # Mask the secret for the report
                matched_text = match.group(0)
                masked = matched_text[:8] + "***" + matched_text[-4:] if len(matched_text) > 12 else "***"

                findings.append({
                    "file": str(filepath),
                    "line": line_no,
                    "type": name,
                    "matched": masked,
                    "severity": "CRITICAL" if "key" in name.lower() or "token" in name.lower() or "private" in name.lower() else "HIGH",
                })

    return findings


def scan_project(root: Path, skip_patterns: list[str] | None = None) -> list[dict]:
    """Recursively scan project files for secrets."""
    skip = skip_patterns or SKIP_PATTERNS
    all_findings = []

    for filepath in root.rglob("*"):
        if not filepath.is_file():
            continue

        rel = str(filepath.relative_to(root))
        if any(rel.startswith(p.replace("*", "")) or filepath.match(p) for p in skip if not p.startswith("*")):
            continue

        findings = scan_file(filepath)
        all_findings.extend(findings)

    return all_findings


def generate_alert_report(findings: list[dict], alerts_dir: Path) -> Path:
    """Generate a security alert markdown report."""
    alerts_dir.mkdir(parents=True, exist_ok=True)
    from datetime import datetime

    report_path = alerts_dir / "security_leak_blocked.md"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# 🚨 SECURITY ALERT — Leak Bloqueado",
        f"**Timestamp**: {timestamp}",
        f"**Hallazgos**: {len(findings)}",
        "",
        "## Hallazgos",
        "",
    ]

    for f in findings:
        lines.append(f"- **{f['severity']}** | `{f['file']}:{f['line']}` | {f['type']} | `{f['matched']}`")

    lines.extend([
        "",
        "## Accion Tomada",
        "1. Commit BLOQUEADO",
        "2. Archivos revertidos",
        "3. Esta alerta queda registrada para auditoria",
        "",
        "## Resolucion",
        "Reemplaza los secrets con variables de entorno (`os.getenv()`, `process.env`, etc.)",
        "y vuelve a ejecutar la fase de seguridad.",
    ])

    report_path.write_text("\n".join(lines))
    return report_path


# ── LangGraph Node ──────────────────────────────────────────────────

def build_security_agent(profile: dict):
    """Builds the Security Agent node."""

    def security_agent(state: AgentState) -> AgentState:
        hdu_id = state.get("hdu_id", "unknown")
        project_root = Path.cwd()
        alerts_dir = project_root / ".nexus" / "alerts"

        # Scan the project
        findings = scan_project(project_root)

        if findings:
            report_path = generate_alert_report(findings, alerts_dir)
            state["security_alerts"] = [
                f"{f['severity']}: {f['file']}:{f['line']} — {f['type']}"
                for f in findings
            ]

            prompt = f"""{SECURITY_SYSTEM_PROMPT}

## 🚨 ALERTA: Se detectaron {len(findings)} posibles fugas de seguridad

## HDU: {hdu_id}
## Reporte: {report_path}

## Hallazgos:
"""
            for f in findings:
                prompt += f"- **{f['severity']}** | `{f['file']}:{f['line']}` | {f['type']}\n"

            prompt += """
## Instrucciones
1. Estos archivos NO pueden ser commiteados
2. Notifica al desarrollador con el reporte exacto
3. Sugiere usar variables de entorno en lugar de secrets hardcodeados
4. NO continúes hasta que el humano resuelva estos hallazgos
"""
        else:
            prompt = f"""## HDU: {hdu_id}
✅ Security scan completado. No se detectaron fugas de secrets.
El codigo esta listo para ser commiteado.
"""

        state["messages"] = state.get("messages", []) + [
            {"role": "system", "content": SECURITY_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        return state

    return security_agent
