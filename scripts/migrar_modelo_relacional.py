"""Migra una BD SQLite de SuperChampion al modelo relacional final (con tabla `equipos`).

Uso:
    python scripts/migrar_modelo_relacional.py RUTA_BD            # simulacro sobre una COPIA (no toca la original)
    python scripts/migrar_modelo_relacional.py RUTA_BD --aplicar  # respalda y migra RUTA_BD

Reglas:
- Se conserva Año, Campeonato, la copa "Supercampeones Chicureo" y su torneo. Las demás copas
  sin torneos (p.ej. "Supercampeones 2") se eliminan para crearlas desde la app (rol Master).
- Equipo = (copa_id, categoria_nombre, nombre); reemplaza grupos.equipos y partidos.equipo_local/visita (texto).
- Todo en una transacción; se verifican conteos y PRAGMA foreign_key_check antes de confirmar.
"""
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime

COPA_CONSERVAR = "Supercampeones Chicureo"

DDL = """
CREATE TABLE anios (id INTEGER PRIMARY KEY AUTOINCREMENT, valor INTEGER NOT NULL, orden INTEGER DEFAULT 0, activo INTEGER DEFAULT 1);
CREATE TABLE campeonatos (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, anio_id INTEGER NOT NULL,
    orden INTEGER DEFAULT 0, activo INTEGER DEFAULT 1,
    FOREIGN KEY (anio_id) REFERENCES anios(id) ON DELETE CASCADE);
CREATE TABLE copas (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, campeonato_id INTEGER NOT NULL,
    orden INTEGER DEFAULT 0, activo INTEGER DEFAULT 1, color TEXT, modo_campeon TEXT DEFAULT 'final_lideres',
    criterios_desempate TEXT DEFAULT 'dg,gf,h2h,pg,gc', puntos_victoria INTEGER DEFAULT 3, puntos_empate INTEGER DEFAULT 1,
    FOREIGN KEY (campeonato_id) REFERENCES campeonatos(id) ON DELETE CASCADE);
CREATE TABLE torneos (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, tipo TEXT NOT NULL, copa_id INTEGER NOT NULL,
    orden INTEGER DEFAULT 0, activo INTEGER DEFAULT 1, fecha_inicio DATE, fecha_fin DATE,
    modo_campeon TEXT DEFAULT 'final_lideres',
    FOREIGN KEY (copa_id) REFERENCES copas(id) ON DELETE CASCADE);
CREATE TABLE jornadas (id INTEGER PRIMARY KEY AUTOINCREMENT, torneo_id INTEGER NOT NULL, fecha DATE NOT NULL,
    nombre TEXT NOT NULL, orden INTEGER NOT NULL, lugar TEXT, horario TEXT,
    FOREIGN KEY (torneo_id) REFERENCES torneos(id) ON DELETE CASCADE);
CREATE TABLE categorias (id INTEGER PRIMARY KEY AUTOINCREMENT, jornada_id INTEGER NOT NULL, nombre TEXT NOT NULL,
    orden INTEGER NOT NULL, FOREIGN KEY (jornada_id) REFERENCES jornadas(id) ON DELETE CASCADE);
CREATE TABLE grupos (id INTEGER PRIMARY KEY AUTOINCREMENT, categoria_id INTEGER NOT NULL, fecha_jornada_id INTEGER NOT NULL,
    nombre TEXT NOT NULL,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE CASCADE,
    FOREIGN KEY (fecha_jornada_id) REFERENCES jornadas(id) ON DELETE CASCADE);
CREATE TABLE equipos (id INTEGER PRIMARY KEY AUTOINCREMENT, copa_id INTEGER NOT NULL, categoria_nombre TEXT NOT NULL,
    nombre TEXT NOT NULL, FOREIGN KEY (copa_id) REFERENCES copas(id) ON DELETE CASCADE,
    UNIQUE(copa_id, categoria_nombre, nombre));
CREATE TABLE grupo_equipos (id INTEGER PRIMARY KEY AUTOINCREMENT, grupo_id INTEGER NOT NULL, equipo_id INTEGER NOT NULL,
    orden INTEGER DEFAULT 0,
    FOREIGN KEY (grupo_id) REFERENCES grupos(id) ON DELETE CASCADE,
    FOREIGN KEY (equipo_id) REFERENCES equipos(id) ON DELETE CASCADE,
    UNIQUE(grupo_id, equipo_id));
CREATE TABLE partidos (id INTEGER PRIMARY KEY AUTOINCREMENT, grupo_id INTEGER NOT NULL, categoria_id INTEGER NOT NULL,
    fecha_jornada_id INTEGER NOT NULL, equipo_local_id INTEGER NOT NULL, equipo_visita_id INTEGER NOT NULL,
    goles_local INTEGER DEFAULT 0, goles_visita INTEGER DEFAULT 0, jugado INTEGER DEFAULT 0,
    es_definicion INTEGER DEFAULT 0, orden INTEGER DEFAULT 0, en_vivo INTEGER DEFAULT 0,
    hora TEXT DEFAULT '', cancha TEXT DEFAULT '',
    FOREIGN KEY (grupo_id) REFERENCES grupos(id) ON DELETE CASCADE,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE CASCADE,
    FOREIGN KEY (fecha_jornada_id) REFERENCES jornadas(id) ON DELETE CASCADE,
    FOREIGN KEY (equipo_local_id) REFERENCES equipos(id),
    FOREIGN KEY (equipo_visita_id) REFERENCES equipos(id));
CREATE TABLE campeonato_permisos (id INTEGER PRIMARY KEY AUTOINCREMENT, campeonato_id INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL, rol TEXT NOT NULL, fecha_asignacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (campeonato_id) REFERENCES campeonatos(id) ON DELETE CASCADE, UNIQUE(campeonato_id, usuario_id));
CREATE TABLE configuracion (clave TEXT PRIMARY KEY, valor TEXT NOT NULL);
"""

