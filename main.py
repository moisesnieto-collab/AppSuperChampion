import asyncio
import os
import flet as ft
from datetime import datetime, timedelta
from backend.database.schema import inicializar_db
from backend.database.repositories import JornadaRepository, CampeonatoRepository, TorneoRepository
from config.preferencias import configurar as configurar_preferencias, cargar_ultima_seleccion, guardar_seleccion_completa, cargar_seleccion_completa
from backend.services.torneo_service import TorneoService
from backend.services.anio_service import AnioService
from backend.services.campeonato_service import CampeonatoService
from backend.services.copa_service import CopaService
from config.settings import APP_TITLE, APP_THEME_MODE, APP_BGCOLOR
from config.constants import (
    COLOR_FONDO, COLOR_AMBAR, COLOR_CELESTE, COLOR_CELESTE_BOTON,
    COLOR_VERDE, COLOR_ROJO, COLOR_SUBTEXTO, COLOR_TEXTO, COLOR_TARJETA, COLOR_BORDE,
    estilo_pill_3d, BG, NAV_BG
)
from frontend.components.vista_rediseno import (
    fecha_sin_hora, tema_copa, crear_cabecera_campeonato, crear_filtros, crear_estado_vacio, crear_skeleton,
    crear_navegacion, cargar_jerarquia, crear_resumen_estado,
)
from frontend.components.header import crear_header
from frontend.components.selector_categoria import crear_selector_categoria_y_dia
from frontend.components.tabla_posiciones import crear_tabla_posiciones
from frontend.components.lista_partidos import crear_lista_partidos
from frontend.components.tarjeta_campeon import crear_tarjeta_campeon


APP_VERSION = "1.7.0"
_commit = (os.environ.get("RENDER_GIT_COMMIT") or "")[:7]
VERSION_TXT = f"v{APP_VERSION}" + (f" ({_commit})" if _commit else "")
print(f"[SuperChampion] Iniciando {VERSION_TXT}")


