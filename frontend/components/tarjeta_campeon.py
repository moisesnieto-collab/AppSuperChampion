import flet as ft
from typing import Callable, Optional
from config.constants import (
    COLOR_TARJETA, COLOR_BORDE, COLOR_CELESTE, COLOR_TEXTO,
    COLOR_SUBTEXTO, COLOR_VERDE, COLOR_ROJO, COLOR_AMBAR, COLOR_DORADO,
    COLOR_TARJETA_SEGUNDARIA
)


def crear_tarjeta_campeon(
    estado_campeon: dict,
    es_organizador: bool,
    on_generar_desempate: Optional[Callable[[int, str, str], None]] = None,
    on_generar_final: Optional[Callable[[], None]] = None
) -> ft.Container:
    """
    Renderiza la tarjeta de estado del campeonato con indicador de campeón o necesidad de desempate.
    """
    
    estado = estado_campeon.get("estado", "SIN_DATOS")
    
    # Determinar contenido según el estado
    if estado == "CAMPEON_DEFINIDO":
        campeon = estado_campeon.get("campeon", "Desconocido")
        motivo = estado_campeon.get("motivo", "")
        
        contenido = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.EMOJI_EVENTS, color=COLOR_DORADO, size=32),
                ft.Text("¡CAMPEÓN DEFINIDO!", size=18, weight=ft.FontWeight.BOLD, color=COLOR_DORADO),
            ], spacing=12),
            ft.Divider(color=COLOR_BORDE, height=1),
            ft.Container(
                content=ft.Text(
                    campeon.upper(),
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=COLOR_TEXTO,
                    text_align=ft.TextAlign.CENTER
                ),
                padding=16,
                bgcolor="#3B2D05",
                border_radius=12,
                border=ft.border.all(2, COLOR_DORADO)
            ),
            ft.Text(
                motivo,
                size=12,
                color=COLOR_SUBTEXTO,
                text_align=ft.TextAlign.CENTER,
                italic=True
            ),
        ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        color_borde = COLOR_DORADO
        icono_estado = ft.Icons.VERIFIED
        color_icono = COLOR_DORADO
        
    elif estado == "DESEMPATE_PENDIENTE":
        equipo1 = estado_campeon.get("equipo1", "")
        equipo2 = estado_campeon.get("equipo2", "")
        motivo = estado_campeon.get("motivo", "")
        partido_id = estado_campeon.get("partido_id")
        
        contenido = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.SPORTS, color=COLOR_AMBAR, size=28),
                ft.Text("PARTIDO DE DESEMPATE", size=16, weight=ft.FontWeight.BOLD, color=COLOR_AMBAR),
            ], spacing=12),
            ft.Divider(color=COLOR_BORDE, height=1),
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Text(
                            equipo1,
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=COLOR_TEXTO,
                            text_align=ft.TextAlign.CENTER
                        ),
                        expand=True
                    ),
                    ft.Text("VS", size=14, weight=ft.FontWeight.BOLD, color=COLOR_SUBTEXTO),
                    ft.Container(
                        content=ft.Text(
                            equipo2,
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=COLOR_TEXTO,
                            text_align=ft.TextAlign.CENTER
                        ),
                        expand=True
                    ),
                ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                padding=12,
                bgcolor=COLOR_TARJETA_SEGUNDARIA,
                border_radius=8,
            ),
            ft.Text(
                motivo,
                size=12,
                color=COLOR_SUBTEXTO,
                text_align=ft.TextAlign.CENTER
            ),
        ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        color_borde = COLOR_AMBAR
        icono_estado = ft.Icons.PENDING
        color_icono = COLOR_AMBAR
        
    elif estado == "EMPATE_REQUIERE_DESEMPATE":
        equipo1 = estado_campeon.get("equipo1", "")
        equipo2 = estado_campeon.get("equipo2", "")
        motivo = estado_campeon.get("motivo", "")
        grupo_id = estado_campeon.get("grupo_id")
        
        contenido = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.WARNING, color=COLOR_ROJO, size=28),
                ft.Text("EMPATE EN 1° LUGAR", size=16, weight=ft.FontWeight.BOLD, color=COLOR_ROJO),
            ], spacing=12),
            ft.Divider(color=COLOR_BORDE, height=1),
            ft.Text(
                motivo,
                size=12,
                color=COLOR_SUBTEXTO,
                text_align=ft.TextAlign.CENTER
            ),
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Text(
                            equipo1,
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=COLOR_TEXTO
                        ),
                        expand=True
                    ),
                    ft.Text("=", size=16, color=COLOR_ROJO),
                    ft.Container(
                        content=ft.Text(
                            equipo2,
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=COLOR_TEXTO
                        ),
                        expand=True
                    ),
                ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                padding=12,
                bgcolor=COLOR_TARJETA_SEGUNDARIA,
                border_radius=8,
            ),
        ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        # Botón para generar partido de desempate (solo organizador)
        if es_organizador and on_generar_desempate and grupo_id:
            contenido.controls.append(
                ft.FilledButton(
                    "⚽ Generar Partido de Desempate",
                    bgcolor=COLOR_VERDE,
                    color=COLOR_TEXTO,
                    on_click=lambda e: on_generar_desempate(grupo_id, equipo1, equipo2)
                )
            )
        
        color_borde = COLOR_ROJO
        icono_estado = ft.Ions.ERROR_OUTLINE
        color_icono = COLOR_ROJO
        
    elif estado == "EN_CURSO":
        puntero = estado_campeon.get("puntero_actual", "Sin definir")
        partidos_jugados = estado_campeon.get("partidos_jugados", "0/0")
        motivo = estado_campeon.get("motivo", "")

        # Parsear partidos jugados para calcular progreso
        try:
            jugados, total = map(int, partidos_jugados.split('/'))
            progreso = (jugados / total * 100) if total > 0 else 0
        except:
            progreso = 0

        contenido = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.HOURGLASS_EMPTY, color=COLOR_SUBTEXTO, size=28),
                ft.Text("CAMPEÓN NO DEFINIDO", size=16, weight=ft.FontWeight.BOLD, color=COLOR_SUBTEXTO),
            ], spacing=12),
            ft.Divider(color=COLOR_BORDE, height=1),
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "El torneo aún está en curso",
                        size=13,
                        color=COLOR_SUBTEXTO,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Text(
                        "Se deben jugar TODOS los partidos para definir el campeón",
                        size=11,
                        color=COLOR_SUBTEXTO,
                        text_align=ft.TextAlign.CENTER,
                        italic=True
                    ),
                    ft.Container(height=8),
                    ft.ProgressBar(
                        value=progreso / 100,
                        bgcolor=COLOR_BORDE,
                        color=COLOR_CELESTE,
                        width=200,
                        height=8,
                        border_radius=4
                    ),
                    ft.Text(
                        f"Progreso: {partidos_jugados} partidos",
                        size=11,
                        color=COLOR_SUBTEXTO,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(height=8),
                    ft.Row([
                        ft.Text("Puntero actual:", size=11, color=COLOR_SUBTEXTO),
                        ft.Text(
                            puntero if puntero else "Por definir",
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=COLOR_TEXTO
                        ),
                    ], spacing=4),
                ], spacing=4),
                padding=12,
                bgcolor=COLOR_TARJETA_SEGUNDARIA,
                border_radius=8,
            ),
            ft.Text(
                motivo,
                size=11,
                color=COLOR_SUBTEXTO,
                text_align=ft.TextAlign.CENTER,
                italic=True
            ),
        ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        color_borde = COLOR_BORDE
        icono_estado = ft.Icons.HOURGLASS_EMPTY
        color_icono = COLOR_SUBTEXTO
        
    elif estado == "SIN_DATOS":
        contenido = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.INFO_OUTLINE, color=COLOR_SUBTEXTO, size=24),
                ft.Text("SIN DATOS", size=16, weight=ft.FontWeight.BOLD, color=COLOR_SUBTEXTO),
            ], spacing=12),
            ft.Text(
                "No hay información disponible del torneo.",
                size=12,
                color=COLOR_SUBTEXTO,
                text_align=ft.TextAlign.CENTER
            ),
        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        color_borde = COLOR_BORDE
        icono_estado = ft.Icons.INFO_OUTLINE
        color_icono = COLOR_SUBTEXTO
        
    else:
        # Estado desconocido
        contenido = ft.Column([
            ft.Text(
                f"Estado: {estado}",
                size=14,
                color=COLOR_SUBTEXTO
            ),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        color_borde = COLOR_BORDE
        icono_estado = ft.Icons.HELP_OUTLINE
        color_icono = COLOR_SUBTEXTO
    
    # Botón para generar final del Día 2 (solo si estamos en Día 2 y es organizador)
    if es_organizador and on_generar_final and estado in ["CAMPEON_DEFINIDO", "EN_CURSO"]:
        # Verificar si estamos en Día 2 (esto se puede inferir del contexto)
        # Por ahora, agregamos el botón condicionalmente
        pass
    
    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(icono_estado, color=color_icono, size=20),
                ft.Text("Estado del Torneo", size=14, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO),
            ], spacing=8),
            ft.Divider(color=COLOR_BORDE, height=1),
            contenido,
        ], spacing=10),
        padding=16,
        bgcolor=COLOR_TARJETA,
        border_radius=10,
        border=ft.border.all(2, color_borde)
    )
