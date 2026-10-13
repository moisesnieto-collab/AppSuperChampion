import flet as ft
from typing import List, Callable, Optional
from datetime import datetime
from config.constants import (
    COLOR_TARJETA, COLOR_BORDE, COLOR_CELESTE, COLOR_CELESTE_BOTON,
    COLOR_TEXTO, COLOR_SUBTEXTO, COLOR_VERDE, COLOR_AMBAR, COLOR_ROJO, COLOR_TARJETA_SEGUNDARIA, COLOR_FONDO,
    mezclar_color, oscurecer_color
)
from backend.models.categoria import Categoria
from backend.models.torneo import Torneo
from backend.models.jornada import Jornada
from backend.models.anio import Anio
from backend.models.campeonato import Campeonato
from backend.models.copa import Copa
from backend.services.torneo_service import TorneoService
from backend.services.anio_service import AnioService
from backend.services.campeonato_service import CampeonatoService
from backend.services.copa_service import CopaService
from backend.database.repositories import JornadaRepository, GrupoRepository
from config.preferencias import guardar_ultima_seleccion, borrar_ultima_seleccion

def crear_selector_categoria_y_dia(
    estado: dict,
    page: ft.Page,
    torneos: List[Torneo],
    categorias: List[Categoria],
    on_cambio_seleccion: Callable[[], None],
    on_crear_grupo: Callable = None,
    on_editar_grupo: Callable = None,
    on_eliminar_grupo: Callable = None,
    on_crear_jornada: Callable = None,
    on_eliminar_jornada: Callable = None,
    on_buscar_jornada: Callable = None,
    anios: List[Anio] = None,
    campeonatos: List[Campeonato] = None,
    copas: List[Copa] = None,
    vista: str = "campeonato"
) -> ft.Container:
    """
    Barra superior con botones	interactivos de Año, Campeonato, Copa, Torneo, Jornada, Categoría y Grupos.
    Nueva jerarquía: Año -> Campeonato -> Copa -> Torneo -> Jornada -> Categoría -> Grupo
    """
    if anios is None:
        anios = AnioService.obtener_anios()
    if campeonatos is None:
        campeonatos = CampeonatoService.obtener_campeonatos()
    if copas is None:
        copas = CopaService.obtener_copas()
    
    anio_activo_id = estado.get("anio_activo_id")
    campeonato_activo_id = estado.get("campeonato_activo_id")
    copa_activa_id = estado.get("copa_activa_id")
    torneo_activo_id = estado.get("torneo_activo_id")
    jornada_activa_id = estado.get("jornada_activa_id")
    cat_activa_id = estado.get("categoria_activa_id")
    grupo_filtro = estado.get("grupo_filtro", "Todos")
    # Las herramientas de edición solo aparecen con PIN y modo "Administrar" activo
    es_organizador = bool(estado.get("es_organizador", False) and estado.get("modo_admin", False))

    # Selector de Año
    def seleccionar_anio(anio_id: int):
        estado["anio_activo_id"] = anio_id
        estado["campeonato_activo_id"] = None
        estado["copa_activa_id"] = None
        estado["torneo_activo_id"] = None
        estado["jornada_activa_id"] = None
        estado["categoria_activa_id"] = None
        # Cargar campeonatos del año seleccionado
        campeonatos_nuevos = CampeonatoService.obtener_campeonatos_por_anio(anio_id)
        if campeonatos_nuevos:
            estado["campeonato_activo_id"] = campeonatos_nuevos[0].id
            # Cargar copas del campeonato
            copas_nuevas = CopaService.obtener_copas_por_campeonato(campeonatos_nuevos[0].id)
            if copas_nuevas:
                estado["copa_activa_id"] = copas_nuevas[0].id
                # Cargar torneos de la copa
                from backend.database.repositories import TorneoRepository
                torneos_nuevos = TorneoRepository.obtener_por_copa(copas_nuevas[0].id)
                if torneos_nuevos:
                    estado["torneo_activo_id"] = torneos_nuevos[0].id
                    # Cargar primera jornada
                    jornadas = TorneoService.obtener_jornadas_por_torneo(torneos_nuevos[0].id)
                    if jornadas:
                        estado["jornada_activa_id"] = jornadas[0].id
                        categorias_jornada = TorneoService.obtener_categorias_por_jornada(jornadas[0].id)
                        if categorias_jornada:
                            estado["categoria_activa_id"] = categorias_jornada[0].id
        on_cambio_seleccion()

    # Selector de Campeonato
    def seleccionar_campeonato(campeonato_id: int):
        estado["campeonato_activo_id"] = campeonato_id
        estado["copa_activa_id"] = None
        estado["torneo_activo_id"] = None
        estado["jornada_activa_id"] = None
        estado["categoria_activa_id"] = None
        # Cargar copas del campeonato seleccionado
        copas_nuevas = CopaService.obtener_copas_por_campeonato(campeonato_id)
        if copas_nuevas:
            estado["copa_activa_id"] = copas_nuevas[0].id
            # Cargar torneos de la copa
            from backend.database.repositories import TorneoRepository
            torneos_nuevos = TorneoRepository.obtener_por_copa(copas_nuevas[0].id)
            if torneos_nuevos:
                estado["torneo_activo_id"] = torneos_nuevos[0].id
                # Cargar primera jornada
                jornadas = TorneoService.obtener_jornadas_por_torneo(torneos_nuevos[0].id)
                if jornadas:
                    estado["jornada_activa_id"] = jornadas[0].id
                    categorias_jornada = TorneoService.obtener_categorias_por_jornada(jornadas[0].id)
                    if categorias_jornada:
                        estado["categoria_activa_id"] = categorias_jornada[0].id
        on_cambio_seleccion()

    # Selector de Copa
    def seleccionar_copa(copa_id: int):
        estado["copa_activa_id"] = copa_id
        estado["torneo_activo_id"] = None
        estado["jornada_activa_id"] = None
        estado["categoria_activa_id"] = None
        # Cargar torneos de la copa seleccionada
        from backend.database.repositories import TorneoRepository
        torneos_nuevos = TorneoRepository.obtener_por_copa(copa_id)
        if torneos_nuevos:
            estado["torneo_activo_id"] = torneos_nuevos[0].id
            # Cargar primera jornada
            jornadas = TorneoService.obtener_jornadas_por_torneo(torneos_nuevos[0].id)
            if jornadas:
                estado["jornada_activa_id"] = jornadas[0].id
                categorias_jornada = TorneoService.obtener_categorias_por_jornada(jornadas[0].id)
                if categorias_jornada:
                    estado["categoria_activa_id"] = categorias_jornada[0].id
        on_cambio_seleccion()

    # Botones de Torneos
    def seleccionar_torneo(torneo_id: int):
        estado["torneo_activo_id"] = torneo_id
        # Cargar la primera jornada del torneo seleccionado
        jornadas = TorneoService.obtener_jornadas_por_torneo(torneo_id)
        if jornadas:
            estado["jornada_activa_id"] = jornadas[0].id
            # Cargar la primera categoría de la jornada
            categorias_jornada = TorneoService.obtener_categorias_por_jornada(jornadas[0].id)
            if categorias_jornada:
                estado["categoria_activa_id"] = categorias_jornada[0].id
            else:
                estado["categoria_activa_id"] = None
        else:
            estado["jornada_activa_id"] = None
            estado["categoria_activa_id"] = None
        on_cambio_seleccion()

    def abrir_modal_nuevo_torneo(e):
        if not copa_activa_id:
            _snack("❌ Debe seleccionar una copa primero", COLOR_ROJO)
            return
        tf_nombre = ft.TextField(
            label="Nombre del Torneo (ej: Copa Colegio 2024)",
            autofocus=True,
        )
        tf_tipo = ft.TextField(
            label="Tipo (ej: Copa, Liga)",
            value="Copa",
        )
        tf_orden = ft.TextField(
            label="Orden de presentación (0 para el último)",
            value="0",
            input_filter=ft.NumbersOnlyInputFilter(),
        )
        texto_error = ft.Text("", color=COLOR_ROJO, size=12)

        def guardar_torneo(ev):
            nom = tf_nombre.value.strip()
            tipo = tf_tipo.value.strip()
            orden_str = tf_orden.value.strip()
            
            if not nom or not tipo:
                texto_error.value = "❌ Todos los campos son obligatorios"
                page.update()
                return
            
            try:
                orden = int(orden_str) if orden_str else 0
                nuevo_id = TorneoService.crear_torneo(nom, tipo, copa_activa_id, orden, es_organizador=True)
                estado["torneo_activo_id"] = nuevo_id
                estado["jornada_activa_id"] = None
                estado["categoria_activa_id"] = None
                dlg_nuevo_torneo.open = False
                on_cambio_seleccion()
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"✅ Torneo '{nom}' creado exitosamente."),
                    bgcolor=COLOR_VERDE
                )
                page.snack_bar.open = True
                page.update()
            except Exception as err:
                texto_error.value = f"❌ {str(err)}"
                page.update()

        dlg_nuevo_torneo = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.ADD_CIRCLE, color=COLOR_VERDE, size=22),
                ft.Text("Nuevo Torneo", weight=ft.FontWeight.BOLD, size=16),
            ]),
            content=ft.Column([
                ft.Text("Crea un nuevo torneo."),
                tf_nombre,
                tf_tipo,
                tf_orden,
                texto_error,
            ], spacing=10, tight=True, width=340),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: setattr(dlg_nuevo_torneo, 'open', False)),
                ft.FilledButton("Crear Torneo", bgcolor=COLOR_VERDE, color=COLOR_TEXTO, on_click=guardar_torneo),
            ],
            bgcolor=COLOR_TARJETA,
        )
        if dlg_nuevo_torneo not in page.overlay:
            page.overlay.append(dlg_nuevo_torneo)
        dlg_nuevo_torneo.open = True
        page.update()

    def abrir_dialogo_eliminar_torneo(e):
        torneo = TorneoService.obtener_torneo_activo()
        if not torneo:
            return
        
        def confirmar_eliminar(ev):
            try:
                TorneoService.eliminar_torneo(torneo_activo_id, es_organizador=True)
                estado["torneo_activo_id"] = None
                estado["jornada_activa_id"] = None
                estado["categoria_activa_id"] = None
                dlg_eliminar_torneo.open = False
                on_cambio_seleccion()
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"✅ Torneo eliminado exitosamente."),
                    bgcolor=COLOR_VERDE
                )
                page.snack_bar.open = True
                page.update()
            except Exception as err:
                dlg_eliminar_torneo.open = False
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"❌ {str(err)}"),
                    bgcolor=COLOR_ROJO
                )
                page.snack_bar.open = True
                page.update()

        dlg_eliminar_torneo = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.WARNING, color=COLOR_AMBAR, size=22),
                ft.Text("Eliminar Torneo", weight=ft.FontWeight.BOLD, size=16),
            ]),
            content=ft.Column([
                ft.Text(f"¿Estás seguro de eliminar el torneo '{torneo.nombre}'?"),
                ft.Text("Esta acción eliminará todas las jornadas, categorías, grupos y partidos asociados.", color=COLOR_ROJO, size=12),
            ], spacing=10, tight=True, width=340),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: setattr(dlg_eliminar_torneo, 'open', False)),
                ft.FilledButton("Eliminar", bgcolor=COLOR_ROJO, color=COLOR_TEXTO, on_click=confirmar_eliminar),
            ],
            bgcolor=COLOR_TARJETA,
        )
        if dlg_eliminar_torneo not in page.overlay:
            page.overlay.append(dlg_eliminar_torneo)
        dlg_eliminar_torneo.open = True
        page.update()

    def abrir_dialogo_editar_orden_torneo(torneo_id: int, nombre_actual: str, orden_actual: int):
        tf_orden = ft.TextField(
            label="Orden de presentación (menor número aparece primero)",
            value=str(orden_actual),
            input_filter=ft.NumbersOnlyInputFilter(),
        )
        texto_error = ft.Text("", color=COLOR_ROJO, size=12)

        def guardar_orden(ev):
            orden_str = tf_orden.value.strip()
            if not orden_str:
                texto_error.value = "❌ El orden es obligatorio"
                page.update()
                return
            
            try:
                orden = int(orden_str)
                TorneoService.actualizar_orden_torneo(torneo_id, orden, es_organizador=True)
                dlg_editar_orden.open = False
                on_cambio_seleccion()
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"✅ Orden del torneo '{nombre_actual}' actualizado."),
                    bgcolor=COLOR_VERDE
                )
                page.snack_bar.open = True
                page.update()
            except Exception as err:
                texto_error.value = f"❌ {str(err)}"
                page.update()

        dlg_editar_orden = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.EDIT, color=COLOR_CELESTE, size=22),
                ft.Text("Editar Orden del Torneo", weight=ft.FontWeight.BOLD, size=16),
            ]),
            content=ft.Column([
                ft.Text(f"Torneo: {nombre_actual}"),
                tf_orden,
                texto_error,
            ], spacing=10, tight=True, width=340),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: setattr(dlg_editar_orden, 'open', False)),
                ft.FilledButton("Guardar", bgcolor=COLOR_CELESTE, color=COLOR_TEXTO, on_click=guardar_orden),
            ],
            bgcolor=COLOR_TARJETA,
        )
        if dlg_editar_orden not in page.overlay:
            page.overlay.append(dlg_editar_orden)
        dlg_editar_orden.open = True
        page.update()

    # ---- CRUD genérico para Año / Campeonato / Copa ----
    def _snack(msg: str, color):
        page.snack_bar = ft.SnackBar(content=ft.Text(msg), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def _abrir_dialogo(dlg):
        if dlg not in page.overlay:
            page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def _modal_formulario(titulo, campos, on_guardar, texto_boton):
        texto_error = ft.Text("", color=COLOR_ROJO, size=12)

        def guardar(ev):
            try:
                on_guardar()
                dlg.open = False
                on_cambio_seleccion()
            except Exception as err:
                texto_error.value = f"❌ {str(err)}"
                page.update()

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.ADD_CIRCLE, color=COLOR_VERDE, size=22),
                ft.Text(titulo, weight=ft.FontWeight.BOLD, size=16),
            ]),
            content=ft.Column(campos + [texto_error], spacing=10, tight=True, width=340),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: (setattr(dlg, 'open', False), page.update())),
                ft.FilledButton(texto_boton, bgcolor=COLOR_VERDE, color=COLOR_TEXTO, on_click=guardar),
            ],
            bgcolor=COLOR_TARJETA,
        )
        _abrir_dialogo(dlg)

    def _modal_eliminar(titulo, mensaje, on_confirmar):
        def confirmar(ev):
            try:
                on_confirmar()
                dlg.open = False
                on_cambio_seleccion()
                _snack("✅ Eliminado exitosamente.", COLOR_VERDE)
            except Exception as err:
                dlg.open = False
                _snack(f"❌ {str(err)}", COLOR_ROJO)

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.WARNING, color=COLOR_AMBAR, size=22),
                ft.Text(titulo, weight=ft.FontWeight.BOLD, size=16),
            ]),
            content=ft.Text(mensaje),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: (setattr(dlg, 'open', False), page.update())),
                ft.FilledButton("Eliminar", bgcolor=COLOR_ROJO, color=COLOR_TEXTO, on_click=confirmar),
            ],
            bgcolor=COLOR_TARJETA,
        )
        _abrir_dialogo(dlg)

    # Año
    def modal_anio(anio=None):
        tf_valor = ft.TextField(
            label="Año", value=str(anio.valor if anio else datetime.now().year),
            input_filter=ft.NumbersOnlyInputFilter(), autofocus=True,
        )

        def guardar():
            valor = int(tf_valor.value.strip())
            if anio:
                from backend.database.repositories import AnioRepository
                AnioRepository.actualizar(anio.id, valor, anio.orden, anio.activo)
            else:
                nuevo_id = AnioService.crear_anio(valor)
                estado["anio_activo_id"] = nuevo_id
                estado["campeonato_activo_id"] = None
                estado["copa_activa_id"] = None
                estado["torneo_activo_id"] = None
                estado["jornada_activa_id"] = None
                estado["categoria_activa_id"] = None

        _modal_formulario("Editar Año" if anio else "Nuevo Año", [tf_valor], guardar, "Guardar" if anio else "Crear")

    def eliminar_anio(anio):
        def op():
            AnioService.eliminar_anio(anio.id)
            estado["pantalla"] = "inicio"
            borrar_ultima_seleccion()
            estado["anio_activo_id"] = None
            estado["campeonato_activo_id"] = None
            estado["copa_activa_id"] = None
            estado["torneo_activo_id"] = None
            estado["jornada_activa_id"] = None
            estado["categoria_activa_id"] = None
        _modal_eliminar("Eliminar Año", f"¿Eliminar el año {anio.valor}? Solo es posible si no tiene campeonatos asociados.", op)

    # Campeonato
    def modal_campeonato(camp=None):
        tf_nombre = ft.TextField(label="Nombre del Campeonato", value=camp.nombre if camp else "", autofocus=True)
        dd_anio = ft.Dropdown(
            label="Año",
            options=[ft.dropdown.Option(key=str(a.id), text=str(a.valor)) for a in anios],
            value=str(camp.anio_id if camp else anio_activo_id) if (camp or anio_activo_id) else None,
        )

        def guardar():
            nombre = tf_nombre.value.strip()
            if not nombre:
                raise ValueError("El nombre es obligatorio")
            if not dd_anio.value:
                raise ValueError("Debe seleccionar un año")
            if camp:
                from backend.database.repositories import CampeonatoRepository
                CampeonatoRepository.actualizar(camp.id, nombre, int(dd_anio.value), camp.orden, camp.activo)
            else:
                estado["anio_activo_id"] = int(dd_anio.value)
                nuevo_id = CampeonatoService.crear_campeonato(nombre, int(dd_anio.value))
                estado["campeonato_activo_id"] = nuevo_id
                estado["copa_activa_id"] = None
                estado["torneo_activo_id"] = None
                estado["jornada_activa_id"] = None
                estado["categoria_activa_id"] = None

        _modal_formulario("Editar Campeonato" if camp else "Nuevo Campeonato", [tf_nombre, dd_anio], guardar, "Guardar" if camp else "Crear")

    def eliminar_campeonato(camp):
        def op():
            CampeonatoService.eliminar_campeonato(camp.id)
            estado["pantalla"] = "inicio"
            borrar_ultima_seleccion()
            estado["campeonato_activo_id"] = None
            estado["copa_activa_id"] = None
            estado["torneo_activo_id"] = None
            estado["jornada_activa_id"] = None
            estado["categoria_activa_id"] = None
        _modal_eliminar("Eliminar Campeonato", f"¿Eliminar el campeonato '{camp.nombre}'? Solo es posible si no tiene copas asociadas.", op)

    # Copa
    PALETA_COPA = ["#0A0E17", "#1E3A8A", "#065F46", "#7F1D1D", "#581C87", "#92400E", "#134E4A", "#831843", "#3F3F46", "#9A3412",
                   "#1F4E9E", "#1D6B43", "#0066D6", "#3B4FB0", "#8C1A5C"]

    def modal_copa(copa=None):
        color_sel = {"v": (copa.color if copa and copa.color else PALETA_COPA[0])}
        fila_colores = ft.Row(wrap=True, spacing=6, run_spacing=6)

        def pintar_paleta():
            fila_colores.controls = [
                ft.Container(
                    width=32, height=32, border_radius=16, bgcolor=col,
                    border=ft.Border.all(3 if col == color_sel["v"] else 1, COLOR_TEXTO if col == color_sel["v"] else COLOR_BORDE),
                    on_click=lambda ev, col=col: elegir_color(col), ink=True,
                ) for col in PALETA_COPA
            ]

        def elegir_color(col):
            color_sel["v"] = col
            pintar_paleta()
            page.update()

        pintar_paleta()
        tf_nombre = ft.TextField(label="Nombre de la Copa", value=copa.nombre if copa else "", autofocus=True)
        dd_camp = ft.Dropdown(
            label="Campeonato",
            options=[ft.dropdown.Option(key=str(c.id), text=c.nombre) for c in campeonatos],
            value=str(copa.campeonato_id if copa else campeonato_activo_id) if (copa or campeonato_activo_id) else None,
        )

        def guardar():
            nombre = tf_nombre.value.strip()
            if not nombre:
                raise ValueError("El nombre es obligatorio")
            if not dd_camp.value:
                raise ValueError("Debe seleccionar un campeonato")
            if copa:
                from backend.database.repositories import CopaRepository
                CopaRepository.actualizar(copa.id, nombre, int(dd_camp.value), copa.orden, copa.activo, color_sel["v"])
            else:
                estado["campeonato_activo_id"] = int(dd_camp.value)
                nuevo_id = CopaService.crear_copa(nombre, int(dd_camp.value), color=color_sel["v"])
                estado["copa_activa_id"] = nuevo_id
                estado["torneo_activo_id"] = None
                estado["jornada_activa_id"] = None
                estado["categoria_activa_id"] = None

        _modal_formulario("Editar Copa" if copa else "Nueva Copa", [tf_nombre, dd_camp, ft.Text("Color de la copa", size=12, color=COLOR_SUBTEXTO), fila_colores], guardar, "Guardar" if copa else "Crear")

    def eliminar_copa(copa):
        def op():
            CopaService.eliminar_copa(copa.id)
            estado["copa_activa_id"] = None
            estado["torneo_activo_id"] = None
            estado["jornada_activa_id"] = None
            estado["categoria_activa_id"] = None
        _modal_eliminar("Eliminar Copa", f"¿Eliminar la copa '{copa.nombre}'? Solo es posible si no tiene torneos asociados.", op)

    def _chip_jerarquia(texto, es_activo_, on_select, on_edit=None, on_delete=None):
        color_txt = COLOR_TEXTO if es_activo_ else COLOR_SUBTEXTO
        fila = [ft.Text(texto, size=12, color=color_txt,
                        weight=ft.FontWeight.BOLD if es_activo_ else ft.FontWeight.NORMAL)]
        if es_organizador and on_edit:
            fila.append(ft.IconButton(icon=ft.Icons.EDIT, icon_color=COLOR_CELESTE, icon_size=14,
                                      tooltip="Editar", on_click=lambda ev: on_edit()))
        if es_organizador and on_delete:
            fila.append(ft.IconButton(icon=ft.Icons.DELETE, icon_color=COLOR_ROJO, icon_size=14,
                                      tooltip="Eliminar", on_click=lambda ev: on_delete()))
        return ft.Container(
            content=ft.Row(fila, spacing=4, tight=True),
            bgcolor=COLOR_CELESTE_BOTON if es_activo_ else COLOR_TARJETA_SEGUNDARIA,
            border=ft.Border.all(1, COLOR_CELESTE if es_activo_ else COLOR_BORDE),
            border_radius=8,
            padding=8,
            on_click=lambda ev: on_select(),
            ink=True,
        )

    def _chip_nuevo(texto, on_click):
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ADD, size=14, color=COLOR_VERDE),
                ft.Text(texto, size=12, color=COLOR_VERDE, weight=ft.FontWeight.BOLD),
            ], spacing=4),
            bgcolor=COLOR_TARJETA_SEGUNDARIA,
            border=ft.Border.all(1, COLOR_VERDE),
            border_radius=8,
            padding=10,
            on_click=lambda ev: on_click(),
            ink=True,
        )

    def _chip_eliminar(texto, on_click):
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.DELETE, size=14, color=COLOR_ROJO),
                ft.Text(texto, size=12, color=COLOR_ROJO, weight=ft.FontWeight.BOLD),
            ], spacing=4),
            bgcolor=COLOR_TARJETA_SEGUNDARIA,
            border=ft.Border.all(1, COLOR_ROJO),
            border_radius=8,
            padding=10,
            on_click=lambda ev: on_click(),
            ink=True,
        )

    # ---- Permisos por campeonato ----
    def modal_permisos():
        if not campeonato_activo_id:
            _snack("❌ Debe seleccionar un campeonato primero", COLOR_ROJO)
            return
        col_lista = ft.Column(spacing=4, tight=True)
        tf_usuario = ft.TextField(label="ID de usuario", input_filter=ft.NumbersOnlyInputFilter())
        dd_rol = ft.Dropdown(
            label="Rol",
            options=[ft.dropdown.Option(key="organizador", text="Organizador"),
                     ft.dropdown.Option(key="master", text="Master")],
            value="organizador",
        )
        texto_error = ft.Text("", color=COLOR_ROJO, size=12)

        def refrescar():
            col_lista.controls.clear()
            permisos = CampeonatoService.obtener_permisos_campeonato(campeonato_activo_id)
            if not permisos:
                col_lista.controls.append(ft.Text("Sin usuarios asignados", size=12, color=COLOR_SUBTEXTO))
            for p in permisos:
                col_lista.controls.append(ft.Row([
                    ft.Text(f"Usuario {p.usuario_id} — {p.rol}", size=12, color=COLOR_TEXTO, expand=True),
                    ft.IconButton(icon=ft.Icons.DELETE, icon_color=COLOR_ROJO, icon_size=16, tooltip="Revocar",
                                  on_click=lambda ev, uid=p.usuario_id: revocar(uid)),
                ]))

        def revocar(uid):
            try:
                CampeonatoService.revocar_permiso(campeonato_activo_id, uid)
                refrescar()
            except Exception as err:
                texto_error.value = f"❌ {str(err)}"
            page.update()

        def agregar(ev):
            try:
                if not tf_usuario.value.strip():
                    raise ValueError("El ID de usuario es obligatorio")
                CampeonatoService.asignar_permiso(campeonato_activo_id, int(tf_usuario.value.strip()), dd_rol.value)
                tf_usuario.value = ""
                texto_error.value = ""
                refrescar()
            except Exception as err:
                texto_error.value = f"❌ {str(err)}"
            page.update()

        refrescar()
        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, color=COLOR_CELESTE, size=22),
                ft.Text("Permisos del Campeonato", weight=ft.FontWeight.BOLD, size=16),
            ]),
            content=ft.Column([col_lista, ft.Divider(height=1), tf_usuario, dd_rol, texto_error],
                              spacing=10, tight=True, width=340),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda ev: (setattr(dlg, 'open', False), page.update())),
                ft.FilledButton("Agregar", bgcolor=COLOR_VERDE, color=COLOR_TEXTO, on_click=agregar),
            ],
            bgcolor=COLOR_TARJETA,
        )
        _abrir_dialogo(dlg)

    chips_anios = [
        _chip_jerarquia(str(a.valor), a.id == anio_activo_id, lambda aid=a.id: seleccionar_anio(aid),
                        lambda a=a: modal_anio(a), lambda a=a: eliminar_anio(a))
        for a in anios
    ]
    campeonatos_visibles = [c for c in campeonatos if anio_activo_id is None or c.anio_id == anio_activo_id]
    chips_campeonatos = [
        _chip_jerarquia(c.nombre, c.id == campeonato_activo_id, lambda cid=c.id: seleccionar_campeonato(cid),
                        lambda c=c: modal_campeonato(c), lambda c=c: eliminar_campeonato(c))
        for c in campeonatos_visibles
    ]
    copas_visibles = [c for c in copas if campeonato_activo_id is None or c.campeonato_id == campeonato_activo_id]
    chips_copas = [
        _chip_jerarquia(c.nombre, c.id == copa_activa_id, lambda cid=c.id: seleccionar_copa(cid),
                        lambda c=c: modal_copa(c), lambda c=c: eliminar_copa(c))
        for c in copas_visibles
    ]
    if es_organizador:
        chips_anios.append(_chip_nuevo("Nuevo Año", modal_anio))
        chips_campeonatos.append(_chip_nuevo("Nuevo Campeonato", modal_campeonato))
        chips_copas.append(_chip_nuevo("Nueva Copa", modal_copa))

    # ---- Pantalla de inicio: Año (lengüetas) + Campeonato (tarjetas) ----
    def entrar_campeonato(c):
        guardar_ultima_seleccion(c.anio_id, c.id)
        estado["anio_activo_id"] = c.anio_id
        estado["pantalla"] = "campeonato"
        seleccionar_campeonato(c.id)

    def volver_inicio(ev=None):
        estado["pantalla"] = "inicio"
        on_cambio_seleccion()

    if vista == "inicio":
        page.bgcolor = COLOR_FONDO
        tarjetas = []
        for c in campeonatos_visibles:
            es_ultimo = (c.id == campeonato_activo_id)
            fila_titulo = [
                ft.Icon(ft.Icons.MILITARY_TECH, color=COLOR_AMBAR if es_ultimo else COLOR_CELESTE, size=28),
                ft.Text(c.nombre, size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO, expand=True),
            ]
            contenido = [ft.Row(fila_titulo, spacing=8)]
            if es_organizador:
                contenido.append(ft.Row([
                    ft.IconButton(icon=ft.Icons.EDIT, icon_color=COLOR_CELESTE, icon_size=18, tooltip="Editar",
                                  on_click=lambda ev, c=c: modal_campeonato(c)),
                    ft.IconButton(icon=ft.Icons.DELETE, icon_color=COLOR_ROJO, icon_size=18, tooltip="Eliminar",
                                  on_click=lambda ev, c=c: eliminar_campeonato(c)),
                ], spacing=0))
            tarjetas.append(ft.Container(
                content=ft.Column(contenido, spacing=8),
                width=260, padding=16, border_radius=12,
                bgcolor=COLOR_CELESTE_BOTON if es_ultimo else COLOR_TARJETA_SEGUNDARIA,
                border=ft.Border.all(1, COLOR_CELESTE if es_ultimo else COLOR_BORDE),
                on_click=lambda ev, c=c: entrar_campeonato(c),
                ink=True,
            ))
        if es_organizador:
            tarjetas.append(ft.Container(
                content=ft.Row([ft.Icon(ft.Icons.ADD, color=COLOR_VERDE, size=22),
                                ft.Text("Nuevo Campeonato", color=COLOR_VERDE, weight=ft.FontWeight.BOLD)], spacing=8),
                width=260, padding=16, border_radius=12, bgcolor=COLOR_TARJETA_SEGUNDARIA,
                border=ft.Border.all(1, COLOR_VERDE), on_click=lambda ev: modal_campeonato(), ink=True,
            ))
        if not anios:
            vacio = ft.Text("No hay años creados. Activa el modo Administrar y crea el primero.", color=COLOR_SUBTEXTO)
        elif not campeonatos_visibles:
            vacio = ft.Text("No hay campeonatos en este año. Crea el primero desde el modo Administrar.", color=COLOR_SUBTEXTO)
        else:
            vacio = None
        return ft.Container(
            content=ft.Column([
                ft.Text("¿Qué campeonato quieres ver?", size=20, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO),
                ft.Text("1. Elige el año", size=13, color=COLOR_SUBTEXTO),
                ft.Row(chips_anios, wrap=True, spacing=8),
                ft.Divider(color=COLOR_BORDE, height=1),
                ft.Text("2. Toca un campeonato para entrar", size=13, color=COLOR_SUBTEXTO),
                vacio if vacio else ft.Container(height=0),
                ft.Row(tarjetas, wrap=True, spacing=12, run_spacing=12),
            ], spacing=12),
            padding=16, bgcolor=COLOR_TARJETA, border_radius=10, border=ft.Border.all(1, COLOR_BORDE),
        )

    # Torneos filtrados por la copa activa
    if copa_activa_id:
        from backend.database.repositories import TorneoRepository as _TorneoRepo
        torneos = _TorneoRepo.obtener_por_copa(copa_activa_id)

    chips_torneos = []
    for t in torneos:
        es_activo = (t.id == torneo_activo_id)
        chip_content = ft.Text(
            f"{t.nombre} ({t.tipo})",
            size=12,
            weight=ft.FontWeight.BOLD if es_activo else ft.FontWeight.NORMAL,
            color=COLOR_TEXTO if es_activo else COLOR_SUBTEXTO,
        )
        
        if es_organizador:
            chip_content = ft.Row([
                ft.Text(
                    f"{t.nombre} ({t.tipo})",
                    size=12,
                    weight=ft.FontWeight.BOLD if es_activo else ft.FontWeight.NORMAL,
                    color=COLOR_TEXTO if es_activo else COLOR_SUBTEXTO,
                    expand=True
                ),
                ft.IconButton(
                    icon=ft.Icons.EDIT,
                    icon_color=COLOR_CELESTE,
                    icon_size=14,
                    tooltip="Editar orden",
                    on_click=lambda ev, tid=t.id, nom=t.nombre, ord=t.orden: abrir_dialogo_editar_orden_torneo(tid, nom, ord)
                )
            ], spacing=4)
        
        chips_torneos.append(
            ft.Container(
                content=chip_content,
                bgcolor=COLOR_CELESTE_BOTON if es_activo else COLOR_TARJETA_SEGUNDARIA,
                border=ft.Border.all(1, COLOR_CELESTE if es_activo else COLOR_BORDE),
                border_radius=8,
                padding=12,
                on_click=lambda ev, tid=t.id: seleccionar_torneo(tid),
                ink=True,
            )
        )

    # Botón Nuevo Torneo (solo para organizadores)
    if es_organizador:
        chips_torneos.append(
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.ADD, size=14, color=COLOR_VERDE),
                    ft.Text("Nuevo Torneo", size=12, color=COLOR_VERDE, weight=ft.FontWeight.BOLD),
                ], spacing=4),
                bgcolor=COLOR_TARJETA_SEGUNDARIA,
                border=ft.Border.all(1, COLOR_VERDE),
                border_radius=8,
                padding=10,
                on_click=abrir_modal_nuevo_torneo,
                ink=True,
            )
        )

    # Botón Eliminar Torneo (solo para organizadores y si hay torneo seleccionado)
    if es_organizador and torneo_activo_id:
        chips_torneos.append(
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.DELETE, size=14, color=COLOR_ROJO),
                    ft.Text("Eliminar", size=12, color=COLOR_ROJO, weight=ft.FontWeight.BOLD),
                ], spacing=4),
                bgcolor=COLOR_TARJETA_SEGUNDARIA,
                border=ft.Border.all(1, COLOR_ROJO),
                border_radius=8,
                padding=10,
                on_click=abrir_dialogo_eliminar_torneo,
                ink=True,
            )
        )

    # Botones de Categorías (ahora filtradas por jornada)
    def seleccionar_cat(cat_id: int):
        estado["categoria_activa_id"] = cat_id
        on_cambio_seleccion()

    def abrir_modal_nueva_cat(e):
        if not jornada_activa_id:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("❌ Debe seleccionar una jornada primero"),
                bgcolor=COLOR_ROJO
            )
            page.snack_bar.open = True
            page.update()
            return

        tf_nombre = ft.TextField(
            label="Nombre de la Categoría (ej: 7° Básico, Pre-Kinder)",
            autofocus=True,
        )
        texto_error = ft.Text("", color=COLOR_ROJO, size=12)

        def guardar_cat(ev):
            nom = tf_nombre.value
            try:
                nuevo_id = TorneoService.crear_categoria(jornada_activa_id, nom, es_organizador=True)
                estado["categoria_activa_id"] = nuevo_id
                dlg_nueva_cat.open = False
                on_cambio_seleccion()
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"✅ Categoría '{nom}' creada exitosamente."),
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

    # Obtener categorías de la jornada activa
    categorias_filtradas = []
    if jornada_activa_id:
        categorias_filtradas = TorneoService.obtener_categorias_por_jornada(jornada_activa_id)

    chips_categorias = []
    for c in categorias_filtradas:
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

    if es_organizador and jornada_activa_id:
        chips_categorias.append(
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.ADD, size=14, color=COLOR_VERDE),
                    ft.Text("Nueva Cat", size=12, color=COLOR_VERDE, weight=ft.FontWeight.BOLD),
                ], spacing=4),
                bgcolor=COLOR_TARJETA_SEGUNDARIA,
                border=ft.Border.all(1, COLOR_VERDE),
                border_radius=8,
                padding=10,
                on_click=abrir_modal_nueva_cat,
                ink=True,
            )
        )

    if es_organizador and cat_activa_id:
        def eliminar_categoria_activa():
            def op():
                TorneoService.eliminar_categoria(cat_activa_id, es_organizador=True)
                estado["categoria_activa_id"] = None
            _modal_eliminar("Eliminar Categoría", "¿Eliminar la categoría activa? Se eliminarán sus grupos y partidos.", op)
        chips_categorias.append(_chip_eliminar("Eliminar Cat", eliminar_categoria_activa))

    # Selector de Jornada (ahora filtradas por torneo)
    def seleccionar_jornada(jornada_id: int):
        estado["jornada_activa_id"] = jornada_id
        # Cargar la primera categoría de la jornada seleccionada
        categorias_jornada = TorneoService.obtener_categorias_por_jornada(jornada_id)
        if categorias_jornada:
            estado["categoria_activa_id"] = categorias_jornada[0].id
        else:
            estado["categoria_activa_id"] = None
        on_cambio_seleccion()

    # Obtener jornadas del torneo activo
    jornadas = []
    if torneo_activo_id:
        jornadas = TorneoService.obtener_jornadas_por_torneo(torneo_activo_id)

    # Crear chips de jornadas - formato minimalista para móviles con scroll
    chips_jornadas = []
    for j in jornadas:
        es_jornada_activa = (j.id == jornada_activa_id)
        # Formatear fecha completa DD-MM-YYYY
        fecha_obj = datetime.fromisoformat(j.fecha)
        fecha_formateada = fecha_obj.strftime("%d-%m-%Y")
        
        # Mostrar nombre + fecha, o solo fecha si el nombre es muy largo
        if len(j.nombre) > 15:
            texto_chip = fecha_formateada
        else:
            texto_chip = f"{j.nombre} {fecha_formateada}"
        
        chips_jornadas.append(
            ft.Container(
                content=ft.Text(texto_chip, size=12, weight=ft.FontWeight.BOLD if es_jornada_activa else ft.FontWeight.NORMAL, color=COLOR_TEXTO if es_jornada_activa else COLOR_SUBTEXTO),
                bgcolor=COLOR_CELESTE_BOTON if es_jornada_activa else COLOR_TARJETA_SEGUNDARIA,
                border=ft.Border.all(1, COLOR_CELESTE if es_jornada_activa else COLOR_BORDE),
                border_radius=8,
                padding=12,
                on_click=lambda ev, jid=j.id: seleccionar_jornada(jid),
                ink=True,
            )
        )

    # Botones de gestión de jornadas (solo organizador) - más compactos
    btn_crear_jornada = None
    btn_eliminar_jornada = None
    btn_buscar_jornada = None

    if es_organizador:
        btn_crear_jornada = ft.Container(
            content=ft.Icon(ft.Icons.ADD, size=12, color=COLOR_VERDE),
            bgcolor=COLOR_TARJETA_SEGUNDARIA,
            border=ft.Border.all(1, COLOR_VERDE),
            border_radius=4,
            padding=4,
            on_click=lambda ev: on_crear_jornada(ev) if on_crear_jornada else None,
            ink=True,
        )

        btn_eliminar_jornada = ft.Container(
            content=ft.Icon(ft.Icons.DELETE, size=12, color=COLOR_ROJO),
            bgcolor=COLOR_TARJETA_SEGUNDARIA,
            border=ft.Border.all(1, COLOR_ROJO),
            border_radius=4,
            padding=4,
            on_click=lambda ev: on_eliminar_jornada(ev) if on_eliminar_jornada else None,
            ink=True,
        )

        btn_buscar_jornada = ft.Container(
            content=ft.Icon(ft.Icons.SEARCH, size=12, color=COLOR_CELESTE),
            bgcolor=COLOR_TARJETA_SEGUNDARIA,
            border=ft.Border.all(1, COLOR_CELESTE),
            border_radius=4,
            padding=4,
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
        grupos_reales = [{"grupo": g} for g in GrupoRepository.obtener_por_categoria_y_jornada(cat_activa_id, jornada_activa_id)]
        nombres_grupos = [g["grupo"].nombre for g in grupos_reales]
    else:
        nombres_grupos = ["Grupo A", "Grupo B"]

    # Agregar opción "Todos"
    chips_grupos.append(
        ft.Container(
            content=ft.Text(
                "Todos",
                size=12,
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
                ft.Text("Nuevo Grupo", size=12, color=COLOR_VERDE, weight=ft.FontWeight.BOLD),
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
                            size=12,
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
                        size=12,
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
                ft.Text("Nuevo Grupo", size=12, color=COLOR_VERDE, weight=ft.FontWeight.BOLD),
            ], spacing=4),
            bgcolor=COLOR_TARJETA_SEGUNDARIA,
            border=ft.Border.all(1, COLOR_VERDE),
            border_radius=6,
            padding=8,
            on_click=lambda ev: on_crear_grupo(ev),
            ink=True,
        )

    def _seccion(icono, titulo, chips, extras=None):
        """Título arriba a la izquierda y lengüetas debajo, adaptadas al ancho."""
        filas = [
            ft.Row([
                ft.Icon(icono, color=COLOR_CELESTE, size=18),
                ft.Text(titulo, size=13, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO),
            ], spacing=6, alignment=ft.MainAxisAlignment.START),
            ft.Row(chips, wrap=True, spacing=6, run_spacing=6, alignment=ft.MainAxisAlignment.START),
        ]
        extras = [x for x in (extras or []) if x is not None]
        if extras:
            filas.append(ft.Row(extras, wrap=True, spacing=6, run_spacing=6))
        return ft.Column(filas, spacing=6, horizontal_alignment=ft.CrossAxisAlignment.START)

    # Cabecera compacta del campeonato: ‹ 2026 · Supercampeones
    camp_obj = next((c for c in campeonatos if c.id == campeonato_activo_id), None)
    anio_obj = next((a for a in anios if camp_obj and a.id == camp_obj.anio_id), None)
    titulo_camp = f"{anio_obj.valor if anio_obj else ''} · {camp_obj.nombre if camp_obj else 'Sin campeonato'}"
    cabecera = ft.Row([
        ft.IconButton(icon=ft.Icons.ARROW_BACK_IOS_NEW, icon_color=COLOR_CELESTE, icon_size=18,
                      tooltip="Cambiar de campeonato", on_click=volver_inicio),
        ft.Text(titulo_camp, size=18, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO, expand=True),
    ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    controles_admin = []
    if es_organizador and camp_obj:
        controles_admin = [ft.Row([
            _chip_nuevo("Editar campeonato", lambda: modal_campeonato(camp_obj)),
            _chip_nuevo("Permisos", modal_permisos),
            _chip_eliminar("Eliminar campeonato", lambda: eliminar_campeonato(camp_obj)),
        ], wrap=True, spacing=6)]

    copa_obj = next((c for c in copas if c.id == copa_activa_id), None)
    color_copa = copa_obj.color if copa_obj and copa_obj.color else None
    page.bgcolor = color_copa or COLOR_FONDO

    if color_copa:
        def _texto_claro(ctrl):
            if isinstance(ctrl, ft.Text):
                if ctrl.color == COLOR_SUBTEXTO:
                    ctrl.color = COLOR_TEXTO
            elif isinstance(ctrl, ft.Row):
                for sub in ctrl.controls:
                    _texto_claro(sub)

        tono_activo = mezclar_color(color_copa, 0.22)
        tono_inactivo = oscurecer_color(color_copa, 0.30)
        for ch in (chips_copas + chips_torneos + chips_jornadas + chips_categorias + chips_grupos
                   + [btn_crear_jornada, btn_buscar_jornada, btn_eliminar_jornada, btn_crear_grupo]):
            if isinstance(ch, ft.Container):
                if ch.bgcolor == COLOR_CELESTE_BOTON:
                    ch.bgcolor = tono_activo
                    _texto_claro(ch.content)
                elif ch.bgcolor in (COLOR_TARJETA_SEGUNDARIA, COLOR_TARJETA):
                    ch.bgcolor = tono_inactivo
                    _texto_claro(ch.content)

    return ft.Container(
        content=ft.Column([
            cabecera,
            *controles_admin,
            ft.Divider(color=COLOR_BORDE, height=1),
            _seccion(ft.Icons.LOCAL_BAR, "Copa", chips_copas),
            ft.Divider(color=COLOR_BORDE, height=1),
            _seccion(ft.Icons.EMOJI_EVENTS, "Torneo", chips_torneos),
            ft.Divider(color=COLOR_BORDE, height=1),
            _seccion(ft.Icons.CALENDAR_TODAY, "Jornada", chips_jornadas, [
                btn_crear_jornada, btn_buscar_jornada, btn_eliminar_jornada]),
            ft.Divider(color=COLOR_BORDE, height=1),
            _seccion(ft.Icons.SCHOOL, "Categoría", chips_categorias),
            ft.Divider(color=COLOR_BORDE, height=1),
            _seccion(ft.Icons.GROUPS, "Grupo", chips_grupos, [btn_crear_grupo]),
        ], spacing=10),
        padding=12,
        bgcolor=color_copa or COLOR_TARJETA,
        border_radius=10,
        border=ft.Border.all(1, COLOR_BORDE),
    )
