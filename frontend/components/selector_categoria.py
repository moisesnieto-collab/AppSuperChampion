import flet as ft
from typing import List, Callable, Optional
from datetime import datetime
from config.constants import (
    COLOR_TARJETA, COLOR_BORDE, COLOR_CELESTE, COLOR_CELESTE_BOTON,
    COLOR_TEXTO, COLOR_SUBTEXTO, COLOR_VERDE, COLOR_AMBAR, COLOR_ROJO, COLOR_TARJETA_SEGUNDARIA
)
from backend.models.categoria import Categoria
from backend.services.torneo_service import TorneoService
from backend.database.repositories import JornadaRepository

def crear_selector_categoria_y_dia(
    estado: dict,
    page: ft.Page,
    categorias: List[Categoria],
    on_cambio_seleccion: Callable[[], None],
    on_crear_grupo: Callable = None,
    on_editar_grupo: Callable = None,
    on_eliminar_grupo: Callable = None,
    on_crear_jornada: Callable = None,
    on_eliminar_jornada: Callable = None,
    on_buscar_jornada: Callable = None
) -> ft.Container:
    """
    Barra superior con botones interactivos de Categoría, Jornada (fecha) y Grupos.
    """
    cat_activa_id = estado.get("categoria_activa_id")
    jornada_activa_id = estado.get("jornada_activa_id")
    grupo_filtro = estado.get("grupo_filtro", "Todos")
    es_organizador = estado.get("es_organizador", False)

    # Botones de Categorías
    def seleccionar_cat(cat_id: int):
        estado["categoria_activa_id"] = cat_id
        # Cargar la primera jornada de la categoría seleccionada
        jornadas = JornadaRepository.obtener_por_categoria(cat_id)
        if jornadas:
            estado["jornada_activa_id"] = jornadas[0]["id"]
        else:
            estado["jornada_activa_id"] = None
        on_cambio_seleccion()

    def abrir_modal_nueva_cat(e):
        tf_nombre = ft.TextField(
            label="Nombre de la Categoría (ej: 7° Básico, Pre-Kinder)",
            autofocus=True,
        )
        texto_error = ft.Text("", color=COLOR_ROJO, size=12)

        def guardar_cat(ev):
            nom = tf_nombre.value
            try:
                nuevo_id = TorneoService.crear_categoria(nom, es_organizador=True)
                estado["categoria_activa_id"] = nuevo_id
                dlg_nueva_cat.open = False
                on_cambio_seleccion()
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"✅ Categoría '{nom}' creada exitosamente con fixture Día 1 y 2."),
                    bgcolor=COLOR_VERDE
                )
                page.snack_bar.open = True
                page.update()
            except Exception as err:
                texto_error.value = f"❌ {str(err)}"
                page.update()

        dlg_nueva_cat = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.ADD_CIRCLE, color=COLOR_VERDE, size=22),
                ft.Text("Nueva Categoría", weight=ft.FontWeight.BOLD, size=16),
            ]),
            content=ft.Column([
                ft.Text("Crea una nueva categoría con cuadrangulares automáticos."),
                tf_nombre,
                texto_error,
            ], spacing=10, tight=True, width=340),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: setattr(dlg_nueva_cat, 'open', False)),
                ft.FilledButton("Crear Categoría", bgcolor=COLOR_VERDE, color=COLOR_TEXTO, on_click=guardar_cat),
            ],
            bgcolor=COLOR_TARJETA,
        )
        if dlg_nueva_cat not in page.overlay:
            page.overlay.append(dlg_nueva_cat)
        dlg_nueva_cat.open = True
        page.update()

    chips_categorias = []
    for c in categorias:
        es_activa = (c.id == cat_activa_id)
        chips_categorias.append(
            ft.Container(
                content=ft.Text(
                    c.nombre,
                    size=12,
                    weight=ft.FontWeight.BOLD if es_activa else ft.FontWeight.NORMAL,
                    color=COLOR_TEXTO if es_activa else COLOR_SUBTEXTO,
                ),
                bgcolor=COLOR_CELESTE_BOTON if es_activa else COLOR_TARJETA_SEGUNDARIA,
                border=ft.Border.all(1, COLOR_CELESTE if es_activa else COLOR_BORDE),
                border_radius=8,
                padding=12,
                on_click=lambda ev, cid=c.id: seleccionar_cat(cid),
                ink=True,
            )
        )

    if es_organizador:
        chips_categorias.append(
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.ADD, size=14, color=COLOR_VERDE),
                    ft.Text("Nueva Cat", size=11, color=COLOR_VERDE, weight=ft.FontWeight.BOLD),
                ], spacing=4),
                bgcolor=COLOR_TARJETA_SEGUNDARIA,
                border=ft.Border.all(1, COLOR_VERDE),
                border_radius=8,
                padding=10,
                on_click=abrir_modal_nueva_cat,
                ink=True,
            )
        )

    # Selector de Jornada (DatePicker)
    def seleccionar_jornada(jornada_id: int):
        estado["jornada_activa_id"] = jornada_id
        on_cambio_seleccion()

    # Obtener jornadas de la categoría activa
    jornadas = []
    if cat_activa_id:
        jornadas = JornadaRepository.obtener_por_categoria(cat_activa_id)

    # Crear chips de jornadas con fechas
    chips_jornadas = []
    for j in jornadas:
        es_jornada_activa = (j["id"] == jornada_activa_id)
        # Formatear fecha DD-MM-YYYY
        fecha_obj = datetime.fromisoformat(j["fecha"])
        fecha_formateada = fecha_obj.strftime("%d-%m-%Y")
        chips_jornadas.append(
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.CALENDAR_TODAY, size=14, color=COLOR_TEXTO if es_jornada_activa else COLOR_SUBTEXTO),
                    ft.Text(fecha_formateada, size=12, weight=ft.FontWeight.BOLD if es_jornada_activa else ft.FontWeight.NORMAL, color=COLOR_TEXTO if es_jornada_activa else COLOR_SUBTEXTO),
                ], spacing=6),
                bgcolor=COLOR_CELESTE_BOTON if es_jornada_activa else COLOR_TARJETA_SEGUNDARIA,
                border=ft.Border.all(1, COLOR_CELESTE if es_jornada_activa else COLOR_BORDE),
                border_radius=8,
                padding=14,
                on_click=lambda ev, jid=j["id"]: seleccionar_jornada(jid),
                ink=True,
            )
        )

    # Botones de gestión de jornadas (solo organizador)
    btn_crear_jornada = None
    btn_eliminar_jornada = None
    btn_buscar_jornada = None

    if es_organizador:
        btn_crear_jornada = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ADD, size=12, color=COLOR_VERDE),
                ft.Text("Nuevo Día", size=10, color=COLOR_VERDE, weight=ft.FontWeight.BOLD),
            ], spacing=4),
            bgcolor=COLOR_TARJETA_SEGUNDARIA,
            border=ft.Border.all(1, COLOR_VERDE),
            border_radius=6,
            padding=8,
            on_click=lambda ev: on_crear_jornada(ev) if on_crear_jornada else None,
            ink=True,
        )

        btn_eliminar_jornada = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.DELETE, size=12, color=COLOR_ROJO),
                ft.Text("Eliminar", size=10, color=COLOR_ROJO, weight=ft.FontWeight.BOLD),
            ], spacing=4),
            bgcolor=COLOR_TARJETA_SEGUNDARIA,
            border=ft.Border.all(1, COLOR_ROJO),
            border_radius=6,
            padding=8,
            on_click=lambda ev: on_eliminar_jornada(ev) if on_eliminar_jornada else None,
            ink=True,
        )

        btn_buscar_jornada = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.SEARCH, size=12, color=COLOR_CELESTE),
                ft.Text("Buscar", size=10, color=COLOR_CELESTE, weight=ft.FontWeight.BOLD),
            ], spacing=4),
            bgcolor=COLOR_TARJETA_SEGUNDARIA,
            border=ft.Border.all(1, COLOR_CELESTE),
            border_radius=6,
            padding=8,
            on_click=lambda ev: on_buscar_jornada(ev) if on_buscar_jornada else None,
            ink=True,
        )

    # Botones de Filtro de Grupo
    def seleccionar_grupo_filtro(filtro: str):
        estado["grupo_filtro"] = filtro
        on_cambio_seleccion()

    chips_grupos = []

    # Obtener grupos reales de la categoría y jornada seleccionados
    grupos_reales = []
    if cat_activa_id and jornada_activa_id:
        grupos_reales = TorneoService.obtener_datos_categoria_dia(cat_activa_id, jornada_activa_id)["grupos"]
        nombres_grupos = [g["grupo"].nombre for g in grupos_reales]
    else:
        nombres_grupos = ["Grupo A", "Grupo B"]

    # Agregar opción "Todos"
    chips_grupos.append(
        ft.Container(
            content=ft.Text(
                "Todos",
                size=11,
                weight=ft.FontWeight.BOLD if grupo_filtro == "Todos" else ft.FontWeight.NORMAL,
                color=COLOR_TEXTO if grupo_filtro == "Todos" else COLOR_SUBTEXTO
            ),
            bgcolor=COLOR_CELESTE_BOTON if grupo_filtro == "Todos" else COLOR_TARJETA,
            border=ft.Border.all(1, COLOR_CELESTE if grupo_filtro == "Todos" else COLOR_BORDE),
            border_radius=6,
            padding=10,
            on_click=lambda ev: seleccionar_grupo_filtro("Todos"),
            ink=True,
        )
    )

    # Botón Crear Grupo (solo organizador)
    btn_crear_grupo = None
    if es_organizador and cat_activa_id and jornada_activa_id:
        btn_crear_grupo = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ADD, size=12, color=COLOR_VERDE),
                ft.Text("Nuevo Grupo", size=10, color=COLOR_VERDE, weight=ft.FontWeight.BOLD),
            ], spacing=4),
            bgcolor=COLOR_TARJETA_SEGUNDARIA,
            border=ft.Border.all(1, COLOR_VERDE),
            border_radius=6,
            padding=8,
            on_click=lambda ev: on_crear_grupo(ev) if on_crear_grupo else None,
            ink=True,
        )

    # Agregar grupos reales
    for g_data in grupos_reales:
        nombre_grupo = g_data["grupo"].nombre
        grupo_id = g_data["grupo"].id
        es_g_activo = (nombre_grupo == grupo_filtro)

        if es_organizador:
            # Con botones de editar/eliminar
            chips_grupos.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(
                            nombre_grupo,
                            size=11,
                            weight=ft.FontWeight.BOLD if es_g_activo else ft.FontWeight.NORMAL,
                            color=COLOR_TEXTO if es_g_activo else COLOR_SUBTEXTO,
                            expand=True
                        ),
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            icon_color=COLOR_CELESTE,
                            icon_size=14,
                            tooltip="Editar Grupo",
                            on_click=lambda ev, gid=grupo_id: on_editar_grupo(gid) if on_editar_grupo else None
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color=COLOR_ROJO,
                            icon_size=14,
                            tooltip="Eliminar Grupo",
                            on_click=lambda ev, gid=grupo_id: on_eliminar_grupo(gid) if on_eliminar_grupo else None
                        )
                    ], spacing=4),
                    bgcolor=COLOR_CELESTE_BOTON if es_g_activo else COLOR_TARJETA,
                    border=ft.Border.all(1, COLOR_CELESTE if es_g_activo else COLOR_BORDE),
                    border_radius=6,
                    padding=8,
                    on_click=lambda ev, g_val=nombre_grupo: seleccionar_grupo_filtro(g_val),
                    ink=True,
                )
            )
        else:
            # Solo visual
            chips_grupos.append(
                ft.Container(
                    content=ft.Text(
                        nombre_grupo,
                        size=11,
                        weight=ft.FontWeight.BOLD if es_g_activo else ft.FontWeight.NORMAL,
                        color=COLOR_TEXTO if es_g_activo else COLOR_SUBTEXTO
                    ),
                    bgcolor=COLOR_CELESTE_BOTON if es_g_activo else COLOR_TARJETA,
                    border=ft.Border.all(1, COLOR_CELESTE if es_g_activo else COLOR_BORDE),
                    border_radius=6,
                    padding=10,
                    on_click=lambda ev, g_val=nombre_grupo: seleccionar_grupo_filtro(g_val),
                    ink=True,
                )
            )

    # Botón para crear nuevo grupo (solo organizador) - se agrega después, no en chips_grupos
    btn_crear_grupo = None
    if es_organizador and on_crear_grupo:
        btn_crear_grupo = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ADD, size=12, color=COLOR_VERDE),
                ft.Text("Nuevo Grupo", size=10, color=COLOR_VERDE, weight=ft.FontWeight.BOLD),
            ], spacing=4),
            bgcolor=COLOR_TARJETA_SEGUNDARIA,
            border=ft.Border.all(1, COLOR_VERDE),
            border_radius=6,
            padding=8,
            on_click=lambda ev: on_crear_grupo(ev),
            ink=True,
        )

    return ft.Container(
        content=ft.Column([
            # Fila 1: Selector de Categorías
            ft.Row([
                ft.Icon(ft.Icons.SCHOOL, color=COLOR_CELESTE, size=18),
                ft.Text("Categoría:", size=13, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO),
                ft.Row(chips_categorias, wrap=True, spacing=6),
            ], wrap=True, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),

            ft.Divider(color=COLOR_BORDE, height=1),

            # Fila 2: Selector de Jornada (Fecha)
            ft.Row([
                ft.Icon(ft.Icons.CALENDAR_TODAY, color=COLOR_CELESTE, size=18),
                ft.Text("Jornada:", size=13, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO),
                ft.Row(chips_jornadas, spacing=6),
                btn_crear_jornada if btn_crear_jornada else ft.Container(width=0, height=0),
                btn_buscar_jornada if btn_buscar_jornada else ft.Container(width=0, height=0),
                btn_eliminar_jornada if btn_eliminar_jornada else ft.Container(width=0, height=0),
            ], wrap=True, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),

            # Fila 3: Filtro de Grupo
            ft.Row([
                ft.Icon(ft.Icons.GROUPS, color=COLOR_CELESTE, size=18),
                ft.Text("Grupo:", size=13, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO),
                ft.Row(chips_grupos, wrap=True, spacing=6),
                btn_crear_grupo if btn_crear_grupo else ft.Container(width=0, height=0),
            ], wrap=True, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ], spacing=10),
        padding=12,
        bgcolor=COLOR_TARJETA,
        border_radius=10,
        border=ft.Border.all(1, COLOR_BORDE),
    )
