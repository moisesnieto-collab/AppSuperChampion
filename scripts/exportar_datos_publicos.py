"""Genera web_publica/datos.json (solo lectura) desde la BD para la página ligera de invitados.

Uso: venv/bin/python scripts/exportar_datos_publicos.py [--cada 15]
"""
import json
import os
import sys
import threading
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import obtener_conexion  # noqa: E402
from backend.services.torneo_service import TorneoService  # noqa: E402

SALIDA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web_publica", "datos.json")


def _filas(cur, sql, args=()):
    cur.execute(sql, args)
    return cur.fetchall()


def generar() -> dict:
    con = obtener_conexion()
    cur = con.cursor()
    copas = []
    for cid, cnombre in _filas(cur, "SELECT id, nombre FROM copas WHERE activo = 1 ORDER BY orden, id"):
        torneos = []
        for tid, tnombre in _filas(cur, "SELECT id, nombre FROM torneos WHERE copa_id = ? AND activo = 1 "
                                        "ORDER BY orden, id", (cid,)):
            jornadas = []
            for jid, jnombre, jfecha in _filas(cur, "SELECT id, nombre, fecha FROM jornadas WHERE torneo_id = ? "
                                            "ORDER BY orden, id", (tid,)):
                cats = []
                for catid, cnom in _filas(cur, "SELECT id, nombre FROM categorias WHERE jornada_id = ? "
                                               "ORDER BY orden, id", (jid,)):
                    partidos = [
                        {"local": r[0], "visita": r[1], "gl": r[2], "gv": r[3], "jugado": bool(r[4]),
                         "vivo": bool(r[5]), "hora": r[6] or "", "cancha": r[7] or ""}
                        for r in _filas(cur, "SELECT equipo_local, equipo_visita, goles_local, goles_visita, "
                                             "jugado, en_vivo, hora, cancha FROM partidos "
                                             "WHERE categoria_id = ? ORDER BY orden, id", (catid,))]
                    try:
                        d = TorneoService.obtener_datos_categoria_dia(catid, jid)
                        grupos = [{"nombre": g["grupo"].nombre, "tabla": [e.to_dict() for e in g["tabla"]]}
                                  for g in d["grupos"]]
                        ec = d["estado_campeon"] or {}
                        campeon = {"estado": ec.get("estado", ""), "campeon": ec.get("campeon") or "",
                                   "motivo": ec.get("motivo", "")}
                    except Exception:
                        grupos, campeon = [], {"estado": "", "campeon": "", "motivo": ""}
                    cats.append({"nombre": cnom, "partidos": partidos, "grupos": grupos, "campeon": campeon})
                jornadas.append({"nombre": jnombre, "fecha": str(jfecha or ""), "categorias": cats})
            torneos.append({"nombre": tnombre, "jornadas": jornadas})
        copas.append({"nombre": cnombre, "torneos": torneos})
    return {"actualizado": datetime.now().isoformat(timespec="seconds"), "copas": copas}


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


def escribir():
    with _lock_escritura:
        _escribir()


def _escribir():
    datos = generar()
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
