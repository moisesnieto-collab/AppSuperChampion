# Plan de Implementación - Ayuda Contextual App de Escritorio

**Fecha:** 18 de octubre de 2026  
**Estado:** Pendiente de implementación  
**Rama Git:** `feature/ayuda-contextual` (por crear)

---

## Objetivo

Implementar un sistema de ayuda contextual amigable para la aplicación de escritorio SuperChampion que facilite el uso a nuevos usuarios, especialmente para las funcionalidades administrativas (modo organizador).

---

## Estrategia General

Combinación de tres elementos:
1. **Botón flotante de ayuda (?)** - Siempre visible
2. **Tooltips en elementos interactivos** - Ayuda rápida al pasar mouse
3. **Modal de ayuda contextual** - Guías detalladas por pantalla

---

## Componentes a Implementar

### 1. Botón Flotante de Ayuda (FAB)

**Ubicación:** Esquina inferior derecha (fixed position)  
**Icono:** `ft.Icons.HELP_OUTLINE` o `ft.Icons.QUESTION_MARK`  
**Color:** `COLOR_CELESTE` o `COLOR_AMBAR` para destacar  
**Comportamiento:**
- Siempre visible en todas las pantallas
- Al hacer click abre modal de ayuda contextual
- Tooltip: "Ayuda y guías de uso"

### 2. Tooltips en Elementos Clave

#### Header (`header.py`)
- Botón LOCK: "Ingresa PIN de seguridad para acceder a modo Organizador"
- Botón EDIT: "Activar modo Administrar (crear, editar, eliminar)"
- Botón EDIT_OFF: "Desactivar modo Administrar"
- Botón LOGOUT: "Cerrar sesión de Organizador y volver a modo Consulta"

#### Selectores (`selector_categoria.py`)
- Año: "Selecciona el año del campeonato"
- Campeonato: "Selecciona el campeonato a gestionar"
- Copa: "Selecciona la copa dentro del campeonato"
- Torneo: "Selecciona el torneo (ej: Copa, Liga)"
- Jornada: "Navega entre jornadas del torneo"
- Categoría: "Selecciona la categoría de juego (ej: Infantil, Juvenil)"

#### Navegación
- Flecha izquierda jornada: "Jornada anterior"
- Flecha derecha jornada: "Jornada siguiente"
- Tab "Marcadores": "Ver lista de partidos y marcadores en vivo"
- Tab "Tabla": "Ver tabla de posiciones por grupos"
- Tab "Estado": "Ver resumen del estado del torneo"

#### Botones de Acción (modo organizador)
- Crear jornada: "Crear una nueva jornada con fecha"
- Editar jornada: "Modificar fecha, lugar u horario de la jornada"
- Eliminar jornada: "Eliminar jornada y todos sus datos"
- Buscar jornada: "Buscar jornada por fecha"
- Crear grupo: "Crear un nuevo grupo con equipos"
- Editar grupo: "Modificar equipos del grupo"
- Eliminar grupo: "Eliminar grupo y sus partidos"

#### Lista de Partidos (`lista_partidos.py`)
- Botón "Guardar": "Guardar marcador del partido"
- Botón "Reiniciar": "Reiniciar marcador a 0-0"
- Botón "Guardar todos": "Guardar todos los marcadores del grupo"
- Switch "VIVO": "Marcar partido como en vivo"
- Campo "Cancha": "Asignar cancha al partido"
- Campo "Hora": "Asignar hora del partido"
- Botón "Programar": "Guardar hora y cancha sin iniciar partido"

### 3. Modal de Ayuda Contextual

**Estructura del Modal:**
- Título: "Ayuda - SuperChampion"
- Contenido dinámico según pantalla/estado
- Secciones:
  1. **Pantalla actual**: Explicación de lo que se está viendo
  2. **Funcionalidades disponibles**: Lista de acciones posibles
  3. **Tips rápidos**: Consejos útiles
  4. **Modo Organizador**: Explicación del PIN y roles (si aplica)

**Contenido por Pantalla:**

#### Pantalla Inicio (selección de campeonato)
- "Selecciona un campeonato para comenzar"
- "Usa los filtros de año para navegar"
- "Modo Master: puedes crear/editar años y campeonatos"

#### Pantalla Campeonato (vista de torneo)
- "Navega por la jerarquía: Copa → Torneo → Jornada → Categoría"
- "Usa los tabs para ver marcadores, tabla o estado"
- "Modo Organizador: edita marcadores, crea jornadas, gestiona grupos"

