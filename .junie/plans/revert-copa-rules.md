---
sessionId: session-261013-165300-hk3z
---

# Requirements

### Overview & Goals
Subir a GitHub los cambios pendientes y actualizar la rama `main` remota.

### Scope
- En: commit de los cambios de código y tests (botón Generar Gran Final solo en modo `final_lideres`, checkbox de borrado de partidos de definición, contador de goles oculto, `es_org` con modo Administrar) y `git push origin main`.
- Fuera: archivos locales (`.ultima_seleccion.json`, `backups/`, `superchampion.db`) y cambios de código nuevos.

# Technical Design

### Proposed Changes
- `git status` y `git diff --stat` para revisar lo pendiente y la rama actual.
- Ejecutar `venv/bin/python -m unittest discover tests` antes del commit.
- `git add` solo de archivos de código, tests y `.junie/plans`; excluir los locales.
- Commit con mensaje descriptivo y `git push origin main` (si no se está en `main`, cambiar o fusionar primero).

### Risks
Si el remoto tiene commits nuevos, hacer `git pull --rebase origin main` antes del push; nunca forzar el push.

# Testing
Suite de tests en verde y `git status` limpio (salvo archivos locales) tras el push.
