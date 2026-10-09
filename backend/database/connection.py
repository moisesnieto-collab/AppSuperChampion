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

    # Si TURSO_TOKEN está presente y URL es de turso, usar API HTTP
    if TURSO_TOKEN and TURSO_URL and TURSO_URL.startswith(("libsql://", "https://", "http://")):
        try:
            if _CONEXION_TURSO is None:
                _CONEXION_TURSO = TursoConnection(TURSO_URL, TURSO_TOKEN)
            return _CONEXION_TURSO
        except Exception as e:
            print(f"Error conectando a Turso: {e}. Usando SQLite local.")

    # Base de datos local SQLite
    con = sqlite3.connect(TURSO_URL or "superchampion.db", check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


class TursoConnection:
    """Wrapper para usar la API HTTP de Turso"""
    def __init__(self, url, token):
        self.url = url.replace("libsql://", "https://")
        self.token = token

    def cursor(self):
        return TursoCursor(self.url, self.token)

    def commit(self):
        pass  # Turso maneja commits automáticamente

    def close(self):
        pass


class TursoCursor:
    """Wrapper para adaptar la API HTTP de Turso a la de sqlite3"""
    def __init__(self, url, token):
        self.url = url
        self.token = token
        self._results = None
        self._lastrowid = None

    def execute(self, sql, params=None):
        import requests
        headers = {"Authorization": f"Bearer {self.token}"}

        if params:
            # Convertir params a formato de Turso
            data = {"statements": [{"q": sql, "params": params}]}
        else:
            data = {"statements": [{"q": sql}]}

        response = requests.post(f"{self.url}", json=data, headers=headers)
        response.raise_for_status()
        result = response.json()

        # La API de Turso devuelve una lista de resultados
        if isinstance(result, list) and len(result) > 0:
            first_result = result[0]
            self._results = first_result.get("response", {}).get("rows", [])
            self._lastrowid = first_result.get("last_insert_rowid")
        elif isinstance(result, dict) and result.get("results"):
            first_result = result["results"][0]
            self._results = first_result.get("response", {}).get("rows", [])
            self._lastrowid = first_result.get("last_insert_rowid")
        else:
            self._results = []

        return self

    def fetchall(self):
        return self._results if self._results else []

    def fetchone(self):
        if self._results and len(self._results) > 0:
            return self._results[0]
        return None

    def executemany(self, sql, params_list):
        import requests
        headers = {"Authorization": f"Bearer {self.token}"}
        
        statements = [{"q": sql, "params": params} for params in params_list]
        data = {"statements": statements}
        
        response = requests.post(f"{self.url}", json=data, headers=headers)
        response.raise_for_status()
        
        return self

    @property
    def lastrowid(self):
        return self._lastrowid