#### Modo Organizador (con PIN)
- "PIN de seguridad requerido para editar"
- "Roles: Master (control total) / Marcador (solo marcadores)"
- "Modo Administrar: activa botones de edición"

---

## Implementación Técnica

### Nuevo Archivo: `frontend/components/ayuda_contextual.py`

```python
import flet as ft
from config.constants import COLOR_CELESTE, COLOR_TARJETA, COLOR_TEXTO, COLOR_SUBTEXTO

# Diccionario de textos de ayuda
TEXTOS_AYUDA = {
    "header": {
        "pin": "Ingresa PIN de seguridad (4 dígitos) para acceder a modo Organizador",
        "admin": "Activa modo Administrar para crear, editar y eliminar elementos",
        "logout": "Cierra sesión de Organizador y vuelve a modo Consulta"
    },
    "selectores": {
        "anio": "Selecciona el año del campeonato",
        "campeonato": "Selecciona el campeonato a gestionar",
        "copa": "Selecciona la copa dentro del campeonato",
        "torneo": "Selecciona el torneo (ej: Copa, Liga)",
        "jornada": "Navega entre jornadas del torneo",
        "categoria": "Selecciona la categoría de juego"
    },
    "partidos": {
        "guardar": "Guarda el marcador del partido y lo marca como jugado",
        "reiniciar": "Reinicia el marcador a 0-0 y marca como pendiente",
        "vivo": "Marca el partido como en vivo para destacar en la vista pública",
        "cancha": "Asigna la cancha donde se jugará el partido",
        "hora": "Asigna la hora de inicio del partido (formato HH:MM)"
    },
    "pantallas": {
        "inicio": "Pantalla de selección de campeonato. Selecciona un campeonato para comenzar.",
        "campeonato": "Vista del torneo. Navega por Copa → Torneo → Jornada → Categoría.",
        "admin": "Modo Organizador activo. Puedes editar marcadores, crear jornadas y gestionar grupos."
    }
}

def crear_boton_ayuda_flotante(page: ft.Page, on_click):
    """Crea el botón flotante de ayuda en la esquina inferior derecha."""
    return ft.FloatingActionButton(
        icon=ft.Icons.HELP_OUTLINE,
        bgcolor=COLOR_CELESTE,
        foreground_color=COLOR_TEXTO,
        tooltip="Ayuda y guías de uso",
        on_click=on_click,
        width=56,
        height=56
    )

def crear_modal_ayuda(estado: dict, pantalla_actual: str):
    """Crea el modal de ayuda con contenido dinámico según la pantalla."""
    texto_pantalla = TEXTOS_AYUDA["pantallas"].get(pantalla_actual, "Ayuda general")
    
    contenido = ft.Column([
        ft.Text(texto_pantalla, size=14, color=COLOR_TEXTO),
        ft.Divider(),
        ft.Text("Funcionalidades disponibles:", size=12, weight=ft.FontWeight.BOLD, color=COLOR_SUBTEXTO),
        # Agregar lista de funcionalidades según pantalla
    ], spacing=10)
    
    return ft.AlertDialog(
        title=ft.Row([
            ft.Icon(ft.Icons.HELP, color=COLOR_CELESTE, size=24),
            ft.Text("Ayuda - SuperChampion", weight=ft.FontWeight.BOLD, size=18),
        ], spacing=8),
        content=ft.Container(content=contenido, width=400, padding=10),
        actions=[
            ft.TextButton("Cerrar", on_click=lambda e: setattr(dlg, 'open', False)),
        ],
        bgcolor=COLOR_TARJETA,
    )

def obtener_tooltip(seccion: str, elemento: str) -> str:
    """Obtiene el texto de tooltip para un elemento específico."""
    return TEXTOS_AYUDA.get(seccion, {}).get(elemento, "")
```

### Integración en `main.py`

**Pasos:**
1. Importar el módulo de ayuda contextual:
   ```python
   from frontend.components.ayuda_contextual import crear_boton_ayuda_flotante, crear_modal_ayuda
   ```

2. Agregar botón flotante al `page.overlay` después de inicializar la página:
   ```python
   def abrir_ayuda(e):
       pantalla = estado.get("pantalla", "inicio")
       dlg_ayuda = crear_modal_ayuda(estado, pantalla)
       if dlg_ayuda not in page.overlay:
           page.overlay.append(dlg_ayuda)
       dlg_ayuda.open = True
       page.update()
   
   btn_ayuda = crear_boton_ayuda_flotante(page, abrir_ayuda)
   page.overlay.append(btn_ayuda)
   ```

