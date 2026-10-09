import flet as ft
from config.constants import (
    COLOR_TARJETA, COLOR_BORDE, COLOR_CELESTE, COLOR_CELESTE_BOTON,
    COLOR_TEXTO, COLOR_SUBTEXTO, COLOR_VERDE, COLOR_AMBAR, COLOR_ROJO, COLOR_DORADO
)
from backend.services.torneo_service import TorneoService

def crear_header(estado: dict, page: ft.Page, on_cambio_rol, on_abrir_dialogo_pin=None) -> ft.Container:
    """
    Crea el Header principal de AppSuperChampion con indicador de rol y diálogo de PIN.
    """
    es_organizador = estado.get("es_organizador", False)

    def cerrar_sesion_organizador(e):
        estado["es_organizador"] = False
        on_cambio_rol()
        page.snack_bar = ft.SnackBar(
            content=ft.Text("👁️ Modo Consulta activado."),
            bgcolor=COLOR_AMBAR,
            duration=2500
        )
        page.snack_bar.open = True
        page.update()

    # Widget de Rol
    if es_organizador:
        badge_rol = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, color=COLOR_VERDE, size=16),
                ft.Text("Mesa de Control (Organizador)", size=12, weight=ft.FontWeight.BOLD, color=COLOR_VERDE),
                ft.IconButton(
                    icon=ft.Icons.LOGOUT,
                    icon_color=COLOR_ROJO,
                    icon_size=16,
                    tooltip="Cerrar Modo Organizador",
                    on_click=cerrar_sesion_organizador
                )
            ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=COLOR_TARJETA,
            border=ft.Border.all(1, COLOR_VERDE),
            padding=8,
            border_radius=8,
        )
    else:
        badge_rol = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.VISIBILITY, color=COLOR_AMBAR, size=15),
                ft.Text("Modo Consulta", size=12, weight=ft.FontWeight.BOLD, color=COLOR_AMBAR),
                ft.IconButton(
                    icon=ft.Icons.LOCK,
                    icon_color=COLOR_CELESTE,
                    tooltip="Acceso Organizador",
                    on_click=on_abrir_dialogo_pin if on_abrir_dialogo_pin else lambda e: None,
                )
            ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            padding=6,
        )

    return ft.Container(
        content=ft.ResponsiveRow([
            ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.EMOJI_EVENTS, color=COLOR_DORADO, size=26),
                    ft.Text(
                        "SuperChampion 🏆",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXTO
                    ),
                ], spacing=8),
                ft.Text(
                    "Gestión y Marcadores en Vivo por Categorías",
                    size=11,
                    color=COLOR_SUBTEXTO
                ),
            ], col={"xs": 12, "sm": 7}),
            ft.Container(
                content=badge_rol,
                col={"xs": 12, "sm": 5}
            ),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=12,
        bgcolor=COLOR_TARJETA,
        border=ft.Border.all(1, COLOR_BORDE),
    )