INDICES = ("partidos(categoria_id)", "partidos(grupo_id)", "partidos(fecha_jornada_id)", "partidos(equipo_local_id)",
           "partidos(equipo_visita_id)", "grupos(categoria_id)", "grupos(fecha_jornada_id)", "categorias(jornada_id)",
           "jornadas(torneo_id)", "torneos(copa_id)", "copas(campeonato_id)", "equipos(copa_id)",
           "grupo_equipos(grupo_id)")

TABLAS = ("anios", "campeonatos", "copas", "torneos", "jornadas", "categorias", "grupos", "partidos",
          "campeonato_permisos", "configuracion")


def columnas(cur, tabla):
    return [r[1] for r in cur.execute(f"PRAGMA table_info({tabla})")]


def copiar(cur, tabla, destino_cols, filtro="", args=()):
    """Copia old_<tabla> -> <tabla> solo con las columnas que existen en origen (el resto usa DEFAULT)."""
    origen = set(columnas(cur, f"old_{tabla}"))
    cols = [c for c in destino_cols if c in origen]
    lista = ", ".join(cols)
    cur.execute(f"INSERT INTO {tabla} ({lista}) SELECT {lista} FROM old_{tabla} {filtro}", args)


def migrar(con):
    cur = con.cursor()
    cur.execute("PRAGMA foreign_keys=OFF")
    cur.execute("BEGIN")
    for t in TABLAS:
        cur.execute(f"ALTER TABLE {t} RENAME TO old_{t}")
    for r in cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'").fetchall():
        cur.execute(f"DROP INDEX {r[0]}")
    for stmt in DDL.strip().split(";\n"):
        if stmt.strip():
            cur.execute(stmt)

    # Copas: solo la conservada y las que tengan torneos
    copas_ok = [r[0] for r in cur.execute(
        "SELECT id FROM old_copas WHERE nombre = ? COLLATE NOCASE OR id IN "
        "(SELECT t.copa_id FROM old_torneos t JOIN old_jornadas j ON j.torneo_id = t.id)", (COPA_CONSERVAR,))]
    if not copas_ok:
        raise RuntimeError(f"No existe la copa '{COPA_CONSERVAR}' ni copas con torneos")
    marca = ",".join("?" * len(copas_ok))
    copiar(cur, "anios", columnas(cur, "anios"))
    copiar(cur, "campeonatos", columnas(cur, "campeonatos"))
    destino = columnas(cur, "copas")
    origen = set(columnas(cur, "old_copas"))
    cl = ", ".join(c for c in destino if c in origen)
    cur.execute(f"INSERT INTO copas ({cl}) SELECT {cl} FROM old_copas WHERE id IN ({marca})", copas_ok)
    copiar(cur, "torneos", columnas(cur, "torneos"), f"WHERE copa_id IN ({marca})", copas_ok)
    cur.execute("DELETE FROM torneos WHERE copa_id NOT IN (SELECT id FROM copas)")
    copiar(cur, "campeonato_permisos", columnas(cur, "campeonato_permisos"))
    copiar(cur, "configuracion", columnas(cur, "configuracion"))

    # Jornadas (sin categoria_id)
    copiar(cur, "jornadas", columnas(cur, "jornadas"), "WHERE torneo_id IN (SELECT id FROM torneos)")

    # Categorías: jornada_id real = jornada usada por sus grupos; si no, la ya asignada; si no, la única jornada
    unica = [r[0] for r in cur.execute("SELECT id FROM jornadas")]
    for cid, nombre, orden, jid in cur.execute(
            "SELECT id, nombre, orden, jornada_id FROM old_categorias ORDER BY id").fetchall():
        g = [r[0] for r in cur.execute(
            "SELECT DISTINCT fecha_jornada_id FROM old_grupos WHERE categoria_id = ?", (cid,))]
        destino_j = g[0] if len(g) == 1 else jid or (unica[0] if len(unica) == 1 else None)
        if len(g) > 1 or destino_j is None or destino_j not in unica:
            raise RuntimeError(f"No se puede determinar la jornada de la categoría {cid} '{nombre}' ({g=}, {jid=})")
        cur.execute("INSERT INTO categorias (id, jornada_id, nombre, orden) VALUES (?,?,?,?)",
                    (cid, destino_j, nombre, orden))

    # Grupos (sin texto de equipos)
    cur.execute("INSERT INTO grupos (id, categoria_id, fecha_jornada_id, nombre) "
                "SELECT id, categoria_id, fecha_jornada_id, nombre FROM old_grupos "
                "WHERE categoria_id IN (SELECT id FROM categorias)")

    # Equipos por (copa, categoría); variantes de mayúsculas/espacios se unifican
    informe = []
    cache = {}

    def equipo_id(grupo_id, nombre):
        copa_id, cat = cur.execute(
            "SELECT t.copa_id, c.nombre FROM grupos g JOIN categorias c ON c.id = g.categoria_id "
            "JOIN jornadas j ON j.id = c.jornada_id JOIN torneos t ON t.id = j.torneo_id WHERE g.id = ?",
            (grupo_id,)).fetchone()
        limpio = " ".join(str(nombre).split())
        clave = (copa_id, cat.casefold(), limpio.casefold())
        if clave not in cache:
            cur.execute("INSERT INTO equipos (copa_id, categoria_nombre, nombre) VALUES (?,?,?)", (copa_id, cat, limpio))
            cache[clave] = (cur.lastrowid, limpio)
        elif cache[clave][1] != limpio:
            informe.append((cache[clave][1], limpio))
        return cache[clave][0]

    for gid, eq in cur.execute("SELECT id, equipos FROM old_grupos WHERE id IN (SELECT id FROM grupos)").fetchall():
        for i, n in enumerate(json.loads(eq or "[]")):
            eid = equipo_id(gid, n)
            cur.execute("INSERT OR IGNORE INTO grupo_equipos (grupo_id, equipo_id, orden) VALUES (?,?,?)", (gid, eid, i))

    # Partidos
    po = set(columnas(cur, "old_partidos"))
    extra = [c for c in ("en_vivo", "hora", "cancha") if c in po]
    sel = ["id", "grupo_id", "categoria_id", "fecha_jornada_id", "equipo_local", "equipo_visita", "goles_local",
           "goles_visita", "jugado", "es_definicion", "orden"] + extra
    for fila in cur.execute(f"SELECT {', '.join(sel)} FROM old_partidos WHERE grupo_id IN (SELECT id FROM grupos)").fetchall():
        d = dict(zip(sel, fila))
        loc, vis = equipo_id(d["grupo_id"], d["equipo_local"]), equipo_id(d["grupo_id"], d["equipo_visita"])
        for eid in (loc, vis):
            cur.execute("INSERT OR IGNORE INTO grupo_equipos (grupo_id, equipo_id, orden) VALUES (?,?,99)",
                        (d["grupo_id"], eid))
        cols = [c for c in sel if c not in ("equipo_local", "equipo_visita")] + ["equipo_local_id", "equipo_visita_id"]
        vals = [d[c] for c in sel if c not in ("equipo_local", "equipo_visita")] + [loc, vis]
        cur.execute(f"INSERT INTO partidos ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})", vals)

    # Equipos huérfanos (sin grupo ni partido)
    cur.execute("DELETE FROM equipos WHERE id NOT IN (SELECT equipo_id FROM grupo_equipos) "
                "AND id NOT IN (SELECT equipo_local_id FROM partidos) AND id NOT IN (SELECT equipo_visita_id FROM partidos)")

    for t in TABLAS:
        cur.execute(f"DROP TABLE old_{t}")
    for i in INDICES:
        t, c = i.rstrip(")").split("(")
        cur.execute(f"CREATE INDEX idx_{t}_{c} ON {i}")
    cur.execute("DELETE FROM sqlite_sequence WHERE name LIKE 'old_%'")
    return informe