3. Asegurar que el botón flotante esté siempre visible (no se borre al actualizar vista)

### Modificaciones en Componentes Existentes

#### `header.py`
- Agregar tooltips a botones que ya tienen (verificar cuáles faltan)
- Asegurar que todos los botones interactivos tengan tooltip descriptivo

#### `selector_categoria.py`
- Agregar tooltips a chips de selección
- Agregar tooltips a botones de acción (crear, editar, eliminar)
- Usar función `obtener_tooltip()` para mantener consistencia

#### `lista_partidos.py`
- Agregar tooltips a botones de guardar/reiniciar
- Agregar tooltips a campos de cancha/hora
- Agregar tooltips al switch de VIVO

#### `vista_rediseno.py`
- Revisar componentes de navegación y filtros
- Agregar tooltips donde falten

---

## Plan de Trabajo

### 1. Preparación del entorno
- [ ] Crear rama `feature/ayuda-contextual` desde main
- [ ] Verificar que no hay cambios pendientes

### 2. Análisis de la arquitectura
- [x] Revisar estructura de `main.py` (1090 líneas)
- [x] Identificar componentes frontend clave
- [x] Identificar puntos de interacción donde se necesita ayuda

### 3. Diseño del sistema de ayuda
- [x] Definir componentes (botón flotante, tooltips, modal)
- [x] Diseñar estructura de textos de ayuda
- [x] Definir contenido por pantalla

### 4. Implementación
- [ ] Crear módulo `frontend/components/ayuda_contextual.py`
- [ ] Implementar botón flotante en `main.py`
- [ ] Agregar tooltips en `header.py`
- [ ] Agregar tooltips en `selector_categoria.py`
- [ ] Agregar tooltips en `lista_partidos.py`
- [ ] Agregar tooltips en `vista_rediseno.py`
- [ ] Implementar modal dinámico según pantalla/estado
- [ ] Definir textos de ayuda para cada funcionalidad

### 5. Pruebas
- [ ] Verificar tooltips en diferentes pantallas
- [ ] Probar modal de ayuda en cada pantalla
- [ ] Validar que no interfiere con funcionalidad existente
- [ ] Probar en modo organizador y modo consulta

### 6. Documentación y merge
- [ ] Actualizar README.md con nueva funcionalidad
- [ ] Commit de cambios con mensaje descriptivo
- [ ] Merge a main (o pull request)

---

## Archivos a Modificar

1. **Nuevo:** `frontend/components/ayuda_contextual.py`
2. **Modificar:** `main.py` - agregar botón flotante y función abrir_ayuda
3. **Modificar:** `frontend/components/header.py` - agregar tooltips
4. **Modificar:** `frontend/components/selector_categoria.py` - agregar tooltips
5. **Modificar:** `frontend/components/lista_partidos.py` - agregar tooltips
6. **Modificar:** `frontend/components/vista_rediseno.py` - agregar tooltips
7. **Modificar:** `README.md` - documentar nueva funcionalidad

---

## Notas Importantes

- **No modificar lógica existente**, solo agregar tooltips y componentes de ayuda
- **Mantener consistencia** en el estilo de los textos de ayuda
- **Usar colores existentes** del tema de la aplicación
- **Probar en ambos modos**: consulta y organizador
- **Considerar accesibilidad**: textos claros y concisos

---

## Siguientes Pasos al Retomar

1. Crear rama git: `git checkout -b feature/ayuda-contextual`
2. Crear archivo `frontend/components/ayuda_contextual.py`
3. Integrar botón flotante en `main.py`
4. Agregar tooltips progresivamente en cada componente
5. Probar y ajustar según feedback

---

## Referencias

- Archivos analizados:
  - `main.py` - 1090 líneas
  - `frontend/components/header.py` - 108 líneas
  - `frontend/components/selector_categoria.py` - 1156 líneas
  - `frontend/components/lista_partidos.py` - 401 líneas
  - `frontend/components/vista_rediseno.py` - pendiente de revisar

- Colores existentes en `config/constants.py`:
  - `COLOR_CELESTE`, `COLOR_CELESTE_BOTON`
  - `COLOR_AMBAR`, `COLOR_VERDE`, `COLOR_ROJO`
  - `COLOR_TEXTO`, `COLOR_SUBTEXTO`
  - `COLOR_TARJETA`, `COLOR_TARJETA_SEGUNDARIA`
