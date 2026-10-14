---
sessionId: session-261013-165300-hk3z
---

# Plan actual: subir cambios a Git y actualizar main

Hay 14 archivos modificados en `main` (roles Master/Organizador con PIN, tabla responsiva, reconexión, Dockerfile, tests). Se dejan fuera `.ultima_seleccion.json` y `backups/` (locales).

### Pasos
1. Ejecutar `venv/bin/python -m unittest discover tests`.
2. `git add` de los archivos modificados (sin los locales) y commit con mensaje en español.
3. `git push origin main`.

---
# Plan anterior: roles Master y Organizador

### Diagnóstico
Hoy no hay identidad de usuario: el acceso es un único PIN (`TorneoService.validar_pin`, `ConfiguracionRepository.obtener_pin`, `main.py` ~línea 156) que pone `estado["es_organizador"]=True`, y `modo_admin` activa las herramientas (`es_org` en `main.py` 651 y `selector_categoria.py`). La tabla `campeonato_permisos` (usuario_id, rol) y el modal Permisos guardan `master`/`organizador`, pero `verificar_permiso` nunca se usa. Como no existe login, los permisos por usuario no se pueden aplicar.

### Decisión de diseño
Usar **dos PIN**: el PIN de Organizador (existente) y un nuevo PIN de Master (`MASTER_PIN` en `config/settings.py` y `.env.example`, con lectura en `ConfiguracionRepository.obtener_pin_master`). El rol queda en `estado["rol"]` (`None` | `organizador` | `master`). El modal Permisos por usuario se elimina, porque no tiene efecto.

### Reglas
- **Master**: todo lo del Organizador, más editar/eliminar campeonato, año, copa y torneo, y cambiar reglas del campeón de la Copa.
- **Organizador**: crear jornadas, categorías y grupos; registrar y reiniciar marcadores; generar desempate/final; eliminar jornada/categoría/grupo.
- **Visitante**: solo consulta.

### Cambios
1. `config/settings.py`, `.env.example`: `MASTER_PIN`.
2. `TorneoService.validar_pin` devuelve el rol (`master`, `organizador` o `None`). `main.py` (diálogo PIN) guarda `estado["rol"]` y mantiene `es_organizador` para compatibilidad. `header.py` muestra el rol y al cerrar sesión limpia `rol`.
3. `selector_categoria.py`: calcular `es_master = rol == "master" and modo_admin`. Las acciones de año, campeonato, copa y torneo (crear, editar, eliminar, permisos) solo se muestran si `es_master`; las de jornada, categoría y grupo, si `es_organizador`.
4. Defensa en servicios: `CampeonatoService`, `CopaService`, `AnioService` y `TorneoService.crear/eliminar_torneo` reciben `es_master` y lanzan `PermissionError` si es falso (patrón ya usado con `es_organizador=True` en `TorneoService`).
5. Quitar `modal_permisos` y la opción "Permisos" del menú ⋮; dejar la tabla `campeonato_permisos` sin uso.

### Pruebas
`venv/bin/python -m unittest discover tests`; añadir tests de `validar_pin` por rol y de `PermissionError` en servicios; revisar a mano con cada PIN.

### Pasos
1. PIN Master y `validar_pin` con rol; estado y header.
2. Restringir acciones en `selector_categoria.py` por rol.
3. Validación en servicios, eliminar Permisos, tests.

---
# Plan anterior: tabla de posiciones responsiva

### Diagnóstico
`frontend/components/tabla_posiciones.py` usa `ft.DataTable` con 10 columnas dentro de un `ft.ListView`. DataTable tiene ancho mínimo fijo (no se adapta): en móvil se corta o desborda, y el `ListView` no da scroll horizontal.

