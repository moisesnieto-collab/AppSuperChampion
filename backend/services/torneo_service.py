from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from backend.database.repositories import (
    CategoriaRepository, GrupoRepository, PartidoRepository, ConfiguracionRepository, 
    JornadaRepository, TorneoRepository
)
from backend.models.categoria import Categoria
from backend.models.grupo import Grupo
from backend.models.partido import Partido
from backend.models.torneo import Torneo
from backend.models.jornada import Jornada
from backend.services.tabla_service import TablaService

class TorneoService:
    @staticmethod
    def validar_pin(pin: str) -> bool:
        """
        Valida si el PIN ingresado corresponde al PIN de Organizador.
        """
        pin_correcto = ConfiguracionRepository.obtener_pin()
        return str(pin).strip() == str(pin_correcto).strip()

    @staticmethod
    def cambiar_pin(pin_actual: str, pin_nuevo: str) -> bool:
        if not TorneoService.validar_pin(pin_actual):
            return False
        if not pin_nuevo or len(pin_nuevo.strip()) < 4:
            return False
        ConfiguracionRepository.actualizar_pin(pin_nuevo.strip())
        return True

    @staticmethod
    def obtener_torneos() -> List[Torneo]:
        return TorneoRepository.obtener_todos()

    @staticmethod
    def obtener_torneo_activo() -> Optional[Torneo]:
        return TorneoRepository.obtener_activo()

    @staticmethod
    def crear_torneo(nombre: str, tipo: str, copa_id: int, orden: int = 0, es_organizador: bool = False) -> int:
        if not es_organizador:
            raise PermissionError("Solo el organizador puede crear torneos")
        return TorneoRepository.crear(nombre, tipo, copa_id, orden)

    @staticmethod
    def actualizar_orden_torneo(torneo_id: int, orden: int, es_organizador: bool = False):
        if not es_organizador:
            raise PermissionError("Solo el organizador puede modificar el orden de torneos")
        TorneoRepository.actualizar_orden(torneo_id, orden)

    @staticmethod
    def eliminar_torneo(torneo_id: int, es_organizador: bool = False):
        if not es_organizador:
            raise PermissionError("Solo el organizador puede eliminar torneos")
        TorneoRepository.eliminar(torneo_id)

    @staticmethod
    def obtener_jornadas_por_torneo(torneo_id: int) -> List[Jornada]:
        return JornadaRepository.obtener_por_torneo(torneo_id)

    @staticmethod
    def obtener_categorias_por_jornada(jornada_id: int) -> List[Categoria]:
        return CategoriaRepository.obtener_por_jornada(jornada_id)

    @staticmethod
    def crear_categoria(jornada_id: int, nombre: str, es_organizador: bool = False) -> int:
        if not es_organizador:
            raise PermissionError("Solo el Organizador / Mesa de Control puede crear categorías.")

        nombre_limpio = nombre.strip()
        if not nombre_limpio:
            raise ValueError("El nombre de la categoría no puede estar vacío.")

        todas = CategoriaRepository.obtener_por_jornada(jornada_id)
        if any(c.nombre.lower() == nombre_limpio.lower() for c in todas):
            raise ValueError(f"La categoría '{nombre_limpio}' ya existe en esta jornada.")

        nuevo_orden = len(todas) + 1
        cat_id = CategoriaRepository.crear(jornada_id, nombre_limpio, nuevo_orden)

        # Crear grupos por defecto para la categoría
        equipos_a = ["Real Dunalastair", "Cobresal", "Colo-Colo", "U. de Chile"]
        g_a_id = GrupoRepository.crear(cat_id, jornada_id, "Grupo A", equipos_a)
        TorneoService._generar_partidos_cuadrangular(cat_id, jornada_id, g_a_id, equipos_a)

        equipos_b = ["U. Católica", "Palestino", "Audax Italiano", "Cobreloa"]
        g_b_id = GrupoRepository.crear(cat_id, jornada_id, "Grupo B", equipos_b)
        TorneoService._generar_partidos_cuadrangular(cat_id, jornada_id, g_b_id, equipos_b)

        return cat_id

    @staticmethod
    def eliminar_categoria(categoria_id: int, es_organizador: bool = False):
        if not es_organizador:
            raise PermissionError("Solo el Organizador / Mesa de Control puede eliminar categorías.")
        CategoriaRepository.eliminar(categoria_id)

    @staticmethod
    def crear_grupo(categoria_id: int, jornada_id: int, nombre: str, equipos: List[str], es_organizador: bool = False) -> int:
        if not es_organizador:
            raise PermissionError("Solo el Organizador / Mesa de Control puede crear grupos.")

        nombre_limpio = nombre.strip()
        if not nombre_limpio:
            raise ValueError("El nombre del grupo no puede estar vacío.")

        if len(equipos) < 2:
            raise ValueError("Un grupo debe tener al menos 2 equipos.")

        # Verificar que no exista un grupo con el mismo nombre en la misma categoría y jornada
        grupos_existentes = GrupoRepository.obtener_por_categoria_y_jornada(categoria_id, jornada_id)
        if any(g.nombre.lower() == nombre_limpio.lower() for g in grupos_existentes):
            raise ValueError(f"Ya existe un grupo llamado '{nombre_limpio}' en esta categoría y jornada.")

        grupo_id = GrupoRepository.crear(categoria_id, jornada_id, nombre_limpio, equipos)

        # Generar partidos automáticamente si hay 4 equipos (cuadrangular)
        if len(equipos) == 4:
            TorneoService._generar_partidos_cuadrangular(categoria_id, jornada_id, grupo_id, equipos)

        return grupo_id

    @staticmethod
    def actualizar_grupo(grupo_id: int, equipos: List[str], es_organizador: bool = False):
        if not es_organizador:
            raise PermissionError("Solo el Organizador / Mesa de Control puede modificar grupos.")

        if len(equipos) < 2:
            raise ValueError("Un grupo debe tener al menos 2 equipos.")

        # Obtener grupo actual
        grupo = GrupoRepository.obtener_por_id(grupo_id)
        if not grupo:
            raise ValueError("Grupo no encontrado.")

        # Eliminar partidos existentes (solo los no definición)
        PartidoRepository.eliminar_partidos_grupo(grupo_id, solo_no_definicion=True)

        # Actualizar equipos
        GrupoRepository.actualizar_equipos(grupo_id, equipos)

        # Regenerar partidos si hay 4 equipos (cuadrangular)
        if len(equipos) == 4:
            TorneoService._generar_partidos_cuadrangular(grupo.categoria_id, grupo.fecha_jornada_id, grupo_id, equipos)

    @staticmethod
    def eliminar_grupo(grupo_id: int, es_organizador: bool = False):
        if not es_organizador:
            raise PermissionError("Solo el Organizador / Mesa de Control puede eliminar grupos.")
        GrupoRepository.eliminar(grupo_id)

    @staticmethod
    def obtener_datos_categoria_dia(categoria_id: int, jornada_id: int) -> Dict[str, Any]:
        """
        Retorna la estructura completa de grupos, partidos, tablas y estado de campeón para la categoría y jornada.
        """
        grupos = GrupoRepository.obtener_por_categoria_y_jornada(categoria_id, jornada_id)
        todos_partidos = PartidoRepository.obtener_por_categoria_y_jornada(categoria_id, jornada_id)

        partidos_definicion = [p for p in todos_partidos if p.es_definicion]

        resultado_grupos = []
        for g in grupos:
            partidos_g = [p for p in todos_partidos if p.grupo_id == g.id and not p.es_definicion]
            tabla_g = TablaService.calcular_tabla(partidos_g, g.equipos)
            resultado_grupos.append({
                "grupo": g,
                "partidos": partidos_g,
                "tabla": tabla_g,
            })

        estado_campeon = TorneoService._calcular_estado_campeon(
            categoria_id, jornada_id, resultado_grupos, partidos_definicion
        )

        return {
            "grupos": resultado_grupos,
            "partidos_definicion": partidos_definicion,
            "estado_campeon": estado_campeon,
        }

    @staticmethod
    def guardar_marcador(partido_id: int, goles_local: int, goles_visita: int, es_organizador: bool = False):
        """
        Guarda o actualiza el marcador de un partido.
        """
        if not es_organizador:
            raise PermissionError("Acción bloqueada: solo la Mesa de Control / Organizador puede registrar marcadores.")
        
        if goles_local < 0 or goles_visita < 0:
            raise ValueError("Los goles no pueden ser negativos.")
        
        PartidoRepository.actualizar_marcador(partido_id, goles_local, goles_visita, jugado=True)

    @staticmethod
    def reiniciar_marcador(partido_id: int, es_organizador: bool = False):
        if not es_organizador:
            raise PermissionError("Acción bloqueada: solo la Mesa de Control / Organizador puede reiniciar marcadores.")
        PartidoRepository.actualizar_marcador(partido_id, 0, 0, jugado=False)

    @staticmethod
    def generar_partido_desempate(categoria_id: int, jornada_id: int, grupo_id: int, equipo1: str, equipo2: str, es_organizador: bool = False) -> int:
        if not es_organizador:
            raise PermissionError("Solo la Mesa de Control / Organizador puede generar partidos de desempate.")

        # Eliminar definiciones previas del mismo grupo si existieran
        todos = PartidoRepository.obtener_por_categoria_y_jornada(categoria_id, jornada_id)
        for p in todos:
            if p.es_definicion and p.grupo_id == grupo_id:
                # Actualizar o eliminar
                pass

        pid = PartidoRepository.crear(
            grupo_id=grupo_id,
            categoria_id=categoria_id,
            jornada_id=jornada_id,
            equipo_local=equipo1,
            equipo_visita=equipo2,
            goles_local=0,
            goles_visita=0,
            jugado=False,
            es_definicion=True,
            orden=99
        )
        return pid

    @staticmethod
    def generar_final_dia2(categoria_id: int, jornada_id: int, es_organizador: bool = False) -> Optional[int]:
        if not es_organizador:
            raise PermissionError("Solo la Mesa de Control / Organizador puede generar la Gran Final.")

        datos = TorneoService.obtener_datos_categoria_dia(categoria_id, jornada_id)
        grupos = datos["grupos"]
        if len(grupos) < 2:
            return None

        tabla_a = grupos[0]["tabla"]
        tabla_b = grupos[1]["tabla"]

        if not tabla_a or not tabla_b:
            return None

        lider_a = tabla_a[0].equipo
        lider_b = tabla_b[0].equipo

        # Revisar si ya existe
        for p in datos["partidos_definicion"]:
            if (p.equipo_local == lider_a and p.equipo_visita == lider_b) or (p.equipo_local == lider_b and p.equipo_visita == lider_a):
                return p.id

        # Crear partido final
        g_id = grupos[0]["grupo"].id
        pid = PartidoRepository.crear(
            grupo_id=g_id,
            categoria_id=categoria_id,
            jornada_id=jornada_id,
            equipo_local=lider_a,
            equipo_visita=lider_b,
            goles_local=0,
            goles_visita=0,
            jugado=False,
            es_definicion=True,
            orden=100
        )
        return pid

    @staticmethod
    def _calcular_estado_campeon(categoria_id: int, jornada_id: int, resultado_grupos: List[Dict[str, Any]], partidos_definicion: List[Partido]) -> Dict[str, Any]:
        """
        Determina el estado del campeonato para la categoría y día:
        - Si hay partido de definición jugado -> Ganador de la definición es Campeón
        - Si hay partido de definición pendiente -> Estado 'DESEMPATE_PENDIENTE'
        - Si todos los partidos del grupo se jugaron:
            - Si 1° tiene más puntos que 2° -> 'CAMPEON_DEFINIDO'
            - Si hay empate en el 1° lugar (pts, dg, gf) -> 'EMPATE_REQUIERE_DESEMPATE'
        - Si aún hay partidos en juego -> 'EN_CURSO'
        """
        # Si hay un partido de definición
        if partidos_definicion:
            partido_def = partidos_definicion[0]
            if partido_def.jugado:
                if partido_def.goles_local > partido_def.goles_visita:
                    ganador = partido_def.equipo_local
                    return {"estado": "CAMPEON_DEFINIDO", "campeon": ganador, "motivo": f"Ganador del Partido de Definición ({partido_def.goles_local} - {partido_def.goles_visita})"}
                elif partido_def.goles_visita > partido_def.goles_local:
                    ganador = partido_def.equipo_visita
                    return {"estado": "CAMPEON_DEFINIDO", "campeon": ganador, "motivo": f"Ganador del Partido de Definición ({partido_def.goles_visita} - {partido_def.goles_local})"}
                else:
                    return {"estado": "EMPATE_DEFINICION", "campeon": None, "motivo": "Empate en el Partido de Definición (Requiere penales)"}
            else:
                return {
                    "estado": "DESEMPATE_PENDIENTE",
                    "equipo1": partido_def.equipo_local,
                    "equipo2": partido_def.equipo_visita,
                    "partido_id": partido_def.id,
                    "motivo": f"Partido de Definición programado: {partido_def.equipo_local} vs {partido_def.equipo_visita}"
                }

        # Analizar grupos - verificar TODOS los grupos de la jornada
        if not resultado_grupos:
            return {"estado": "SIN_DATOS", "campeon": None, "motivo": "No hay grupos cargados"}

        # Calcular partidos totales y completados de TODOS los grupos
        partidos_totales_todos = 0
        partidos_completados_todos = 0

        for grupo_data in resultado_grupos:
            partidos = grupo_data["partidos"]
            partidos_totales_todos += len(partidos)
            partidos_completados_todos += sum(1 for p in partidos if p.jugado)

        # Si no todos los partidos de todos los grupos están jugados, seguir en curso
        if partidos_totales_todos > 0 and partidos_completados_todos < partidos_totales_todos:
            # Crear tabla global combinando todos los equipos de todos los grupos
            tabla_global = []
            for grupo_data in resultado_grupos:
                tabla = grupo_data["tabla"]
                for estadistica in tabla:
                    tabla_global.append(estadistica)
            
            # Ordenar tabla global por puntos, diferencia de gol, goles a favor
            tabla_global.sort(key=lambda x: (x.pts, x.dg, x.gf), reverse=True)
            
            # El puntero actual es el líder de la tabla global
            puntero_actual = tabla_global[0].equipo if tabla_global else "Por definir"

            return {
                "estado": "EN_CURSO",
                "puntero_actual": puntero_actual,
                "partidos_jugados": f"{partidos_completados_todos}/{partidos_totales_todos}",
                "motivo": f"Fase de grupos en desarrollo ({partidos_completados_todos}/{partidos_totales_todos} partidos)"
            }

        # Todos los partidos de todos los grupos están jugados
        # Analizar el primer grupo para determinar el campeón
        grupo_principal = resultado_grupos[0]
        tabla = grupo_principal["tabla"]

        if not tabla or len(tabla) < 2:
            return {"estado": "EN_CURSO", "campeon": None, "motivo": "Torneo en desarrollo"}

        e1 = tabla[0]
        e2 = tabla[1]
        # Lógica jerárquica: Puntos > Diferencia de Goles > Goles a Favor
        if e1.pts > e2.pts or (e1.pts == e2.pts and e1.dg > e2.dg) or (e1.pts == e2.pts and e1.dg == e2.dg and e1.gf > e2.gf):
            return {
                "estado": "CAMPEON_DEFINIDO",
                "campeon": e1.equipo,
                "motivo": f"Puntero exclusivo con {e1.pts} pts (DG: {e1.dg:+d})"
            }
        else:
            # Empate absoluto en primer lugar
            return {
                "estado": "EMPATE_REQUIERE_DESEMPATE",
                "equipo1": e1.equipo,
                "equipo2": e2.equipo,
                "grupo_id": grupo_principal["grupo"].id,
                "motivo": f"Empate absoluto en 1° lugar entre {e1.equipo} y {e2.equipo} ({e1.pts} pts, DG: {e1.dg:+d})"
            }

    @staticmethod
    def _generar_partidos_cuadrangular(cat_id: int, jornada_id: int, grupo_id: int, equipos: list):
        if len(equipos) < 4:
            return
        e1, e2, e3, e4 = equipos[0], equipos[1], equipos[2], equipos[3]
        fixture = [
            (e1, e2, 1),
            (e3, e4, 2),
            (e1, e3, 3),
            (e2, e4, 4),
            (e1, e4, 5),
            (e2, e3, 6),
        ]
        for eq_loc, eq_vis, ord_p in fixture:
            PartidoRepository.crear(
                grupo_id=grupo_id,
                categoria_id=cat_id,
                jornada_id=jornada_id,
                equipo_local=eq_loc,
                equipo_visita=eq_vis,
                orden=ord_p
            )
