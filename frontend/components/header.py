import flet as ft
from config.constants import (
    COLOR_TARJETA, COLOR_BORDE, COLOR_CELESTE, COLOR_CELESTE_BOTON,
    COLOR_TEXTO, COLOR_SUBTEXTO, COLOR_VERDE, COLOR_AMBAR, COLOR_ROJO, COLOR_DORADO
)
from backend.services.torneo_service import TorneoService

def crear_header(estado: dict, page: ft.Page, on_cambio_rol, on_abrir_dialogo_pin=None,
                 color_copa=None, compacto: bool = False) -> ft.Container:
    """
    Crea el Header principal de AppSuperChampion con indicador de rol y diálogo de PIN.
    """
    es_organizador = estado.get("es_organizador", False)

    def cerrar_sesion_organizador(e):
        estado["es_organizador"] = False
        estado["modo_admin"] = False
        on_cambio_rol()
        page.snack_bar = ft.SnackBar(
            content=ft.Text("👁️ Modo Consulta activado."),
            bgcolor=COLOR_AMBAR,
            duration=2500
        )
        page.snack_bar.open = True
        page.update()

    def alternar_modo_admin(e):
        estado["modo_admin"] = not estado.get("modo_admin", False)
        on_cambio_rol()

    modo_admin = estado.get("modo_admin", False)

    # Widget de Rol
    if es_organizador:
        badge_rol = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, color=COLOR_VERDE, size=16),
                ft.Text("Mesa de Control (Organizador)", size=12, weight=ft.FontWeight.BOLD, color=COLOR_VERDE),
                ft.IconButton(
                    icon=ft.Icons.EDIT if not modo_admin else ft.Icons.EDIT_OFF,
                    icon_color=COLOR_AMBAR if modo_admin else COLOR_CELESTE,
                    icon_size=18,
                    tooltip="Salir de Administrar" if modo_admin else "Administrar (crear, editar, eliminar)",
                    on_click=alternar_modo_admin
                ),
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

    titulo = [ft.Row([
        ft.Icon(ft.Icons.EMOJI_EVENTS, color=COLOR_DORADO, size=18 if compacto else 26),
        ft.Text(
            "CampeonatosLive 🏆",
            size=15 if compacto else 20,
            weight=ft.FontWeight.BOLD,
            color=COLOR_TEXTO
        ),
    ], spacing=8)]
    if not compacto:
        titulo.append(ft.Text(
            "Gestión y Marcadores en Vivo por Categorías",
            size=11,
            color=COLOR_SUBTEXTO
        ))

    return ft.Container(
        content=ft.ResponsiveRow([
            ft.Column(titulo, spacing=2, col={"xs": 12, "sm": 7}),
            ft.Container(
                content=badge_rol,
                col={"xs": 12, "sm": 5}
            ),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=4 if compacto else 12,
        bgcolor=color_copa or COLOR_TARJETA,
        border=ft.Border.all(1, COLOR_BORDE),
    )
