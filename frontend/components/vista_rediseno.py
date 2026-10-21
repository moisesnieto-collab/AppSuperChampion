"""Componentes del rediseño (FLET_REDISENO_SPEC.md): cabecera con bottom sheet,
filtros compactos y navegación inferior. La lógica de datos no cambia."""
import flet as ft
from typing import Callable, Optional

from config.constants import (
    BG, SURFACE, SURFACE_2, BORDER, BORDER_2, TEXT, TEXT_2, MUTED, MUTED_2, GOLD, NAV_BG, LIVE, OK,
    COPA_THEMES, RADIO_SEGMENTO, RADIO_CATEGORIA, RADIO_TARJETA, RADIO_COPA, RADIO_SHEET,
)
from config.constants import mezclar_color
from backend.services.torneo_service import TorneoService
from backend.services.anio_service import AnioService
from backend.services.campeonato_service import CampeonatoService
from backend.services.copa_service import CopaService
from backend.database.repositories import TorneoRepository, CampeonatoRepository
from config.preferencias import guardar_ultima_seleccion

TABS = ("Marcadores", "Tabla", "Estado")
_ICONOS_TAB = {
    "Marcadores": (ft.Icons.SPORTS_SOCCER_OUTLINED, ft.Icons.SPORTS_SOCCER),
    "Tabla": (ft.Icons.LEADERBOARD_OUTLINED, ft.Icons.LEADERBOARD),
    "Estado": (ft.Icons.EMOJI_EVENTS_OUTLINED, ft.Icons.EMOJI_EVENTS),
}


def tema_copa(copas: list, copa_id: Optional[int]) -> dict:
    """Devuelve {'solid','bright'} según la posición de la Copa (máx. 4 temas)."""
    idx = next((i for i, c in enumerate(copas) if c.id == copa_id), 0)
    if not copas:
        return COPA_THEMES[0]
    color = getattr(copas[idx], "color", None)
    if color:
        try:
            return {"solid": color, "bright": mezclar_color(color, 0.35)}
        except Exception:
            pass
    return COPA_THEMES[idx % len(COPA_THEMES)]


def _etiqueta(txt: str) -> ft.Text:
    return ft.Text(txt, size=10, weight=ft.FontWeight.W_700, color=MUTED, style=ft.TextStyle(letter_spacing=1.0))


def fecha_sin_hora(fecha) -> str:
    """Devuelve la fecha como DD-MM-YYYY, sin la hora."""
    try:
        from datetime import datetime
        return datetime.fromisoformat(str(fecha)).strftime("%d-%m-%Y")
    except Exception:
        return str(fecha).split("T")[0]


def cargar_jerarquia(estado: dict, copa_id: Optional[int] = None):
    """Rellena torneo/jornada/categoría activos a partir de la copa (primer valor válido)."""
    estado["copa_activa_id"] = copa_id
    estado["torneo_activo_id"] = None
    estado["jornada_activa_id"] = None
    estado["categoria_activa_id"] = None
    estado["grupo_filtro"] = "Todos"
    # Limpiar selección guardada para evitar restauración automática de otra copa
    from config.preferencias import guardar_seleccion_completa
    guardar_seleccion_completa({})
    if not copa_id:
        return
    torneos = TorneoRepository.obtener_por_copa(copa_id)
    if not torneos:
        return
    estado["torneo_activo_id"] = torneos[0].id
    jornadas = TorneoService.obtener_jornadas_por_torneo(torneos[0].id)
    if jornadas:
        estado["jornada_activa_id"] = jornadas[0].id
        cats = TorneoService.obtener_categorias_por_jornada(jornadas[0].id)
        if cats:
            estado["categoria_activa_id"] = cats[0].id


