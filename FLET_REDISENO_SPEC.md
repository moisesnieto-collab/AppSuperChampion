# Rediseño de navegación y UI: CampeonatosLive (Flet)

Instrucciones para aplicar el rediseño a la app existente. Mantén la lógica de datos actual; cambia la estructura de pantallas, los componentes y el tema.

## 1. Objetivo

- Eliminar la pantalla separada de "Año / Campeonato". Se elige en un bottom sheet desde la cabecera.
- Abrir directo en el contenido (marcadores), con la última selección del usuario o la jornada actual.
- Dejar de apilar 5 filtros en bloques. Usar una sola pantalla con filtros compactos y navegación inferior.
- Fondo neutro oscuro fijo. El color de cada Copa se usa solo como acento.
- Mostrar solo opciones que tienen datos. Nunca un filtro vacío con el mensaje "No hay categorías disponibles" sin explicación.

## 2. Tokens

```python
BG        = "#0B1020"   # fondo
SURFACE   = "#121A2B"   # tarjetas
SURFACE_2 = "#141B2D"   # contenedores de chips
BORDER    = "#1E2740"
BORDER_2  = "#2A3350"
TEXT      = "#F1F4FA"
TEXT_2    = "#C5CEE0"
MUTED     = "#9AA6BD"
MUTED_2   = "#8793AB"
LIVE      = "#FF7A7A"
OK        = "#3DD598"
GOLD      = "#FBBF24"   # "Modo consulta"
NAV_BG    = "#0F1526"

# Un tema por Copa (máx. 4). solid = relleno con texto blanco (>4.5:1); bright = acento sobre fondo oscuro
COPA_THEMES = [
    {"solid": "#1B7F53", "bright": "#3DD598"},  # SuperCampeones Chicureo
    {"solid": "#B02E6B", "bright": "#F472B6"},  # SuperCampeones 2
    {"solid": "#2563EB", "bright": "#60A5FA"},  # Supercampeones
    {"solid": "#B45309", "bright": "#FBBF24"},  # 4ª Copa
]
```

- Fuente: Montserrat (pesos 500, 600, 700, 800). Escala: 10 (etiquetas en mayúsculas, `letter_spacing` .1em), 12, 13, 16, 18, 28.
- Espaciado: 8, 12, 16, 24. Radios: 9 (segmento), 12 (chip de categoría), 14 (tarjeta), 22 (chip de Copa), 20 (sheet).
- Áreas táctiles mínimas de 44 px (Copa, flechas de jornada, navegación).

Define el tema de la página una vez: `page.theme_mode = ft.ThemeMode.DARK`, `page.bgcolor = BG`, `page.fonts = {"Montserrat": ...}` y `page.theme = ft.Theme(font_family="Montserrat", color_scheme_seed=...)`. Al cambiar de Copa, solo cambia el acento (`bright` / `solid`).

## 3. Estructura de la pantalla (una sola vista)

```
Column (expand)
├─ Cabecera (Row, space_between)
│   ├─ TextButton → abre BottomSheet de campeonato
│   │     "CampeonatosLive" (11, MUTED) / "Supercampeones 2026" (16, w700) + icono chevron-down
│   └─ Row: eye + "Modo consulta" (11, GOLD, w700) + IconButton candado (acceso admin)
├─ Row scrollable (scroll=AUTO)  → Copa: chips 44 px alto, radio 22
│     activo: bgcolor=solid, texto blanco, punto blanco
│     inactivo: borde BORDER_2, texto TEXT_2, punto=bright
├─ Row scrollable → Categoría: chips 40 px alto, radio 12
│     activo: bgcolor=TEXT, texto BG   |  inactivo: SURFACE_2, borde BORDER_2
├─ Row (center) → Jornada: IconButton ‹  | "JORNADA" (10) + "Día 1 · 27-09-2026" (14, w700) | IconButton ›
│     ‹ y › con opacidad .3 en los extremos
├─ Control de Grupo: Row de 4 botones iguales (Todos, A, B, C) sobre contenedor SURFACE_2, radio 12, padding 4
│     activo: bgcolor "#2C3860", texto blanco
├─ Contenido (Column, expand=True, scroll=AUTO): según pestaña activa
└─ NavigationBar (Marcadores | Tabla | Estado)
      bgcolor=NAV_BG; ícono y etiqueta activos con color bright de la Copa
```

