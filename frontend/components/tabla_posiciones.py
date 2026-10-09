import flet as ft
from typing import List
from config.constants import (
    COLOR_TARJETA, COLOR_BORDE, COLOR_CELESTE, COLOR_TEXTO, 
    COLOR_SUBTEXTO, COLOR_VERDE, COLOR_DORADO, COLOR_ROJO, COLOR_TARJETA_SEGUNDARIA
)
from backend.models.tabla import EstadisticaEquipo

def crear_tabla_posiciones(nombre_grupo: str, tabla: List[EstadisticaEquipo]) -> ft.Container:
    """
    Renderiza la tabla de posiciones oficial del grupo con estadísticas completas y líder destacado.
    """
    filas = []

    for idx, stat in enumerate(tabla, start=1):
        es_lider = (idx == 1 and stat.pj > 0)
        color_texto_fila = COLOR_DORADO if es_lider else COLOR_TEXTO
        weight_fila = ft.FontWeight.BOLD if es_lider else ft.FontWeight.NORMAL

        badge_pos = ft.Container(
            content=ft.Text(
                f"🥇 {idx}" if (es_lider) else str(idx),
                size=11,
                weight=ft.FontWeight.BOLD,
                color=COLOR_DORADO if es_lider else COLOR_SUBTEXTO,
            ),
            width=36
        )

        nombre_equipo = ft.Text(
            stat.equipo,
            size=12,
            weight=weight_fila,
            color=color_texto_fila,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

        dg_str = f"{stat.dg:+d}" if stat.dg != 0 else "0"
        color_dg = COLOR_VERDE if stat.dg > 0 else (COLOR_ROJO if stat.dg < 0 else COLOR_SUBTEXTO)

        filas.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(badge_pos),
                    ft.DataCell(nombre_equipo),
                    ft.DataCell(ft.Text(str(stat.pj), size=12, color=COLOR_SUBTEXTO)),
                    ft.DataCell(ft.Text(str(stat.pg), size=12, color=COLOR_TEXTO)),
                    ft.DataCell(ft.Text(str(stat.pe), size=12, color=COLOR_SUBTEXTO)),
                    ft.DataCell(ft.Text(str(stat.pp), size=12, color=COLOR_SUBTEXTO)),
                    ft.DataCell(ft.Text(str(stat.gf), size=12, color=COLOR_TEXTO)),
                    ft.DataCell(ft.Text(str(stat.gc), size=12, color=COLOR_SUBTEXTO)),
                    ft.DataCell(ft.Text(dg_str, size=12, weight=ft.FontWeight.BOLD, color=color_dg)),
                    ft.DataCell(
                        ft.Container(
                            content=ft.Text(
                                str(stat.pts),
                                size=13,
                                weight=ft.FontWeight.BOLD,
                                color=COLOR_CELESTE if not es_lider else COLOR_DORADO,
                            ),
                            bgcolor=COLOR_TARJETA_SEGUNDARIA if not es_lider else "#3B2D05",
                            padding=8,
                            border_radius=6,
                        )
                    ),
                ]
            )
        )

    tabla_widget = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("#", size=11, color=COLOR_SUBTEXTO, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Equipo", size=11, color=COLOR_SUBTEXTO, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("PJ", size=11, color=COLOR_SUBTEXTO, weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(ft.Text("PG", size=11, color=COLOR_SUBTEXTO, weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(ft.Text("PE", size=11, color=COLOR_SUBTEXTO, weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(ft.Text("PP", size=11, color=COLOR_SUBTEXTO, weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(ft.Text("GF", size=11, color=COLOR_SUBTEXTO, weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(ft.Text("GC", size=11, color=COLOR_SUBTEXTO, weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(ft.Text("DG", size=11, color=COLOR_SUBTEXTO, weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(ft.Text("Pts", size=12, color=COLOR_CELESTE, weight=ft.FontWeight.BOLD), numeric=True),
        ],
        rows=filas,
        column_spacing=12,
        horizontal_margin=8,
        heading_row_height=32,
        data_row_min_height=36,
        data_row_max_height=42,
    )

    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.LEADERBOARD, color=COLOR_CELESTE, size=18),
                ft.Text(f"Tabla de Posiciones - {nombre_grupo}", size=14, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO),
            ], spacing=8),
            ft.Divider(color=COLOR_BORDE, height=1),
            ft.ListView([tabla_widget]),
        ], spacing=8),
        padding=12,
        bgcolor=COLOR_TARJETA,
        border_radius=10,
        border=ft.Border.all(1, COLOR_BORDE),
    )
