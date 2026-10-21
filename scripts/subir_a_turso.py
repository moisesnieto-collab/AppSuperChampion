"""Sube una BD local YA migrada al modelo relacional (ver migrar_modelo_relacional.py) a Turso.

Uso (con el venv del proyecto y TURSO_URL / TURSO_TOKEN en .env):
    venv/bin/python scripts/subir_a_turso.py [RUTA_BD_LOCAL]            # simulacro: solo compara y respalda
    venv/bin/python scripts/subir_a_turso.py [RUTA_BD_LOCAL] --aplicar  # REEMPLAZA las tablas de Turso

Antes de reemplazar, guarda en backups/turso_respaldo_<fecha>.json todas las filas actuales de Turso.
Al terminar verifica que los conteos de Turso coinciden con la BD local.
"""
import json
import os
import sqlite3
import sys
from datetime import datetime

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import config.settings as settings  # noqa: E402

ORDEN = ("anios", "campeonatos", "copas", "torneos", "jornadas", "categorias", "grupos", "equipos",
         "grupo_equipos", "partidos", "campeonato_permisos", "configuracion")


def tablas(cur):
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    return [r[0] for r in cur.fetchall()]


def columnas(cur, tabla):
    cur.execute(f"PRAGMA table_info({tabla})")
    return [r[1] for r in cur.fetchall()]


def volcar(cur):
    datos = {}
    for t in tablas(cur):
        cols = columnas(cur, t)
        cur.execute(f"SELECT * FROM {t}")
        datos[t] = {"columnas": cols, "filas": [list(r) for r in cur.fetchall()]}
    return datos


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    aplicar = "--aplicar" in sys.argv
    ruta = args[0] if args else os.path.join(RAIZ, "superchampion.db")
    if not settings.TURSO_URL.startswith(("libsql://", "https://", "wss://")) or not settings.TURSO_TOKEN:
        sys.exit("TURSO_URL / TURSO_TOKEN no apuntan a Turso. Revisa el archivo .env")

    local = sqlite3.connect(ruta)
    lc = local.cursor()
    if "equipos" in columnas(lc, "grupos") or "equipos" not in tablas(lc):
        sys.exit("La BD local aún usa el modelo antiguo. Ejecuta antes scripts/migrar_modelo_relacional.py --aplicar")
    ddl = {r[0]: r[1] for r in lc.execute("SELECT name, sql FROM sqlite_master WHERE type='table' "
                                         "AND name NOT LIKE 'sqlite_%'")}
    idx = [r[0] for r in lc.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")]
    local_datos = volcar(lc)

    import libsql_experimental as libsql
    con = libsql.connect(settings.TURSO_URL, auth_token=settings.TURSO_TOKEN)
    cur = con.cursor()
    remoto = volcar(cur)

    os.makedirs(os.path.join(RAIZ, "backups"), exist_ok=True)
    respaldo = os.path.join(RAIZ, "backups", f"turso_respaldo_{datetime.now():%Y%m%d_%H%M%S}.json")
    with open(respaldo, "w", encoding="utf-8") as f:
        json.dump(remoto, f, ensure_ascii=False, default=str)
    print("Respaldo de Turso:", respaldo)

    print(f"{'tabla':22}{'Turso':>8}{'Local':>8}")
    for t in sorted(set(remoto) | set(local_datos)):
        print(f"{t:22}{len(remoto.get(t, {}).get('filas', [])):>8}{len(local_datos.get(t, {}).get('filas', [])):>8}")

    if not aplicar:
        print("\nSimulacro: no se cambió nada en Turso. Usa --aplicar para reemplazar las tablas de Turso.")
        return

    cur.execute("PRAGMA foreign_keys=OFF")
    for t in reversed(list(remoto)):
        cur.execute(f"DROP TABLE IF EXISTS {t}")
    for t in [t for t in ORDEN if t in ddl] + [t for t in ddl if t not in ORDEN]:
        cur.execute(ddl[t])
    for sql in idx:
        cur.execute(sql)
    for t in [t for t in ORDEN if t in local_datos] + [t for t in local_datos if t not in ORDEN]:
        cols = local_datos[t]["columnas"]
        marca = ", ".join("?" * len(cols))
        for fila in local_datos[t]["filas"]:
            cur.execute(f"INSERT INTO {t} ({', '.join(cols)}) VALUES ({marca})", tuple(fila))
    con.commit()

    cur = con.cursor()
    malos = []
    for t, d in local_datos.items():
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        n = cur.fetchone()[0]
        if n != len(d["filas"]):
            malos.append((t, n, len(d["filas"])))
    if malos:
        sys.exit(f"ERROR: conteos distintos (tabla, Turso, local): {malos}. Respaldo en {respaldo}")
    print("OK: Turso quedó igual a la BD local.")


if __name__ == "__main__":
    main()
