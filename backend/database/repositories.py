import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.database.connection import obtener_conexion
from backend.models.categoria import Categoria
from backend.models.grupo import Grupo
from backend.models.partido import Partido
from backend.models.torneo import Torneo
from backend.models.jornada import Jornada
from backend.models.anio import Anio
from backend.models.campeonato import Campeonato
from backend.models.copa import Copa, MODO_CAMPEON_DEFECTO, CRITERIOS_DEFECTO
from backend.models.campeonato_permiso import CampeonatoPermiso


class TorneoRepository:
    @staticmethod
    def obtener_todos() -> List[Torneo]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("SELECT id, nombre, tipo, copa_id, orden, activo, fecha_inicio, fecha_fin FROM torneos ORDER BY orden ASC, id DESC")
        rows = cursor.fetchall()
        return [
            Torneo(
                id=r[0], nombre=r[1], tipo=r[2], copa_id=r[3], orden=r[4],
                activo=bool(r[5]), fecha_inicio=r[6], fecha_fin=r[7]
            )
            for r in rows
        ]

    @staticmethod
    def obtener_por_copa(copa_id: int) -> List[Torneo]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("SELECT id, nombre, tipo, copa_id, orden, activo, fecha_inicio, fecha_fin FROM torneos WHERE copa_id = ? ORDER BY orden ASC, id DESC", (copa_id,))
        rows = cursor.fetchall()
        return [
            Torneo(
                id=r[0], nombre=r[1], tipo=r[2], copa_id=r[3], orden=r[4],
                activo=bool(r[5]), fecha_inicio=r[6], fecha_fin=r[7]
            )
            for r in rows
        ]

    @staticmethod
    def obtener_por_id(torneo_id: int) -> Optional[Torneo]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute(
            "SELECT id, nombre, tipo, copa_id, orden, activo, fecha_inicio, fecha_fin FROM torneos WHERE id = ?",
            (torneo_id,)
        )
        row = cursor.fetchone()
        if row:
            return Torneo(
                id=row[0], nombre=row[1], tipo=row[2], copa_id=row[3], orden=row[4],
                activo=bool(row[5]), fecha_inicio=row[6], fecha_fin=row[7]
            )
        return None

    @staticmethod
    def obtener_activo() -> Optional[Torneo]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute(
            "SELECT id, nombre, tipo, copa_id, orden, activo, fecha_inicio, fecha_fin FROM torneos WHERE activo = 1 ORDER BY orden ASC, id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row:
            return Torneo(
                id=row[0], nombre=row[1], tipo=row[2], copa_id=row[3], orden=row[4],
                activo=bool(row[5]), fecha_inicio=row[6], fecha_fin=row[7]
            )
        return None

    @staticmethod
    def crear(nombre: str, tipo: str, copa_id: int, orden: int = 0, activo: bool = True, fecha_inicio: str = None, fecha_fin: str = None) -> int:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute(
            "INSERT INTO torneos (nombre, tipo, copa_id, orden, activo, fecha_inicio, fecha_fin) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (nombre, tipo, copa_id, orden, 1 if activo else 0, fecha_inicio, fecha_fin)
        )
        con.commit()
        return cursor.lastrowid

    @staticmethod
    def actualizar_activo(torneo_id: int, activo: bool):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute(
            "UPDATE torneos SET activo = ? WHERE id = ?",
            (1 if activo else 0, torneo_id)
        )
        con.commit()

    @staticmethod
    def actualizar_orden(torneo_id: int, orden: int):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute(
            "UPDATE torneos SET orden = ? WHERE id = ?",
            (orden, torneo_id)
        )
        con.commit()

    @staticmethod
    def eliminar(torneo_id: int):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("DELETE FROM torneos WHERE id = ?", (torneo_id,))
        con.commit()


class JornadaRepository:
    @staticmethod
    def obtener_por_torneo(torneo_id: int) -> List[Jornada]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute(
            "SELECT id, torneo_id, fecha, nombre, orden, lugar, horario FROM jornadas WHERE torneo_id = ? ORDER BY fecha ASC, orden ASC",
            (torneo_id,)
        )
        rows = cursor.fetchall()
        return [
            Jornada(id=r[0], torneo_id=r[1], fecha=r[2], nombre=r[3], orden=r[4], lugar=r[5], horario=r[6])
            for r in rows
        ]

    @staticmethod
    def obtener_por_id(jornada_id: int) -> Optional[Jornada]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute(
            "SELECT id, torneo_id, fecha, nombre, orden, lugar, horario FROM jornadas WHERE id = ?",
            (jornada_id,)
        )
        row = cursor.fetchone()
        if row:
            return Jornada(id=row[0], torneo_id=row[1], fecha=row[2], nombre=row[3], orden=row[4], lugar=row[5], horario=row[6])
        return None

    @staticmethod
    def crear(torneo_id: int, fecha: str, nombre: str, orden: int, lugar: str = None, horario: str = None) -> int:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute(
            "INSERT INTO jornadas (torneo_id, fecha, nombre, orden, lugar, horario) VALUES (?, ?, ?, ?, ?, ?)",
            (torneo_id, fecha, nombre, orden, lugar, horario)
        )
        con.commit()
        return cursor.lastrowid

    @staticmethod
    def actualizar(jornada_id: int, fecha: str, nombre: str, lugar: str = None, horario: str = None):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute(
            "UPDATE jornadas SET fecha = ?, nombre = ?, lugar = ?, horario = ? WHERE id = ?",
            (fecha, nombre, lugar, horario, jornada_id)
        )
        con.commit()

    @staticmethod
    def eliminar(jornada_id: int):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("DELETE FROM jornadas WHERE id = ?", (jornada_id,))
        con.commit()

    @staticmethod
    def buscar_por_fecha(torneo_id: int, fecha: str) -> Optional[Jornada]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute(
            "SELECT id, torneo_id, fecha, nombre, orden, lugar, horario FROM jornadas WHERE torneo_id = ? AND fecha = ?",
            (torneo_id, fecha)
        )
        row = cursor.fetchone()
        if row:
            return Jornada(id=row[0], torneo_id=row[1], fecha=row[2], nombre=row[3], orden=row[4], lugar=row[5], horario=row[6])
        return None


class CategoriaRepository:
    @staticmethod
    def obtener_por_jornada(jornada_id: int) -> List[Categoria]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute(
            "SELECT id, jornada_id, nombre, orden FROM categorias WHERE jornada_id = ? ORDER BY orden ASC, id ASC",
            (jornada_id,)
        )
        rows = cursor.fetchall()
        return [Categoria(id=r[0], jornada_id=r[1], nombre=r[2], orden=r[3]) for r in rows]

    @staticmethod
    def obtener_todas() -> List[Categoria]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("SELECT id, jornada_id, nombre, orden FROM categorias ORDER BY orden ASC, id ASC")
        rows = cursor.fetchall()
        return [Categoria(id=r[0], jornada_id=r[1], nombre=r[2], orden=r[3]) for r in rows]

    @staticmethod
    def obtener_por_id(categoria_id: int) -> Optional[Categoria]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("SELECT id, jornada_id, nombre, orden FROM categorias WHERE id = ?", (categoria_id,))
        row = cursor.fetchone()
        if row:
            return Categoria(id=row[0], jornada_id=row[1], nombre=row[2], orden=row[3])
        return None

    @staticmethod
    def crear(jornada_id: int, nombre: str, orden: int = 1) -> int:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("INSERT INTO categorias (jornada_id, nombre, orden) VALUES (?, ?, ?)", (jornada_id, nombre, orden))
        con.commit()
        return cursor.lastrowid

    @staticmethod
    def eliminar(categoria_id: int):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("DELETE FROM categorias WHERE id = ?", (categoria_id,))
        cursor.execute("DELETE FROM grupos WHERE categoria_id = ?", (categoria_id,))
        cursor.execute("DELETE FROM partidos WHERE categoria_id = ?", (categoria_id,))
        con.commit()


class GrupoRepository:
    @staticmethod
    def obtener_por_categoria_y_jornada(categoria_id: int, jornada_id: int) -> List[Grupo]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute(
            "SELECT id, categoria_id, fecha_jornada_id, nombre, equipos FROM grupos WHERE categoria_id = ? AND fecha_jornada_id = ? ORDER BY id ASC",
            (categoria_id, jornada_id)
        )
        rows = cursor.fetchall()
        grupos = []
        for r in rows:
            try:
                equipos = json.loads(r[4])
            except Exception:
                equipos = []
            grupos.append(Grupo(id=r[0], categoria_id=r[1], fecha_jornada_id=r[2], nombre=r[3], equipos=equipos))
        return grupos

    @staticmethod
    def crear(categoria_id: int, jornada_id: int, nombre: str, equipos: List[str]) -> int:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute(
            "INSERT INTO grupos (categoria_id, fecha_jornada_id, nombre, equipos) VALUES (?, ?, ?, ?)",
            (categoria_id, jornada_id, nombre, json.dumps(equipos))
        )
        con.commit()
        return cursor.lastrowid

    @staticmethod
    def actualizar_equipos(grupo_id: int, equipos: List[str]):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute(
            "UPDATE grupos SET equipos = ? WHERE id = ?",
            (json.dumps(equipos), grupo_id)
        )
        con.commit()

    @staticmethod
    def eliminar(grupo_id: int):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("DELETE FROM grupos WHERE id = ?", (grupo_id,))
        cursor.execute("DELETE FROM partidos WHERE grupo_id = ?", (grupo_id,))
        con.commit()

    @staticmethod
    def obtener_por_id(grupo_id: int) -> Optional[Grupo]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute(
            "SELECT id, categoria_id, fecha_jornada_id, nombre, equipos FROM grupos WHERE id = ?",
            (grupo_id,)
        )
        row = cursor.fetchone()
        if row:
            try:
                equipos = json.loads(row[4])
            except Exception:
                equipos = []
            return Grupo(id=row[0], categoria_id=row[1], fecha_jornada_id=row[2], nombre=row[3], equipos=equipos)
        return None


class PartidoRepository:
    @staticmethod
    def obtener_por_grupo(grupo_id: int) -> List[Partido]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("""
            SELECT id, grupo_id, categoria_id, fecha_jornada_id, equipo_local, equipo_visita,
                   goles_local, goles_visita, jugado, es_definicion, orden
            FROM partidos
            WHERE grupo_id = ?
            ORDER BY orden ASC, id ASC
        """, (grupo_id,))
        rows = cursor.fetchall()
        return [
            Partido(
                id=r[0], grupo_id=r[1], categoria_id=r[2], fecha_jornada_id=r[3],
                equipo_local=r[4], equipo_visita=r[5], goles_local=r[6],
                goles_visita=r[7], jugado=bool(r[8]), es_definicion=bool(r[9]), orden=r[10]
            )
            for r in rows
        ]

    @staticmethod
    def obtener_por_categoria_y_jornada(categoria_id: int, jornada_id: int) -> List[Partido]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("""
            SELECT id, grupo_id, categoria_id, fecha_jornada_id, equipo_local, equipo_visita,
                   goles_local, goles_visita, jugado, es_definicion, orden
            FROM partidos
            WHERE categoria_id = ? AND fecha_jornada_id = ?
            ORDER BY grupo_id ASC, orden ASC, id ASC
        """, (categoria_id, jornada_id))
        rows = cursor.fetchall()
        return [
            Partido(
                id=r[0], grupo_id=r[1], categoria_id=r[2], fecha_jornada_id=r[3],
                equipo_local=r[4], equipo_visita=r[5], goles_local=r[6],
                goles_visita=r[7], jugado=bool(r[8]), es_definicion=bool(r[9]), orden=r[10]
            )
            for r in rows
        ]

    @staticmethod
    def obtener_por_id(partido_id: int) -> Optional[Partido]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("""
            SELECT id, grupo_id, categoria_id, fecha_jornada_id, equipo_local, equipo_visita,
                   goles_local, goles_visita, jugado, es_definicion, orden
            FROM partidos
            WHERE id = ?
        """, (partido_id,))
        r = cursor.fetchone()
        if r:
            return Partido(
                id=r[0], grupo_id=r[1], categoria_id=r[2], fecha_jornada_id=r[3],
                equipo_local=r[4], equipo_visita=r[5], goles_local=r[6],
                goles_visita=r[7], jugado=bool(r[8]), es_definicion=bool(r[9]), orden=r[10]
            )
        return None

    @staticmethod
    def crear(grupo_id: int, categoria_id: int, jornada_id: int, equipo_local: str, equipo_visita: str,
              goles_local: int = 0, goles_visita: int = 0, jugado: bool = False,
              es_definicion: bool = False, orden: int = 0) -> int:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("""
            INSERT INTO partidos
            (grupo_id, categoria_id, fecha_jornada_id, equipo_local, equipo_visita, goles_local, goles_visita, jugado, es_definicion, orden)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (grupo_id, categoria_id, jornada_id, equipo_local, equipo_visita, goles_local, goles_visita, 1 if jugado else 0, 1 if es_definicion else 0, orden))
        con.commit()
        return cursor.lastrowid

    @staticmethod
    def actualizar_marcador(partido_id: int, goles_local: int, goles_visita: int, jugado: bool = True):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("""
            UPDATE partidos
            SET goles_local = ?, goles_visita = ?, jugado = ?
            WHERE id = ?
        """, (goles_local, goles_visita, 1 if jugado else 0, partido_id))
        con.commit()

    @staticmethod
    def eliminar_partidos_grupo(grupo_id: int, solo_no_definicion: bool = False):
        con = obtener_conexion()
        cursor = con.cursor()
        if solo_no_definicion:
            cursor.execute(
                "DELETE FROM partidos WHERE grupo_id = ? AND es_definicion = 0",
                (grupo_id,)
            )
        else:
            cursor.execute("DELETE FROM partidos WHERE grupo_id = ?", (grupo_id,))
        con.commit()

    @staticmethod
    def eliminar_partidos_definicion(categoria_id: int, jornada_id: int):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute(
            "DELETE FROM partidos WHERE categoria_id = ? AND fecha_jornada_id = ? AND es_definicion = 1",
            (categoria_id, jornada_id)
        )
        con.commit()


class ConfiguracionRepository:
    @staticmethod
    def obtener_pin() -> str:
        from config.settings import ORGANIZADOR_PIN
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("SELECT valor FROM configuracion WHERE clave = 'pin_organizador'")
        row = cursor.fetchone()
        if row:
            return row[0]
        return ORGANIZADOR_PIN

    @staticmethod
    def obtener_pin_master() -> str:
        from config.settings import MASTER_PIN
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("SELECT valor FROM configuracion WHERE clave = 'pin_master'")
        row = cursor.fetchone()
        if row:
            return row[0]
        return MASTER_PIN

    @staticmethod
    def actualizar_pin(nuevo_pin: str):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("""
            INSERT INTO configuracion (clave, valor) VALUES ('pin_organizador', ?)
            ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor
        """, (nuevo_pin,))
        con.commit()


class AnioRepository:
    @staticmethod
    def obtener_todos() -> List[Anio]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("SELECT id, valor, orden, activo FROM anios ORDER BY orden ASC, valor DESC")
        rows = cursor.fetchall()
        return [Anio(id=r[0], valor=r[1], orden=r[2], activo=bool(r[3])) for r in rows]

    @staticmethod
    def obtener_por_id(anio_id: int) -> Optional[Anio]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("SELECT id, valor, orden, activo FROM anios WHERE id = ?", (anio_id,))
        row = cursor.fetchone()
        if row:
            return Anio(id=row[0], valor=row[1], orden=row[2], activo=bool(row[3]))
        return None

    @staticmethod
    def obtener_activo() -> Optional[Anio]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("SELECT id, valor, orden, activo FROM anios WHERE activo = 1 ORDER BY orden ASC, valor DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            return Anio(id=row[0], valor=row[1], orden=row[2], activo=bool(row[3]))
        return None

    @staticmethod
    def crear(valor: int, orden: int = 0, activo: bool = True) -> int:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("INSERT INTO anios (valor, orden, activo) VALUES (?, ?, ?)", (valor, orden, 1 if activo else 0))
        con.commit()
        return cursor.lastrowid

    @staticmethod
    def actualizar_activo(anio_id: int, activo: bool):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("UPDATE anios SET activo = ? WHERE id = ?", (1 if activo else 0, anio_id))
        con.commit()

    @staticmethod
    def actualizar_orden(anio_id: int, orden: int):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("UPDATE anios SET orden = ? WHERE id = ?", (orden, anio_id))
        con.commit()

    @staticmethod
    def actualizar(anio_id: int, valor: int, orden: int = 0, activo: bool = True):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("UPDATE anios SET valor = ?, orden = ?, activo = ? WHERE id = ?", (valor, orden, 1 if activo else 0, anio_id))
        con.commit()

    @staticmethod
    def eliminar(anio_id: int):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("DELETE FROM anios WHERE id = ?", (anio_id,))
        con.commit()


class CampeonatoRepository:
    @staticmethod
    def obtener_todos() -> List[Campeonato]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("SELECT id, nombre, anio_id, orden, activo FROM campeonatos ORDER BY orden ASC, id DESC")
        rows = cursor.fetchall()
        return [Campeonato(id=r[0], nombre=r[1], anio_id=r[2], orden=r[3], activo=bool(r[4])) for r in rows]

    @staticmethod
    def obtener_por_id(campeonato_id: int) -> Optional[Campeonato]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("SELECT id, nombre, anio_id, orden, activo FROM campeonatos WHERE id = ?", (campeonato_id,))
        row = cursor.fetchone()
        if row:
            return Campeonato(id=row[0], nombre=row[1], anio_id=row[2], orden=row[3], activo=bool(row[4]))
        return None

    @staticmethod
    def obtener_por_anio(anio_id: int) -> List[Campeonato]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("SELECT id, nombre, anio_id, orden, activo FROM campeonatos WHERE anio_id = ? ORDER BY orden ASC, id DESC", (anio_id,))
        rows = cursor.fetchall()
        return [Campeonato(id=r[0], nombre=r[1], anio_id=r[2], orden=r[3], activo=bool(r[4])) for r in rows]

    @staticmethod
    def obtener_activo() -> Optional[Campeonato]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("SELECT id, nombre, anio_id, orden, activo FROM campeonatos WHERE activo = 1 ORDER BY orden ASC, id DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            return Campeonato(id=row[0], nombre=row[1], anio_id=row[2], orden=row[3], activo=bool(row[4]))
        return None

    @staticmethod
    def crear(nombre: str, anio_id: int, orden: int = 0, activo: bool = True) -> int:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("INSERT INTO campeonatos (nombre, anio_id, orden, activo) VALUES (?, ?, ?, ?)", (nombre, anio_id, orden, 1 if activo else 0))
        con.commit()
        return cursor.lastrowid

    @staticmethod
    def actualizar_activo(campeonato_id: int, activo: bool):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("UPDATE campeonatos SET activo = ? WHERE id = ?", (1 if activo else 0, campeonato_id))
        con.commit()

    @staticmethod
    def actualizar_orden(campeonato_id: int, orden: int):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("UPDATE campeonatos SET orden = ? WHERE id = ?", (orden, campeonato_id))
        con.commit()

    @staticmethod
    def actualizar(campeonato_id: int, nombre: str, anio_id: int, orden: int = 0, activo: bool = True):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("UPDATE campeonatos SET nombre = ?, anio_id = ?, orden = ?, activo = ? WHERE id = ?", (nombre, anio_id, orden, 1 if activo else 0, campeonato_id))
        con.commit()

    @staticmethod
    def eliminar(campeonato_id: int):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("DELETE FROM campeonatos WHERE id = ?", (campeonato_id,))
        con.commit()


def _a_copa(r) -> Copa:
    return Copa(id=r[0], nombre=r[1], campeonato_id=r[2], orden=r[3], activo=bool(r[4]), color=r[5],
                modo_campeon=r[6] or MODO_CAMPEON_DEFECTO,
                criterios_desempate=r[7] or CRITERIOS_DEFECTO,
                puntos_victoria=3 if r[8] is None else r[8],
                puntos_empate=1 if r[9] is None else r[9])


class CopaRepository:
    @staticmethod
    def obtener_todos() -> List[Copa]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("SELECT id, nombre, campeonato_id, orden, activo, color, modo_campeon, criterios_desempate, puntos_victoria, puntos_empate FROM copas ORDER BY orden ASC, id DESC")
        rows = cursor.fetchall()
        return [_a_copa(r) for r in rows]

    @staticmethod
    def obtener_por_id(copa_id: int) -> Optional[Copa]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("SELECT id, nombre, campeonato_id, orden, activo, color, modo_campeon, criterios_desempate, puntos_victoria, puntos_empate FROM copas WHERE id = ?", (copa_id,))
        row = cursor.fetchone()
        if row:
            return _a_copa(row)
        return None

    @staticmethod
    def obtener_por_campeonato(campeonato_id: int) -> List[Copa]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("SELECT id, nombre, campeonato_id, orden, activo, color, modo_campeon, criterios_desempate, puntos_victoria, puntos_empate FROM copas WHERE campeonato_id = ? ORDER BY orden ASC, id DESC", (campeonato_id,))
        rows = cursor.fetchall()
        return [_a_copa(r) for r in rows]

    @staticmethod
    def obtener_activo() -> Optional[Copa]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("SELECT id, nombre, campeonato_id, orden, activo, color, modo_campeon, criterios_desempate, puntos_victoria, puntos_empate FROM copas WHERE activo = 1 ORDER BY orden ASC, id DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            return _a_copa(row)
        return None

    @staticmethod
    def crear(nombre: str, campeonato_id: int, orden: int = 0, activo: bool = True, color: Optional[str] = None,
              modo_campeon: str = MODO_CAMPEON_DEFECTO, criterios_desempate: str = CRITERIOS_DEFECTO,
              puntos_victoria: int = 3, puntos_empate: int = 1) -> int:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("INSERT INTO copas (nombre, campeonato_id, orden, activo, color, modo_campeon, criterios_desempate, puntos_victoria, puntos_empate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (nombre, campeonato_id, orden, 1 if activo else 0, color, modo_campeon, criterios_desempate, puntos_victoria, puntos_empate))
        con.commit()
        return cursor.lastrowid

    @staticmethod
    def actualizar_activo(copa_id: int, activo: bool):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("UPDATE copas SET activo = ? WHERE id = ?", (1 if activo else 0, copa_id))
        con.commit()

    @staticmethod
    def actualizar_orden(copa_id: int, orden: int):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("UPDATE copas SET orden = ? WHERE id = ?", (orden, copa_id))
        con.commit()

    @staticmethod
    def actualizar(copa_id: int, nombre: str, campeonato_id: int, orden: int = 0, activo: bool = True, color: Optional[str] = None,
                   modo_campeon: str = MODO_CAMPEON_DEFECTO, criterios_desempate: str = CRITERIOS_DEFECTO,
                   puntos_victoria: int = 3, puntos_empate: int = 1):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("UPDATE copas SET nombre = ?, campeonato_id = ?, orden = ?, activo = ?, color = ?, modo_campeon = ?, criterios_desempate = ?, puntos_victoria = ?, puntos_empate = ? WHERE id = ?",
                       (nombre, campeonato_id, orden, 1 if activo else 0, color, modo_campeon, criterios_desempate, puntos_victoria, puntos_empate, copa_id))
        con.commit()

    @staticmethod
    def eliminar(copa_id: int):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("DELETE FROM copas WHERE id = ?", (copa_id,))
        con.commit()


class CampeonatoPermisoRepository:
    @staticmethod
    def obtener_por_campeonato(campeonato_id: int) -> List[CampeonatoPermiso]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("SELECT id, campeonato_id, usuario_id, rol, fecha_asignacion FROM campeonato_permisos WHERE campeonato_id = ?", (campeonato_id,))
        rows = cursor.fetchall()
        return [CampeonatoPermiso(id=r[0], campeonato_id=r[1], usuario_id=r[2], rol=r[3], fecha_asignacion=r[4]) for r in rows]

    @staticmethod
    def obtener_por_usuario(usuario_id: int) -> List[CampeonatoPermiso]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("SELECT id, campeonato_id, usuario_id, rol, fecha_asignacion FROM campeonato_permisos WHERE usuario_id = ?", (usuario_id,))
        rows = cursor.fetchall()
        return [CampeonatoPermiso(id=r[0], campeonato_id=r[1], usuario_id=r[2], rol=r[3], fecha_asignacion=r[4]) for r in rows]

    @staticmethod
    def asignar_permiso(campeonato_id: int, usuario_id: int, rol: str) -> int:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("INSERT INTO campeonato_permisos (campeonato_id, usuario_id, rol) VALUES (?, ?, ?)", (campeonato_id, usuario_id, rol))
        con.commit()
        return cursor.lastrowid

    @staticmethod
    def revocar_permiso(campeonato_id: int, usuario_id: int):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("DELETE FROM campeonato_permisos WHERE campeonato_id = ? AND usuario_id = ?", (campeonato_id, usuario_id))
        con.commit()

    @staticmethod
    def verificar_permiso(campeonato_id: int, usuario_id: int) -> Optional[str]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("SELECT rol FROM campeonato_permisos WHERE campeonato_id = ? AND usuario_id = ?", (campeonato_id, usuario_id))
        row = cursor.fetchone()
        if row:
            return row[0]
        return None
