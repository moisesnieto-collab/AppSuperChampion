import flet as ft
from typing import List, Callable
from config.constants import (
    COLOR_TARJETA, COLOR_BORDE, COLOR_CELESTE, COLOR_TEXTO,
    COLOR_SUBTEXTO, COLOR_VERDE, COLOR_ROJO, COLOR_AMBAR, COLOR_TARJETA_SEGUNDARIA
)
from backend.models.partido import Partido


def crear_lista_partidos(
    grupo_nombre: str,
    partidos: List[Partido],
    es_organizador: bool,
    on_guardar_marcador: Callable[[int, int, int], None],
    on_reiniciar_marcador: Callable[[int], None]
) -> ft.Container:
    """
    Renderiza la lista de partidos del grupo con marcadores.
    - Modo consulta: visualización solo lectura
    - Modo organizador: inputs editables + botón guardar
    """
    
    filas_partidos = []
    
    for partido in partidos:
        es_definicion = partido.es_definicion
        color_fondo = "#2D1B00" if es_definicion else None
        
        # Indicador de estado del partido
        if partido.jugado:
            estado_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color=COLOR_VERDE, size=16)
            estado_texto = "Jugado"
            estado_color = COLOR_VERDE
        else:
            estado_icon = ft.Icon(ft.Icons.SCHEDULE, color=COLOR_AMBAR, size=16)
            estado_texto = "Pendiente"
            estado_color = COLOR_AMBAR
        
        if es_definicion:
            estado_texto = "Definición"
            estado_color = "#F59E0B"
        
        # Modo consulta: visualización solo lectura
        if not es_organizador:
            fila_partido = ft.Container(
                content=ft.Column([
                    # Estado del partido (arriba)
                    ft.Container(
                        content=ft.Row([
                            estado_icon,
                            ft.Text(estado_texto, size=11, color=estado_color, weight=ft.FontWeight.BOLD),
                        ], spacing=6),
                        padding=4,
                    ),
                    # Equipos y marcador
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Text(
                                    partido.equipo_local,
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    color=COLOR_TEXTO,
                                    text_align=ft.TextAlign.RIGHT,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS
                                ),
                                expand=True
                            ),
                            ft.Container(
                                content=ft.Row([
                                    ft.Container(
                                        content=ft.Text(
                                            str(partido.goles_local),
                                            size=20,
                                            weight=ft.FontWeight.BOLD,
                                            color=COLOR_CELESTE
                                        ),
                                        width=35
                                    ),
                                    ft.Text("-", size=18, color=COLOR_SUBTEXTO),
                                    ft.Container(
                                        content=ft.Text(
                                            str(partido.goles_visita),
                                            size=20,
                                            weight=ft.FontWeight.BOLD,
                                            color=COLOR_CELESTE
                                        ),
                                        width=35
                                    ),
                                ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
                                padding=10,
                                bgcolor=COLOR_TARJETA_SEGUNDARIA,
                                border_radius=8,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    partido.equipo_visita,
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    color=COLOR_TEXTO,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS
                                ),
                                expand=True
                            ),
                        ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                    ),
                ], spacing=6),
                padding=10,
                bgcolor=color_fondo,
                border=ft.Border.all(1, COLOR_BORDE),
                border_radius=8,
            )
        else:
            # Modo organizador: inputs editables
            tf_goles_local = ft.TextField(
                value=str(partido.goles_local),
                width=50,
                text_align=ft.TextAlign.CENTER,
                text_size=16,
                keyboard_type=ft.KeyboardType.NUMBER,
                max_length=2
            )
            tf_goles_visita = ft.TextField(
                value=str(partido.goles_visita),
                width=50,
                text_align=ft.TextAlign.CENTER,
                text_size=16,
                keyboard_type=ft.KeyboardType.NUMBER,
                max_length=2
            )
            
            def guardar_marcador(e, p_id=partido.id, tf_loc=tf_goles_local, tf_vis=tf_goles_visita):
                try:
                    g_loc = int(tf_loc.value) if tf_loc.value else 0
                    g_vis = int(tf_vis.value) if tf_vis.value else 0
                    on_guardar_marcador(p_id, g_loc, g_vis)
                except ValueError:
                    pass
            
            def reiniciar_marcador(e, p_id=partido.id):
                on_reiniciar_marcador(p_id)
            
            fila_partido = ft.Container(
                content=ft.Column([
                    # Estado del partido (arriba)
                    ft.Container(
                        content=ft.Row([
                            estado_icon,
                            ft.Text(estado_texto, size=11, color=estado_color, weight=ft.FontWeight.BOLD),
                        ], spacing=6),
                        padding=4,
                    ),
                    # Equipos y marcador
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Text(
                                    partido.equipo_local,
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    color=COLOR_TEXTO,
                                    text_align=ft.TextAlign.RIGHT,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS
                                ),
                                expand=True
                            ),
                            ft.Container(
                                content=ft.Row([
                                    tf_goles_local,
                                    ft.Text("-", size=18, color=COLOR_SUBTEXTO),
                                    tf_goles_visita,
                                ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
                                padding=10,
                                bgcolor=COLOR_TARJETA_SEGUNDARIA,
                                border_radius=8,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    partido.equipo_visita,
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    color=COLOR_TEXTO,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS
                                ),
                                expand=True
                            ),
                        ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                    ),
                    # Botones de acción (abajo)
                    ft.Container(
                        content=ft.Row([
                            ft.FilledButton(
                                "💾 Guardar",
                                bgcolor=COLOR_VERDE,
                                color=COLOR_TEXTO,
                                expand=True,
                                on_click=guardar_marcador
                            ),
                            ft.IconButton(
                                icon=ft.Icons.REFRESH,
                                icon_color=COLOR_ROJO,
                                icon_size=20,
                                tooltip="Reiniciar marcador",
                                on_click=reiniciar_marcador
                            )
                        ], spacing=8),
                        padding=4,
                    ),
                ], spacing=6),
                padding=10,
                bgcolor=color_fondo,
                border=ft.Border.all(1, COLOR_CELESTE),
                border_radius=8,
            )
        
        filas_partidos.append(fila_partido)
    
    # Si no hay partidos
    if not filas_partidos:
        filas_partidos.append(
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.EVENT_BUSY, size=32, color=COLOR_SUBTEXTO),
                    ft.Text("No hay partidos programados", size=12, color=COLOR_SUBTEXTO),
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20
            )
        )
    
    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.SPORTS_SOCCER, color=COLOR_CELESTE, size=18),
                ft.Text(
                    f"Partidos - {grupo_nombre}",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=COLOR_TEXTO
                ),
                ft.Container(
                    content=ft.Text(
                        f"{len(partidos)} partidos",
                        size=11,
                        color=COLOR_SUBTEXTO
                    ),
                    bgcolor=COLOR_TARJETA_SEGUNDARIA,
                    padding=8,
                    border_radius=12
                )
            ], spacing=8),
            ft.Divider(color=COLOR_BORDE, height=1),
            ft.Column(filas_partidos, spacing=8),
        ], spacing=8),
        padding=12,
        bgcolor=COLOR_TARJETA,
        border_radius=10,
        border=ft.Border.all(1, COLOR_BORDE)
    )