def abrir_sheet_campeonato(estado: dict, page: ft.Page, on_cambio: Callable):
    """Bottom sheet 'Elegir campeonato': chips de año y lista de campeonatos."""
    def cerrar():
        page.pop_dialog()

    def elegir_anio(aid):
        estado["anio_activo_id"] = aid
        camps = CampeonatoService.obtener_campeonatos_por_anio(aid)
        if camps:
            elegir_camp(camps[0].id, cerrar_sheet=False)
        construir()

    def elegir_camp(cid, cerrar_sheet=True):
        estado["campeonato_activo_id"] = cid
        estado["pantalla"] = "campeonato"
        copas = CopaService.obtener_copas_por_campeonato(cid)
        cargar_jerarquia(estado, copas[0].id if copas else None)
        guardar_ultima_seleccion(estado.get("anio_activo_id"), cid)
        if cerrar_sheet:
            cerrar()
            on_cambio()

    cuerpo = ft.Column(tight=True, spacing=12, scroll=ft.ScrollMode.AUTO)

    def construir():
        anios = AnioService.obtener_anios()
        camps = CampeonatoService.obtener_campeonatos_por_anio(estado.get("anio_activo_id")) \
            if estado.get("anio_activo_id") else []
        chips = [
            ft.Container(
                content=ft.Text(str(a.valor), size=13, weight=ft.FontWeight.W_700,
                                color=BG if a.id == estado.get("anio_activo_id") else TEXT_2),
                height=44, padding=ft.Padding.symmetric(horizontal=18), alignment=ft.Alignment.CENTER,
                border_radius=RADIO_COPA,
                bgcolor=TEXT if a.id == estado.get("anio_activo_id") else SURFACE_2,
                border=ft.Border.all(1, BORDER_2),
                on_click=lambda e, aid=a.id: elegir_anio(aid), ink=True, tooltip=f"Año {a.valor}",
            ) for a in anios
        ]
        filas = []
        for c in camps:
            activo = c.id == estado.get("campeonato_activo_id")
            filas.append(ft.Container(
                content=ft.Row([
                    ft.Text(c.nombre, size=14, weight=ft.FontWeight.W_700, color=TEXT, expand=True,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Icon(ft.Icons.CHECK_CIRCLE if activo else ft.Icons.CHEVRON_RIGHT,
                            color="#3DD598" if activo else MUTED, size=20),
                ]),
                height=56, padding=ft.Padding.symmetric(horizontal=14), border_radius=RADIO_TARJETA,
                bgcolor=SURFACE, border=ft.Border.all(1.5 if activo else 1, "#3DD598" if activo else BORDER),
                on_click=lambda e, cid=c.id: elegir_camp(cid), ink=True,
                tooltip=c.nombre,
            ))
        if not filas:
            filas = [ft.Text("No hay campeonatos en este año.", size=13, color=MUTED)]
        cuerpo.controls = [
            ft.Text("Elegir campeonato", size=18, weight=ft.FontWeight.W_800, color=TEXT),
            _etiqueta("AÑO"),
            ft.Row(chips, wrap=True, spacing=8, run_spacing=8),
            _etiqueta("CAMPEONATO"),
            *filas,
        ]
        try:
            cuerpo.update()
        except Exception:
            pass

    construir()
    page.show_dialog(ft.BottomSheet(
        content=ft.Container(content=cuerpo, padding=20, bgcolor=BG,
                             border_radius=ft.BorderRadius.only(top_left=RADIO_SHEET, top_right=RADIO_SHEET)),
        bgcolor=BG, scrollable=True,
    ))


def crear_cabecera_campeonato(estado: dict, page: ft.Page, on_cambio: Callable, accent: str,
                              badge_rol=None) -> ft.Container:
    camp = CampeonatoRepository.obtener_por_id(estado["campeonato_activo_id"]) \
        if estado.get("campeonato_activo_id") else None
    nombre = camp.nombre if camp else "Elegir campeonato"
    modo = "Administrar" if estado.get("modo_admin") else "Modo consulta"
    return ft.Container(
        content=ft.Row([
            ft.TextButton(
                content=ft.Row([
                    ft.Column([
                        ft.Text("CampeonatosLive", size=11, color=MUTED),
                        ft.Text(nombre, size=16, weight=ft.FontWeight.W_700, color=TEXT, max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS),
                    ], spacing=0, tight=True),
                    ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN, color=accent, size=22),
                ], spacing=6, tight=True),
                tooltip="Elegir año y campeonato",
                on_click=lambda e: abrir_sheet_campeonato(estado, page, on_cambio),
            ),
            ft.Container(content=badge_rol, expand=True, alignment=ft.Alignment.CENTER_RIGHT)
            if badge_rol is not None else ft.Row([
                ft.Icon(ft.Icons.VISIBILITY if not estado.get("modo_admin") else ft.Icons.EDIT, size=14, color=GOLD),
                ft.Text(modo, size=11, weight=ft.FontWeight.W_700, color=GOLD),
            ], spacing=4),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.Padding.symmetric(horizontal=12, vertical=4),
    )


def crear_filtros(estado: dict, page: ft.Page, on_cambio: Callable, tema: dict, copas: list,
                  categorias: list, jornadas: list, grupos_nombres: list,
                  acciones: Optional[dict] = None) -> ft.Control:
    """Copa (44 px), Categoría (40 px), navegador de Jornada y control de Grupo.
    `acciones` ({sección: [IconButton]}) alimenta los botones ⋮ con bottom sheet de mantenedores."""
    solid, bright = tema["solid"], tema["bright"]
    acciones = acciones or {}

    def boton_mas(titulo, secciones):
        grupos = [(s, acciones.get(s)) for s in secciones if acciones.get(s)]
        if not grupos:
            return None

        def ejecutar(btn):
            page.pop_dialog()
            btn.on_click(None)

        def abrir(e):
            cuerpo = [ft.Text(f"Administrar · {titulo}", size=18, weight=ft.FontWeight.W_800, color=TEXT)]
            for sec, btns in grupos:
                cuerpo.append(_etiqueta(sec.upper()))
                for b in btns:
                    cuerpo.append(ft.Container(
                        content=ft.Row([ft.Icon(b.icon, color=b.icon_color, size=22),
                                        ft.Text(b.tooltip, size=14, weight=ft.FontWeight.W_700, color=TEXT,
                                                expand=True)], spacing=12),
                        height=52, padding=ft.Padding.symmetric(horizontal=14), border_radius=RADIO_TARJETA,
                        bgcolor=SURFACE, border=ft.Border.all(1, BORDER),
                        on_click=lambda ev, b=b: ejecutar(b), ink=True,
                    ))
            cuerpo.append(ft.Container(
                content=ft.Row([ft.Icon(ft.Icons.ARROW_BACK, color=TEXT_2, size=20),
                                ft.Text("Volver", size=14, weight=ft.FontWeight.W_700, color=TEXT_2)],
                               alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                height=48, border_radius=RADIO_TARJETA, border=ft.Border.all(1, BORDER_2),
                on_click=lambda ev: page.pop_dialog(), ink=True, tooltip="Volver sin cambios",
            ))
            page.show_dialog(ft.BottomSheet(
                content=ft.Container(
                    content=ft.Column(cuerpo, tight=True, spacing=10, scroll=ft.ScrollMode.AUTO),
                    padding=20, bgcolor=BG,
                    border_radius=ft.BorderRadius.only(top_left=RADIO_SHEET, top_right=RADIO_SHEET)),
                bgcolor=BG, scrollable=True))

        return ft.IconButton(ft.Icons.MORE_VERT, icon_color=TEXT_2, tooltip=f"Administrar {titulo.lower()}",
                             on_click=abrir, width=44, height=44)

    # Copas: se deshabilitan (opacidad .4) las que no tienen torneos
    def elegir_copa(cid):
        cargar_jerarquia(estado, cid)
        estado["copa_abierta"] = False
        on_cambio()

    chips_copa = []
    for i, c in enumerate(copas):
        t = tema_copa(copas, c.id)
        activa = c.id == estado.get("copa_activa_id")
        con_datos = bool(TorneoRepository.obtener_por_copa(c.id))
        
        # Opción 1: Borde grueso del color de copa + fondo más claro
        if activa:
            # Fondo más claro del color de la copa para mejor contraste
            bg_color = TEXT
            border = ft.Border.all(3, t["bright"])
            text_color = "#0B1020"
            dot_color = t["bright"]
        else:
            bg_color = SURFACE_2
            border = None
            text_color = TEXT_2
            dot_color = t["bright"]
        
        chips_copa.append(ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE, size=18, color=t["bright"]) if activa
                else ft.Container(width=8, height=8, border_radius=4, bgcolor=dot_color),
                ft.Text(c.nombre, size=14 if activa else 13,
                        weight=ft.FontWeight.W_900 if activa else ft.FontWeight.W_700, color=text_color),
            ], spacing=8, tight=True),
            height=44, padding=ft.Padding.symmetric(horizontal=16), border_radius=RADIO_COPA,
            alignment=ft.Alignment.CENTER,
            bgcolor=bg_color,
            border=border,
            opacity=1 if activa else (0.5 if con_datos else 0.35),
            on_click=lambda e, cid=c.id: elegir_copa(cid), ink=True, tooltip=f"Copa {c.nombre}",
        ))

    # Torneo: oculto si hay uno solo; con varios, botón Filtros
    torneos = TorneoRepository.obtener_por_copa(estado["copa_activa_id"]) if estado.get("copa_activa_id") else []
    def elegir_torneo(tid):
        estado["torneo_activo_id"] = tid
        estado["jornada_activa_id"] = None
        estado["categoria_activa_id"] = None
        estado["torneo_abierta"] = False
        js = TorneoService.obtener_jornadas_por_torneo(tid)
        if js:
            estado["jornada_activa_id"] = js[0].id
            cs = TorneoService.obtener_categorias_por_jornada(js[0].id)
            if cs:
                estado["categoria_activa_id"] = cs[0].id
        on_cambio()

    chips_torneo = []
    for t in torneos:
        activo_t = t.id == estado.get("torneo_activo_id")
        chips_torneo.append(ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE, size=18, color=bright) if activo_t
                else ft.Container(width=8, height=8, border_radius=4, bgcolor=bright),
                ft.Text(t.nombre, size=14 if activo_t else 13,
                        weight=ft.FontWeight.W_900 if activo_t else ft.FontWeight.W_700,
                        color="#0B1020" if activo_t else TEXT_2),
            ], spacing=8, tight=True),
            height=44, padding=ft.Padding.symmetric(horizontal=16), border_radius=RADIO_COPA,
            alignment=ft.Alignment.CENTER,
            bgcolor=TEXT if activo_t else SURFACE_2,
            border=ft.Border.all(3, bright) if activo_t else None,
            opacity=1 if activo_t else 0.5,
            on_click=lambda e, tid=t.id: elegir_torneo(tid), ink=True, tooltip=f"Torneo {t.nombre}",
        ))

    # Responsivo: los chips pasan a la siguiente línea según el ancho disponible

    # Categorías
    def elegir_cat(cid):
        estado["categoria_activa_id"] = cid
        estado["grupo_filtro"] = "Todos"
        estado["cat_abierta"] = False
        on_cambio()

    chips_cat = [ft.Container(
        content=ft.Text(c.nombre, size=13, weight=ft.FontWeight.W_700,
                        color=BG if c.id == estado.get("categoria_activa_id") else TEXT_2),
        height=40, padding=ft.Padding.symmetric(horizontal=14), border_radius=RADIO_CATEGORIA,
        alignment=ft.Alignment.CENTER,
        bgcolor=TEXT if c.id == estado.get("categoria_activa_id") else SURFACE_2,
        border=ft.Border.all(1, BORDER_2), on_click=lambda e, cid=c.id: elegir_cat(cid), ink=True,
        tooltip=f"Categoría {c.nombre}",
    ) for c in categorias]

    # Jornada ‹ ›
    ids = [j.id for j in jornadas]
    pos = ids.index(estado["jornada_activa_id"]) if estado.get("jornada_activa_id") in ids else -1
    jornada_act = jornadas[pos] if pos >= 0 else None

    def mover(delta):
        nuevo = pos + delta
        if not (0 <= nuevo < len(jornadas)):
            return
        nombre_cat = next((c.nombre for c in categorias if c.id == estado.get("categoria_activa_id")), None)
        estado["jornada_activa_id"] = jornadas[nuevo].id
        cs = TorneoService.obtener_categorias_por_jornada(jornadas[nuevo].id)
        estado["categoria_activa_id"] = next((c.id for c in cs if c.nombre == nombre_cat), cs[0].id if cs else None)
        on_cambio()

    mas_jornada = boton_mas("jornada", ["Jornada"])
    nav_jornada = ft.Row([
        ft.IconButton(ft.Icons.CHEVRON_LEFT, icon_color=TEXT, width=44, height=44, tooltip="Jornada anterior",
                      opacity=0.3 if pos <= 0 else 1, disabled=pos <= 0, on_click=lambda e: mover(-1)),
        ft.Column([
            _etiqueta("JORNADA"),
            ft.Text((f"{jornada_act.nombre} · {fecha_sin_hora(jornada_act.fecha)}"
                     + (" ★ pública" if jornada_act.id == TorneoService.obtener_jornada_publica() else ""))
                    if jornada_act else "Sin jornadas",
                    size=14, weight=ft.FontWeight.W_700, color=TEXT),
        ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ft.IconButton(ft.Icons.CHEVRON_RIGHT, icon_color=TEXT, width=44, height=44, tooltip="Jornada siguiente",
                      opacity=0.3 if pos < 0 or pos >= len(jornadas) - 1 else 1,
                      disabled=pos < 0 or pos >= len(jornadas) - 1, on_click=lambda e: mover(1)),
        *([mas_jornada] if mas_jornada else []),
    ], alignment=ft.MainAxisAlignment.CENTER)

    def seccion(titulo, valor, abierta, clave, contenido, extra=None):
        def alternar(e):
            estado[clave] = not estado.get(clave, False)
            on_cambio()
        cab = ft.Container(
            content=ft.Row([
                _etiqueta(titulo),
                ft.Text(valor, size=14, weight=ft.FontWeight.W_700, color=TEXT, expand=True,
                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Icon(ft.Icons.KEYBOARD_ARROW_UP if abierta else ft.Icons.KEYBOARD_ARROW_DOWN,
                        color=bright, size=22),
            ], spacing=10),
            height=44, padding=ft.Padding.symmetric(horizontal=14), border_radius=RADIO_COPA,
            bgcolor=SURFACE_2, border=ft.Border.all(1, BORDER_2), on_click=alternar, ink=True,
            tooltip=("Ocultar " if abierta else "Cambiar ") + titulo.lower(),
        )
        extras = [x for x in (extra if isinstance(extra, list) else [extra]) if x is not None]
        fila_cab = ft.Row([ft.Container(cab, expand=True), *extras], spacing=4) if extras else cab
        return ft.Column([fila_cab, contenido] if abierta else [fila_cab], spacing=8)

    copa_nombre = next((c.nombre for c in copas if c.id == estado.get("copa_activa_id")), "Seleccionar")
    cat_nombre = next((c.nombre for c in categorias if c.id == estado.get("categoria_activa_id")), "Seleccionar")
    copa_abierta = estado.get("copa_abierta", False)
    cat_abierta = estado.get("cat_abierta", False)
    fila_chips_copa = ft.Row(chips_copa, wrap=True, spacing=8, run_spacing=8)

    controles = [seccion("COPA", copa_nombre, copa_abierta, "copa_abierta", fila_chips_copa,
                         boton_mas("copa", ["Campeonato", "Copa"]))]
    if torneos:
        torneo_nombre = next((t.nombre for t in torneos if t.id == estado.get("torneo_activo_id")), "Seleccionar")
        controles.append(seccion("TORNEO", torneo_nombre, estado.get("torneo_abierta", False), "torneo_abierta",
                                 ft.Row(chips_torneo, wrap=True, spacing=8, run_spacing=8),
                                 boton_mas("torneo", ["Torneo"])))
    mas_cat = boton_mas("categoría", ["Categoría", "Grupo"])
    if chips_cat or mas_cat:
        controles.append(seccion("CATEGORÍA", cat_nombre, cat_abierta, "cat_abierta",
                                 ft.Row(chips_cat, wrap=True, spacing=8, run_spacing=8), mas_cat))
    controles.append(nav_jornada)

    # Grupo: oculto si solo existe "Todos"
    if len(grupos_nombres) > 1:
        def elegir_grupo(n):
            estado["grupo_filtro"] = n
            on_cambio()
        opciones = ["Todos", *[n.replace("Grupo ", "") if n.startswith("Grupo ") else n for n in grupos_nombres]]
        reales = ["Todos", *grupos_nombres]
        actual = estado.get("grupo_filtro", "Todos")
        controles.append(ft.Container(
            content=ft.Row([ft.Container(
                content=ft.Text(op, size=12, weight=ft.FontWeight.W_700, color=TEXT if real == actual else MUTED),
                expand=True, height=36, alignment=ft.Alignment.CENTER, border_radius=RADIO_SEGMENTO,
                bgcolor="#2C3860" if real == actual else None,
                on_click=lambda e, r=real: elegir_grupo(r), ink=True, tooltip=f"Grupo {op}",
            ) for op, real in zip(opciones, reales)], spacing=4),
            bgcolor=SURFACE_2, border_radius=RADIO_CATEGORIA, padding=4,
        ))
    return ft.Column(controles, spacing=8)


def crear_estado_vacio(titulo: str, detalle: str, icono, texto_boton: Optional[str] = None,
                       on_click: Optional[Callable] = None) -> ft.Container:
    ctrls = [ft.Icon(icono, size=44, color=MUTED_2),
             ft.Text(titulo, size=16, weight=ft.FontWeight.W_700, color=TEXT, text_align=ft.TextAlign.CENTER),
             ft.Text(detalle, size=13, color=MUTED, text_align=ft.TextAlign.CENTER)]
    if texto_boton and on_click:
        ctrls.append(ft.OutlinedButton(texto_boton, on_click=lambda e: on_click()))
    return ft.Container(
        content=ft.Column(ctrls, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
        padding=32, bgcolor=SURFACE, border_radius=RADIO_TARJETA, border=ft.Border.all(1, BORDER),
    )


def crear_skeleton(n: int = 3) -> list:
    return [ft.Container(height=96, bgcolor=SURFACE, border_radius=RADIO_TARJETA,
                         border=ft.Border.all(1, BORDER), opacity=0.6) for _ in range(n)]


def crear_navegacion(tab: str, bright: str, on_tab: Callable) -> ft.NavigationBar:
    return ft.NavigationBar(
        destinations=[ft.NavigationBarDestination(icon=_ICONOS_TAB[t][0], selected_icon=_ICONOS_TAB[t][1],
                                                  label=t, tooltip=t) for t in TABS],
        selected_index=TABS.index(tab) if tab in TABS else 0,
        bgcolor=NAV_BG, indicator_color=bright + "33" if len(bright) == 7 else None,
        on_change=lambda e: on_tab(TABS[e.control.selected_index]),
        height=64,
    )


def crear_resumen_estado(partidos: list, copa: str, categoria: str, jornada: str, bright: str) -> ft.Control:
    """Estado: 3 cifras (Finalizados, En vivo, Por jugar) y tarjeta 'Mostrando'."""
    fin = sum(1 for p in partidos if p.jugado and not p.en_vivo)
    en_vivo = sum(1 for p in partidos if p.en_vivo)
    por_jugar = len(partidos) - fin - en_vivo

    def cifra(valor, etiqueta, color):
        return ft.Container(
            content=ft.Column([ft.Text(str(valor), size=28, weight=ft.FontWeight.W_800, color=color),
                               ft.Text(etiqueta, size=11, color=MUTED)],
                              spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True, padding=12, bgcolor=SURFACE, border_radius=RADIO_TARJETA,
            border=ft.Border.all(1, BORDER),
        )

    def fila(k, v):
        return ft.Row([ft.Text(k, size=12, color=MUTED, width=90),
                       ft.Text(v, size=13, weight=ft.FontWeight.W_700, color=TEXT, expand=True)])

    return ft.Column([
        ft.Row([cifra(fin, "Finalizados", TEXT), cifra(en_vivo, "En vivo", LIVE), cifra(por_jugar, "Por jugar", bright)],
               spacing=8),
        ft.Container(
            content=ft.Row([PuntoPulsante(OK),
                            ft.Text("Marcadores en vivo conectados. Se actualizan solos, no necesitas refrescar.",
                                    size=12, color=TEXT_2, expand=True)], spacing=10),
            padding=12, bgcolor=SURFACE, border_radius=RADIO_TARJETA, border=ft.Border.all(1, BORDER)),
        ft.Container(
            content=ft.Column([_etiqueta("MOSTRANDO"), fila("Copa", copa), fila("Categoría", categoria),
                               fila("Jornada", jornada)], spacing=6),
            padding=12, bgcolor=SURFACE, border_radius=RADIO_TARJETA, border=ft.Border.all(1, BORDER)),
    ], spacing=8)


class PuntoPulsante(ft.Container):
    """Punto de 8 px que parpadea suavemente (VIVO / conexión en vivo)."""

    def __init__(self, color: str):
        super().__init__(width=8, height=8, border_radius=4, bgcolor=color,
                         animate_opacity=ft.Animation(700, ft.AnimationCurve.EASE_IN_OUT))
        self._activo = False

    def did_mount(self):
        self._activo = True
        self.page.run_task(self._pulsar)

    def will_unmount(self):
        self._activo = False

    async def _pulsar(self):
        import asyncio
        while self._activo:
            try:
                self.opacity = 0.25 if self.opacity == 1 else 1
                self.update()
            except Exception:
                break
            await asyncio.sleep(0.8)
