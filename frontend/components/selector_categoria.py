import flet as ft
from typing import List, Callable, Optional
from datetime import datetime
from config.constants import (
    COLOR_TARJETA, COLOR_BORDE, COLOR_CELESTE, COLOR_CELESTE_BOTON,
    COLOR_TEXTO, COLOR_SUBTEXTO, COLOR_VERDE, COLOR_AMBAR, COLOR_ROJO, COLOR_TARJETA_SEGUNDARIA, COLOR_FONDO,
    mezclar_color, oscurecer_color, estilo_pill_3d
)
from backend.models.categoria import Categoria
from backend.models.torneo import Torneo
from backend.models.jornada import Jornada
from backend.models.anio import Anio
from backend.models.campeonato import Campeonato
from backend.models.copa import Copa, MODOS_CAMPEON, CRITERIOS_DESEMPATE
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
    vista: str = "campeonato",
    acciones_out: dict = None
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
    es_organizador = bool(estado.get("es_organizador", False) and estado.get("modo_admin", False)
                          and estado.get("rol") != "marcador")
    es_master = bool(es_organizador and estado.get("rol") == "master")

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
        dd_modo_t = ft.Dropdown(
            label="Cómo se define el campeón",
            options=[ft.dropdown.Option(key=k, text=v) for k, v in MODOS_CAMPEON.items()],
            value="final_lideres",
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
                nuevo_id = TorneoService.crear_torneo(nom, tipo, copa_activa_id, orden, es_master=True,
                                                    modo_campeon=dd_modo_t.value or "final_lideres")
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
                dd_modo_t,
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

    def abrir_dialogo_editar_torneo(t):
        tf_n = ft.TextField(label="Nombre del Torneo", value=t.nombre)
        tf_o = ft.TextField(label="Orden de presentación", value=str(t.orden),
                            input_filter=ft.NumbersOnlyInputFilter())
        dd_m = ft.Dropdown(
            label="Cómo se define el campeón",
            options=[ft.dropdown.Option(key=k, text=v) for k, v in MODOS_CAMPEON.items()],
            value=t.modo_campeon,
        )
        chk = ft.Checkbox(
            label="Borrar partidos de desempate/final si cambia la regla del campeón (irreversible)",
            value=True,
        )

        def guardar():
            nombre = tf_n.value.strip()
            if not nombre:
                raise ValueError("El nombre es obligatorio")
            nuevo = dd_m.value or "final_lideres"
            TorneoService.actualizar_torneo(t.id, nombre, int(tf_o.value or 0), nuevo, es_master=True)
            if chk.value and nuevo != t.modo_campeon:
                from backend.database.repositories import PartidoRepository
                for j in TorneoService.obtener_jornadas_por_torneo(t.id):
                    for c in TorneoService.obtener_categorias_por_jornada(j.id):
                        PartidoRepository.eliminar_partidos_definicion(c.id, j.id)

        _modal_formulario("Editar Torneo", [tf_n, tf_o, dd_m, chk], guardar, "Guardar")

    def abrir_dialogo_eliminar_torneo(e):
        torneo = TorneoService.obtener_torneo_activo()
        if not torneo:
            return
        
        def confirmar_eliminar(ev):
            try:
                TorneoService.eliminar_torneo(torneo_activo_id, es_master=True)
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
                TorneoService.actualizar_orden_torneo(torneo_id, orden, es_master=True)
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
                nuevo_id = AnioService.crear_anio(valor, es_master=True)
                estado["anio_activo_id"] = nuevo_id
                estado["campeonato_activo_id"] = None
                estado["copa_activa_id"] = None
                estado["torneo_activo_id"] = None
                estado["jornada_activa_id"] = None
                estado["categoria_activa_id"] = None

        _modal_formulario("Editar Año" if anio else "Nuevo Año", [tf_valor], guardar, "Guardar" if anio else "Crear")

    def eliminar_anio(anio):
        def op():
            AnioService.eliminar_anio(anio.id, es_master=True)
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
                nuevo_id = CampeonatoService.crear_campeonato(nombre, int(dd_anio.value), es_master=True)
                estado["campeonato_activo_id"] = nuevo_id
                estado["copa_activa_id"] = None
                estado["torneo_activo_id"] = None
                estado["jornada_activa_id"] = None
                estado["categoria_activa_id"] = None

        _modal_formulario("Editar Campeonato" if camp else "Nuevo Campeonato", [tf_nombre, dd_anio], guardar, "Guardar" if camp else "Crear")

    def eliminar_campeonato(camp):
        def op():
            CampeonatoService.eliminar_campeonato(camp.id, es_master=True)
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

        # --- Reglas de la copa: puntos y orden de criterios de desempate ---
        tf_pv = ft.TextField(label="Puntos por victoria", value=str(copa.puntos_victoria if copa else 3),
                             input_filter=ft.NumbersOnlyInputFilter(), expand=True)
        tf_pe = ft.TextField(label="Puntos por empate", value=str(copa.puntos_empate if copa else 1),
                             input_filter=ft.NumbersOnlyInputFilter(), expand=True)
        activos = list(copa.lista_criterios()) if copa else ["dg", "gf", "h2h", "pg", "gc"]
        orden_crit = activos + [k for k in CRITERIOS_DESEMPATE if k not in activos]
        habilitados = {k: (k in activos) for k in CRITERIOS_DESEMPATE}
        col_crit = ft.Column(spacing=0, tight=True)

        def pintar_criterios():
            filas = []
            for idx, k in enumerate(orden_crit):
                filas.append(ft.Row([
                    ft.Checkbox(value=habilitados[k], on_change=lambda ev, k=k: alternar(k, ev.control.value)),
                    ft.Text(f"{idx + 1}. {CRITERIOS_DESEMPATE[k]}", size=12, color=COLOR_TEXTO, expand=True),
                    ft.IconButton(icon=ft.Icons.ARROW_UPWARD, icon_size=16, on_click=lambda ev, i=idx: mover(i, -1)),
                    ft.IconButton(icon=ft.Icons.ARROW_DOWNWARD, icon_size=16, on_click=lambda ev, i=idx: mover(i, 1)),
                ], spacing=0))
            col_crit.controls = filas

        def alternar(k, v):
            habilitados[k] = bool(v)

        def mover(i, d):
            j = i + d
            if 0 <= j < len(orden_crit):
                orden_crit[i], orden_crit[j] = orden_crit[j], orden_crit[i]
                pintar_criterios()
                page.update()

        pintar_criterios()
        bloque_reglas = ft.Column([
            ft.Row([tf_pv, tf_pe], spacing=8),
            ft.Text("Desempate del puntero de grupo (tras los puntos). Marca los criterios y ordénalos:",
                    size=12, color=COLOR_SUBTEXTO),
            col_crit,
        ], spacing=8)

        def guardar():
            nombre = tf_nombre.value.strip()
            if not nombre:
                raise ValueError("El nombre es obligatorio")
            if not dd_camp.value:
                raise ValueError("Debe seleccionar un campeonato")
            reglas = dict(
                modo_campeon=copa.modo_campeon if copa else "final_lideres",
                criterios_desempate=",".join(k for k in orden_crit if habilitados[k]),
                puntos_victoria=int(tf_pv.value or 3),
                puntos_empate=int(tf_pe.value or 1),
            )
            if copa:
                from backend.database.repositories import CopaRepository
                CopaRepository.actualizar(copa.id, nombre, int(dd_camp.value), copa.orden, copa.activo, color_sel["v"], **reglas)
            else:
                estado["campeonato_activo_id"] = int(dd_camp.value)
                nuevo_id = CopaService.crear_copa(nombre, int(dd_camp.value), color=color_sel["v"], es_master=True, **reglas)
                estado["copa_activa_id"] = nuevo_id
                estado["torneo_activo_id"] = None
                estado["jornada_activa_id"] = None
                estado["categoria_activa_id"] = None

        _modal_formulario("Editar Copa" if copa else "Nueva Copa", [ft.Column([tf_nombre, dd_camp, ft.Text("Color de la copa", size=12, color=COLOR_SUBTEXTO), fila_colores,
                                                                                     ft.Divider(height=1), bloque_reglas],
                                                                                    spacing=10, scroll=ft.ScrollMode.AUTO, height=420)], guardar, "Guardar" if copa else "Crear")

    def eliminar_copa(copa):
        def op():
            CopaService.eliminar_copa(copa.id, es_master=True)
            estado["copa_activa_id"] = None
            estado["torneo_activo_id"] = None
            estado["jornada_activa_id"] = None
            estado["categoria_activa_id"] = None
        _modal_eliminar("Eliminar Copa", f"¿Eliminar la copa '{copa.nombre}'? Solo es posible si no tiene torneos asociados.", op)

    def _chip_jerarquia(texto, es_activo_, on_select, on_edit=None, on_delete=None):
        color_txt = COLOR_TEXTO if es_activo_ else COLOR_SUBTEXTO
        fila = [ft.Text(texto, size=12, color=color_txt,
                        weight=ft.FontWeight.BOLD if es_activo_ else ft.FontWeight.NORMAL)]
        if es_master and on_edit:
            fila.append(ft.IconButton(icon=ft.Icons.EDIT, icon_color=COLOR_CELESTE, icon_size=14,
                                      tooltip="Editar", on_click=lambda ev: on_edit()))
        if es_master and on_delete:
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
        _chip_jerarquia(c.nombre, c.id == copa_activa_id, lambda cid=c.id: seleccionar_copa(cid))
        for c in copas_visibles
    ]
    if es_master:
        chips_anios.append(_chip_nuevo("Nuevo Año", modal_anio))
        chips_campeonatos.append(_chip_nuevo("Nuevo Campeonato", modal_campeonato))

    def _icono_accion(icono, color, tooltip, on_click):
        return ft.IconButton(icon=icono, icon_color=color, icon_size=18, tooltip=tooltip,
                             on_click=lambda ev: on_click())

    copa_sel = next((c for c in copas_visibles if c.id == copa_activa_id), None)
    acc_copa = []
    if es_master:
        acc_copa.append(_icono_accion(ft.Icons.ADD, COLOR_VERDE, "Nueva copa", modal_copa))
        if copa_sel:
            acc_copa.append(_icono_accion(ft.Icons.EDIT, COLOR_CELESTE, "Editar copa", lambda: modal_copa(copa_sel)))
            acc_copa.append(_icono_accion(ft.Icons.DELETE, COLOR_ROJO, "Eliminar copa", lambda: eliminar_copa(copa_sel)))

    def _menu_admin(items):
        """Agrupa acciones de administración en un menú desplegable."""
        return ft.PopupMenuButton(
            icon=ft.Icons.MORE_VERT, icon_color=COLOR_SUBTEXTO, tooltip="Administrar",
            items=[ft.PopupMenuItem(content=txt, icon=ico, on_click=lambda ev, f=f: f())
                   for txt, ico, f in items],
        )

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
        anio_por_id = {a.id: a.valor for a in anios}
        color_base_inicio = COLOR_CELESTE_BOTON
        tarjetas = []
        for c in campeonatos_visibles:
            es_ultimo = (c.id == campeonato_activo_id)
            fila = [
                ft.Icon(ft.Icons.MILITARY_TECH, color=COLOR_AMBAR if es_ultimo else COLOR_CELESTE, size=26),
                ft.Column([
                    ft.Text(c.nombre, size=15, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO),
                    ft.Text(str(anio_por_id.get(c.anio_id, "")), size=11, color=COLOR_SUBTEXTO),
                ], spacing=0, expand=True),
            ]
            fila.append(ft.Icon(ft.Icons.CHEVRON_RIGHT, color=COLOR_SUBTEXTO, size=22))
            tarjetas.append(ft.Container(
                content=ft.Row(fila, spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.Padding.symmetric(horizontal=14, vertical=10), border_radius=14,
                animate=ft.Animation(150),
                **estilo_pill_3d(color_base_inicio, es_ultimo),
                on_click=lambda ev, c=c: entrar_campeonato(c),
                ink=True,
                col={"xs": 12, "sm": 6, "md": 4},
            ))
        anio_sel = next((a for a in anios if a.id == anio_activo_id), None)
        camp_sel = next((c for c in campeonatos_visibles if c.id == campeonato_activo_id), None)
        acc_anio, acc_camp = [], []
        if es_master:
            acc_anio.append(_icono_accion(ft.Icons.ADD, COLOR_VERDE, "Nuevo año", modal_anio))
            if anio_sel:
                acc_anio.append(_icono_accion(ft.Icons.EDIT, COLOR_CELESTE, "Editar año", lambda: modal_anio(anio_sel)))
                acc_anio.append(_icono_accion(ft.Icons.DELETE, COLOR_ROJO, "Eliminar año", lambda: eliminar_anio(anio_sel)))
            acc_camp.append(_icono_accion(ft.Icons.ADD, COLOR_VERDE, "Nuevo campeonato", modal_campeonato))
            if camp_sel:
                acc_camp.append(_icono_accion(ft.Icons.EDIT, COLOR_CELESTE, "Editar campeonato", lambda: modal_campeonato(camp_sel)))
                acc_camp.append(_icono_accion(ft.Icons.DELETE, COLOR_ROJO, "Eliminar campeonato", lambda: eliminar_campeonato(camp_sel)))

        def _etiqueta(t):
            return ft.Text(t, size=11, weight=ft.FontWeight.BOLD, color=COLOR_SUBTEXTO)

        pills_anios = [
            ft.Container(
                content=ft.Text(str(a.valor), size=12, color=COLOR_TEXTO if a.id == anio_activo_id else COLOR_SUBTEXTO,
                                weight=ft.FontWeight.BOLD if a.id == anio_activo_id else ft.FontWeight.NORMAL),
                padding=ft.Padding.symmetric(horizontal=16, vertical=8), border_radius=20,
                animate=ft.Animation(150),
                **estilo_pill_3d(COLOR_CELESTE_BOTON, a.id == anio_activo_id),
                on_click=lambda ev, aid=a.id: seleccionar_anio(aid), ink=True,
            ) for a in anios
        ]
        if not anios or not campeonatos_visibles:
            msg = ("No hay años creados. Activa el modo Administrar y crea el primero." if not anios else
                   "No hay campeonatos en este año. Crea el primero desde el modo Administrar.")
            vacio = ft.Column([
                ft.Icon(ft.Icons.EMOJI_EVENTS_OUTLINED, size=40, color=COLOR_SUBTEXTO),
                ft.Text(msg, color=COLOR_SUBTEXTO, text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8)
        else:
            vacio = None
        return ft.Container(
            content=ft.Column([
                ft.Text("¿Qué campeonato quieres ver?", size=18, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO),
                _etiqueta("AÑO"),
                ft.Row(pills_anios, wrap=True, spacing=8, run_spacing=6),
                ft.Row(acc_anio, spacing=0) if acc_anio else ft.Container(height=0),
                ft.Divider(color=COLOR_BORDE, height=1),
                _etiqueta("CAMPEONATO"),
                vacio if vacio else ft.Container(height=0),
                ft.ResponsiveRow(tarjetas, spacing=10, run_spacing=10),
                ft.Row(acc_camp, spacing=0) if acc_camp else ft.Container(height=0),
            ], spacing=12),
            padding=14, bgcolor=COLOR_TARJETA, border_radius=14, border=ft.Border.all(1, COLOR_BORDE),
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

    acc_torneo = []
    if es_master:
        acc_torneo.append(_icono_accion(ft.Icons.ADD, COLOR_VERDE, "Nuevo torneo", lambda: abrir_modal_nuevo_torneo(None)))
        torneo_obj = next((t for t in torneos if t.id == torneo_activo_id), None)
        if torneo_obj:
            acc_torneo.append(_icono_accion(
                ft.Icons.EDIT, COLOR_CELESTE, "Editar torneo",
                lambda: abrir_dialogo_editar_torneo(torneo_obj)))
            acc_torneo.append(_icono_accion(ft.Icons.DELETE, COLOR_ROJO, "Eliminar torneo",
                                            lambda: abrir_dialogo_eliminar_torneo(None)))

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
                ft.Text("Crea una nueva categoría (los grupos se crean manualmente)."),
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

    acc_cat = []
    if es_organizador and jornada_activa_id:
        acc_cat.append(_icono_accion(ft.Icons.ADD, COLOR_VERDE, "Nueva categoría", lambda: abrir_modal_nueva_cat(None)))
    if es_organizador and cat_activa_id:
        def eliminar_categoria_activa():
            def op():
                TorneoService.eliminar_categoria(cat_activa_id, es_organizador=True)
                estado["categoria_activa_id"] = None
            _modal_eliminar("Eliminar Categoría", "¿Eliminar la categoría activa? Se eliminarán sus grupos y partidos.", op)
        acc_cat.append(_icono_accion(ft.Icons.DELETE, COLOR_ROJO, "Eliminar categoría", eliminar_categoria_activa))

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

    acc_jornada = []
    if es_organizador:
        acc_jornada.append(_icono_accion(ft.Icons.ADD, COLOR_VERDE, "Nueva jornada",
                                         lambda: on_crear_jornada(None) if on_crear_jornada else None))
        acc_jornada.append(_icono_accion(ft.Icons.SEARCH, COLOR_CELESTE, "Buscar jornada",
                                         lambda: on_buscar_jornada(None) if on_buscar_jornada else None))
        if jornada_activa_id:
            acc_jornada.append(_icono_accion(ft.Icons.DELETE, COLOR_ROJO, "Eliminar jornada",
                                             lambda: on_eliminar_jornada(None) if on_eliminar_jornada else None))

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

    # Agregar grupos reales
    for g_data in grupos_reales:
        nombre_grupo = g_data["grupo"].nombre
        grupo_id = g_data["grupo"].id
        es_g_activo = (nombre_grupo == grupo_filtro)

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

    grupo_activo_obj = next((g["grupo"] for g in grupos_reales if g["grupo"].nombre == grupo_filtro), None)
    acc_grupo = []
    if es_organizador and cat_activa_id and jornada_activa_id:
        if on_crear_grupo:
            acc_grupo.append(_icono_accion(ft.Icons.ADD, COLOR_VERDE, "Nuevo grupo", lambda: on_crear_grupo(None)))
        if grupo_activo_obj and on_editar_grupo:
            acc_grupo.append(_icono_accion(ft.Icons.EDIT, COLOR_CELESTE, "Editar grupo",
                                           lambda: on_editar_grupo(grupo_activo_obj.id)))
        if grupo_activo_obj and on_eliminar_grupo:
            acc_grupo.append(_icono_accion(ft.Icons.DELETE, COLOR_ROJO, "Eliminar grupo",
                                           lambda: on_eliminar_grupo(grupo_activo_obj.id)))

    # Modo menú ⋮: no dibuja nada, solo entrega las acciones permitidas por sección
    if acciones_out is not None:
        acc_campeonato = []
        if es_master:
            acc_campeonato.append(_icono_accion(ft.Icons.ADD, COLOR_VERDE, "Nuevo campeonato", modal_campeonato))
            camp_sel_m = next((c for c in campeonatos if c.id == campeonato_activo_id), None)
            if camp_sel_m:
                acc_campeonato.append(_icono_accion(ft.Icons.EDIT, COLOR_CELESTE, "Editar campeonato",
                                                    lambda: modal_campeonato(camp_sel_m)))
                acc_campeonato.append(_icono_accion(ft.Icons.DELETE, COLOR_ROJO, "Eliminar campeonato",
                                                    lambda: eliminar_campeonato(camp_sel_m)))
        acciones_out.update({"Campeonato": acc_campeonato, "Copa": acc_copa, "Torneo": acc_torneo,
                             "Jornada": acc_jornada, "Categoría": acc_cat, "Grupo": acc_grupo})
        return ft.Container(height=0)

    def _seccion(icono, titulo, chips, acciones=None):
        """Etiqueta, pills que se adaptan al ancho y, debajo, iconos de acción."""
        filas = [
            ft.Text(titulo.upper(), size=10, weight=ft.FontWeight.BOLD, color=COLOR_SUBTEXTO),
            ft.Row(list(chips), wrap=True, spacing=6, run_spacing=6, alignment=ft.MainAxisAlignment.START),
        ]
        if acciones:
            filas.append(ft.Row(list(acciones), spacing=0, alignment=ft.MainAxisAlignment.START))
        return ft.Column(filas, spacing=2, horizontal_alignment=ft.CrossAxisAlignment.START)

    # Cabecera compacta del campeonato: ‹ 2026 · Supercampeones
    camp_obj = next((c for c in campeonatos if c.id == campeonato_activo_id), None)
    anio_obj = next((a for a in anios if camp_obj and a.id == camp_obj.anio_id), None)
    titulo_camp = f"{anio_obj.valor if anio_obj else ''} · {camp_obj.nombre if camp_obj else 'Sin campeonato'}"
    cabecera_ctrls = [
        ft.IconButton(icon=ft.Icons.ARROW_BACK_IOS_NEW, icon_color=COLOR_CELESTE, icon_size=18,
                      tooltip="Cambiar de campeonato", on_click=volver_inicio),
        ft.Text(titulo_camp, size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO, expand=True,
                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
    ]
    if es_master and camp_obj:
        cabecera_ctrls.append(_menu_admin([
            ("Editar campeonato", ft.Icons.EDIT, lambda: modal_campeonato(camp_obj)),
            ("Eliminar campeonato", ft.Icons.DELETE, lambda: eliminar_campeonato(camp_obj)),
        ]))
    cabecera = ft.Row(cabecera_ctrls, spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    controles_admin = []

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

        for ch in (chips_copas + chips_torneos + chips_jornadas + chips_categorias + chips_grupos
                   ):
            if isinstance(ch, ft.Container):
                if ch.bgcolor == COLOR_CELESTE_BOTON:
                    for k, v in estilo_pill_3d(color_copa, True).items():
                        setattr(ch, k, v)
                    _texto_claro(ch.content)
                elif ch.bgcolor in (COLOR_TARJETA_SEGUNDARIA, COLOR_TARJETA):
                    for k, v in estilo_pill_3d(color_copa, False).items():
                        setattr(ch, k, v)
                    _texto_claro(ch.content)

    for ch in (chips_copas + chips_torneos + chips_jornadas + chips_categorias + chips_grupos
               ):
        if isinstance(ch, ft.Container):
            ch.border_radius = 20
            ch.animate = ft.Animation(150)

    return ft.Container(
        content=ft.Column([
            cabecera,
            ft.Divider(color=COLOR_BORDE, height=1),
            *controles_admin,
            _seccion(ft.Icons.LOCAL_BAR, "Copa", chips_copas, acc_copa),
            ft.Divider(color=COLOR_BORDE, height=1),
            _seccion(ft.Icons.EMOJI_EVENTS, "Torneo", chips_torneos, acc_torneo),
            ft.Divider(color=COLOR_BORDE, height=1),
            _seccion(ft.Icons.CALENDAR_TODAY, "Jornada", chips_jornadas, acc_jornada),
            ft.Divider(color=COLOR_BORDE, height=1),
            _seccion(ft.Icons.SCHOOL, "Categoría", chips_categorias, acc_cat),
            ft.Divider(color=COLOR_BORDE, height=1),
            _seccion(ft.Icons.GROUPS, "Grupo", chips_grupos, acc_grupo),
        ], spacing=8),
        padding=10,
        bgcolor=color_copa or COLOR_TARJETA,
        border_radius=10,
        border=ft.Border.all(1, COLOR_BORDE),
    )
