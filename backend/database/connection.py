import os
import sqlite3
from typing import Any
from config.settings import TURSO_URL, TURSO_TOKEN

_CONEXION_TURSO = None

def obtener_conexion() -> Any:
    """
    Retorna una conexión a la base de datos (Turso si está configurado o SQLite local).
    """
    global _CONEXION_TURSO
    
    # Si TURSO_TOKEN está presente y URL es de turso, usar libsql_experimental
    if TURSO_TOKEN and TURSO_URL and TURSO_URL.startswith(("libsql://", "https://", "http://")):
        try:
            import libsql_experimental as libsql
            if _CONEXION_TURSO is None:
                _CONEXION_TURSO = libsql.connect(TURSO_URL, auth_token=TURSO_TOKEN)
            return _CONEXION_TURSO
        except Exception as e:
            print(f"Error conectando a Turso: {e}. Usando SQLite local.")
    
    # Base de datos local SQLite / LibSQL local
    try:
        import libsql_experimental as libsql
        return libsql.connect(TURSO_URL or "superchampion.db")
    except Exception:
        con = sqlite3.connect(TURSO_URL or "superchampion.db", check_same_thread=False)
        con.row_factory = sqlite3.Row
        return con
