import json
from datetime import datetime, timedelta
from backend.database.connection import obtener_conexion
from config.constants import CATEGORIAS_DEFAULT, DIAS_DEFAULT, GRUPOS_DEFAULT

SCHEMA_VERSION = "3"


def inicializar_db():
    """
    Crea las tablas de AppSuperChampion e inicializa torneos, categorías y grupos por defecto si no existen.
    Nueva jerarquía: Año -> Campeonato -> Copa -> Torneo -> Jornada -> Categoría -> Grupo -> Partido
    """
    con = obtener_conexion()
    cursor = con.cursor()

    # Camino rápido: si el esquema ya fue inicializado, evita ~40 viajes de red a Turso en cada arranque
    try:
        cursor.execute("SELECT valor FROM configuracion WHERE clave = 'schema_version'")
        fila = cursor.fetchone()
        if fila and fila[0] == SCHEMA_VERSION:
            return
    except Exception:
        pass

    # Tabla Años
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS anios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        valor INTEGER NOT NULL,
        orden INTEGER DEFAULT 0,
        activo INTEGER DEFAULT 1
    )
    """)

    # Tabla Campeonatos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS campeonatos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        anio_id INTEGER NOT NULL,
        orden INTEGER DEFAULT 0,
        activo INTEGER DEFAULT 1,
        FOREIGN KEY (anio_id) REFERENCES anios(id) ON DELETE CASCADE
    )
    """)

    # Tabla Copas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS copas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        campeonato_id INTEGER NOT NULL,
        orden INTEGER DEFAULT 0,
        activo INTEGER DEFAULT 1,
        FOREIGN KEY (campeonato_id) REFERENCES campeonatos(id) ON DELETE CASCADE
    )
    """)
    for _col, _def in (("color", "TEXT"),
                       ("modo_campeon", "TEXT DEFAULT 'final_lideres'"),
                       ("criterios_desempate", "TEXT DEFAULT 'dg,gf,h2h,pg,gc'"),
                       ("puntos_victoria", "INTEGER DEFAULT 3"),
                       ("puntos_empate", "INTEGER DEFAULT 1")):
        try:
            cursor.execute(f"ALTER TABLE copas ADD COLUMN {_col} {_def}")
        except Exception:
            pass

    # Tabla Torneos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS torneos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        tipo TEXT NOT NULL,
        copa_id INTEGER NOT NULL,
        orden INTEGER DEFAULT 0,
        activo INTEGER DEFAULT 1,
        fecha_inicio DATE,
        fecha_fin DATE,
        FOREIGN KEY (copa_id) REFERENCES copas(id) ON DELETE CASCADE
    )
    """)

    # modo_campeon vive en el torneo; al crear la columna se copia el valor de su copa
    try:
        cursor.execute("ALTER TABLE torneos ADD COLUMN modo_campeon TEXT DEFAULT 'final_lideres'")
        cursor.execute("UPDATE torneos SET modo_campeon = COALESCE((SELECT c.modo_campeon FROM copas c WHERE c.id = torneos.copa_id), 'final_lideres')")
    except Exception:
        pass

    # Migración: bases antiguas tienen torneos.anio NOT NULL (reemplazado por copa_id)
    try:
        cursor.execute("PRAGMA table_info(torneos)")
        columnas_torneos = [r[1] for r in cursor.fetchall()]
        if "anio" in columnas_torneos:
            cursor.execute("ALTER TABLE torneos DROP COLUMN anio")
    except Exception as err:
        print(f"No se pudo migrar torneos.anio: {err}")

    # Tabla Jornadas (ahora pertenece a Torneo)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jornadas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        torneo_id INTEGER NOT NULL,
        fecha DATE NOT NULL,
        nombre TEXT NOT NULL,
        orden INTEGER NOT NULL,
        lugar TEXT,
        horario TEXT,
        FOREIGN KEY (torneo_id) REFERENCES torneos(id) ON DELETE CASCADE
    )
    """)

    # Tabla Categorías (ahora pertenece a Jornada)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        jornada_id INTEGER NOT NULL,
        nombre TEXT NOT NULL,
        orden INTEGER NOT NULL,
        FOREIGN KEY (jornada_id) REFERENCES jornadas(id) ON DELETE CASCADE
    )
    """)

    # Tabla Grupos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS grupos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        categoria_id INTEGER NOT NULL,
        fecha_jornada_id INTEGER NOT NULL,
        nombre TEXT NOT NULL,
        FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE CASCADE,
        FOREIGN KEY (fecha_jornada_id) REFERENCES jornadas(id) ON DELETE CASCADE
    )
    """)

    # Tabla Equipos (por copa y categoría)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS equipos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        copa_id INTEGER NOT NULL,
        categoria_nombre TEXT NOT NULL,
        nombre TEXT NOT NULL,
        FOREIGN KEY (copa_id) REFERENCES copas(id) ON DELETE CASCADE,
        UNIQUE(copa_id, categoria_nombre, nombre)
    )
    """)

    # Tabla Grupo-Equipos (muchos a muchos)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS grupo_equipos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        grupo_id INTEGER NOT NULL,
        equipo_id INTEGER NOT NULL,
        orden INTEGER DEFAULT 0,
        FOREIGN KEY (grupo_id) REFERENCES grupos(id) ON DELETE CASCADE,
        FOREIGN KEY (equipo_id) REFERENCES equipos(id) ON DELETE CASCADE,
        UNIQUE(grupo_id, equipo_id)
    )
    """)

    # Tabla Partidos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS partidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        grupo_id INTEGER NOT NULL,
        categoria_id INTEGER NOT NULL,
        fecha_jornada_id INTEGER NOT NULL,
        equipo_local_id INTEGER NOT NULL,
        equipo_visita_id INTEGER NOT NULL,
        goles_local INTEGER DEFAULT 0,
        goles_visita INTEGER DEFAULT 0,
        jugado INTEGER DEFAULT 0,
        es_definicion INTEGER DEFAULT 0,
        orden INTEGER DEFAULT 0,
        FOREIGN KEY (grupo_id) REFERENCES grupos(id) ON DELETE CASCADE,
        FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE CASCADE,
        FOREIGN KEY (fecha_jornada_id) REFERENCES jornadas(id) ON DELETE CASCADE,
        FOREIGN KEY (equipo_local_id) REFERENCES equipos(id),
        FOREIGN KEY (equipo_visita_id) REFERENCES equipos(id)
    )
    """)

    # Tabla de Configuración y Claves (ej. PIN organizador)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS configuracion (
        clave TEXT PRIMARY KEY,
        valor TEXT NOT NULL
    )
    """)

    # Tabla de Permisos por Campeonato
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS campeonato_permisos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campeonato_id INTEGER NOT NULL,
        usuario_id INTEGER NOT NULL,
        rol TEXT NOT NULL,
        fecha_asignacion DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (campeonato_id) REFERENCES campeonatos(id) ON DELETE CASCADE,
        UNIQUE(campeonato_id, usuario_id)
    )
    """)

    for _col, _def in (("en_vivo", "INTEGER DEFAULT 0"), ("hora", "TEXT DEFAULT ''"),
                       ("cancha", "TEXT DEFAULT ''")):
        try:
            cursor.execute(f"ALTER TABLE partidos ADD COLUMN {_col} {_def}")
        except Exception:
            pass

    for _idx in ("partidos(categoria_id)", "partidos(grupo_id)", "partidos(fecha_jornada_id)",
                 "grupos(categoria_id)", "grupos(fecha_jornada_id)", "categorias(jornada_id)",
                 "jornadas(torneo_id)", "torneos(copa_id)", "copas(campeonato_id)",
                 "equipos(copa_id)", "grupo_equipos(grupo_id)"):
        _t, _c = _idx.rstrip(")").split("(")
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{_t}_{_c} ON {_idx}")
        except Exception:
            pass

    # Los índices de equipos de partidos solo existen en el modelo nuevo; los compuestos cubren las consultas más frecuentes
    for _nombre, _def in (
            ("idx_partidos_equipo_local_id", "partidos(equipo_local_id)"),
            ("idx_partidos_equipo_visita_id", "partidos(equipo_visita_id)"),
            ("idx_grupo_equipos_equipo_id", "grupo_equipos(equipo_id)"),
            ("idx_partidos_cat_jornada", "partidos(categoria_id, fecha_jornada_id)"),
            ("idx_grupos_cat_jornada", "grupos(categoria_id, fecha_jornada_id)"),
            ("idx_torneos_activo", "torneos(activo, orden)"),
            ("idx_campeonato_permisos_camp", "campeonato_permisos(campeonato_id)")):
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {_nombre} ON {_def}")
        except Exception:
            pass

    con.commit()

    cursor.execute("PRAGMA table_info(grupos)")
    if "equipos" in [r[1] for r in cursor.fetchall()]:
        raise RuntimeError(
            "La base de datos usa el modelo antiguo (grupos.equipos). Ejecuta primero: "
            "python scripts/migrar_modelo_relacional.py <RUTA_BD> --aplicar")

    cursor.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('schema_version', ?)", (SCHEMA_VERSION,))
    con.commit()

    # Poblar datos por defecto si están vacíos
    cursor.execute("SELECT COUNT(*) FROM anios")
    count_anios = cursor.fetchone()[0]
    
    if count_anios == 0:
        anio_actual = datetime.now().year
        # Crear año actual
        cursor.execute("INSERT INTO anios (valor, orden, activo) VALUES (?, 1, 1)", (anio_actual,))
        anio_id = cursor.lastrowid

        # Crear campeonato por defecto
        cursor.execute("INSERT INTO campeonatos (nombre, anio_id, orden, activo) VALUES (?, ?, 1, 1)", ("Supercampeones", anio_id))
        campeonato_id = cursor.lastrowid

        # Crear copa por defecto
        cursor.execute("INSERT INTO copas (nombre, campeonato_id, orden, activo) VALUES (?, ?, 1, 1)", ("Copa Supercampeones", campeonato_id))
        copa_id = cursor.lastrowid

        # Crear torneo por defecto
        cursor.execute(
            "INSERT INTO torneos (nombre, tipo, copa_id, orden, activo) VALUES (?, ?, ?, 1, 1)",
            (f"Torneo {anio_actual}", "Apertura", copa_id)
        )
        torneo_id = cursor.lastrowid

        # Crear jornadas por defecto (Día 1 y Día 2)
        fecha_base = datetime.now().date()
        for i, dia_nombre in enumerate(DIAS_DEFAULT, start=1):
            fecha_jornada = fecha_base + timedelta(days=i-1)
            cursor.execute(
                "INSERT INTO jornadas (torneo_id, fecha, nombre, orden) VALUES (?, ?, ?, ?)",
                (torneo_id, fecha_jornada.isoformat(), dia_nombre, i)
            )
            jornada_id = cursor.lastrowid

            # Crear categorías por defecto para esta jornada
            for idx, cat_nombre in enumerate(CATEGORIAS_DEFAULT, start=1):
                cursor.execute(
                    "INSERT INTO categorias (jornada_id, nombre, orden) VALUES (?, ?, ?)",
                    (jornada_id, cat_nombre, idx)
                )
                cat_id = cursor.lastrowid

                # Grupo A
                equipos_a = ["Real Dunalastair", "Cobresal", "Colo-Colo", "U. de Chile"]
                grupo_a_id = _crear_grupo(cursor, copa_id, cat_id, cat_nombre, jornada_id, "Grupo A", equipos_a)
                _crear_partidos_cuadrangular(cursor, cat_id, jornada_id, grupo_a_id, equipos_a)

                # Grupo B
                equipos_b = ["U. Católica", "Palestino", "Audax Italiano", "Cobreloa"]
                grupo_b_id = _crear_grupo(cursor, copa_id, cat_id, cat_nombre, jornada_id, "Grupo B", equipos_b)
                _crear_partidos_cuadrangular(cursor, cat_id, jornada_id, grupo_b_id, equipos_b)

        con.commit()

