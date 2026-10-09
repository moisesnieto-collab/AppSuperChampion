"""
Script para migrar el schema de la base de datos a Turso.
Ejecutar: python scripts/migrate_turso.py
"""
import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

TURSO_URL = os.getenv("TURSO_URL")
TURSO_TOKEN = os.getenv("TURSO_TOKEN")

if not TURSO_URL or not TURSO_TOKEN:
    print("❌ Error: TURSO_URL y TURSO_TOKEN deben estar configurados en .env")
    sys.exit(1)

try:
    import libsql_experimental as libsql
    print("✓ Conectando a Turso...")
    con = libsql.connect(TURSO_URL, auth_token=TURSO_TOKEN)
    cursor = con.cursor()
    
    # Ejecutar el schema directamente
    print("✓ Creando tablas...")
    
    # Tabla Categorías
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        orden INTEGER NOT NULL
    )
    """)
    
    # Tabla Jornadas
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
        jugado BOOLEAN DEFAULT 0,
        es_definicion BOOLEAN DEFAULT 0,
        orden INTEGER NOT NULL,
        FOREIGN KEY (grupo_id) REFERENCES grupos(id) ON DELETE CASCADE,
        FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE CASCADE,
        FOREIGN KEY (fecha_jornada_id) REFERENCES jornadas(id) ON DELETE CASCADE
    )
    """)
    
    con.commit()
    
    print("✓ Schema migrado exitosamente a Turso")
    print(f"✓ Base de datos: {TURSO_URL}")
    
except ImportError as e:
    print(f"❌ Error: libsql-experimental no está instalado: {e}")
    print("   Ejecutar: pip install libsql-experimental")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error durante la migración: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
