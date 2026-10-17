"""Publica en R2 la jornada pública: completa (botón) o solo la categoría afectada (al grabar)."""
import os
import threading

_DEBOUNCE_S = 2.0
_lock = threading.Lock()
_timer = None
_pendientes = set()
_documento = None


def _habilitado() -> bool:
    return all(os.getenv(k) for k in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET"))


def _exportador():
    from scripts import exportar_datos_publicos
    return exportar_datos_publicos


def publicar_jornada_completa(jornada_id=None) -> dict:
    """Exporta toda la jornada (marcada o indicada) y la sube. Devuelve el documento publicado."""
    global _documento
    exp = _exportador()
    with _lock:
        datos = exp.generar(jornada_id)
        exp.escribir(datos=datos)
        _documento = datos
    return datos


def reemplazar_categoria(documento: dict, nodo: dict) -> bool:
    """Reemplaza en el documento el nodo de categoría con el mismo id. True si lo encontró."""
    for copa in documento.get("copas", []):
        for torneo in copa.get("torneos", []):
            for jor in torneo.get("jornadas", []):
                for i, c in enumerate(jor.get("categorias", [])):
                    if c.get("id") == nodo["id"]:
                        jor["categorias"][i] = nodo
                        return True
    return False


def _publicar_pendientes():
    global _timer, _documento
    with _lock:
        _timer = None
        cats = list(_pendientes)
        _pendientes.clear()
    try:
        exp = _exportador()
        if _documento is None:
            publicar_jornada_completa()
            return
        from datetime import datetime, timezone
        from backend.database.connection import obtener_conexion
        cur = obtener_conexion().cursor()
        with _lock:
            doc = _documento
            jid = doc.get("jornada_id")
            cambio = False
            for catid in cats:
                fila = exp._filas(cur, "SELECT nombre, jornada_id FROM categorias WHERE id = ?", (catid,))
                if not fila or fila[0][1] != jid:
                    continue
                nodo = exp._exportar_categoria(cur, catid, jid, fila[0][0])
                cambio = reemplazar_categoria(doc, nodo) or cambio
            if cambio:
                doc["actualizado"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
                exp.escribir(datos=doc)
    except Exception as e:
        print("Error publicando datos públicos:", e)


def publicar_categoria(categoria_id: int):
    """Agenda la actualización incremental de una categoría (agrupa escrituras seguidas)."""
    global _timer
    if not _habilitado():
        return
    with _lock:
        _pendientes.add(categoria_id)
        if _timer is not None:
            return
        _timer = threading.Timer(_DEBOUNCE_S, _publicar_pendientes)
        _timer.daemon = True
        _timer.start()


def publicar_categoria_de_partido(partido_id: int):
    try:
        from backend.database.repositories import PartidoRepository
        p = PartidoRepository.obtener_por_id(partido_id)
        if p:
            publicar_categoria(p.categoria_id)
    except Exception as e:
        print("Error agendando publicación:", e)
