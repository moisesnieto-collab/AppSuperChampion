import threading
import libsql_experimental as sqlite3
import config.settings as settings

import time

_local = threading.local()

# Caché de lecturas (SELECT) de vida corta: evita ir a la red por cada consulta repetida.
_TTL = 3.0
_cache = {}
_cache_lock = threading.Lock()


def _es_error_conexion(err: Exception) -> bool:
    texto = str(err).lower()
    return "hrana" in texto or "connection closed" in texto or "stream" in texto and "expired" in texto


def _nueva_conexion():
    clave = (settings.TURSO_URL, settings.TURSO_TOKEN)
    con = sqlite3.connect(settings.TURSO_URL, auth_token=settings.TURSO_TOKEN)
    _local.con = con
    _local.clave = clave
    return con


class _Cursor:
    """Cursor que reconecta y reintenta una vez si Turso cerró la conexión inactiva."""

    def __init__(self, cur):
        self._cur = cur

    _rows = None
    _pos = 0

    def _ejecutar(self, *args, **kwargs):
        try:
            self._cur.execute(*args, **kwargs)
        except ValueError as err:
            if not _es_error_conexion(err):
                raise
            self._cur = _nueva_conexion().cursor()
            self._cur.execute(*args, **kwargs)

    def execute(self, *args, **kwargs):
        self._rows = None
        self._pos = 0
        sql = str(args[0]).lstrip().upper() if args else ""
        if not sql.startswith(("SELECT", "PRAGMA")) or kwargs:
            with _cache_lock:
                _cache.clear()
            self._ejecutar(*args, **kwargs)
            return self
        try:
            clave = (settings.TURSO_URL, args[0], repr(args[1:]))
        except Exception:
            clave = None
        ahora = time.monotonic()
        with _cache_lock:
            hit = _cache.get(clave) if clave else None
        if hit and ahora - hit[0] < _TTL:
            self._rows = hit[1]
            self.description = hit[2]
            return self
        self._ejecutar(*args, **kwargs)
        rows = self._cur.fetchall()
        desc = getattr(self._cur, "description", None)
        self._rows = rows
        self.description = desc
        if clave:
            with _cache_lock:
                _cache[clave] = (ahora, rows, desc)
        return self

    def fetchall(self):
        if self._rows is None:
            return self._cur.fetchall()
        r = self._rows[self._pos:]
        self._pos = len(self._rows)
        return list(r)

    def fetchone(self):
        if self._rows is None:
            return self._cur.fetchone()
        if self._pos >= len(self._rows):
            return None
        self._pos += 1
        return self._rows[self._pos - 1]

    def __getattr__(self, nombre):
        return getattr(self._cur, nombre)


class _Conexion:
    def __init__(self, con):
        self._con = con

    def cursor(self):
        return _Cursor(self._con.cursor())

    def commit(self):
        with _cache_lock:
            _cache.clear()
        return self._con.commit()

    def __getattr__(self, nombre):
        return getattr(self._con, nombre)


def obtener_conexion():
    """Devuelve una conexión Turso/LibSQL reutilizada por hilo.

    Abrir una conexión nueva en cada consulta implica un handshake de red
    completo contra Turso. Si la conexión reutilizada se cierra por
    inactividad, el cursor reconecta y reintenta automáticamente.
    """
    clave = (settings.TURSO_URL, settings.TURSO_TOKEN)
    con = getattr(_local, "con", None)
    if con is None or getattr(_local, "clave", None) != clave:
        con = _nueva_conexion()
    return _Conexion(con)
