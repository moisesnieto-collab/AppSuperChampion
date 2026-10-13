import threading
import libsql_experimental as sqlite3
import config.settings as settings

_local = threading.local()


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

    def execute(self, *args, **kwargs):
        try:
            self._cur.execute(*args, **kwargs)
        except ValueError as err:
            if not _es_error_conexion(err):
                raise
            self._cur = _nueva_conexion().cursor()
            self._cur.execute(*args, **kwargs)
        return self

    def __getattr__(self, nombre):
        return getattr(self._cur, nombre)


class _Conexion:
    def __init__(self, con):
        self._con = con

    def cursor(self):
        return _Cursor(self._con.cursor())

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
