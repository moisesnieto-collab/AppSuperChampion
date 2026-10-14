import json
import os
from typing import Optional, Tuple

_ARCHIVO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".ultima_seleccion.json")


def guardar_ultima_seleccion(anio_id: int, campeonato_id: int) -> None:
    """Guarda el último Año/Campeonato elegido para entrar directo la próxima vez."""
    try:
        with open(_ARCHIVO, "w", encoding="utf-8") as f:
            json.dump({"anio_id": anio_id, "campeonato_id": campeonato_id}, f)
    except OSError:
        pass


def cargar_ultima_seleccion() -> Tuple[Optional[int], Optional[int]]:
    try:
        with open(_ARCHIVO, "r", encoding="utf-8") as f:
            datos = json.load(f)
        return datos.get("anio_id"), datos.get("campeonato_id")
    except (OSError, ValueError):
        return None, None


def borrar_ultima_seleccion() -> None:
    try:
        os.remove(_ARCHIVO)
    except OSError:
        pass


_CLAVES = ("copa_activa_id", "torneo_activo_id", "jornada_activa_id", "categoria_activa_id", "grupo_filtro", "tab_contenido")


def guardar_seleccion_completa(estado: dict) -> None:
    """Guarda año, campeonato, copa, torneo, jornada, categoría, grupo y pestaña."""
    datos = {"anio_id": estado.get("anio_activo_id"), "campeonato_id": estado.get("campeonato_activo_id")}
    datos.update({k: estado.get(k) for k in _CLAVES})
    try:
        with open(_ARCHIVO, "w", encoding="utf-8") as f:
            json.dump(datos, f)
    except OSError:
        pass


def cargar_seleccion_completa() -> dict:
    try:
        with open(_ARCHIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}