### Cambios
1. Reemplazar `DataTable` por filas `ft.Row`: cabecera + una fila por equipo. Columnas fijas pequeñas (`width`) para `#`, PJ, DG, Pts, y el nombre del equipo con `expand=True` y `ellipsis`, así siempre cabe.
2. Columnas secundarias (PG, PE, PP, GF, GC) con parámetro `compacto: bool`. `main.py` pasa `compacto = (page.width or 0) < 600`; en móvil se ocultan, en escritorio se muestran. Se recalcula en `actualizar_vista` y en `page.on_resize`.
3. Conservar: líder dorado 🥇, color de Copa (`color_copa`), colores de DG y badge de Pts.
4. Leyenda corta bajo la tabla en modo compacto ("PJ jugados · DG dif. goles · Pts puntos").

### Pruebas
`venv/bin/python -m unittest discover tests`; ajustar `tests/test_componentes_color.py` si inspecciona la tabla; revisión manual en móvil y escritorio.

### Pasos
1. Reescribir `crear_tabla_posiciones` con filas y parámetro `compacto`.
2. Pasar `compacto` desde `main.py` y refrescar en `on_resize`; ejecutar tests.

---
# Plan anterior: la app queda congelada al perder el foco y volver

### Diagnóstico
En web, Flet usa un WebSocket por sesión. Al pasar el navegador/iPhone a segundo plano, el sistema suspende el socket (o Render lo corta por inactividad). Al volver, el cliente queda con la UI vieja y los clics no llegan al servidor; solo recargar crea una sesión nueva. `main.py` (línea 944) usa `ft.run(main, export_asgi_app=True)` sin ninguna gestión de reconexión, y el `Dockerfile` ejecuta uvicorn con valores por defecto.

### Cambios
1. `main.py`: registrar `page.on_disconnect`/`page.on_connect` (verificar nombres en Flet 1.0.3); al reconectar, llamar a `actualizar_vista()` y `page.update()`.
2. `main.py`: si la sesión ya no existe y la reconexión falla, mostrar un aviso "Conexión perdida, toca para recargar" con botón `page.launch_url(page.url)`/recarga automática.
3. `Dockerfile`/arranque: pasar `--ws-ping-interval 20 --ws-ping-timeout 60` a uvicorn y definir `FLET_SESSION_TIMEOUT` mayor para no descartar sesiones inactivas.
4. Documentar que Render gratuito duerme la app; sugerir UptimeRobot.

### Pruebas
`venv/bin/python -m unittest discover tests`; prueba manual: abrir en el iPhone, bloquear 1 min, volver y navegar.

### Pasos
1. Verificar API de eventos de Flet 1.0.3.
2. Implementar reconexión y aviso en `main.py`.
3. Ajustar uvicorn/Dockerfile y ejecutar tests.

---
# Plan anterior: layout responsivo e iconos de acción bajo cada objeto

### Objetivo
1. Todas las pantallas responsivas (se adaptan al ancho).
2. Acciones crear/eliminar/editar solo como iconos (sin texto), ubicadas debajo del objeto al que afectan.

### Cambios en `frontend/components/selector_categoria.py` (`_seccion` y chips)
- Reemplazar la fila con scroll horizontal por `ft.Row(wrap=True, run_spacing=6)`, así los pills pasan a la línea siguiente según el ancho. Para pantallas muy estrechas el contenedor usa `expand=True` y sin ancho fijo.
- Crear helper `_icono_accion(icono, color, tooltip, on_click)`: `IconButton` pequeño (size 18) con tooltip; sustituye a `_chip_nuevo`/`_chip_eliminar` y a los botones de texto "Nuevo Torneo", "Nueva Cat", "Eliminar", "Nuevo Grupo", "Eliminar Cat".
- `_seccion` devuelve: etiqueta, fila de pills y, DEBAJO, una fila de iconos de acción (＋ crear, 🗑 eliminar, ✎ editar, 🔍 buscar) solo si es organizador. Se pasan como parámetro `acciones`.
- Quitar editar/eliminar embebidos dentro de los pills (Copa, Torneo, Grupo): se editan/eliminan con los iconos de la sección actuando sobre el elemento activo.
- Pantalla de inicio: tarjetas de campeonato con `col={"xs":12,"sm":6,"md":4}`; icono ＋ bajo la rejilla; menú ⋮ por tarjeta se mantiene.
- Cabecera: título con `expand=True` y `overflow=ELLIPSIS`.

