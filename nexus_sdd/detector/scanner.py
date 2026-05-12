"""
Project Scanner — Detecta el stack tecnologico del proyecto.

Analiza archivos de configuracion, dependencias y estructura
para determinar:
  - Tipo: web, mobile, backend, cli, library
  - Lenguajes: Python, TypeScript, Go, Kotlin, Swift, Dart, etc.
  - Frameworks: React, Vue, Next.js, FastAPI, Django, Flutter, etc.
  - Testing: pytest, vitest, JUnit, etc.
  - Base de datos: PostgreSQL, MongoDB, SQLite, etc.

Basado en esto, recomienda que skills instalar.
"""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DetectedProject:
    type: str  # web, mobile, backend, cli, library, fullstack
    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    testing: list[str] = field(default_factory=list)
    databases: list[str] = field(default_factory=list)
    package_managers: list[str] = field(default_factory=list)
    recommended_skills: list[str] = field(default_factory=list)
    confidence: dict[str, float] = field(default_factory=dict)


# ── Signature Database ──────────────────────────────────────────────
# Maps files/patterns → technology

SIGNATURES: dict[str, dict[str, Any]] = {
    # ── Package Managers ──
    "package.json": {
        "type": "npm",
        "category": "package_manager",
        "languages": ["javascript", "typescript"],
    },
    "pnpm-lock.yaml": {"type": "pnpm", "category": "package_manager"},
    "yarn.lock": {"type": "yarn", "category": "package_manager"},
    "bun.lockb": {"type": "bun", "category": "package_manager"},
    "pyproject.toml": {
        "type": "python",
        "category": "package_manager",
        "languages": ["python"],
    },
    "requirements.txt": {"type": "pip", "category": "package_manager", "languages": ["python"]},
    "Pipfile": {"type": "pipenv", "category": "package_manager", "languages": ["python"]},
    "go.mod": {"type": "go_modules", "category": "package_manager", "languages": ["go"]},
    "Cargo.toml": {"type": "cargo", "category": "package_manager", "languages": ["rust"]},
    "build.gradle.kts": {"type": "gradle_kotlin", "category": "package_manager", "languages": ["kotlin", "java"]},
    "build.gradle": {"type": "gradle", "category": "package_manager", "languages": ["kotlin", "java"]},
    "pom.xml": {"type": "maven", "category": "package_manager", "languages": ["java"]},
    "Podfile": {"type": "cocoapods", "category": "package_manager", "languages": ["swift", "objc"]},
    "pubspec.yaml": {"type": "dart_pub", "category": "package_manager", "languages": ["dart"]},

    # ── Web Frameworks ──
    "next.config.js": {"type": "nextjs", "category": "framework", "project_type": "web"},
    "next.config.ts": {"type": "nextjs", "category": "framework", "project_type": "web"},
    "next.config.mjs": {"type": "nextjs", "category": "framework", "project_type": "web"},
    "svelte.config.js": {"type": "svelte", "category": "framework", "project_type": "web"},
    "vite.config.ts": {"type": "vite", "category": "bundler", "project_type": "web"},
    "vite.config.js": {"type": "vite", "category": "bundler", "project_type": "web"},
    "tailwind.config.ts": {"type": "tailwind", "category": "css_framework"},
    "tailwind.config.js": {"type": "tailwind", "category": "css_framework"},
    "postcss.config.js": {"type": "postcss", "category": "css_tool"},

    # ── Mobile ──
    "android/": {"type": "android", "category": "platform", "project_type": "mobile"},
    "ios/": {"type": "ios", "category": "platform", "project_type": "mobile"},
    "app/build.gradle.kts": {"type": "android_app", "category": "platform", "project_type": "mobile"},

    # ── Backend ──
    "manage.py": {"type": "django", "category": "framework", "project_type": "backend"},
    "alembic.ini": {"type": "alembic", "category": "migration", "project_type": "backend"},
    "migrations/": {"type": "db_migrations", "category": "migration", "project_type": "backend"},

    # ── Testing ──
    "vitest.config.ts": {"type": "vitest", "category": "testing"},
    "vitest.config.js": {"type": "vitest", "category": "testing"},
    "jest.config.js": {"type": "jest", "category": "testing"},
    "jest.config.ts": {"type": "jest", "category": "testing"},
    "playwright.config.ts": {"type": "playwright", "category": "testing"},
    "playwright.config.js": {"type": "playwright", "category": "testing"},
    "cypress.config.ts": {"type": "cypress", "category": "testing"},
    "pytest.ini": {"type": "pytest", "category": "testing"},
    "conftest.py": {"type": "pytest", "category": "testing"},

    # ── Databases ──
    "schema.prisma": {"type": "prisma", "category": "orm"},
    "drizzle.config.ts": {"type": "drizzle", "category": "orm"},
    "knexfile.js": {"type": "knex", "category": "orm"},
    "docker-compose.yml": {"type": "docker", "category": "infra"},
    "docker-compose.yaml": {"type": "docker", "category": "infra"},
    "Dockerfile": {"type": "docker", "category": "infra"},
}


