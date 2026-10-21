"""Convierte un respaldo JSON de Turso (modelo antiguo) en una BD SQLite local lista para migrar.

Uso: python scripts/turso_json_a_local.py RESPALDO.json SALIDA.db
Luego: scripts/migrar_modelo_relacional.py SALIDA.db --aplicar  y  scripts/subir_a_turso.py SALIDA.db --aplicar
"""
import json
import sqlite3
import sys

datos = json.load(open(sys.argv[1], encoding="utf-8"))
con = sqlite3.connect(sys.argv[2])
for t, d in datos.items():
    cols = d["columnas"]
    defs = ", ".join(f"{c} INTEGER PRIMARY KEY" if c == "id" else (f"{c} TEXT PRIMARY KEY" if (t, c) == ("configuracion", "clave") else c) for c in cols)
    con.execute(f"CREATE TABLE {t} ({defs})")
    con.executemany(f"INSERT INTO {t} VALUES ({','.join('?' * len(cols))})", d["filas"])
con.commit()
