"""
Constantes de estilos, paleta de colores oscuros y opciones de torneo para AppSuperChampion.
"""

# Paleta de colores Dark Theme
COLOR_FONDO = "#0A0E17"
COLOR_TARJETA = "#111827"
COLOR_TARJETA_SEGUNDARIA = "#1F2937"
COLOR_BORDE = "#374151"
COLOR_BORDE_ACTIVO = "#38BDF8"

# Tokens del rediseño (FLET_REDISENO_SPEC.md)
BG = "#0B1020"
SURFACE = "#121A2B"
SURFACE_2 = "#141B2D"
BORDER = "#1E2740"
BORDER_2 = "#2A3350"
TEXT = "#F1F4FA"
TEXT_2 = "#C5CEE0"
MUTED = "#9AA6BD"
MUTED_2 = "#8793AB"
LIVE = "#FF7A7A"
OK = "#3DD598"
GOLD = "#FBBF24"
NAV_BG = "#0F1526"
COPA_THEMES = [
    {"solid": "#1B7F53", "bright": "#3DD598"},
    {"solid": "#B02E6B", "bright": "#F472B6"},
    {"solid": "#2563EB", "bright": "#60A5FA"},
    {"solid": "#B45309", "bright": "#FBBF24"},
]
RADIO_SEGMENTO, RADIO_CATEGORIA, RADIO_TARJETA, RADIO_COPA, RADIO_SHEET = 9, 12, 14, 22, 20
ESPACIADO = (8, 12, 16, 24)

# Acentos y Estados
COLOR_CELESTE = "#38BDF8"
COLOR_CELESTE_BOTON = "#0284C7"
COLOR_TEXTO = "#F9FAFB"
COLOR_SUBTEXTO = "#9CA3AF"
COLOR_VERDE = "#10B981"
COLOR_ROJO = "#EF4444"
COLOR_AMBAR = "#F59E0B"
COLOR_DORADO = "#FBBF24"
COLOR_GRIS_CLARO = "#4B5563"

# Categorías por defecto
CATEGORIAS_DEFAULT = [
    "1° Básico",
    "2° Básico",
    "3° Básico",
    "4° Básico",
    "5° Básico",
    "6° Básico",
]

# Días por defecto
DIAS_DEFAULT = ["Día 1", "Día 2"]

# Grupos por defecto
GRUPOS_DEFAULT = ["Grupo A", "Grupo B"]

# PIN por defecto para modo Organizador / Mesa de Control
PIN_ORGANIZADOR_DEFAULT = "1234"


def mezclar_color(hexa: str, f: float) -> str:
    """Mezcla un color hexadecimal con blanco según factor f (0 a 1)."""
    h = hexa.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02X%02X%02X" % tuple(int(c + (255 - c) * f) for c in (r, g, b))


def estilo_pill_3d(color_base: str, activo: bool) -> dict:
    """Atributos de Container con relieve 3D (degradado, borde y sombra) para pills y pestañas."""
    import flet as ft
    if activo:
        return dict(
            bgcolor=mezclar_color(color_base, 0.30),
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_CENTER, end=ft.Alignment.BOTTOM_CENTER,
                colors=[mezclar_color(color_base, 0.50), mezclar_color(color_base, 0.20)],
            ),
            border=ft.Border.all(1, mezclar_color(color_base, 0.70)),
            shadow=ft.BoxShadow(blur_radius=6, offset=ft.Offset(0, 3), color="#99000000"),
        )
    return dict(
        bgcolor=oscurecer_color(color_base, 0.30),
        gradient=None,
        border=ft.Border.all(1, mezclar_color(color_base, 0.10)),
        shadow=ft.BoxShadow(blur_radius=2, offset=ft.Offset(0, 1), color="#66000000"),
    )


def oscurecer_color(hexa: str, f: float) -> str:
    """Oscurece un color hexadecimal según factor f (0 a 1)."""
    h = hexa.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02X%02X%02X" % tuple(int(c * (1 - f)) for c in (r, g, b))
