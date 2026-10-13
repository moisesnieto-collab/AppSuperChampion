from typing import List, Dict, Any
from backend.models.partido import Partido
from functools import cmp_to_key
from backend.models.tabla import EstadisticaEquipo
from backend.models.copa import CRITERIOS_DEFECTO

class TablaService:
    @staticmethod
    def calcular_tabla(partidos: List[Partido], equipos: List[str], criterios: List[str] = None,
                       pts_victoria: int = 3, pts_empate: int = 1) -> List[EstadisticaEquipo]:
        """
        Calcula la tabla de posiciones a partir de los partidos jugados y la lista de equipos.
        Criterios de ordenamiento:
        1. Puntos (Pts) desc
        2. Diferencia de Goles (DG) desc
        3. Goles a Favor (GF) desc
        4. Enfrentamiento directo entre empatados
        5. Nombre de equipo asc
        """
        stats: Dict[str, EstadisticaEquipo] = {
            eq: EstadisticaEquipo(equipo=eq) for eq in equipos if eq
        }

        # Asegurar que cualquier equipo presente en los partidos esté en la tabla
        for p in partidos:
            if p.equipo_local and p.equipo_local not in stats:
                stats[p.equipo_local] = EstadisticaEquipo(equipo=p.equipo_local)
            if p.equipo_visita and p.equipo_visita not in stats:
                stats[p.equipo_visita] = EstadisticaEquipo(equipo=p.equipo_visita)

        # Procesar partidos jugados (excluyendo partidos de definición del cálculo de fase de grupos)
        partidos_jugados = [p for p in partidos if p.jugado and not p.es_definicion]

        for p in partidos_jugados:
            loc = p.equipo_local
            vis = p.equipo_visita
            g_loc = p.goles_local
            g_vis = p.goles_visita

            if loc not in stats or vis not in stats:
                continue

            stats[loc].pj += 1
            stats[vis].pj += 1
            stats[loc].gf += g_loc
            stats[loc].gc += g_vis
            stats[vis].gf += g_vis
            stats[vis].gc += g_loc

            stats[loc].dg = stats[loc].gf - stats[loc].gc
            stats[vis].dg = stats[vis].gf - stats[vis].gc

            if g_loc > g_vis:
                stats[loc].pg += 1
                stats[loc].pts += pts_victoria
                stats[vis].pp += 1
            elif g_loc < g_vis:
                stats[vis].pg += 1
                stats[vis].pts += pts_victoria
                stats[loc].pp += 1
            else:
                stats[loc].pe += 1
                stats[vis].pe += 1
                stats[loc].pts += pts_empate
                stats[vis].pts += pts_empate

        tabla = list(stats.values())
        criterios = criterios or CRITERIOS_DEFECTO.split(",")

        def directo(a: str, b: str):
            """(puntos de a, puntos de b, dif. de goles de a) en los partidos entre a y b."""
            pa = pb = dga = 0
            for p in partidos_jugados:
                if {p.equipo_local, p.equipo_visita} != {a, b}:
                    continue
                ga = p.goles_local if p.equipo_local == a else p.goles_visita
                gb = p.goles_visita if p.equipo_local == a else p.goles_local
                dga += ga - gb
                if ga > gb:
                    pa += pts_victoria
                elif ga < gb:
                    pb += pts_victoria
                else:
                    pa += pts_empate
                    pb += pts_empate
            return pa, pb, dga

        def comparar(x: EstadisticaEquipo, y: EstadisticaEquipo) -> int:
            if x.pts != y.pts:
                return -1 if x.pts > y.pts else 1
            for c in criterios:
                if c == "dg":
                    vx, vy = x.dg, y.dg
                elif c == "pg":
                    vx, vy = x.pg, y.pg
                elif c == "gf":
                    vx, vy = x.gf, y.gf
                elif c == "gc":
                    vx, vy = -x.gc, -y.gc
                elif c == "h2h":
                    vx, vy, _ = directo(x.equipo, y.equipo)
                elif c == "dg_h2h":
                    _, _, vx = directo(x.equipo, y.equipo)
                    vy = -vx
                else:
                    continue
                if vx != vy:
                    return -1 if vx > vy else 1
            return 0

        tabla.sort(key=cmp_to_key(lambda x, y: comparar(x, y) or ((x.equipo > y.equipo) - (x.equipo < y.equipo))))
        for i, e in enumerate(tabla):
            e.empate_con_siguiente = i + 1 < len(tabla) and comparar(e, tabla[i + 1]) == 0
        return tabla
