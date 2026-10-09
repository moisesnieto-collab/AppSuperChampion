import json
from datetime import datetime, timedelta
from backend.database.connection import obtener_conexion
from config.constants import CATEGORIAS_DEFAULT, DIAS_DEFAULT, GRUPOS_DEFAULT

def inicializar_db():
    """
    Crea las tablas de AppSuperChampion e inicializa categorías y grupos por defecto si no existen.
    """
    con = obtener_conexion()
    cursor = con.cursor()

    # Tabla Categorías
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        orden INTEGER NOT NULL
    )
    """)

    # Tabla Jornadas (nueva)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jornadas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        categoria_id INTEGER NOT NULL,
        fecha DATE NOT NULL,
        nombre TEXT NOT NULL,
        orden INTEGER NOT NULL,
        FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE CASCADE
    )
    """)

    # Tabla Grupos (modificar campo dia a fecha)
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

    # Tabla Partidos (modificar campo dia a fecha)
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

    con.commit()

    # Poblar categorías por defecto si está vacía
    cursor.execute("SELECT COUNT(*) FROM categorias")
    count = cursor.fetchone()[0]
    if count == 0:
        for idx, cat_nombre in enumerate(CATEGORIAS_DEFAULT, start=1):
            cursor.execute("INSERT INTO categorias (nombre, orden) VALUES (?, ?)", (cat_nombre, idx))
            cat_id = cursor.lastrowid

            # Crear jornadas por defecto (Día 1 y Día 2 como fechas)
            fecha_base = datetime.now().date()
            for i, dia_nombre in enumerate(DIAS_DEFAULT, start=1):
                fecha_jornada = fecha_base + timedelta(days=i-1)
                cursor.execute(
                    "INSERT INTO jornadas (categoria_id, fecha, nombre, orden) VALUES (?, ?, ?, ?)",
                    (cat_id, fecha_jornada.isoformat(), dia_nombre, i)
                )
                jornada_id = cursor.lastrowid

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
