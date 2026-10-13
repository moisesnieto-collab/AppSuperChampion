import os
import flet as ft
from datetime import datetime, timedelta
from backend.database.schema import inicializar_db
from backend.database.repositories import JornadaRepository, CampeonatoRepository
from config.preferencias import cargar_ultima_seleccion
from backend.services.torneo_service import TorneoService
from backend.services.anio_service import AnioService
from backend.services.campeonato_service import CampeonatoService
from backend.services.copa_service import CopaService
from config.settings import APP_TITLE, APP_THEME_MODE, APP_BGCOLOR
from config.constants import (
    COLOR_FONDO, COLOR_AMBAR, COLOR_CELESTE, COLOR_CELESTE_BOTON,
    COLOR_VERDE, COLOR_ROJO, COLOR_SUBTEXTO, COLOR_TEXTO, COLOR_TARJETA
)
from frontend.components.header import crear_header
from frontend.components.selector_categoria import crear_selector_categoria_y_dia
from frontend.components.tabla_posiciones import crear_tabla_posiciones
from frontend.components.lista_partidos import crear_lista_partidos
from frontend.components.tarjeta_campeon import crear_tarjeta_campeon


def main(page: ft.Page):
    # Configuración de la página
    page.title = APP_TITLE
    page.theme_mode = APP_THEME_MODE
    page.fonts = {
        "Montserrat": "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf",
    }
    page.theme = ft.Theme(font_family="Montserrat")
    page.dark_theme = ft.Theme(font_family="Montserrat")
    page.bgcolor = COLOR_FONDO
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO
    page.window_min_width = 1000
    page.window_min_height = 700

    # Inicializar base de datos
    inicializar_db()

    # Estado global de la aplicación
    estado = {
        "es_organizador": False,
        "anio_activo_id": None,
        "campeonato_activo_id": None,
        "copa_activa_id": None,
        "torneo_activo_id": None,
        "jornada_activa_id": None,
        "categoria_activa_id": None,
        "grupo_filtro": "Todos",
        "modo_admin": False,
        "pantalla": "inicio",
    }

    # Cargar datos iniciales - jerarquía completa
    anios = AnioService.obtener_anios()
    if anios:
        # Seleccionar el año activo o el primero
        anio_activo = AnioService.obtener_anio_activo()
        if anio_activo:
            estado["anio_activo_id"] = anio_activo.id
        else:
            estado["anio_activo_id"] = anios[0].id

        # Recordar la última selección: si existe, se entra directo al campeonato
        _, camp_ultimo_id = cargar_ultima_seleccion()
        camp_ultimo = CampeonatoRepository.obtener_por_id(camp_ultimo_id) if camp_ultimo_id else None
        if camp_ultimo:
            estado["anio_activo_id"] = camp_ultimo.anio_id
            estado["pantalla"] = "campeonato"

        # Cargar campeonatos del año
        campeonatos = CampeonatoService.obtener_campeonatos_por_anio(estado["anio_activo_id"])
        if campeonatos:
            campeonato_activo = CampeonatoService.obtener_campeonato_activo()
            if camp_ultimo:
                estado["campeonato_activo_id"] = camp_ultimo.id
            elif campeonato_activo and campeonato_activo.anio_id == estado["anio_activo_id"]:
                estado["campeonato_activo_id"] = campeonato_activo.id
            else:
                estado["campeonato_activo_id"] = campeonatos[0].id
            
            # Cargar copas del campeonato
            copas = CopaService.obtener_copas_por_campeonato(estado["campeonato_activo_id"])
            if copas:
                copa_activa = CopaService.obtener_copa_activo()
                if copa_activa and copa_activa.campeonato_id == estado["campeonato_activo_id"]:
                    estado["copa_activa_id"] = copa_activa.id
                else:
                    estado["copa_activa_id"] = copas[0].id
                
                # Cargar torneos de la copa
                from backend.database.repositories import TorneoRepository
                torneos = TorneoRepository.obtener_por_copa(estado["copa_activa_id"])
                if torneos:
                    torneo_activo = TorneoService.obtener_torneo_activo()
                    if torneo_activo and any(t.id == torneo_activo.id for t in torneos):
                        estado["torneo_activo_id"] = torneo_activo.id
                    else:
                        estado["torneo_activo_id"] = torneos[0].id
                    
                    # Cargar la primera jornada del torneo
                    jornadas = TorneoService.obtener_jornadas_por_torneo(estado["torneo_activo_id"])
                    if jornadas:
                        estado["jornada_activa_id"] = jornadas[0].id
                        # Cargar la primera categoría de la jornada
                        categorias = TorneoService.obtener_categorias_por_jornada(jornadas[0].id)
                        if categorias:
                            estado["categoria_activa_id"] = categorias[0].id

    # Contenedor principal para el contenido dinámico
    contenido_principal = ft.Column([], scroll=ft.ScrollMode.AUTO, spacing=16)

    # Contenedor para el selector (se actualiza dinámicamente)
    selector_container = ft.Container()

    # Crear diálogo PIN persistente
    tf_pin = ft.TextField(
        label="PIN de Acceso (4 dígitos)",
        password=True,
        can_reveal_password=True,
        text_size=16,
        autofocus=True,
        keyboard_type=ft.KeyboardType.NUMBER,
        max_length=8,
    )
    texto_error_pin = ft.Text("", color=COLOR_ROJO, size=12)

    dlg_pin = ft.AlertDialog(
        title=ft.Row([
            ft.Icon(ft.Icons.LOCK, color=COLOR_AMBAR, size=22),
            ft.Text("Acceso Mesa de Control", weight=ft.FontWeight.BOLD, size=16),
        ], spacing=8),
        content=ft.Column([
            ft.Text(
                "Ingresa el PIN de seguridad para habilitar la edición de marcadores y fixture.",
                size=13,
                color=COLOR_SUBTEXTO
            ),
            tf_pin,
            texto_error_pin,
        ], spacing=10, tight=True, width=320),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda ev: setattr(dlg_pin, 'open', False)),
            ft.FilledButton(
                "Desbloquear",
                bgcolor=COLOR_CELESTE_BOTON,
                color=COLOR_TEXTO,
                on_click=lambda ev: verificar_pin(ev)
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
 )

    def verificar_pin(ev):
        pin_ingresado = tf_pin.value
        if TorneoService.validar_pin(pin_ingresado):
            estado["es_organizador"] = True
            dlg_pin.open = False
            on_cambio_rol()
            page.snack_bar = ft.SnackBar(
                content=ft.Text("👑 Modo Organizador activado. Puedes editar marcadores y fixture."),
                bgcolor=COLOR_VERDE,
                duration=3000
            )
            page.snack_bar.open = True
            page.update()
        else:
            texto_error_pin.value = "❌ PIN incorrecto. Intenta nuevamente."
            page.update()

    def abrir_dialogo_pin(e):
        if dlg_pin not in page.overlay:
            page.overlay.append(dlg_pin)
        dlg_pin.open = True
        page.update()

    # Diálogo para crear grupo
    def abrir_dialogo_crear_grupo(e):
        tf_nombre_grupo = ft.TextField(label="Nombre del Grupo (ej: Grupo C)")
        tf_equipos = ft.TextField(
            label="Equipos (separados por coma)",
            hint_text="Equipo1, Equipo2, Equipo3, Equipo4",
            text_size=12
        )
        texto_error_grupo = ft.Text("", color=COLOR_ROJO, size=12)

        def guardar_grupo(ev):
            nombre = tf_nombre_grupo.value.strip()
            equipos_str = tf_equipos.value.strip()
            equipos = [e.strip() for e in equipos_str.split(",") if e.strip()]

            if not nombre:
                texto_error_grupo.value = "❌ El nombre del grupo es obligatorio."
                page.update()
                return

            if len(equipos) < 2:
                texto_error_grupo.value = "❌ Mínimo 2 equipos requeridos."
                page.update()
                return

            try:
                cat_id = estado.get("categoria_activa_id")
                jornada_id = estado.get("jornada_activa_id")
                if not jornada_id:
                    raise ValueError("No hay una jornada seleccionada")
                TorneoService.crear_grupo(cat_id, jornada_id, nombre, equipos, es_organizador=True)
                dlg_grupo.open = False
                actualizar_vista()
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"✅ Grupo '{nombre}' creado con {len(equipos)} equipos."),
                    bgcolor=COLOR_VERDE,
                    duration=3000
                )
                page.snack_bar.open = True
                page.update()
            except Exception as err:
                texto_error_grupo.value = f"❌ {str(err)}"
                page.update()

        dlg_grupo = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.GROUP_ADD, color=COLOR_VERDE, size=22),
                ft.Text("Crear Nuevo Grupo", weight=ft.FontWeight.BOLD, size=16),
            ], spacing=8),
            content=ft.Column([
                ft.Text("Crea un nuevo grupo con equipos para la categoría y día seleccionados."),
                tf_nombre_grupo,
                tf_equipos,
                texto_error_grupo,
            ], spacing=10, tight=True, width=400),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: setattr(dlg_grupo, 'open', False)),
                ft.FilledButton("Crear Grupo", bgcolor=COLOR_VERDE, color=COLOR_TEXTO, on_click=guardar_grupo),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=COLOR_TARJETA,
        )
        if dlg_grupo not in page.overlay:
            page.overlay.append(dlg_grupo)
        dlg_grupo.open = True
        page.update()

    # Diálogo para editar grupo
    def abrir_dialogo_editar_grupo(grupo_id: int):
        jornada_id = estado.get("jornada_activa_id")
        if not jornada_id:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("❌ No hay una jornada seleccionada"),
                bgcolor=COLOR_ROJO,
                duration=3000
            )
            page.snack_bar.open = True
            page.update()
            return

        grupo = TorneoService.obtener_datos_categoria_dia(
            estado.get("categoria_activa_id"),
            jornada_id
        )["grupos"]

        grupo_data = next((g for g in grupo if g["grupo"].id == grupo_id), None)
        if not grupo_data:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("❌ Grupo no encontrado"),
                bgcolor=COLOR_ROJO,
                duration=2000
            )
            page.snack_bar.open = True
            page.update()
            return

        g = grupo_data["grupo"]
        equipos_str = ", ".join(g.equipos)

        tf_nombre_grupo = ft.TextField(label="Nombre del Grupo", value=g.nombre)
        tf_equipos = ft.TextField(
            label="Equipos (separados por coma)",
            value=equipos_str,
            text_size=12
        )
        texto_error_grupo = ft.Text("", color=COLOR_ROJO, size=12)

        def guardar_grupo(ev):
            nombre = tf_nombre_grupo.value.strip()
            equipos_str_nuevo = tf_equipos.value.strip()
            equipos = [e.strip() for e in equipos_str_nuevo.split(",") if e.strip()]

            if not nombre:
                texto_error_grupo.value = "❌ El nombre del grupo es obligatorio."
                page.update()
                return

            if len(equipos) < 2:
                texto_error_grupo.value = "❌ Mínimo 2 equipos requeridos."
                page.update()
                return

            try:
                TorneoService.actualizar_grupo(grupo_id, equipos, es_organizador=True)
                dlg_editar_grupo.open = False
                actualizar_vista()
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"✅ Grupo '{nombre}' actualizado con {len(equipos)} equipos."),
                    bgcolor=COLOR_VERDE,
                    duration=3000
                )
                page.snack_bar.open = True
                page.update()
            except Exception as err:
                texto_error_grupo.value = f"❌ {str(err)}"
                page.update()

        dlg_editar_grupo = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.EDIT, color=COLOR_CELESTE, size=22),
                ft.Text("Editar Grupo", weight=ft.FontWeight.BOLD, size=16),
            ], spacing=8),
            content=ft.Column([
                ft.Text("Modifica los equipos del grupo. Los partidos se regenerarán automáticamente."),
                tf_nombre_grupo,
                tf_equipos,
                texto_error_grupo,
            ], spacing=10, tight=True, width=400),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: setattr(dlg_editar_grupo, 'open', False)),
                ft.FilledButton("Guardar", bgcolor=COLOR_CELESTE, color=COLOR_TEXTO, on_click=guardar_grupo),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=COLOR_TARJETA,
        )
        if dlg_editar_grupo not in page.overlay:
            page.overlay.append(dlg_editar_grupo)
        dlg_editar_grupo.open = True
        page.update()

    # Diálogo para crear jornada
    def abrir_dialogo_crear_jornada(e):
        torneo_id = estado.get("torneo_activo_id")
        if not torneo_id:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("❌ No hay un torneo seleccionado"),
                bgcolor=COLOR_ROJO,
                duration=3000
            )
            page.snack_bar.open = True
            page.update()
            return

        dp_fecha = ft.DatePicker(
            first_date=datetime.now() - timedelta(days=365*5),
            last_date=datetime.now() + timedelta(days=365),
        )
        btn_fecha = ft.IconButton(
            icon=ft.Icons.CALENDAR_MONTH,
            icon_color=COLOR_CELESTE,
            tooltip="Seleccionar fecha",
            on_click=lambda e: (
                page.overlay.append(dp_fecha) if dp_fecha not in page.overlay else None,
                setattr(dp_fecha, 'open', True),
                page.update()
            )
        )
        texto_fecha = ft.Text("Selecciona una fecha", color=COLOR_SUBTEXTO)

        def on_fecha_change(e):
            if dp_fecha.value:
                texto_fecha.value = dp_fecha.value.strftime("%d-%m-%Y")
                texto_fecha.color = COLOR_TEXTO
                page.update()

        dp_fecha.on_change = on_fecha_change

        tf_nombre = ft.TextField(label="Nombre (ej: Día 3)")
        tf_lugar = ft.TextField(label="Lugar (opcional)")
        tf_horario = ft.TextField(label="Horario HH:MM (opcional)", hint_text="09:30")
        texto_error = ft.Text("", color=COLOR_ROJO, size=12)

        def guardar_jornada(ev):
            if not dp_fecha.value:
                texto_error.value = "❌ Debes seleccionar una fecha"
                page.update()
                return
            horario_val = tf_horario.value.strip()
            if horario_val:
                try:
                    datetime.strptime(horario_val, "%H:%M")
                except ValueError:
                    texto_error.value = "❌ Horario inválido, use formato HH:MM"
                    page.update()
                    return

            nombre = tf_nombre.value.strip() or f"Día {len(JornadaRepository.obtener_por_torneo(torneo_id)) + 1}"
            fecha = dp_fecha.value.isoformat()

            try:
                # Obtener el orden máximo actual
                jornadas = JornadaRepository.obtener_por_torneo(torneo_id)
                nuevo_orden = len(jornadas) + 1

                jornada_id = JornadaRepository.crear(torneo_id, fecha, nombre, nuevo_orden,
                                                     lugar=tf_lugar.value.strip() or None,
                                                     horario=horario_val or None)
                estado["jornada_activa_id"] = jornada_id
                dlg_crear_jornada.open = False
                actualizar_vista()
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"✅ Jornada '{nombre}' ({dp_fecha.value.strftime('%d-%m-%Y')}) creada"),
                    bgcolor=COLOR_VERDE,
                    duration=3000
                )
                page.snack_bar.open = True
                page.update()
            except Exception as err:
                texto_error.value = f"❌ {str(err)}"
                page.update()

        dlg_crear_jornada = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.ADD, color=COLOR_VERDE, size=22),
                ft.Text("Nueva Jornada", weight=ft.FontWeight.BOLD, size=16),
            ]),
            content=ft.Column([
                ft.Text("Selecciona la fecha de la nueva jornada"),
                ft.Row([btn_fecha, texto_fecha], spacing=10),
                tf_nombre,
                tf_lugar,
                tf_horario,
                texto_error,
            ], spacing=10, tight=True, width=340),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: setattr(dlg_crear_jornada, 'open', False)),
                ft.FilledButton("Crear Jornada", bgcolor=COLOR_VERDE, color=COLOR_TEXTO, on_click=guardar_jornada),
            ],
            bgcolor=COLOR_TARJETA,
        )
        if dlg_crear_jornada not in page.overlay:
            page.overlay.append(dlg_crear_jornada)
        dlg_crear_jornada.open = True
        page.update()

    # Diálogo para eliminar jornada
    def abrir_dialogo_eliminar_jornada(e):
        jornada_id = estado.get("jornada_activa_id")
        if not jornada_id:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("❌ No hay una jornada seleccionada"),
                bgcolor=COLOR_ROJO,
                duration=3000
            )
            page.snack_bar.open = True
            page.update()
            return

        jornada = JornadaRepository.obtener_por_id(jornada_id)
        if not jornada:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("❌ Jornada no encontrada"),
                bgcolor=COLOR_ROJO,
                duration=3000
            )
            page.snack_bar.open = True
            page.update()
            return

        def confirmar_eliminar(ev):
            try:
                JornadaRepository.eliminar(jornada_id)
                # Cargar la primera jornada disponible
                torneo_id = estado.get("torneo_activo_id")
                jornadas = JornadaRepository.obtener_por_torneo(torneo_id)
                if jornadas:
                    estado["jornada_activa_id"] = jornadas[0].id
                else:
                    estado["jornada_activa_id"] = None
                dlg_eliminar_jornada.open = False
                actualizar_vista()
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("✅ Jornada eliminada correctamente"),
                    bgcolor=COLOR_VERDE,
                    duration=3000
                )
                page.snack_bar.open = True
                page.update()
            except Exception as err:
                texto_error.value = f"❌ {str(err)}"
                page.update()

        texto_error = ft.Text("", color=COLOR_ROJO, size=12)

        dlg_eliminar_jornada = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.WARNING, color=COLOR_AMBAR, size=22),
                ft.Text("Eliminar Jornada", weight=ft.FontWeight.BOLD, size=16),
            ]),
            content=ft.Column([
                ft.Text(f"¿Estás seguro de eliminar la jornada '{jornada['nombre']}' ({jornada['fecha']})?"),
                ft.Text("Esto eliminará todos los grupos y partidos de esta jornada.", color=COLOR_ROJO, size=12),
                texto_error,
            ], spacing=10, tight=True, width=340),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: setattr(dlg_eliminar_jornada, 'open', False)),
                ft.FilledButton("Eliminar", bgcolor=COLOR_ROJO, color=COLOR_TEXTO, on_click=confirmar_eliminar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=COLOR_TARJETA,
        )
        if dlg_eliminar_jornada not in page.overlay:
            page.overlay.append(dlg_eliminar_jornada)
        dlg_eliminar_jornada.open = True
        page.update()

    # Diálogo para buscar jornada
    def abrir_dialogo_buscar_jornada(e):
        torneo_id = estado.get("torneo_activo_id")
        if not torneo_id:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("❌ No hay un torneo seleccionado"),
                bgcolor=COLOR_ROJO,
                duration=3000
            )
            page.snack_bar.open = True
            page.update()
            return

        dp_fecha = ft.DatePicker(
            first_date=datetime.now() - timedelta(days=365*5),
            last_date=datetime.now() + timedelta(days=365),
        )
        btn_fecha = ft.IconButton(
            icon=ft.Icons.CALENDAR_MONTH,
            icon_color=COLOR_CELESTE,
            tooltip="Seleccionar fecha",
            on_click=lambda e: (
                page.overlay.append(dp_fecha) if dp_fecha not in page.overlay else None,
                setattr(dp_fecha, 'open', True),
                page.update()
            )
        )
        texto_fecha = ft.Text("Selecciona una fecha", color=COLOR_SUBTEXTO)

        def on_fecha_change(e):
            if dp_fecha.value:
                texto_fecha.value = dp_fecha.value.strftime("%d-%m-%Y")
                texto_fecha.color = COLOR_TEXTO
                page.update()

        dp_fecha.on_change = on_fecha_change

        texto_error = ft.Text("", color=COLOR_ROJO, size=12)

        def buscar_jornada(ev):
            if not dp_fecha.value:
                texto_error.value = "❌ Debes seleccionar una fecha"
                page.update()
                return

            fecha = dp_fecha.value.isoformat()
            jornada = JornadaRepository.buscar_por_fecha(torneo_id, fecha)

            if jornada:
                estado["jornada_activa_id"] = jornada.id
                dlg_buscar_jornada.open = False
                actualizar_vista()
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"✅ Jornada '{jornada.nombre}' encontrada"),
                    bgcolor=COLOR_VERDE,
                    duration=3000
                )
                page.snack_bar.open = True
                page.update()
            else:
                texto_error.value = "❌ No existe una jornada con esa fecha"
                page.update()

        dlg_buscar_jornada = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.SEARCH, color=COLOR_CELESTE, size=22),
                ft.Text("Buscar Jornada", weight=ft.FontWeight.BOLD, size=16),
            ]),
            content=ft.Column([
                ft.Text("Selecciona la fecha de la jornada a buscar"),
                ft.Row([btn_fecha, texto_fecha], spacing=10),
                texto_error,
            ], spacing=10, tight=True, width=340),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: setattr(dlg_buscar_jornada, 'open', False)),
                ft.FilledButton("Buscar", bgcolor=COLOR_CELESTE, color=COLOR_TEXTO, on_click=buscar_jornada),
            ],
            bgcolor=COLOR_TARJETA,
        )
        if dlg_buscar_jornada not in page.overlay:
            page.overlay.append(dlg_buscar_jornada)
        dlg_buscar_jornada.open = True
        page.update()

    # Diálogo para eliminar grupo
    def abrir_dialogo_eliminar_grupo(grupo_id: int):
        def confirmar_eliminar(ev):
            try:
                TorneoService.eliminar_grupo(grupo_id, es_organizador=True)
                dlg_eliminar_grupo.open = False
                actualizar_vista()
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("✅ Grupo eliminado correctamente."),
                    bgcolor=COLOR_VERDE,
                    duration=3000
                )
                page.snack_bar.open = True
                page.update()
            except Exception as err:
                dlg_eliminar_grupo.open = False
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"❌ Error: {str(err)}"),
                    bgcolor=COLOR_ROJO,
                    duration=3000
                )
                page.snack_bar.open = True
                page.update()

        dlg_eliminar_grupo = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.WARNING, color=COLOR_AMBAR, size=22),
                ft.Text("Eliminar Grupo", weight=ft.FontWeight.BOLD, size=16),
            ], spacing=8),
            content=ft.Text(
                "¿Estás seguro de eliminar este grupo? Se eliminarán todos los partidos asociados. Esta acción no se puede deshacer.",
                color=COLOR_SUBTEXTO
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: setattr(dlg_eliminar_grupo, 'open', False)),
                ft.FilledButton("Eliminar", bgcolor=COLOR_ROJO, color=COLOR_TEXTO, on_click=confirmar_eliminar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=COLOR_TARJETA,
        )
        if dlg_eliminar_grupo not in page.overlay:
            page.overlay.append(dlg_eliminar_grupo)
        dlg_eliminar_grupo.open = True
        page.update()

    def actualizar_vista():
        """Recarga toda la vista basada en el estado actual."""
        cat_id = estado.get("categoria_activa_id")
        jornada_id = estado.get("jornada_activa_id")
        grupo_filtro = estado.get("grupo_filtro", "Todos")
        es_org = estado.get("es_organizador", False)

        # Pantalla de inicio: solo Año y Campeonato
        if estado.get("pantalla", "inicio") == "inicio":
            selector_container.content = crear_selector_categoria_y_dia(
                estado, page, [], [], on_cambio_seleccion, vista="inicio"
            )
            header_nuevo = crear_header(estado, page, on_cambio_rol, abrir_dialogo_pin)
            header.content = header_nuevo.content
            header.bgcolor = header_nuevo.bgcolor
            header.padding = header_nuevo.padding
            contenido_principal.controls = []
            page.update()
            return

        # Cargar categorías de la jornada activa
        categorias_actual = []
        if jornada_id:
            categorias_actual = TorneoService.obtener_categorias_por_jornada(jornada_id)

        # Actualizar selector
        selector_nuevo = crear_selector_categoria_y_dia(
            estado, page, torneos, categorias_actual, on_cambio_seleccion,
            on_crear_grupo=abrir_dialogo_crear_grupo,
            on_editar_grupo=abrir_dialogo_editar_grupo,
            on_eliminar_grupo=abrir_dialogo_eliminar_grupo,
            on_crear_jornada=abrir_dialogo_crear_jornada,
            on_eliminar_jornada=abrir_dialogo_eliminar_jornada,
            on_buscar_jornada=abrir_dialogo_buscar_jornada
        )
        selector_container.content = selector_nuevo

        # Actualizar header
        _cid = estado.get("copa_activa_id")
        _copa = CopaService.obtener_copa_por_id(_cid) if _cid else None
        header_nuevo = crear_header(estado, page, on_cambio_rol, abrir_dialogo_pin,
                                    color_copa=_copa.color if _copa and _copa.color else None,
                                    compacto=True)
        header.content = header_nuevo.content
        header.bgcolor = header_nuevo.bgcolor
        header.padding = header_nuevo.padding

        if not cat_id:
            contenido_principal.controls = [
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.ERROR_OUTLINE, size=48, color=ft.Colors.RED_400),
                        ft.Text("No hay categorías disponibles", size=16, color=ft.Colors.GREY_400),
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=40
                )
            ]
            page.update()
            return

        if not jornada_id:
            contenido_principal.controls = [
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.CALENDAR_TODAY, size=48, color=ft.Colors.GREY_400),
                        ft.Text("No hay jornadas disponibles", size=16, color=ft.Colors.GREY_400),
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=40
                )
            ]
            page.update()
            return

        # Obtener datos del torneo
        datos = TorneoService.obtener_datos_categoria_dia(cat_id, jornada_id)
        grupos = datos["grupos"]
        partidos_definicion = datos["partidos_definicion"]
        estado_campeon = datos["estado_campeon"]

        # Obtener color de la copa activa
        copa_activa_id = estado.get("copa_activa_id")
        copa_activa = CopaService.obtener_copa_por_id(copa_activa_id) if copa_activa_id else None
        color_copa = copa_activa.color if copa_activa and copa_activa.color else None

        # Filtrar grupos según el filtro seleccionado
        if grupo_filtro != "Todos":
            grupos = [g for g in grupos if g["grupo"].nombre == grupo_filtro]

        # Construir contenido
        nuevos_controles = []

        # Tarjeta de campeón/estado del torneo (primero)
        nuevos_controles.append(
            crear_tarjeta_campeon(
                estado_campeon=estado_campeon,
                es_organizador=es_org,
                on_generar_desempate=on_generar_desempate,
                on_generar_final=on_generar_final,
                color_copa=color_copa
            )
        )

        # Agregar tablas de posiciones y partidos por grupo
        for g_data in grupos:
            grupo = g_data["grupo"]
            partidos = g_data["partidos"]
            tabla = g_data["tabla"]

            # Tabla de posiciones
            nuevos_controles.append(crear_tabla_posiciones(grupo.nombre, tabla, color_copa=color_copa))

            # Lista de partidos
            nuevos_controles.append(
                crear_lista_partidos(
                    grupo_nombre=grupo.nombre,
                    partidos=partidos,
                    es_organizador=es_org,
                    on_guardar_marcador=on_guardar_marcador,
                    on_reiniciar_marcador=on_reiniciar_marcador,
                    color_copa=color_copa
                )
            )

        # Partidos de definición (desempate / final)
        if partidos_definicion:
            nuevos_controles.append(
                crear_lista_partidos(
                    grupo_nombre="Partidos de Definición",
                    partidos=partidos_definicion,
                    es_organizador=es_org,
                    on_guardar_marcador=on_guardar_marcador,
                    on_reiniciar_marcador=on_reiniciar_marcador,
                    color_copa=color_copa
                )
            )

        contenido_principal.controls = nuevos_controles
        page.update()

    def on_cambio_rol():
        """Callback cuando cambia el rol (organizador/consulta)."""
        actualizar_vista()

    def on_cambio_seleccion():
        """Callback cuando cambia la selección de categoría, día o grupo."""
        actualizar_vista()

    def on_guardar_marcador(partido_id: int, goles_local: int, goles_visita: int):
        """Callback para guardar un marcador."""
        try:
            TorneoService.guardar_marcador(
                partido_id, goles_local, goles_visita, 
                es_organizador=estado.get("es_organizador", False)
            )
            page.snack_bar = ft.SnackBar(
                content=ft.Text("✅ Marcador guardado"),
                bgcolor=ft.Colors.GREEN_600,
                duration=2000
            )
            page.snack_bar.open = True
            actualizar_vista()
        except Exception as e:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"❌ Error: {str(e)}"),
                bgcolor=ft.Colors.RED_600,
                duration=3000
            )
            page.snack_bar.open = True
            page.update()

    def on_reiniciar_marcador(partido_id: int):
        """Callback para reiniciar un marcador."""
        try:
            TorneoService.reiniciar_marcador(
                partido_id, es_organizador=estado.get("es_organizador", False)
            )
            page.snack_bar = ft.SnackBar(
                content=ft.Text("🔄 Marcador reiniciado"),
                bgcolor=ft.Colors.AMBER_600,
                duration=2000
            )
            page.snack_bar.open = True
            actualizar_vista()
        except Exception as e:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"❌ Error: {str(e)}"),
                bgcolor=ft.Colors.RED_600,
                duration=3000
            )
            page.snack_bar.open = True
            page.update()

    def on_generar_desempate(grupo_id: int, equipo1: str, equipo2: str):
        """Callback para generar un partido de desempate."""
        try:
            cat_id = estado.get("categoria_activa_id")
            jornada_id = estado.get("jornada_activa_id")
            if not jornada_id:
                raise ValueError("No hay una jornada seleccionada")
            TorneoService.generar_partido_desempate(
                cat_id, jornada_id, grupo_id, equipo1, equipo2,
                es_organizador=estado.get("es_organizador", False)
            )
            page.snack_bar = ft.SnackBar(
                content=ft.Text("⚽ Partido de desempate generado"),
                bgcolor=ft.Colors.GREEN_600,
                duration=2000
            )
            page.snack_bar.open = True
            actualizar_vista()
        except Exception as e:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"❌ Error: {str(e)}"),
                bgcolor=ft.Colors.RED_600,
                duration=3000
            )
            page.snack_bar.open = True
            page.update()

    def on_generar_final():
        """Callback para generar la final del Día 2."""
        try:
            cat_id = estado.get("categoria_activa_id")
            jornada_id = estado.get("jornada_activa_id")
            if not jornada_id:
                raise ValueError("No hay una jornada seleccionada")
            TorneoService.generar_final_dia2(
                cat_id, jornada_id, es_organizador=estado.get("es_organizador", False)
            )
            page.snack_bar = ft.SnackBar(
                content=ft.Text("🏆 Gran Final generada"),
                bgcolor=ft.Colors.GREEN_600,
                duration=2000
            )
            page.snack_bar.open = True
            actualizar_vista()
        except Exception as e:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"❌ Error: {str(e)}"),
                bgcolor=ft.Colors.RED_600,
                duration=3000
            )
            page.snack_bar.open = True
            page.update()

    # Header
    header = crear_header(estado, page, on_cambio_rol, abrir_dialogo_pin)

    # Guardar referencia al header para actualizaciones parciales
    header_ref = {"widget": header}

    # Layout principal
    page.add(
        ft.Column(
            [
                header,
                ft.Container(
                    content=selector_container,
                    padding=12
                ),
                ft.Container(
                    content=contenido_principal,
                    padding=8,
                    expand=True
                ),
            ],
            spacing=0,
            expand=True
        )
    )

    # Cargar vista inicial
    actualizar_vista()


# Export ASGI app for production deployment (Render, Docker)
# This creates the app without running it - uvicorn will run it
app = ft.run(main, export_asgi_app=True)


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8080))
    try:
        # Si estamos en Render (variable PORT definida), usar uvicorn
        if os.environ.get("PORT"):
            # Run with uvicorn
            import uvicorn
            uvicorn.run(app, host="0.0.0.0", port=puerto)
        else:
            # Modo local/desktop - run the app directly
            ft.run(main)
    except Exception as e:
        print(f"[ERROR] Application error: {e}")
        import traceback
        traceback.print_exc()
        raise
