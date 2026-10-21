"""Genera web_publica/datos.json (solo lectura) desde la BD para la página ligera de invitados.

Uso: venv/bin/python scripts/exportar_datos_publicos.py [--cada 15]
"""
import json
import os
import sys
import threading
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import obtener_conexion  # noqa: E402
from backend.services.torneo_service import TorneoService  # noqa: E402

SALIDA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web_publica", "datos.json")


def _filas(cur, sql, args=()):
    cur.execute(sql, args)
    return cur.fetchall()


def _exportar_categoria(cur, catid, jid, nombre) -> dict:
    partidos = [
        {"local": r[0], "visita": r[1], "gl": r[2], "gv": r[3], "jugado": bool(r[4]),
         "vivo": bool(r[5]), "hora": r[6] or "", "cancha": r[7] or "", "grupo": r[8] or ""}
        for r in _filas(cur, "SELECT el.nombre, ev.nombre, p.goles_local, p.goles_visita, "
                             "p.jugado, p.en_vivo, p.hora, p.cancha, g.nombre FROM partidos p "
                             "JOIN equipos el ON el.id = p.equipo_local_id "
                             "JOIN equipos ev ON ev.id = p.equipo_visita_id "
                             "LEFT JOIN grupos g ON g.id = p.grupo_id "
                             "WHERE p.categoria_id = ? ORDER BY p.orden, p.id", (catid,))]
    try:
        d = TorneoService.obtener_datos_categoria_dia(catid, jid)
        grupos = [{"nombre": g["grupo"].nombre, "tabla": [e.to_dict() for e in g["tabla"]]}
                  for g in d["grupos"]]
        ec = d["estado_campeon"] or {}
        campeon = {"estado": ec.get("estado", ""), "campeon": ec.get("campeon") or "",
                   "motivo": ec.get("motivo", "")}
    except Exception:
        grupos, campeon = [], {"estado": "", "campeon": "", "motivo": ""}
    return {"id": catid, "nombre": nombre, "partidos": partidos, "grupos": grupos, "campeon": campeon}


def resolver_jornada_id(cur, jornada_id=None):
    """Jornada indicada, o la marcada como pública, o la primera con partidos del primer torneo activo."""
    if jornada_id:
        return jornada_id
    from backend.database.repositories import ConfiguracionRepository
    marcada = ConfiguracionRepository.obtener_jornada_publica()
    if marcada and _filas(cur, "SELECT 1 FROM jornadas WHERE id = ?", (marcada,)):
        return marcada
    for (tid,) in _filas(cur, "SELECT t.id FROM torneos t JOIN copas c ON c.id = t.copa_id "
                              "WHERE t.activo = 1 AND c.activo = 1 ORDER BY c.orden, c.id, t.orden, t.id"):
        filas = _filas(cur, "SELECT j.id FROM jornadas j WHERE j.torneo_id = ? ORDER BY j.orden, j.id", (tid,))
        for (jid,) in filas:
            if _filas(cur, "SELECT 1 FROM partidos WHERE fecha_jornada_id = ? LIMIT 1", (jid,)):
                return jid
        if filas:
            return filas[0][0]
        break
    return None


def generar(jornada_id=None) -> dict:
    """Exporta solo una jornada (con TODAS sus categorías) dentro de su copa/torneo."""
    con = obtener_conexion()
    cur = con.cursor()
    ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    jid = resolver_jornada_id(cur, jornada_id)
    filas = _filas(cur, "SELECT j.id, j.nombre, j.fecha, t.id, t.nombre, c.id, c.nombre FROM jornadas j "
                        "JOIN torneos t ON t.id = j.torneo_id JOIN copas c ON c.id = t.copa_id "
                        "WHERE j.id = ?", (jid,)) if jid else []
    if not filas:
        return {"actualizado": ahora, "jornada_id": None, "copas": []}
    jid, jnombre, jfecha, _tid, tnombre, _cid, cnombre = filas[0]
    cats = [_exportar_categoria(cur, catid, jid, cnom)
            for catid, cnom in _filas(cur, "SELECT id, nombre FROM categorias WHERE jornada_id = ? "
                                           "ORDER BY orden, id", (jid,))]
    jornada = {"id": jid, "nombre": jnombre, "fecha": str(jfecha or ""), "categorias": cats}
    return {"actualizado": ahora, "jornada_id": jid,
            "copas": [{"nombre": cnombre, "torneos": [{"nombre": tnombre, "jornadas": [jornada]}]}]}


def subir_r2(ruta):
    """Sube datos.json a Cloudflare R2 (API S3) si R2_* está definido en el entorno."""
    cfg = {k: os.getenv(k) for k in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET")}
    if not all(cfg.values()):
        return False
    import boto3
    s3 = boto3.client(
        "s3", endpoint_url=f"https://{cfg['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=cfg["R2_ACCESS_KEY_ID"], aws_secret_access_key=cfg["R2_SECRET_ACCESS_KEY"],
        region_name="auto")
    with open(ruta, "rb") as f:
        s3.put_object(Bucket=cfg["R2_BUCKET"], Key="datos.json", Body=f.read(),
                      ContentType="application/json", CacheControl="public, max-age=5")
    return True


_lock_escritura = threading.Lock()


def escribir(jornada_id=None, datos=None):
    with _lock_escritura:
        _escribir(jornada_id, datos)


def _escribir(jornada_id=None, datos=None):
    datos = datos if datos is not None else generar(jornada_id)
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    tmp = f"{SALIDA}.{os.getpid()}.{threading.get_ident()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False)
    os.replace(tmp, SALIDA)
    try:
        if subir_r2(SALIDA):
            print("datos.json subido a R2")
    except Exception as e:
        print("Error subiendo a R2:", e)


if __name__ == "__main__":
    cada = int(sys.argv[sys.argv.index("--cada") + 1]) if "--cada" in sys.argv else 0
    while True:
        escribir()
        print("datos.json actualizado", datetime.now().strftime("%H:%M:%S"))
        if not cada:
            break
        time.sleep(cada)
