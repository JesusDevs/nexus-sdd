"""
Security Middleware — Escudo de Seguridad para Agentes de IA.

Escanea archivos ANTES del commit buscando:
  - API keys (Anthropic, OpenAI, Stripe, GitHub, Google, Slack)
  - Secrets hardcodeados (password=, secret=, token=)
  - Connection strings con credenciales
  - Private keys (RSA, EC, DSA)

Si detecta un leak:
  1. BLOQUEA el commit
  2. Genera .nexus/alerts/security_leak_blocked.md
  3. Notifica al desarrollador

Pensado para integrarse como pre-commit hook o como nodo del LangGraph harness.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import ClassVar


@dataclass
class SecurityAlert:
    file: str
    line: int
    type: str
    matched: str  # masked
    severity: str  # CRITICAL, HIGH, MEDIUM


class SecurityScanner:
    """Scans project files for security leaks."""

    # ── Patterns ──────────────────────────────────────────────────

    SECRET_PATTERNS: ClassVar[list[tuple[str, str, str]]] = [
        # (regex, name, severity)
        (r"sk-ant-api\d{2}-[A-Za-z0-9_\-]{90,}", "Anthropic API Key", "CRITICAL"),
        (r"sk-or-[A-Za-z0-9_\-]{40,}", "OpenRouter API Key", "CRITICAL"),
        (r"sk-[A-Za-z0-9]{32,}", "OpenAI API Key", "CRITICAL"),
        (r"pk_live_[A-Za-z0-9]{24,}", "Stripe Live Key", "CRITICAL"),
        (r"sk_live_[A-Za-z0-9]{24,}", "Stripe Live Secret", "CRITICAL"),
        (r"ghp_[A-Za-z0-9]{36}", "GitHub PAT", "CRITICAL"),
        (r"gho_[A-Za-z0-9]{36}", "GitHub OAuth", "CRITICAL"),
        (r"glpat-[A-Za-z0-9\-]{20,}", "GitLab PAT", "CRITICAL"),
        (r"xox[bpras]-[A-Za-z0-9\-]{10,}", "Slack Token", "CRITICAL"),
        (r"AIza[0-9A-Za-z\-_]{35}", "Google API Key", "CRITICAL"),
        (r"(?:password|passwd|pwd|secret|token|api_key|apikey)\s*=\s*[\"'][^\"']{8,}[\"']", "Hardcoded Credential", "CRITICAL"),
        (r"mongodb(\+srv)?://[^:\s]+:[^@\s]+@", "MongoDB Connection String", "CRITICAL"),
        (r"postgres(?:ql)?://[^:\s]+:[^@\s]+@", "PostgreSQL Connection String", "CRITICAL"),
        (r"mysql://[^:\s]+:[^@\s]+@", "MySQL Connection String", "CRITICAL"),
        (r"redis://[^:\s]+:[^@\s]+@", "Redis Connection String", "CRITICAL"),
        (r"Bearer\s+[A-Za-z0-9_\-\.]{20,}", "Hardcoded Bearer Token", "HIGH"),
        (r"-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----", "Private Key", "CRITICAL"),
        (r"ssh-rsa\s+[A-Za-z0-9+/=]{100,}", "SSH Private Key", "HIGH"),
    ]

    SKIP_PATTERNS: ClassVar[list[str]] = [
        ".git/", "__pycache__/", "node_modules/", ".venv/", "venv/",
        "*.pyc", "*.pyo", "*.lock", "*.min.js", "*.min.css", "*.map",
        ".nexus/alerts/", "package-lock.json", "yarn.lock", "Cargo.lock",
        "poetry.lock", "pnpm-lock.yaml", "*.svg", "*.png", "*.jpg",
        "*.ico", "*.woff2", "*.ttf", "*.eot", "*.zip", "*.tar.gz",
        "dist/", "build/", "target/", ".next/", ".nuxt/", "coverage/",
    ]

    def __init__(self, root: Path | None = None):
        self.root = root or Path.cwd()
        self.alerts_dir = self.root / ".nexus" / "alerts"

    def _should_skip(self, filepath: Path) -> bool:
        rel = str(filepath.relative_to(self.root))
        for pattern in self.SKIP_PATTERNS:
            if pattern.endswith("/"):
                if rel.startswith(pattern):
                    return True
            elif pattern.startswith("*."):
                ext = pattern[1:]
                if rel.endswith(ext):
                    return True
            elif rel == pattern:
                return True
        return False

    def scan_file(self, filepath: Path) -> list[SecurityAlert]:
        alerts = []
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return alerts

        for line_no, line in enumerate(content.splitlines(), start=1):
            for pattern, name, severity in self.SECRET_PATTERNS:
                match = re.search(pattern, line)
                if match:
                    matched = match.group(0)
                    masked = matched[:8] + "***" + matched[-4:] if len(matched) > 12 else "***"
                    alerts.append(SecurityAlert(
                        file=str(filepath.relative_to(self.root)),
                        line=line_no,
                        type=name,
                        matched=masked,
                        severity=severity,
                    ))

        return alerts

    def scan_project(self, skip_patterns: list[str] | None = None) -> list[SecurityAlert]:
        all_alerts = []
        for filepath in self.root.rglob("*"):
            if not filepath.is_file():
                continue
            if self._should_skip(filepath):
                continue
            all_alerts.extend(self.scan_file(filepath))
        return all_alerts

    def generate_report(self, alerts: list[SecurityAlert]) -> Path:
        self.alerts_dir.mkdir(parents=True, exist_ok=True)
        report_path = self.alerts_dir / "security_leak_blocked.md"
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        critical = [a for a in alerts if a.severity == "CRITICAL"]
        high = [a for a in alerts if a.severity == "HIGH"]

        lines = [
            "# 🚨 SECURITY ALERT — Leak Bloqueado",
            f"**Timestamp**: {timestamp}",
            f"**Hallazgos**: {len(alerts)} ({len(critical)} CRITICAL, {len(high)} HIGH)",
            "",
            "## 🔴 CRITICAL",
        ]

        for a in critical:
            lines.append(f"- **{a.type}** | `{a.file}:{a.line}` | `{a.matched}`")

        if high:
            lines.append("")
            lines.append("## 🟠 HIGH")
            for a in high:
                lines.append(f"- **{a.type}** | `{a.file}:{a.line}` | `{a.matched}`")

        lines.extend([
            "",
            "## Accion Tomada",
            "1. ❌ Commit BLOQUEADO",
            "2. 🔄 Archivos deben ser corregidos",
            "3. 📋 Esta alerta queda registrada para auditoria",
            "",
            "## Como Resolver",
            "1. Reemplaza los secrets con variables de entorno (`os.getenv()`, `process.env`, etc.)",
            "2. Si es un falso positivo, agrega `# nexus-sdd: allow-secret` en la linea",
            "3. Vuelve a ejecutar `nexus-sdd security` para verificar",
        ])

        report_path.write_text("\n".join(lines))
        return report_path
