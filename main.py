import flet as ft
from datetime import datetime, timedelta
from backend.database.schema import inicializar_db
from backend.database.repositories import JornadaRepository
from backend.services.torneo_service import TorneoService
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
        "categoria_activa_id": None,
        "jornada_activa_id": None,  # Ahora es un ID de jornada en lugar de un string
        "grupo_filtro": "Todos",
    }

    # Cargar categorías iniciales
    categorias = TorneoService.obtener_categorias()
    if categorias:
        estado["categoria_activa_id"] = categorias[0].id
        # Cargar la primera jornada de la categoría
        from backend.database.repositories import JornadaRepository
        jornadas = JornadaRepository.obtener_por_categoria(categorias[0].id)
        if jornadas:
            estado["jornada_activa_id"] = jornadas[0]["id"]

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
        cat_id = estado.get("categoria_activa_id")
        if not cat_id:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("❌ No hay una categoría seleccionada"),
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
        texto_error = ft.Text("", color=COLOR_ROJO, size=12)

        def guardar_jornada(ev):
            if not dp_fecha.value:
                texto_error.value = "❌ Debes seleccionar una fecha"
                page.update()
                return

            nombre = tf_nombre.value.strip() or f"Día {len(JornadaRepository.obtener_por_categoria(cat_id)) + 1}"
            fecha = dp_fecha.value.isoformat()

            try:
                # Obtener el orden máximo actual
                jornadas = JornadaRepository.obtener_por_categoria(cat_id)
                nuevo_orden = len(jornadas) + 1

                jornada_id = JornadaRepository.crear(cat_id, fecha, nombre, nuevo_orden)
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
                cat_id = estado.get("categoria_activa_id")
                jornadas = JornadaRepository.obtener_por_categoria(cat_id)
                if jornadas:
                    estado["jornada_activa_id"] = jornadas[0]["id"]
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
        cat_id = estado.get("categoria_activa_id")
        if not cat_id:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("❌ No hay una categoría seleccionada"),
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
            jornada = JornadaRepository.buscar_por_fecha(cat_id, fecha)

            if jornada:
                estado["jornada_activa_id"] = jornada["id"]
                dlg_buscar_jornada.open = False
                actualizar_vista()
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"✅ Jornada '{jornada['nombre']}' encontrada"),
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

        # Actualizar selector
        selector_nuevo = crear_selector_categoria_y_dia(
            estado, page, categorias, on_cambio_seleccion,
            on_crear_grupo=abrir_dialogo_crear_grupo,
            on_editar_grupo=abrir_dialogo_editar_grupo,
            on_eliminar_grupo=abrir_dialogo_eliminar_grupo,
            on_crear_jornada=abrir_dialogo_crear_jornada,
            on_eliminar_jornada=abrir_dialogo_eliminar_jornada,
            on_buscar_jornada=abrir_dialogo_buscar_jornada
        )
        selector_container.content = selector_nuevo

        # Actualizar header
        header_nuevo = crear_header(estado, page, on_cambio_rol, abrir_dialogo_pin)
        header.content = header_nuevo.content

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
                on_generar_final=on_generar_final
            )
        )

        # Agregar tablas de posiciones y partidos por grupo
        for g_data in grupos:
            grupo = g_data["grupo"]
            partidos = g_data["partidos"]
            tabla = g_data["tabla"]

            # Tabla de posiciones
            nuevos_controles.append(crear_tabla_posiciones(grupo.nombre, tabla))

            # Lista de partidos
            nuevos_controles.append(
                crear_lista_partidos(
                    grupo_nombre=grupo.nombre,
                    partidos=partidos,
                    es_organizador=es_org,
                    on_guardar_marcador=on_guardar_marcador,
                    on_reiniciar_marcador=on_reiniciar_marcador
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
                    on_reiniciar_marcador=on_reiniciar_marcador
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


if __name__ == "__main__":
    ft.run(main)
