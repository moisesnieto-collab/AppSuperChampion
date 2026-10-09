import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.database.connection import obtener_conexion
from backend.models.categoria import Categoria
from backend.models.grupo import Grupo
from backend.models.partido import Partido


class JornadaRepository:
    @staticmethod
    def obtener_por_categoria(categoria_id: int) -> List[Dict[str, Any]]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute(
            "SELECT id, categoria_id, fecha, nombre, orden FROM jornadas WHERE categoria_id = ? ORDER BY orden ASC, fecha ASC",
            (categoria_id,)
        )
        rows = cursor.fetchall()
        return [
            {
                "id": r[0],
                "categoria_id": r[1],
                "fecha": r[2],
                "nombre": r[3],
                "orden": r[4]
            }
            for r in rows
        ]

    @staticmethod
    def obtener_por_id(jornada_id: int) -> Optional[Dict[str, Any]]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute(
            "SELECT id, categoria_id, fecha, nombre, orden FROM jornadas WHERE id = ?",
            (jornada_id,)
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "categoria_id": row[1],
                "fecha": row[2],
                "nombre": row[3],
                "orden": row[4]
            }
        return None

    @staticmethod
    def crear(categoria_id: int, fecha: str, nombre: str, orden: int) -> int:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute(
            "INSERT INTO jornadas (categoria_id, fecha, nombre, orden) VALUES (?, ?, ?, ?)",
            (categoria_id, fecha, nombre, orden)
        )
        con.commit()
        return cursor.lastrowid

    @staticmethod
    def actualizar(jornada_id: int, fecha: str, nombre: str):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute(
            "UPDATE jornadas SET fecha = ?, nombre = ? WHERE id = ?",
            (fecha, nombre, jornada_id)
        )
        con.commit()

    @staticmethod
    def eliminar(jornada_id: int):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("DELETE FROM jornadas WHERE id = ?", (jornada_id,))
        con.commit()

    @staticmethod
    def buscar_por_fecha(categoria_id: int, fecha: str) -> Optional[Dict[str, Any]]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute(
            "SELECT id, categoria_id, fecha, nombre, orden FROM jornadas WHERE categoria_id = ? AND fecha = ?",
            (categoria_id, fecha)
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "categoria_id": row[1],
                "fecha": row[2],
                "nombre": row[3],
                "orden": row[4]
            }
        return None


class CategoriaRepository:
    @staticmethod
    def obtener_todas() -> List[Categoria]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("SELECT id, nombre, orden FROM categorias ORDER BY orden ASC, id ASC")
        rows = cursor.fetchall()
        return [Categoria(id=r[0], nombre=r[1], orden=r[2]) for r in rows]

    @staticmethod
    def obtener_por_id(categoria_id: int) -> Optional[Categoria]:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("SELECT id, nombre, orden FROM categorias WHERE id = ?", (categoria_id,))
        row = cursor.fetchone()
        if row:
            return Categoria(id=row[0], nombre=row[1], orden=row[2])
        return None

    @staticmethod
    def crear(nombre: str, orden: int = 1) -> int:
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("INSERT INTO categorias (nombre, orden) VALUES (?, ?)", (nombre, orden))
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
            grupos.append(Grupo(id=r[0], categoria_id=r[1], dia=jornada_id, nombre=r[3], equipos=equipos))
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
            return Grupo(id=row[0], categoria_id=row[1], dia=row[2], nombre=row[3], equipos=equipos)
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
                id=r[0], grupo_id=r[1], categoria_id=r[2], dia=r[3],
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
                id=r[0], grupo_id=r[1], categoria_id=r[2], dia=r[3],
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
                id=r[0], grupo_id=r[1], categoria_id=r[2], dia=r[3],
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
    def actualizar_pin(nuevo_pin: str):
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("""
            INSERT INTO configuracion (clave, valor) VALUES ('pin_organizador', ?)
            ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor
        """, (nuevo_pin,))
        con.commit()