def conteos(con, tablas):
    return {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tablas}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    ruta, aplicar = sys.argv[1], "--aplicar" in sys.argv
    if not os.path.exists(ruta):
        sys.exit(f"No existe {ruta}")
    sello = datetime.now().strftime("%Y%m%d_%H%M%S")
    if aplicar:
        respaldo = f"{ruta}.respaldo_{sello}"
        shutil.copy2(ruta, respaldo)
        print("Respaldo:", respaldo)
        trabajo = ruta
    else:
        trabajo = f"{ruta}.simulacro_{sello}"
        shutil.copy2(ruta, trabajo)
        print("Simulacro sobre copia:", trabajo)

    con = sqlite3.connect(trabajo, isolation_level=None)
    antes = conteos(con, ("jornadas", "categorias", "grupos", "partidos"))
    print("Antes:", antes)
    try:
        informe = migrar(con)
        fk = con.execute("PRAGMA foreign_key_check").fetchall()
        if fk:
            raise RuntimeError(f"Registros huérfanos: {fk[:5]}")
        despues = conteos(con, ("jornadas", "categorias", "grupos", "partidos"))
        if despues != antes:
            raise RuntimeError(f"Los conteos no coinciden: {antes} -> {despues}")
        con.execute("COMMIT")
    except Exception as err:
        con.execute("ROLLBACK")
        con.close()
        sys.exit(f"ERROR, nada cambió: {err}")
    print("Después:", conteos(con, ("anios", "campeonatos", "copas", "torneos", "jornadas", "categorias", "grupos",
                                   "equipos", "grupo_equipos", "partidos")))
    if informe:
        print("Nombres unificados (conservado, variante):", informe)
    con.execute("PRAGMA foreign_keys=ON")
    con.close()
    print("OK")


if __name__ == "__main__":
    main()