Componentes Flet sugeridos: `ft.NavigationBar`, `ft.BottomSheet`, `ft.SegmentedButton` o `Row` de `Container`, `ft.Chip` o `Container` con `on_click`, `ft.Row(scroll=ft.ScrollMode.AUTO)`.

## 4. Pestañas

### Marcadores
Una sección por grupo visible (`GRUPO A`, `GRUPO B`, `GRUPO C`), cada una con:
- Encabezado: punto `bright` + etiqueta 12/w800, `letter_spacing` .1em, color TEXT_2.
- Tarjeta SURFACE, borde BORDER, radio 14, con **6 filas** (todos contra todos en grupos de 4): pares (1-2, 3-4, 1-3, 2-4, 1-4, 2-3).
- Cada fila: columna izquierda de 54 px con hora (12, w700) y debajo el estado; a la derecha los dos equipos apilados, cada uno con su marcador alineado a la derecha (15, w800).
- Estado: `Final` (MUTED_2) / punto pulsante + `VIVO` (LIVE) / cancha cuando está por jugar. El estado siempre lleva texto, no solo color.
- Ganador en w800, el otro en w500. Por jugar: marcador "–" en MUTED_2.

### Tabla
Una tarjeta por grupo con columnas `# | EQUIPO | PJ | DG | PTS`. El líder del grupo con fondo `bright` al 12 % de opacidad y número en `bright`. Ordenar por puntos y luego por diferencia de goles.

### Estado
- 3 tarjetas con cifras (28, w800): Finalizados, En vivo (LIVE), Por jugar (bright).
- Tarjeta con punto pulsante verde: "Marcadores en vivo conectados. Se actualizan solos, no necesitas refrescar."
- Tarjeta "Mostrando": Copa, Categoría, Jornada.

## 5. BottomSheet de campeonato
Se abre desde la cabecera. Contiene:
- Título "Elegir campeonato" (18, w800).
- Chips de AÑO (alto 44).
- Lista de CAMPEONATO, una fila de 56 px por opción, con borde y check en la opción activa.
- Al elegir, cierra el sheet y recarga la vista. Reemplaza la pantalla actual de selección.

## 6. Reglas de datos y estados

- **Persistencia**: guardar en `page.client_storage` la última selección (año, campeonato, copa, categoría, grupo). Al abrir, restaurarla. Si no existe, usar la primera Copa con datos y la jornada actual o en vivo.
- **Filtros dependientes**: Copa → Categoría → Jornada. Al cambiar un nivel, reiniciar los inferiores al primer valor válido.
- **Opciones sin datos**: ocultar o deshabilitar (opacidad .4) las Copas y categorías sin datos. Ocultar el control de Grupo si solo existe "Todos". Ocultar Torneo si hay una única opción (ej. "Clausura"); si hay varias, ponerlo como filtro dentro de un botón "Filtros" que abre un bottom sheet.
- **Estado vacío**: icono + título + qué hacer. Ejemplo: "Aún no hay categorías en esta Copa. Prueba otra Copa o vuelve pronto." Con un botón para volver a la última Copa con datos.
- **Carga**: mostrar skeletons (tarjetas grises) en lugar de pantalla vacía.
- **Actualización en vivo**: refrescar solo las filas que cambian, sin reconstruir toda la pantalla; mantener la posición del scroll.
- **Modo consulta / admin**: el candado conserva su comportamiento actual.

## 7. Accesibilidad

- Contraste mínimo 4.5:1 para texto (los valores de `solid` y `MUTED_2` ya lo cumplen).
- Cada control con `tooltip` o etiqueta clara (flechas de jornada, candado, selector).
- No depender solo del color: los estados llevan texto (`VIVO`, `Final`).

## 8. Criterios de aceptación

1. La app abre directo en Marcadores sin pasar por la pantalla de año y campeonato.
2. Copa, categoría, jornada y grupo caben en menos de un cuarto del alto de la ventana.
3. Cambiar de Copa cambia solo los acentos, nunca el fondo.
4. No existe ninguna pantalla con filtros vacíos y el mensaje "No hay categorías disponibles" sin acción.
5. Las 4 Copas, 6 categorías, 3 grupos de 4 equipos y 6 partidos por grupo se ven sin desbordar en 390 px de ancho y en escritorio.
