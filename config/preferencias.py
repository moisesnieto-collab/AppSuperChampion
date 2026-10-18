import json
import os
from typing import Optional, Tuple

_KEY = "ultima_seleccion"
_prefs = None  # SharedPreferences por usuario (navegador) cuando la app corre en web
_page = None


def configurar(page) -> None:
    """En web guarda en el navegador de cada usuario; en escritorio usa el archivo local."""
    global _prefs, _page
    if not getattr(page, "web", False):
        return
    import flet as ft
    _page = page
    _prefs = ft.SharedPreferences()
    page.services.append(_prefs)


async def _seguro(fn, *args):
    """Ejecuta una llamada a SharedPreferences sin propagar errores (evita trazas en el log)."""
    try:
        return await fn(*args)
    except Exception:
        return None


def _leer() -> dict:
    if _prefs is not None:
        try:
            raw = _page.run_task(_seguro, _prefs.get, _KEY).result(timeout=5)
            return json.loads(raw) if raw else {}
        except Exception:
            return {}
    try:
        with open(_ARCHIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _escribir(datos: dict) -> None:
    if _prefs is not None:
        try:
            _page.run_task(_seguro, _prefs.set, _KEY, json.dumps(datos))
        except Exception:
            pass
        return
    try:
        with open(_ARCHIVO, "w", encoding="utf-8") as f:
            json.dump(datos, f)
    except OSError:
        pass


_ARCHIVO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".ultima_seleccion.json")


def guardar_ultima_seleccion(anio_id: int, campeonato_id: int) -> None:
    """Guarda el último Año/Campeonato elegido para entrar directo la próxima vez."""
    _escribir({"anio_id": anio_id, "campeonato_id": campeonato_id})


def cargar_ultima_seleccion() -> Tuple[Optional[int], Optional[int]]:
    datos = _leer()
    return datos.get("anio_id"), datos.get("campeonato_id")


def borrar_ultima_seleccion() -> None:
    if _prefs is not None:
        try:
            _page.run_task(_seguro, _prefs.remove, _KEY)
        except Exception:
            pass
        return
    try:
        os.remove(_ARCHIVO)
    except OSError:
        pass


_CLAVES = ("copa_activa_id", "torneo_activo_id", "jornada_activa_id", "categoria_activa_id", "grupo_filtro", "tab_contenido")


def guardar_seleccion_completa(estado: dict) -> None:
    """Guarda año, campeonato, copa, torneo, jornada, categoría, grupo y pestaña."""
    datos = {"anio_id": estado.get("anio_activo_id"), "campeonato_id": estado.get("campeonato_activo_id")}
    datos.update({k: estado.get(k) for k in _CLAVES})
    _escribir(datos)


def cargar_seleccion_completa() -> dict:
    return _leer()
