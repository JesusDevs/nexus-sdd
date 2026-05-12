---
name: android
description: Android development with official CLI, Jetpack Compose, AGP 9, and Google skills
category: mobile
stack: [android, kotlin, java, jetpack-compose, gradle, agp]
triggers: [android, kotlin, java, compose, gradle, agp, apk, emulator, sdk, jetpack]
source: https://github.com/android/skills
---

# Android Skill

## Agent Attitude
Eres un desarrollador Android con Kotlin + Jetpack Compose. Siempre usas la CLI oficial (`android`) para tareas de configuración, build y emulación. Prefieres Compose sobre XML Views. Material 3 por defecto.

## Prerrequisitos

### Android CLI (obligatorio)
```bash
# Instalar
curl -fsSL https://developer.android.com/studio/cli -o android-cli.zip
unzip android-cli.zip && chmod +x android && sudo mv android /usr/local/bin/

# Verificar
android --version
android update

# Configurar para agentes
android init   # Instala la skill android-cli para Gemini/Claude/Codex
```

### Skills Oficiales de Google
```bash
# Listar skills disponibles
android skills list --long

# Instalar skills recomendadas para desarrollo general
android skills add --all

# Skills específicas según necesidad:
android skills add edge-to-edge          # Pantallas borde a borde
android skills add navigation-3          # Navegación con Navigation 3
android skills add migrate-xml-views-to-jetpack-compose  # Migración a Compose
android skills add agp-9-upgrade         # Actualización a AGP 9
android skills add camera1-to-camerax    # Migración Camera1 → CameraX
android skills add r8-analyzer           # Optimización R8
android skills add play-billing-library-version-upgrade  # Play Billing
android skills add perfetto-sql          # Profiling con Perfetto
```

## Reglas

### Proyecto
- `android create --name=<app> --output=<path>` para nuevos proyectos.
- `android describe` para metadata del proyecto actual.
- `android info` para verificar SDK path.

### Build y Deploy
- `android run --apks=<path>` para instalar en dispositivo/emulador.
- `android sdk list <pattern>` antes de instalar paquetes SDK.
- `android sdk install <package@version>` con versión específica.

### Emulador
- `android emulator list` para ver dispositivos disponibles.
- `android emulator create --profile=<profile>` para crear AVD.
- `android emulator start <name>` para iniciar.
- `android emulator stop <serial>` para detener.

### UI y Testing
- `android layout --output=ui.json` para árbol de layout.
- `android screen capture --annotate --output=screen.png` para screenshot anotada.
- `android screen resolve --screenshot=screen.png --string="input tap #5"` para coordenadas de UI.

### Documentación
- `android docs search "<query>"` para buscar en la knowledge base de Android.
- `android docs fetch kb://android/topic/...` para leer documentación oficial.

## Do's
- Jetpack Compose + Material 3 para UI nueva. NO XML Views.
- Kotlin 2.0+ con coroutines. NO AsyncTask ni callbacks.
- Navigation 3 para navegación type-safe.
- AGP 9+ y Gradle Kotlin DSL (`build.gradle.kts`).
- `android skills add` para mantener skills actualizadas (Google las actualiza).
- Edge-to-edge en todas las apps nuevas.
- Perfetto para profiling (reemplaza a systrace).

## Don'ts
- NO XML Views en features nuevos (usar Compose).
- NO `android:allowBackup="true"` sin saber qué estás exponiendo.
- NO hardcodear API keys en `AndroidManifest.xml` ni `build.gradle`.
- NO `AsyncTask`, `AsyncTaskLoader`, `LoaderManager` (deprecated).
- NO `support.v4` ni `support.v7` (usar AndroidX).
- NO `android run` sin antes verificar el device target si hay múltiples.

## Skills Oficiales (github.com/android/skills)

| Skill | Cuándo usar |
|-------|-------------|
| `android-cli` | Siempre. Base para cualquier proyecto. |
| `edge-to-edge` | Apps nuevas. Obligatorio para Android 15+. |
| `navigation-3` | Navegación type-safe entre pantallas. |
| `migrate-xml-views-to-jetpack-compose` | Proyecto legacy con XML Views. |
| `agp-9-upgrade` | Actualizar Android Gradle Plugin. |
| `camera1-to-camerax` | Migrar cámara antigua a CameraX. |
| `r8-analyzer` | Optimizar ofuscación y shrinking. |
| `play-billing-library-version-upgrade` | Actualizar billing de Google Play. |
| `perfetto-sql` | Profiling avanzado con Perfetto. |
| `display-ai-glasses-with-jetpack-compose-glimmer` | XR / AI glasses. |

## Seguridad

Las skills oficiales de Google (`github.com/android/skills`) son seguras por defecto.
Nexus-SDD las valida por hash SHA antes de instalarlas automáticamente.

```bash
# Nexus-SDD instala skills oficiales con verificación
nexus-sdd skill install @android/edge-to-edge   # Verifica firma de Google
nexus-sdd skill install android                 # Nuestra skill wrapper
```

## Comandos Recomendados
- `android create list` — Ver plantillas disponibles
- `android describe` — Metadata del proyecto
- `android sdk list platforms` — Plataformas instaladas
- `android sdk update` — Actualizar todo el SDK
- `android emulator list` — Dispositivos disponibles
- `android layout --pretty` — Árbol de UI legible
- `android run --apks=app/build/outputs/apk/debug/app-debug.apk` — Deploy
- `android skills list --long` — Skills oficiales disponibles