def _read_json(filepath: Path) -> dict:
    try:
        return json.loads(filepath.read_text())
    except Exception:
        return {}


def _read_toml(filepath: Path) -> dict:
    try:
        if tomllib:
            return tomllib.loads(filepath.read_text())
    except Exception:
        pass
    return {}


def _scan_package_json(data: dict) -> list[str]:
    """Extract frameworks from package.json dependencies."""
    found = []
    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {}), **data.get("peerDependencies", {})}

    framework_map = {
        "react": "react",
        "vue": "vue",
        "@angular/core": "angular",
        "svelte": "svelte",
        "next": "nextjs",
        "nuxt": "nuxt",
        "remix-run": "remix",
        "@solidjs/core": "solidjs",
        "express": "express",
        "@nestjs/core": "nestjs",
        "fastify": "fastify",
        "@fastify": "fastify",
        "react-native": "react-native",
        "expo": "expo",
        "electron": "electron",
        "tauri": "tauri",
    }

    for dep_key, framework in framework_map.items():
        if dep_key in deps:
            found.append(framework)

    # Testing
    test_map = {
        "vitest": "vitest",
        "jest": "jest",
        "@playwright/test": "playwright",
        "cypress": "cypress",
        "mocha": "mocha",
        "jasmine": "jasmine",
    }
    for dep_key, test_fw in test_map.items():
        if dep_key in deps:
            found.append(test_fw)

    # ORMs
    orm_map = {
        "prisma": "prisma",
        "@prisma/client": "prisma",
        "drizzle-orm": "drizzle",
        "typeorm": "typeorm",
        "knex": "knex",
        "mongoose": "mongoose",
        "sequelize": "sequelize",
    }
    for dep_key, orm in orm_map.items():
        if dep_key in deps:
            found.append(orm)

    return found


def _scan_pyproject(data: dict) -> list[str]:
    """Extract frameworks from pyproject.toml."""
    found = []
    deps = data.get("project", {}).get("dependencies", [])
    opt_deps = data.get("project", {}).get("optional-dependencies", {})
    all_deps = deps + [d for deps_list in opt_deps.values() for d in deps_list]

    dep_str = " ".join(all_deps).lower()

    py_frameworks = {
        "fastapi": "fastapi",
        "django": "django",
        "flask": "flask",
        "langgraph": "langgraph",
        "langchain": "langchain",
        "pydantic": "pydantic",
        "sqlalchemy": "sqlalchemy",
        "tortoise-orm": "tortoise",
        "beanie": "beanie",
        "pytest": "pytest",
        "behave": "behave",
        "playwright": "playwright",
    }

    for key, fw in py_frameworks.items():
        if key in dep_str:
            found.append(fw)

    return found


