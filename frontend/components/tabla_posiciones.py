import flet as ft
from typing import List, Optional
from config.constants import (
    COLOR_TARJETA, COLOR_BORDE, COLOR_CELESTE, COLOR_TEXTO, 
    COLOR_SUBTEXTO, COLOR_VERDE, COLOR_DORADO, COLOR_ROJO, COLOR_TARJETA_SEGUNDARIA,
    oscurecer_color
)
from backend.models.tabla import EstadisticaEquipo

def crear_tabla_posiciones(nombre_grupo: str, tabla: List[EstadisticaEquipo], color_copa: Optional[str] = None,
                           compacto: bool = False) -> ft.Container:
    """
    Tabla de posiciones responsiva hecha con filas. En modo compacto (móvil) oculta PG, PE, PP, GF y GC.
    """
    bg_tarjeta = color_copa or COLOR_TARJETA
    bg_secundaria = oscurecer_color(color_copa, 0.30) if color_copa else COLOR_TARJETA_SEGUNDARIA

    def celda(txt, w, color=COLOR_SUBTEXTO, bold=False, size=12):
        return ft.Container(
            content=ft.Text(txt, size=size, color=color, text_align=ft.TextAlign.CENTER,
                            weight=ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL),
            width=w, alignment=ft.Alignment.CENTER,
        )

    def fila_cabecera():
        ctrls = [celda("#", 36, bold=True, size=11),
                 ft.Text("Equipo", size=11, color=COLOR_SUBTEXTO, weight=ft.FontWeight.BOLD, expand=True),
                 celda("PJ", 28, bold=True, size=11)]
        if not compacto:
            for t in ("PG", "PE", "PP", "GF", "GC"):
                ctrls.append(celda(t, 28, bold=True, size=11))
        ctrls.append(celda("DG", 32, bold=True, size=11))
        ctrls.append(celda("Pts", 40, color=COLOR_CELESTE, bold=True, size=11))
        return ft.Row(ctrls, spacing=2)

    filas = []
    for idx, stat in enumerate(tabla, start=1):
        es_lider = (idx == 1 and stat.pj > 0)
        color_texto_fila = COLOR_DORADO if es_lider else COLOR_TEXTO
        weight_fila = ft.FontWeight.BOLD if es_lider else ft.FontWeight.NORMAL

        badge_pos = ft.Container(
            content=ft.Text(
                f"🥇 {idx}" if es_lider else str(idx),
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
            max_lines=1,
            expand=True,
        )

        dg_str = f"{stat.dg:+d}" if stat.dg != 0 else "0"
        color_dg = COLOR_VERDE if stat.dg > 0 else (COLOR_ROJO if stat.dg < 0 else COLOR_SUBTEXTO)

        ctrls = [badge_pos, nombre_equipo, celda(str(stat.pj), 28)]
        if not compacto:
            ctrls += [celda(str(stat.pg), 28, COLOR_TEXTO), celda(str(stat.pe), 28),
                      celda(str(stat.pp), 28), celda(str(stat.gf), 28, COLOR_TEXTO),
                      celda(str(stat.gc), 28)]
        ctrls.append(celda(dg_str, 32, color_dg, True))
        ctrls.append(ft.Container(
            content=ft.Text(str(stat.pts), size=13, weight=ft.FontWeight.BOLD,
                            color=COLOR_CELESTE if not es_lider else COLOR_DORADO,
                            text_align=ft.TextAlign.CENTER),
            bgcolor=bg_secundaria if not es_lider else "#3B2D05",
            width=40, padding=ft.Padding.symmetric(vertical=6), border_radius=6,
            alignment=ft.Alignment.CENTER,
        ))
        filas.append(ft.Row(ctrls, spacing=2, vertical_alignment=ft.CrossAxisAlignment.CENTER))

    extra = []
    if compacto:
        extra.append(ft.Text("PJ jugados · DG dif. goles · Pts puntos", size=10, color=COLOR_SUBTEXTO))

    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.LEADERBOARD, color=COLOR_CELESTE, size=18),
                ft.Text(f"Tabla de Posiciones - {nombre_grupo}", size=14, weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXTO, expand=True, overflow=ft.TextOverflow.ELLIPSIS),
            ], spacing=8),
            ft.Divider(color=COLOR_BORDE, height=1),
            fila_cabecera(),
            *filas,
            *extra,
        ], spacing=6),
        padding=12,
        bgcolor=bg_tarjeta,
        border_radius=10,
        border=ft.Border.all(1, COLOR_BORDE),
    )