def main(page: ft.Page):
    # Configuración de la página
    page.title = APP_TITLE
    page.theme_mode = ft.ThemeMode.DARK
    page.fonts = {
        "Montserrat": "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf",
    }
    page.theme = ft.Theme(font_family="Montserrat", color_scheme_seed="#3DD598")
    page.dark_theme = ft.Theme(font_family="Montserrat", color_scheme_seed="#3DD598")
    page.bgcolor = BG
    page.padding = 0
    page.scroll = None
    page.window_min_width = 1000
    page.window_min_height = 700

    configurar_preferencias(page)

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

    torneos = []
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

        # Restaurar Copa, torneo, jornada, categoría y grupo guardados (si siguen siendo válidos)
        guardado = cargar_seleccion_completa()
        if camp_ultimo and guardado.get("campeonato_id") == camp_ultimo.id:
            try:
                copas_g = {c.id for c in CopaService.obtener_copas_por_campeonato(camp_ultimo.id)}
                if guardado.get("copa_activa_id") in copas_g:
                    estado["copa_activa_id"] = guardado["copa_activa_id"]
                    ts = {t.id for t in TorneoRepository.obtener_por_copa(estado["copa_activa_id"])}
                    if guardado.get("torneo_activo_id") in ts:
                        estado["torneo_activo_id"] = guardado["torneo_activo_id"]
                        js = {j.id for j in TorneoService.obtener_jornadas_por_torneo(estado["torneo_activo_id"])}
                        if guardado.get("jornada_activa_id") in js:
                            estado["jornada_activa_id"] = guardado["jornada_activa_id"]
                            cs = {c.id for c in TorneoService.obtener_categorias_por_jornada(estado["jornada_activa_id"])}
                            estado["categoria_activa_id"] = guardado["categoria_activa_id"] \
                                if guardado.get("categoria_activa_id") in cs else (next(iter(cs), None))
                            estado["grupo_filtro"] = guardado.get("grupo_filtro") or "Todos"
                if guardado.get("tab_contenido") in ("Marcadores", "Tabla", "Estado"):
                    estado["tab_contenido"] = guardado["tab_contenido"]
            except Exception:
                pass

    # Contenedor principal para el contenido dinámico
    scroll_estado = {"y": 0.0}

    def _guardar_scroll(ev):
        scroll_estado["y"] = ev.pixels

    contenido_principal = ft.Column([], scroll=ft.ScrollMode.AUTO, spacing=16, on_scroll=_guardar_scroll)

    # Contenedor para el selector (se actualiza dinámicamente)
    selector_container = ft.Container()
    cabecera_container = ft.Container()
    filtros_container = ft.Container(padding=ft.Padding.symmetric(horizontal=12, vertical=4))
    nav_container = ft.Container()

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
        rol = TorneoService.validar_pin(pin_ingresado)
        if rol:
            estado["es_organizador"] = True
            estado["rol"] = rol
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
                TorneoService.copiar_categorias_de_ultima_jornada(torneo_id, jornada_id)
                estado["jornada_activa_id"] = jornada_id
                _cats = TorneoService.obtener_categorias_por_jornada(jornada_id)
                estado["categoria_activa_id"] = _cats[0].id if _cats else None
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
                ft.Text(f"¿Estás seguro de eliminar la jornada '{jornada.nombre}' ({jornada.fecha})?"),
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

    def actualizar_vista(conservar_scroll: bool = False):
        """Recarga toda la vista basada en el estado actual."""
        cat_id = estado.get("categoria_activa_id")
        jornada_id = estado.get("jornada_activa_id")
        grupo_filtro = estado.get("grupo_filtro", "Todos")
        es_org = bool(estado.get("es_organizador", False) and estado.get("modo_admin", False))

        # Pantalla de inicio: solo Año y Campeonato
        if estado.get("pantalla", "inicio") == "inicio" and estado.get("campeonato_activo_id"):
            estado["pantalla"] = "campeonato"
        if estado.get("pantalla", "inicio") == "inicio":
            cabecera_container.content = None
            filtros_container.content = None
            nav_container.content = None
            selector_container.content = crear_selector_categoria_y_dia(
                estado, page, [], [], on_cambio_seleccion, vista="inicio"
            )
            header_nuevo = crear_header(estado, page, on_cambio_rol, abrir_dialogo_pin)
            header.content = header_nuevo.content
            header.bgcolor = header_nuevo.bgcolor
            header.padding = header_nuevo.padding
            header.visible = True
            contenido_principal.controls = []
            page.update()
            return

        torneo_id = estado.get("torneo_activo_id")
        copas_c = CopaService.obtener_copas_por_campeonato(estado["campeonato_activo_id"]) \
            if estado.get("campeonato_activo_id") else []
        tema = tema_copa(copas_c, estado.get("copa_activa_id"))
        bright = tema["bright"]
        categorias_actual = TorneoService.obtener_categorias_por_jornada(jornada_id) if jornada_id else []
        jornadas_actual = TorneoService.obtener_jornadas_por_torneo(torneo_id) if torneo_id else []

        copa_activa_id = estado.get("copa_activa_id")
        copa_activa = CopaService.obtener_copa_por_id(copa_activa_id) if copa_activa_id else None
        color_copa = None  # fondo neutro fijo; la Copa solo aporta el acento

        datos = TorneoService.obtener_datos_categoria_dia(cat_id, jornada_id) if (cat_id and jornada_id) else None
        grupos_todos = datos["grupos"] if datos else []
        nombres_grupos = [g["grupo"].nombre for g in grupos_todos]
        if estado.get("grupo_filtro", "Todos") not in ["Todos", *nombres_grupos]:
            estado["grupo_filtro"] = "Todos"
        grupo_filtro = estado.get("grupo_filtro", "Todos")

        tab = estado.get("tab_contenido", "Marcadores")
        if not page.web:
            guardar_seleccion_completa(estado)

        def elegir_tab(nombre):
            estado["tab_contenido"] = nombre
            actualizar_vista()

        header.visible = False
        badge = crear_header(estado, page, on_cambio_rol, abrir_dialogo_pin, solo_badge=True)
        cabecera_container.content = crear_cabecera_campeonato(estado, page, on_cambio_seleccion, bright, badge)
        # Herramientas de administración (solo con PIN y modo Administrar): menú ⋮ por sección
        acciones_admin = {}
        if es_org:
            crear_selector_categoria_y_dia(
                estado, page, torneos, categorias_actual, on_cambio_seleccion,
                on_crear_grupo=abrir_dialogo_crear_grupo,
                on_editar_grupo=abrir_dialogo_editar_grupo,
                on_eliminar_grupo=abrir_dialogo_eliminar_grupo,
                on_crear_jornada=abrir_dialogo_crear_jornada,
                on_eliminar_jornada=abrir_dialogo_eliminar_jornada,
                on_buscar_jornada=abrir_dialogo_buscar_jornada,
                acciones_out=acciones_admin,
            )
        selector_container.height = None
        selector_container.content = None
        filtros_container.content = crear_filtros(
            estado, page, on_cambio_seleccion, tema, copas_c, categorias_actual, jornadas_actual, nombres_grupos,
            acciones_admin)
        nav_container.content = crear_navegacion(tab, bright, elegir_tab)
        page.bgcolor = tema["solid"]

        def ultima_copa_con_datos():
            for c in copas_c:
                if TorneoRepository.obtener_por_copa(c.id):
                    cargar_jerarquia(estado, c.id)
                    actualizar_vista()
                    return

        if not cat_id:
            contenido_principal.controls = [crear_estado_vacio(
                "Aún no hay categorías en esta Copa",
                "Prueba otra Copa o vuelve pronto.", ft.Icons.INBOX_OUTLINED,
                "Ir a la última Copa con datos", ultima_copa_con_datos)]
            page.update()
            return

        if not jornada_id:
            contenido_principal.controls = [crear_estado_vacio(
                "No hay jornadas disponibles", "Vuelve pronto o prueba otra Copa.",
                ft.Icons.CALENDAR_TODAY, "Ir a la última Copa con datos", ultima_copa_con_datos)]
            page.update()
            return

        grupos = grupos_todos
        partidos_definicion = datos["partidos_definicion"]
        estado_campeon = datos["estado_campeon"]

        if grupo_filtro != "Todos":
            grupos = [g for g in grupos if g["grupo"].nombre == grupo_filtro]

        nuevos_controles = []

        if tab == "Estado":
            todos = [p for g in grupos_todos for p in g["partidos"]] + list(partidos_definicion or [])
            cat_nom = next((c.nombre for c in categorias_actual if c.id == cat_id), "")
            jor = next((j for j in jornadas_actual if j.id == jornada_id), None)
            nuevos_controles.append(crear_resumen_estado(
                todos, copa_activa.nombre if copa_activa else "", cat_nom,
                f"{jor.nombre} · {fecha_sin_hora(jor.fecha)}" if jor else "", bright))
            nuevos_controles.append(
                crear_tarjeta_campeon(
                    estado_campeon=estado_campeon,
                    es_organizador=es_org,
                    on_generar_desempate=on_generar_desempate,
                    on_generar_final=on_generar_final if datos and datos.get("copa") and datos["copa"].modo_campeon == "final_lideres" else None,
                    color_copa=color_copa
                )
            )

        for g_data in grupos:
            grupo = g_data["grupo"]
            if tab == "Tabla":
                nuevos_controles.append(crear_tabla_posiciones(
                    grupo.nombre, g_data["tabla"], color_copa=color_copa, compacto=True, acento=bright))
            if tab == "Marcadores":
                nuevos_controles.append(
                    crear_lista_partidos(
                        grupo_nombre=grupo.nombre,
                        partidos=g_data["partidos"],
                        es_organizador=es_org,
                        on_guardar_marcador=on_guardar_marcador,
                        on_reiniciar_marcador=on_reiniciar_marcador,
                        on_actualizar_programacion=on_actualizar_programacion,
                        on_guardar_todos=on_guardar_todos,
                        color_copa=None if es_org else bright
                    )
                )

        if partidos_definicion and tab == "Marcadores":
            nuevos_controles.append(
                crear_lista_partidos(
                    grupo_nombre="Partidos de Definición",
                    partidos=partidos_definicion,
                    es_organizador=es_org,
                    on_guardar_marcador=on_guardar_marcador,
                    on_reiniciar_marcador=on_reiniciar_marcador,
                    on_actualizar_programacion=on_actualizar_programacion,
                    color_copa=None if es_org else bright
                )
            )

        if tab in ("Marcadores", "Tabla") and not grupos:
            nuevos_controles.append(crear_estado_vacio(
                "Aún no hay grupos en esta categoría", "Prueba otra categoría o vuelve pronto.",
                ft.Icons.GROUPS_OUTLINED))

        y_previo = scroll_estado["y"] if conservar_scroll else 0.0
        contenido_principal.controls = nuevos_controles
        page.update()
        if conservar_scroll and y_previo > 0:
            try:
                page.run_task(contenido_principal.scroll_to, offset=y_previo, duration=0)
            except Exception:
                pass

    def on_cambio_rol():
        """Callback cuando cambia el rol (organizador/consulta)."""
        actualizar_vista()

    def on_cambio_seleccion():
        """Callback cuando cambia la selección de categoría, día o grupo."""
        actualizar_vista()

    def on_guardar_marcador(partido_id: int, goles_local: int, goles_visita: int):
        """Callback para guardar un marcador."""
        # Solo guarda; la tarjeta se actualiza sola (sin reconstruir toda la vista).
        try:
            TorneoService.guardar_marcador(
                partido_id, goles_local, goles_visita,
                es_organizador=estado.get("es_organizador", False),
                categoria_id=estado.get("categoria_activa_id")
            )
            page.snack_bar = ft.SnackBar(content=ft.Text("✅ Marcador guardado"),
                                         bgcolor=ft.Colors.GREEN_600, duration=1500)
            page.snack_bar.open = True
            page.update()
        except Exception as e:
            page.snack_bar = ft.SnackBar(content=ft.Text(f"❌ Error: {str(e)}"),
                                         bgcolor=ft.Colors.RED_600, duration=3000)
            page.snack_bar.open = True
            page.update()
            raise

    def on_guardar_todos(lote) -> bool:
        """Guarda varios marcadores en una sola transacción."""
        try:
            TorneoService.guardar_marcadores(
                lote, es_organizador=estado.get("es_organizador", False),
                categoria_id=estado.get("categoria_activa_id"))
            page.snack_bar = ft.SnackBar(content=ft.Text(f"✅ {len(lote)} marcadores guardados"),
                                         bgcolor=ft.Colors.GREEN_600, duration=2000)
            ok = True
        except Exception as e:
            page.snack_bar = ft.SnackBar(content=ft.Text(f"❌ Error: {str(e)}"),
                                         bgcolor=ft.Colors.RED_600, duration=3000)
            ok = False
        page.snack_bar.open = True
        page.update()
        return ok

    def on_actualizar_programacion(partido_id: int, hora: str, cancha: str):
        """Guarda hora y cancha sin cambiar el estado del partido."""
        try:
            TorneoService.actualizar_programacion(
                partido_id, hora, cancha, es_organizador=estado.get("es_organizador", False))
            page.snack_bar = ft.SnackBar(content=ft.Text("🕒 Programación guardada"),
                                         bgcolor=ft.Colors.GREEN_600, duration=2000)
        except Exception as e:
            page.snack_bar = ft.SnackBar(content=ft.Text(f"❌ Error: {str(e)}"),
                                         bgcolor=ft.Colors.RED_600, duration=3000)
        page.snack_bar.open = True
        actualizar_vista(conservar_scroll=True)

    def on_reiniciar_marcador(partido_id: int):
        """Callback para reiniciar un marcador."""
        try:
            TorneoService.reiniciar_marcador(
                partido_id, es_organizador=estado.get("es_organizador", False)
            )
            page.snack_bar = ft.SnackBar(content=ft.Text("🔄 Marcador reiniciado"),
                                         bgcolor=ft.Colors.AMBER_600, duration=1500)
            page.snack_bar.open = True
            page.update()
        except Exception as e:
            page.snack_bar = ft.SnackBar(content=ft.Text(f"❌ Error: {str(e)}"),
                                         bgcolor=ft.Colors.RED_600, duration=3000)
            page.snack_bar.open = True
            page.update()
            raise

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
            resultado = TorneoService.generar_final_dia2(
                cat_id, jornada_id, es_organizador=estado.get("es_organizador", False)
            )
            page.snack_bar = ft.SnackBar(
                content=ft.Text("🏆 Gran Final generada" if resultado else
                                "⚠️ Se necesitan al menos 2 grupos para generar la Gran Final"),
                bgcolor=ft.Colors.GREEN_600 if resultado else ft.Colors.AMBER_600,
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
                cabecera_container,
                filtros_container,
                ft.Container(content=selector_container, padding=ft.Padding.symmetric(horizontal=12)),
                ft.Container(
                    content=contenido_principal,
                    padding=8,
                    expand=True
                ),
                nav_container,
                ft.Container(
                    content=ft.Text(VERSION_TXT, size=10, color=COLOR_SUBTEXTO),
                    alignment=ft.Alignment.CENTER, padding=ft.Padding.only(bottom=2)),
            ],
            spacing=0,
            expand=True
        )
    )

    def on_reconectar(e=None):
        try:
            actualizar_vista()
            page.update()
        except Exception as err:
            print(f"Error al reconectar: {err}")

    page.on_connect = on_reconectar

    def on_resize(e=None):
        try:
            actualizar_vista()
        except Exception as err:
            print(f"Error al redimensionar: {err}")

    page.on_resize = on_resize

    def _firma_datos():
        cat_id = estado.get("categoria_activa_id")
        jornada_id = estado.get("jornada_activa_id")
        if not (cat_id and jornada_id):
            return None
        datos = TorneoService.obtener_datos_categoria_dia(cat_id, jornada_id)
        partidos = [p for g in datos["grupos"] for p in g["partidos"]] + list(datos["partidos_definicion"] or [])
        return (cat_id, jornada_id, tuple(
            (p.id, p.goles_local, p.goles_visita, p.jugado, p.en_vivo, p.hora) for p in partidos))

    async def sondeo_en_vivo():
        """Refresca la vista solo cuando cambian los marcadores; conserva el scroll."""
        ultima = None
        while True:
            await asyncio.sleep(10)
            try:
                if estado.get("modo_admin", False):
                    ultima = None
                    continue
                firma = _firma_datos()
                if ultima is not None and firma != ultima:
                    actualizar_vista(conservar_scroll=True)
                ultima = firma
            except Exception as err:
                print(f"Error en sondeo en vivo: {err}")

    # Cargar vista inicial
    actualizar_vista()
    page.run_task(sondeo_en_vivo)


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
