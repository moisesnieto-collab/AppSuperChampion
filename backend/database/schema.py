import json
from datetime import datetime, timedelta
from backend.database.connection import obtener_conexion
from config.constants import CATEGORIAS_DEFAULT, DIAS_DEFAULT, GRUPOS_DEFAULT

def inicializar_db():
    """
    Crea las tablas de AppSuperChampion e inicializa torneos, categorías y grupos por defecto si no existen.
    Nueva jerarquía: Año -> Campeonato -> Copa -> Torneo -> Jornada -> Categoría -> Grupo -> Partido
    """
    con = obtener_conexion()
    cursor = con.cursor()

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
        equipos TEXT NOT NULL,
        FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE CASCADE,
        FOREIGN KEY (fecha_jornada_id) REFERENCES jornadas(id) ON DELETE CASCADE
    )
    """)

    # Tabla Partidos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS partidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        grupo_id INTEGER NOT NULL,
        categoria_id INTEGER NOT NULL,
        fecha_jornada_id INTEGER NOT NULL,
        equipo_local TEXT NOT NULL,
        equipo_visita TEXT NOT NULL,
        goles_local INTEGER DEFAULT 0,
        goles_visita INTEGER DEFAULT 0,
        jugado INTEGER DEFAULT 0,
        es_definicion INTEGER DEFAULT 0,
        orden INTEGER DEFAULT 0,
        FOREIGN KEY (grupo_id) REFERENCES grupos(id) ON DELETE CASCADE,
        FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE CASCADE,
        FOREIGN KEY (fecha_jornada_id) REFERENCES jornadas(id) ON DELETE CASCADE
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
                cursor.execute(
                    "INSERT INTO grupos (categoria_id, fecha_jornada_id, nombre, equipos) VALUES (?, ?, ?, ?)",
                    (cat_id, jornada_id, "Grupo A", json.dumps(equipos_a))
                )
                grupo_a_id = cursor.lastrowid
                _crear_partidos_cuadrangular(cursor, cat_id, jornada_id, grupo_a_id, equipos_a)

                # Grupo B
                equipos_b = ["U. Católica", "Palestino", "Audax Italiano", "Cobreloa"]
                cursor.execute(
                    "INSERT INTO grupos (categoria_id, fecha_jornada_id, nombre, equipos) VALUES (?, ?, ?, ?)",
                    (cat_id, jornada_id, "Grupo B", json.dumps(equipos_b))
                )
                grupo_b_id = cursor.lastrowid
                _crear_partidos_cuadrangular(cursor, cat_id, jornada_id, grupo_b_id, equipos_b)

        con.commit()

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

    for eq_loc, eq_vis, ord_partido in fixture:
        cursor.execute("""
            INSERT INTO partidos
            (grupo_id, categoria_id, fecha_jornada_id, equipo_local, equipo_visita, goles_local, goles_visita, jugado, es_definicion, orden)
            VALUES (?, ?, ?, ?, ?, 0, 0, 0, 0, ?)
        """, (grupo_id, cat_id, jornada_id, eq_loc, eq_vis, ord_partido))