### `main.py`
- Pills de Marcadores/Tabla/Estado en `ft.Row(wrap=True)`; contenedores sin anchos fijos.

### Pruebas
`venv/bin/python -m unittest discover tests` y revisión visual en móvil y escritorio.

### Pasos
1. Helper de iconos y `_seccion` con acciones debajo.
2. Convertir filas a wrap y limpiar botones con texto/embebidos.
3. Ajustar inicio y `main.py`, y ejecutar tests.

---
# Plan anterior (histórico)

# Requirements

### Arreglo actual: NameError COLOR_BORDE
`main.py` línea 749 usa `COLOR_BORDE`, pero el import de `config.constants` (líneas 12-15) no lo incluye. Solución: añadir `COLOR_BORDE` a ese import. Sin otros cambios.

### (Contexto anterior) Overview & Goals
Rediseñar la segunda pantalla (vista de campeonato) con patrones de apps deportivas (SofaScore, FotMob, Liga/Copa apps): navegación compacta, marcadores primero, y menos filtros apilados.

### Primera pantalla (inicio)
Aplicar el mismo lenguaje visual a la pantalla de inicio (`vista == "inicio"` en `selector_categoria.py`) para que toda la app sea coherente:
- Años como pills de una sola fila con scroll horizontal (`border_radius=20`, `wrap=False`).
- Campeonatos como tarjetas de ancho completo en móvil (rejilla en escritorio), con icono, nombre, año y flecha `chevron_right`; la tarjeta del último campeonato se destaca.
- Título "¿Qué campeonato quieres ver?" más sobrio, sin divisores ni pasos numerados; estado vacío con icono y texto.
- Botones de administrar (editar/eliminar/nuevo) agrupados en un `PopupMenuButton` por tarjeta.
- El header de inicio (`header.py`) mantiene su aspecto normal y comparte tipografía y radios con la segunda pantalla.

### Problema actual
`selector_categoria.py` apila 5 secciones (Copa, Torneo, Jornada, Categoría, Grupo) con chips que se envuelven en varias filas, antes de ver un solo marcador. En móvil el usuario debe hacer scroll para llegar al contenido.

### Scope
- En: layout del selector y orden de la pantalla en `main.py`; sin cambios de BD ni de lógica de negocio.
- Fuera: cambios al modo Administrar más allá de reubicar sus botones.

### Functional Requirements
- Una sola fila horizontal con scroll por nivel (chips tipo "pill"), en vez de filas envueltas.
- Copa como pestañas superiores; Torneo y Jornada como selectores desplegables compactos; Categoría como pills con scroll; Grupo como segmento (Todos / A / B).
- Contenido principal ordenado: Estado del Torneo, Marcadores, Tabla (pestañas Marcadores / Tabla en móvil).
- Controles de administración ocultos tras un menú o botón flotante.

# Technical Design

### Proposed Changes
- `selector_categoria.py`: `_seccion` pasa a filas con `scroll=ft.ScrollMode.AUTO` y `wrap=False`; Torneo y Jornada se renderizan con `ft.Dropdown`/`PopupMenuButton` compactos en una sola fila; cabecera sticky con título y botón atrás.
- Sustituir los `Divider` y títulos por etiquetas pequeñas; pills con `border_radius=20`.
- `main.py` (`actualizar_vista`): usar `ft.Tabs` (Marcadores / Tabla / Estado) para la zona de contenido en pantallas estrechas.
- Acciones de admin (nuevo/editar/eliminar) agrupadas en un `PopupMenuButton` por nivel.

- Primera pantalla: reescribir el bloque `if vista == "inicio":` de `selector_categoria.py` reutilizando los mismos helpers de pills y menú de admin que la segunda pantalla.

### Risks
Flet 1.0.3: verificar API de `Tabs`/`PopupMenuButton`; mantener la lógica de colores por Copa.

# Testing
Ejecutar `venv/bin/python -m unittest discover tests` y revisar visualmente en móvil y escritorio.
