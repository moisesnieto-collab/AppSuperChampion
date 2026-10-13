"""
Migration script to update database schema for Torneo hierarchy.
New hierarchy: Torneo -> Jornada -> Categoria -> Grupo -> Partido
"""
import json
from datetime import datetime, timedelta
from backend.database.connection import obtener_conexion


def migrate_to_torneo_hierarchy():
    """
    Migrates existing database to new Torneo hierarchy.
    - Creates torneos table
    - Adds torneo_id to jornadas
    - Adds jornada_id to categorias
    - Migrates existing data
    """
    con = obtener_conexion()
    cursor = con.cursor()
    
    try:
        # Check if torneos table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='torneos'")
        torneos_exists = cursor.fetchone()
        
        if not torneos_exists:
            print("Creating torneos table...")
            cursor.execute("""
            CREATE TABLE torneos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                tipo TEXT NOT NULL,
                anio INTEGER NOT NULL,
                activo INTEGER DEFAULT 1,
                fecha_inicio DATE,
                fecha_fin DATE
            )
            """)
            con.commit()
            
            # Create default tournament
            anio_actual = datetime.now().year
            cursor.execute(
                "INSERT INTO torneos (nombre, tipo, anio, activo) VALUES (?, ?, ?, 1)",
                (f"Torneo {anio_actual}", "Apertura", anio_actual)
            )
            con.commit()
            torneo_id = cursor.lastrowid
            print(f"Created default tournament with ID: {torneo_id}")
        else:
            # Get existing tournament
            cursor.execute("SELECT id FROM torneos WHERE activo = 1 LIMIT 1")
            row = cursor.fetchone()
            if row:
                torneo_id = row[0]
                print(f"Using existing active tournament with ID: {torneo_id}")
            else:
                cursor.execute("SELECT id FROM torneos ORDER BY id DESC LIMIT 1")
                row = cursor.fetchone()
                torneo_id = row[0] if row else None
                if not torneo_id:
                    # Create default tournament if table exists but is empty
                    anio_actual = datetime.now().year
                    cursor.execute(
                        "INSERT INTO torneos (nombre, tipo, anio, activo) VALUES (?, ?, ?, 1)",
                        (f"Torneo {anio_actual}", "Apertura", anio_actual)
                    )
                    con.commit()
                    torneo_id = cursor.lastrowid
                    print(f"Created default tournament with ID: {torneo_id}")
                else:
                    print(f"Using existing tournament with ID: {torneo_id}")
        
        # Check if jornadas table has torneo_id column
        cursor.execute("PRAGMA table_info(jornadas)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'torneo_id' not in columns:
            print("Adding torneo_id to jornadas table...")
            cursor.execute("ALTER TABLE jornadas ADD COLUMN torneo_id INTEGER")
            
            # Update existing jornadas with the tournament ID
            cursor.execute("UPDATE jornadas SET torneo_id = ?", (torneo_id,))
            print("Updated jornadas with torneo_id")
        
        # Check if categorias table has jornada_id column
        cursor.execute("PRAGMA table_info(categorias)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'jornada_id' not in columns:
            print("Adding jornada_id to categorias table...")
            cursor.execute("ALTER TABLE categorias ADD COLUMN jornada_id INTEGER")
            
            # Migrate existing categorias to jornadas
            # First, get all jornadas
            cursor.execute("SELECT id, categoria_id FROM jornadas")
            jornadas = cursor.fetchall()
            
            for jornada_id, old_cat_id in jornadas:
                # Update categorias that belong to this jornada
                cursor.execute(
                    "UPDATE categorias SET jornada_id = ? WHERE id = ?",
                    (jornada_id, old_cat_id)
                )
            print("Migrated categorias to jornada_id")
        
        # Remove old categoria_id from jornadas if it still exists
        if 'categoria_id' in columns:
            print("Removing categoria_id column from jornadas table...")
            # SQLite doesn't support DROP COLUMN directly, need to recreate table
            cursor.execute("""
                CREATE TABLE jornadas_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    torneo_id INTEGER,
                    fecha TEXT NOT NULL,
                    nombre TEXT,
                    orden INTEGER
                )
            """)
            # Copy data excluding categoria_id
            cursor.execute("""
                INSERT INTO jornadas_new (id, torneo_id, fecha, nombre, orden)
                SELECT id, torneo_id, fecha, nombre, orden FROM jornadas
            """)
            # Drop old table and rename new one
            cursor.execute("DROP TABLE jornadas")
            cursor.execute("ALTER TABLE jornadas_new RENAME TO jornadas")
            print("Removed categoria_id column from jornadas")

        con.commit()
        print("Migration completed successfully!")
        return True
        
    except Exception as e:
        con.rollback()
        print(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    migrate_to_torneo_hierarchy()