def _crear_grupo(cursor, copa_id, cat_id, cat_nombre, jornada_id, nombre, equipos) -> int:
    cursor.execute("INSERT INTO grupos (categoria_id, fecha_jornada_id, nombre) VALUES (?, ?, ?)",
                   (cat_id, jornada_id, nombre))
    grupo_id = cursor.lastrowid
    for i, eq in enumerate(equipos):
        cursor.execute("INSERT INTO grupo_equipos (grupo_id, equipo_id, orden) VALUES (?, ?, ?)",
                       (grupo_id, _equipo_semilla(cursor, copa_id, cat_nombre, eq), i))
    return grupo_id


def _equipo_semilla(cursor, copa_id, cat_nombre, nombre) -> int:
    cursor.execute("SELECT id FROM equipos WHERE copa_id = ? AND categoria_nombre = ? AND nombre = ?",
                   (copa_id, cat_nombre, nombre))
    fila = cursor.fetchone()
    if fila:
        return fila[0]
    cursor.execute("INSERT INTO equipos (copa_id, categoria_nombre, nombre) VALUES (?, ?, ?)",
                   (copa_id, cat_nombre, nombre))
    return cursor.lastrowid


def _crear_partidos_cuadrangular(cursor, cat_id: int, jornada_id: int, grupo_id: int, equipos: list):
    """
    Genera fixture estándar para un cuadrangular de 4 equipos (3 fechas / 6 partidos).
    """
    if len(equipos) < 4:
        return

    e1, e2, e3, e4 = equipos[0], equipos[1], equipos[2], equipos[3]
    fixture = [
        # Fecha 1
        (e1, e2, 1),
        (e3, e4, 2),
        # Fecha 2
        (e1, e3, 3),
        (e2, e4, 4),
        # Fecha 3
        (e1, e4, 5),
        (e2, e3, 6),
    ]

    cursor.execute("SELECT equipo_id, e.nombre FROM grupo_equipos ge JOIN equipos e ON e.id = ge.equipo_id "
                   "WHERE ge.grupo_id = ?", (grupo_id,))
    ids = {n: i for i, n in cursor.fetchall()}
    for eq_loc, eq_vis, ord_partido in fixture:
        cursor.execute("""
            INSERT INTO partidos
            (grupo_id, categoria_id, fecha_jornada_id, equipo_local_id, equipo_visita_id, goles_local, goles_visita, jugado, es_definicion, orden)
            VALUES (?, ?, ?, ?, ?, 0, 0, 0, 0, ?)
        """, (grupo_id, cat_id, jornada_id, ids[eq_loc], ids[eq_vis], ord_partido))
