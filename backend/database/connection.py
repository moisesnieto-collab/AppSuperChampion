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

    # Si TURSO_TOKEN está presente y URL es de turso, usar cliente turso
    if TURSO_TOKEN and TURSO_URL and TURSO_URL.startswith(("libsql://", "https://", "http://")):
        try:
            from turso import Client
            if _CONEXION_TURSO is None:
                _CONEXION_TURSO = Client(url=TURSO_URL, auth_token=TURSO_TOKEN)
            return TursoConnection(_CONEXION_TURSO)
        except Exception as e:
            print(f"Error conectando a Turso: {e}. Usando SQLite local.")

    # Base de datos local SQLite
    con = sqlite3.connect(TURSO_URL or "superchampion.db", check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


class TursoConnection:
    """Wrapper para adaptar la API de Turso a la de sqlite3"""
    def __init__(self, client):
        self.client = client

    def cursor(self):
        return TursoCursor(self.client)

    def commit(self):
        pass  # Turso maneja commits automáticamente

    def close(self):
        pass


class TursoCursor:
    """Wrapper para adaptar el cursor de Turso a la de sqlite3"""
    def __init__(self, client):
        self.client = client
        self._results = None

    def execute(self, sql, params=None):
        if params:
            self._results = self.client.execute(sql, params)
        else:
            self._results = self.client.execute(sql)
        return self

    def fetchall(self):
        if self._results:
            return self._results
        return []

    def fetchone(self):
        if self._results and len(self._results) > 0:
            return self._results[0]
        return None

    def executemany(self, sql, params_list):
        for params in params_list:
            self.client.execute(sql, params)
        return self
