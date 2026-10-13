"""
Script de migración para agregar jerarquía Año -> Campeonato -> Copa
Migra datos existentes de torneos a la nueva estructura
"""
import sqlite3
from datetime import datetime
from backend.database.connection import obtener_conexion

def ejecutar_migracion():
    """
    Ejecuta la migración de datos existentes a la nueva estructura
    """
    con = obtener_conexion()
    cursor = con.cursor()
    
    print("Iniciando migración...")
    
    # 1. Verificar si las nuevas tablas ya existen
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='anios'")
    if cursor.fetchone():
        print("Las tablas nuevas ya existen. Abortando migración.")
        return
    
    # 2. Crear backup de datos existentes
    print("Creando backup de torneos existentes...")
    cursor.execute("SELECT * FROM torneos")
    torneos_existentes = cursor.fetchall()
    
    # 3. Crear nuevas tablas (ya están en schema.py, pero las ejecutamos aquí)
    print("Creando nuevas tablas...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS anios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        valor INTEGER NOT NULL,
        orden INTEGER DEFAULT 0,
        activo INTEGER DEFAULT 1
    )
    """)
    
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
    
    # 4. Agregar columnas a jornadas
    print("Actualizando tabla jornadas...")
    cursor.execute("ALTER TABLE jornadas ADD COLUMN lugar TEXT")
    cursor.execute("ALTER TABLE jornadas ADD COLUMN horario TEXT")
    
    # 5. Migrar datos
    print("Migrando datos...")
    
    # Obtener años únicos de torneos existentes
    años_unicos = set()
    for torneo in torneos_existentes:
        # torneo: (id, nombre, tipo, anio, orden, activo, fecha_inicio, fecha_fin)
        anio = torneo[3]
        años_unicos.add(anio)
    
    # Crear años
    for anio in sorted(años_unicos):
        cursor.execute("INSERT INTO anios (valor, orden, activo) VALUES (?, ?, 1)", (anio, anio))
        print(f"  - Creado año: {anio}")
    
    # Crear campeonato por defecto para cada año
    for anio in sorted(años_unicos):
        cursor.execute("SELECT id FROM anios WHERE valor = ?", (anio,))
        anio_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO campeonatos (nombre, anio_id, orden, activo) VALUES (?, ?, 1, 1)", 
                      ("Supercampeones", anio_id))
        print(f"  - Creado campeonato para año {anio}")
    
    # Crear copa por defecto para cada campeonato
    cursor.execute("SELECT id, anio_id FROM campeonatos")
    campeonatos = cursor.fetchall()
    for camp_id, anio_id in campeonatos:
        cursor.execute("INSERT INTO copas (nombre, campeonato_id, orden, activo) VALUES (?, ?, 1, 1)", 
                      ("Copa Supercampeones", camp_id))
        print(f"  - Creada copa para campeonato {camp_id}")
    
    # Migrar torneos a copas
    for torneo in torneos_existentes:
        torneo_id = torneo[0]
        nombre = torneo[1]
        tipo = torneo[2]
        anio = torneo[3]
        orden = torneo[4]
        activo = torneo[5]
        fecha_inicio = torneo[6]
        fecha_fin = torneo[7]
        
        # Obtener copa_id correspondiente
        cursor.execute("SELECT id FROM anios WHERE valor = ?", (anio,))
        anio_id = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM campeonatos WHERE anio_id = ?", (anio_id,))
        camp_id = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM copas WHERE campeonato_id = ?", (camp_id,))
        copa_id = cursor.fetchone()[0]
        
        # Actualizar torneo con copa_id
        cursor.execute("""
            UPDATE torneos 
            SET copa_id = ?
            WHERE id = ?
        """, (copa_id, torneo_id))
        print(f"  - Migrado torneo: {nombre} -> copa_id {copa_id}")
    
    # 6. Eliminar columna anio de torneos (SQLite no soporta DROP COLUMN directamente)
    # En SQLite, necesitamos recrear la tabla
    print("Recreando tabla torneos sin columna anio...")
    cursor.execute("""
        CREATE TABLE torneos_new (
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
    
    cursor.execute("""
        INSERT INTO torneos_new (id, nombre, tipo, copa_id, orden, activo, fecha_inicio, fecha_fin)
        SELECT id, nombre, tipo, copa_id, orden, activo, fecha_inicio, fecha_fin FROM torneos
    """)
    
    cursor.execute("DROP TABLE torneos")
    cursor.execute("ALTER TABLE torneos_new RENAME TO torneos")
    
    con.commit()
    print("Migración completada exitosamente!")
    
    # Mostrar resumen
    cursor.execute("SELECT COUNT(*) FROM anios")
    print(f"Total años: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM campeonatos")
    print(f"Total campeonatos: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM copas")
    print(f"Total copas: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM torneos")
    print(f"Total torneos: {cursor.fetchone()[0]}")

if __name__ == "__main__":
    ejecutar_migracion()