def _scan_go_mod(content: str) -> list[str]:
    found = []
    go_frameworks = {
        "gin-gonic/gin": "gin",
        "fiber": "fiber",
        "echo": "echo",
        "chi": "chi",
        "gorilla/mux": "gorilla-mux",
        "gorm.io/gorm": "gorm",
        "sqlx": "sqlx",
        "ent": "ent",
        "graphql": "graphql",
    }
    for key, fw in go_frameworks.items():
        if key in content:
            found.append(fw)
    return found


class ProjectScanner:
    """Scans a project directory and detects its technology stack."""

    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root else Path.cwd()
        self.files: dict[str, Path] = {}
        self._index_files()

    def _index_files(self):
        """Index all non-ignored files in the project."""
        for filepath in self.root.rglob("*"):
            if not filepath.is_file():
                continue
            rel = str(filepath.relative_to(self.root))
            # Skip common ignores
            if any(p in rel for p in ["node_modules", ".git", "__pycache__", ".venv", "venv", ".next", "dist", "build", "target"]):
                continue
            self.files[rel] = filepath

    def scan(self) -> DetectedProject:
        """Full scan. Returns a complete DetectedProject."""
        result = DetectedProject(type="unknown")

        # Detect by signatures
        matched_signatures = []
        for sig_path, sig_info in SIGNATURES.items():
            if sig_path.endswith("/"):
                # Directory check
                if any(f.startswith(sig_path) for f in self.files):
                    matched_signatures.append(sig_info)
            elif sig_path in self.files:
                matched_signatures.append(sig_info)

        for sig in matched_signatures:
            cat = sig.get("category", "")
            stype = sig.get("type", "")

            if cat == "package_manager":
                if stype not in result.package_managers:
                    result.package_managers.append(stype)
                for lang in sig.get("languages", []):
                    if lang not in result.languages:
                        result.languages.append(lang)
            elif cat == "framework":
                if stype not in result.frameworks:
                    result.frameworks.append(stype)
            elif cat == "testing":
                if stype not in result.testing:
                    result.testing.append(stype)
            elif cat == "orm":
                pass  # Handled below
            elif cat == "platform" or cat == "infra":
                pass

            if "project_type" in sig:
                pt = sig["project_type"]
                if pt not in result.type.split(","):
                    result.type = pt if result.type == "unknown" else f"{result.type}+{pt}"

        # Deep scan package files
        if "package.json" in self.files:
            data = _read_json(self.files["package.json"])
            extra = _scan_package_json(data)
            for item in extra:
                if item in {"vitest", "jest", "playwright", "cypress"}:
                    if item not in result.testing:
                        result.testing.append(item)
                elif item in {"prisma", "drizzle", "typeorm", "mongoose"}:
                    if item not in result.databases:
                        result.databases.append(item)
                else:
                    if item not in result.frameworks:
                        result.frameworks.append(item)

        if "pyproject.toml" in self.files:
            data = _read_toml(self.files["pyproject.toml"])
            extra = _scan_pyproject(data)
            for item in extra:
                if item in {"pytest", "behave", "playwright"}:
                    if item not in result.testing:
                        result.testing.append(item)
                elif item in {"sqlalchemy", "tortoise", "beanie"}:
                    if item not in result.databases:
                        result.databases.append(item)
                else:
                    if item not in result.frameworks:
                        result.frameworks.append(item)
            if "langgraph" in extra or "langchain" in extra:
                result.type = "ai-agent" if result.type == "unknown" else f"{result.type}+ai-agent"

        if "go.mod" in self.files:
            content = self.files["go.mod"].read_text()
            extra = _scan_go_mod(content)
            for item in extra:
                if item in {"gorm", "ent", "sqlx"}:
                    if item not in result.databases:
                        result.databases.append(item)
                else:
                    if item not in result.frameworks:
                        result.frameworks.append(item)

        # Detect mobile-specific
        if "pubspec.yaml" in self.files:
            if "flutter" not in result.frameworks:
                result.frameworks.append("flutter")
            if "dart" not in result.languages:
                result.languages.append("dart")
            result.type = "mobile" if result.type == "unknown" else result.type

        # Use Gradle to detect Kotlin/Java
        if any(f.endswith(".gradle.kts") for f in self.files):
            if "kotlin" not in result.languages:
                result.languages.append("kotlin")
            result.type = "mobile" if "android" in str(self.files).lower() else result.type

        # Infer project type from frameworks if still unknown
        if result.type == "unknown":
            web_fw = {"nextjs", "react", "vue", "svelte", "angular", "solidjs", "remix", "nuxt"}
            mobile_fw = {"flutter", "react-native", "expo", "swiftui"}
            backend_fw = {"fastapi", "django", "flask", "express", "nestjs", "gin", "fiber", "echo", "spring-boot"}

            if result.frameworks:
                fw_set = set(result.frameworks)
                if fw_set & web_fw:
                    result.type = "web"
                elif fw_set & mobile_fw:
                    result.type = "mobile"
                elif fw_set & backend_fw:
                    result.type = "backend"

        if result.type == "unknown":
            if result.languages:
                result.type = "cli"

        # Recommend skills
        result.recommended_skills = self._recommend_skills(result)

        return result

    def _recommend_skills(self, project: DetectedProject) -> list[str]:
        """Map detected stack → skill files to install."""
        skills = []

        # Base skills (always)
        skills.append("openspec")
        skills.append("engram")

        # Language skills
        lang_skill_map = {
            "python": "python-best-practices",
            "typescript": "typescript-strict",
            "javascript": "javascript-es6",
            "go": "go-idiomatic",
            "rust": "rust-safe",
            "kotlin": "kotlin-idiomatic",
            "swift": "swift-modern",
            "dart": "dart-effective",
            "java": "java-clean",
        }
        for lang in project.languages:
            if lang in lang_skill_map:
                skills.append(lang_skill_map[lang])

        # Framework skills
        fw_skill_map = {
            "react": "react",
            "vue": "vue",
            "nextjs": "nextjs",
            "svelte": "svelte",
            "angular": "angular",
            "react-native": "react-native",
            "expo": "expo",
            "flutter": "flutter",
            "fastapi": "fastapi",
            "django": "django",
            "flask": "flask",
            "express": "express",
            "nestjs": "nestjs",
            "gin": "go-fiber",
            "fiber": "go-fiber",
            "langgraph": "langgraph-python",
            "electron": "electron",
            "tauri": "tauri",
        }
        for fw in project.frameworks:
            if fw in fw_skill_map:
                skills.append(fw_skill_map[fw])

        # Testing skills
        test_skill_map = {
            "pytest": "pytest",
            "vitest": "vitest",
            "jest": "jest",
            "playwright": "playwright",
            "cypress": "cypress",
            "behave": "bdd-behave",
        }
        for t in project.testing:
            if t in test_skill_map:
                skills.append(test_skill_map[t])

        # BDD (always recommended if Behave/Cucumber detected)
        if "behave" in project.testing or "cucumber" in str(project.frameworks):
            if "bdd-behave" not in skills:
                skills.append("bdd-behave")

        # DB skills
        db_skill_map = {
            "prisma": "prisma",
            "drizzle": "drizzle",
            "sqlalchemy": "sqlalchemy",
            "gorm": "gorm",
            "mongoose": "mongoose",
        }
        for db in project.databases:
            if db in db_skill_map:
                skills.append(db_skill_map[db])

        return skills


def detect_project_type(path: str | None = None) -> DetectedProject:
    """Quick one-shot detection."""
    root = Path(path) if path else Path.cwd()
    scanner = ProjectScanner(root)
    return scanner.scan()
