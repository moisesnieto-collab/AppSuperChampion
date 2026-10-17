"""Publica datos.json en R2 automáticamente tras cada escritura del organizador (debounce)."""
import threading

_DEBOUNCE_S = 2.0
_lock = threading.Lock()
_timer = None
_publicando = threading.local()


def _habilitado() -> bool:
    import os
    return all(os.getenv(k) for k in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET"))


def _publicar():
    global _timer
    with _lock:
        _timer = None
    _publicando.activo = True
    try:
        from scripts import exportar_datos_publicos
        exportar_datos_publicos.escribir()
    except Exception as e:
        print("Error publicando datos públicos:", e)
    finally:
        _publicando.activo = False


def solicitar_publicacion():
    """Agenda una publicación; varias escrituras seguidas se agrupan en una sola."""
    global _timer
    if getattr(_publicando, "activo", False) or not _habilitado():
        return
    with _lock:
        if _timer is not None:
            return
        _timer = threading.Timer(_DEBOUNCE_S, _publicar)
        _timer.daemon = True
        _timer.start()
