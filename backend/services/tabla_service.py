from typing import List, Dict, Any
from backend.models.partido import Partido
from backend.models.tabla import EstadisticaEquipo

class TablaService:
    @staticmethod
    def calcular_tabla(partidos: List[Partido], equipos: List[str]) -> List[EstadisticaEquipo]:
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
                stats[loc].pts += 3
                stats[vis].pp += 1
            elif g_loc < g_vis:
                stats[vis].pg += 1
                stats[vis].pts += 3
                stats[loc].pp += 1
            else:
                stats[loc].pe += 1
                stats[vis].pe += 1
                stats[loc].pts += 1
                stats[vis].pts += 1

        tabla = list(stats.values())

        # Ordenamiento preliminar por Puntos, DG, GF
        def criterio_base(item: EstadisticaEquipo):
            return (-item.pts, -item.dg, -item.gf, item.equipo)

        tabla.sort(key=criterio_base)

        # Criterio de desempate por enfrentamiento directo si hay 2 equipos empatados en Pts, DG, GF
        if len(tabla) >= 2:
            for i in range(len(tabla) - 1):
                e1 = tabla[i]
                e2 = tabla[i + 1]
                if e1.pts == e2.pts and e1.dg == e2.dg and e1.gf == e2.gf:
                    # Buscar enfrentamiento directo entre e1 y e2
                    for p in partidos_jugados:
                        if (p.equipo_local == e1.equipo and p.equipo_visita == e2.equipo) or \
                           (p.equipo_local == e2.equipo and p.equipo_visita == e1.equipo):
                            g_e1 = p.goles_local if p.equipo_local == e1.equipo else p.goles_visita
                            g_e2 = p.goles_visita if p.equipo_local == e1.equipo else p.goles_local
                            if g_e2 > g_e1:
                                # e2 ganó el enfrentamiento directo -> intercambiar
                                tabla[i], tabla[i + 1] = tabla[i + 1], tabla[i]
                            break

        return tabla
