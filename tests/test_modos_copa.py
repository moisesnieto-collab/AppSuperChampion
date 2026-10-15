"""Pruebas exhaustivas para todos los modos de Copa: final_lideres, liguilla_lideres, tabla_unica"""
import os
import shutil
import tempfile
import unittest

from backend.database.schema import inicializar_db
from backend.database.repositories import JornadaRepository, PartidoRepository, GrupoRepository, CategoriaRepository, TorneoRepository
from backend.services.anio_service import AnioService
from backend.services.campeonato_service import CampeonatoService
from backend.services.copa_service import CopaService
from backend.services.torneo_service import TorneoService

EQUIPOS = ["Alfa", "Beta", "Gama", "Delta"]


class BaseDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp()
        import config.settings
        cls.original = config.settings.TURSO_URL
        config.settings.TURSO_URL = os.path.join(cls.dir, "test_modos_copa.db")
        config.settings.TURSO_TOKEN = ""
        inicializar_db()

    @classmethod
    def tearDownClass(cls):
        import config.settings
        config.settings.TURSO_URL = cls.original
        shutil.rmtree(cls.dir, ignore_errors=True)

    def crear_jerarquia(self, anio=2200, nombre="Camp", modo_campeon="final_lideres", criterios="dg,gf,h2h"):
        self.anio_id = AnioService.crear_anio(anio, es_master=True)
        self.camp_id = CampeonatoService.crear_campeonato(nombre, self.anio_id, es_master=True)
        self.copa_id = CopaService.crear_copa(
            "Copa A", self.camp_id, color="#1E3A8A", es_master=True,
            criterios_desempate=criterios
        )
        self.torneo_id = TorneoService.crear_torneo("Torneo 1", "Copa", self.copa_id, es_master=True,
                                                    modo_campeon=modo_campeon)
        self.jornada_id = JornadaRepository.crear(self.torneo_id, "2200-05-01", "Día 1", 1)
        self.cat_id = TorneoService.crear_categoria(self.jornada_id, "7° Básico", es_organizador=True)
        self.grupo_id = TorneoService.crear_grupo(self.cat_id, self.jornada_id, "Grupo A", EQUIPOS, es_organizador=True)

    def partidos(self):
        return TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)["grupos"][0]["partidos"]

    def jugar_todos_partidos_grupo(self, resultados=None):
        """Juega todos los partidos de un grupo con resultados específicos o por defecto"""
        partidos = self.partidos()
        if resultados is None:
            # Resultados por defecto: Alfa gana todos, Beta pierde todos, etc.
            resultados = [(3, 0), (3, 0), (3, 0), (0, 3), (0, 3), (2, 1)]
        for i, p in enumerate(partidos):
            if i < len(resultados):
                gl, gv = resultados[i]
                TorneoService.guardar_marcador(p.id, gl, gv, es_organizador=True)


class TestModoFinalLideres(BaseDB):
    """Pruebas para modo_campeon = 'final_lideres' (Final entre líderes de grupo)"""

    def test_final_lideres_un_grupo_campeon_definido(self):
        """Un solo grupo: el líder directo es campeón sin final"""
        self.crear_jerarquia(2300, "Final1", "final_lideres")
        # Alfa gana sus 3 partidos (9 pts), Beta gana 2 (6 pts), Gama gana 1 (3 pts), Delta 0
        self.jugar_todos_partidos_grupo([(3, 0), (3, 0), (3, 0), (0, 3), (0, 3), (0, 3)])
        
        datos = TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)
        estado = datos["estado_campeon"]
        
        self.assertEqual(estado["estado"], "CAMPEON_DEFINIDO")
        self.assertEqual(estado["campeon"], "Alfa")
        self.assertIn("Puntero exclusivo", estado["motivo"])

    def test_final_lideres_dos_grupos_genera_final(self):
        """Dos grupos: genera final entre los líderes"""
        self.crear_jerarquia(2301, "Final2", "final_lideres")
        
        # Crear segundo grupo
        equipos_b = ["Epsilon", "Zeta", "Eta", "Theta"]
        g2_id = TorneoService.crear_grupo(self.cat_id, self.jornada_id, "Grupo B", equipos_b, es_organizador=True)
        
        # Jugar todos los partidos
        datos = TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)
        for g in datos["grupos"]:
            for p in g["partidos"]:
                TorneoService.guardar_marcador(p.id, 3, 0, es_organizador=True)
        
        # Generar final
        final_id = TorneoService.generar_final_dia2(self.cat_id, self.jornada_id, es_organizador=True)
        self.assertIsNotNone(final_id)
        
        datos = TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)
        self.assertTrue(len(datos["partidos_definicion"]) > 0)

    def test_final_lideres_tres_grupos_mejores_dos(self):
        """Tres grupos: final entre los 2 mejores líderes"""
        self.crear_jerarquia(2302, "Final3", "final_lideres")

        # Crear grupos adicionales
        equipos_b = ["Epsilon", "Zeta", "Eta", "Theta"]
        equipos_c = ["Iota", "Kappa", "Lambda", "Mu"]
        TorneoService.crear_grupo(self.cat_id, self.jornada_id, "Grupo B", equipos_b, es_organizador=True)
        TorneoService.crear_grupo(self.cat_id, self.jornada_id, "Grupo C", equipos_c, es_organizador=True)

        # Jugar partidos con resultados que definan claramente a los mejores
        datos = TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)
        grupos = datos["grupos"]

        # Grupo A: Alfa domina (9 pts) - gana todos sus partidos
        for p in grupos[0]["partidos"]:
            if p.equipo_local == "Alfa":
                TorneoService.guardar_marcador(p.id, 3, 0, es_organizador=True)
            else:
                TorneoService.guardar_marcador(p.id, 0, 3, es_organizador=True)

        # Grupo B: Epsilon domina (9 pts) - gana todos sus partidos
        for p in grupos[1]["partidos"]:
            if p.equipo_local == "Epsilon":
                TorneoService.guardar_marcador(p.id, 3, 0, es_organizador=True)
            else:
                TorneoService.guardar_marcador(p.id, 0, 3, es_organizador=True)

        # Grupo C: resultados mezclados (Iota 6 pts)
        resultados_c = [(3, 0), (1, 1), (0, 3), (3, 0), (1, 1), (0, 3)]
        for i, p in enumerate(grupos[2]["partidos"]):
            if i < len(resultados_c):
                TorneoService.guardar_marcador(p.id, resultados_c[i][0], resultados_c[i][1], es_organizador=True)

        # Generar final
        final_id = TorneoService.generar_final_dia2(self.cat_id, self.jornada_id, es_organizador=True)
        self.assertIsNotNone(final_id)

        datos = TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)
        final = datos["partidos_definicion"][0]
        # Debe ser entre Alfa y Epsilon (los 2 mejores líderes)
        self.assertIn(final.equipo_local, ["Alfa", "Epsilon"])
        self.assertIn(final.equipo_visita, ["Alfa", "Epsilon"])


class TestModoLiguillaLideres(BaseDB):
    """Pruebas para modo_campeon = 'liguilla_lideres' (Liguilla entre líderes)"""

    def test_liguilla_lideres_tres_grupos(self):
        """Tres grupos: liguilla todos contra todos entre líderes"""
        self.crear_jerarquia(2400, "Liguilla1", "liguilla_lideres")
        
        # Crear grupos adicionales
        equipos_b = ["Epsilon", "Zeta", "Eta", "Theta"]
        equipos_c = ["Iota", "Kappa", "Lambda", "Mu"]
        TorneoService.crear_grupo(self.cat_id, self.jornada_id, "Grupo B", equipos_b, es_organizador=True)
        TorneoService.crear_grupo(self.cat_id, self.jornada_id, "Grupo C", equipos_c, es_organizador=True)
        
        # Jugar todos los partidos de fase de grupos
        datos = TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)
        for g in datos["grupos"]:
            for p in g["partidos"]:
                TorneoService.guardar_marcador(p.id, 1, 1, es_organizador=True)  # Empates para simplicidad
        
        # Generar liguilla
        final_id = TorneoService.generar_final_dia2(self.cat_id, self.jornada_id, es_organizador=True)
        self.assertIsNotNone(final_id)
        
        datos = TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)
        partidos_def = datos["partidos_definicion"]
        
        # Debe generar 3 partidos (3 líderes: A vs B, A vs C, B vs C)
        self.assertEqual(len(partidos_def), 3)

    def test_liguilla_lideres_campeon_por_puntos(self):
        """Liguilla: el campeón se define por puntos en la liguilla"""
        self.crear_jerarquia(2401, "Liguilla2", "liguilla_lideres")
        
        # Crear 3 grupos
        equipos_b = ["Epsilon", "Zeta", "Eta", "Theta"]
        equipos_c = ["Iota", "Kappa", "Lambda", "Mu"]
        TorneoService.crear_grupo(self.cat_id, self.jornada_id, "Grupo B", equipos_b, es_organizador=True)
        TorneoService.crear_grupo(self.cat_id, self.jornada_id, "Grupo C", equipos_c, es_organizador=True)
        
        # Jugar fase de grupos
        datos = TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)
        for g in datos["grupos"]:
            for p in g["partidos"]:
                TorneoService.guardar_marcador(p.id, 3, 0, es_organizador=True)
        
        # Generar liguilla
        TorneoService.generar_final_dia2(self.cat_id, self.jornada_id, es_organizador=True)
        
        # Jugar liguilla con resultados específicos
        datos = TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)
        partidos_def = datos["partidos_definicion"]
        
        # Alfa gana sus 2 partidos (6 pts), Epsilon gana 1 (3 pts), Iota pierde todos (0 pts)
        TorneoService.guardar_marcador(partidos_def[0].id, 3, 0, es_organizador=True)  # Alfa vs Epsilon
        TorneoService.guardar_marcador(partidos_def[1].id, 3, 0, es_organizador=True)  # Alfa vs Iota
        TorneoService.guardar_marcador(partidos_def[2].id, 3, 0, es_organizador=True)  # Epsilon vs Iota
        
        datos = TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)
        estado = datos["estado_campeon"]
        
        self.assertEqual(estado["estado"], "CAMPEON_DEFINIDO")
        self.assertEqual(estado["campeon"], "Alfa")
        self.assertIn("liguilla", estado["motivo"].lower())

    def test_liguilla_lideres_empate_requiere_desempate(self):
        """Liguilla: empate en puntos requiere desempate manual"""
        self.crear_jerarquia(2402, "Liguilla3", "liguilla_lideres")
        
        # Crear 3 grupos
        equipos_b = ["Epsilon", "Zeta", "Eta", "Theta"]
        equipos_c = ["Iota", "Kappa", "Lambda", "Mu"]
        TorneoService.crear_grupo(self.cat_id, self.jornada_id, "Grupo B", equipos_b, es_organizador=True)
        TorneoService.crear_grupo(self.cat_id, self.jornada_id, "Grupo C", equipos_c, es_organizador=True)
        
        # Jugar fase de grupos
        datos = TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)
        for g in datos["grupos"]:
            for p in g["partidos"]:
                TorneoService.guardar_marcador(p.id, 3, 0, es_organizador=True)
        
        # Generar liguilla
        TorneoService.generar_final_dia2(self.cat_id, self.jornada_id, es_organizador=True)
        
        # Jugar liguilla con empate
        datos = TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)
        partidos_def = datos["partidos_definicion"]
        
        # Todos empatan: Alfa 1-1 Epsilon, Alfa 1-1 Iota, Epsilon 1-1 Iota
        for p in partidos_def:
            TorneoService.guardar_marcador(p.id, 1, 1, es_organizador=True)
        
        datos = TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)
        estado = datos["estado_campeon"]
        
        self.assertEqual(estado["estado"], "EMPATE_DEFINICION")
        self.assertIsNone(estado["campeon"])


class TestModoTablaUnica(BaseDB):
    """Pruebas para modo_campeon = 'tabla_unica' (Líder de tabla general sin final)"""

    def test_tabla_unica_campeon_sin_final(self):
        """Tabla única: el líder de la tabla general es campeón directamente"""
        self.crear_jerarquia(2500, "Tabla1", "tabla_unica")

        # Crear segundo grupo
        equipos_b = ["Epsilon", "Zeta", "Eta", "Theta"]
        TorneoService.crear_grupo(self.cat_id, self.jornada_id, "Grupo B", equipos_b, es_organizador=True)

        # Jugar todos los partidos con resultados que generen un campeón claro
        datos = TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)
        grupos = datos["grupos"]

        # Grupo A: Alfa domina (9 pts, DG +9)
        for p in grupos[0]["partidos"]:
            if p.equipo_local == "Alfa":
                TorneoService.guardar_marcador(p.id, 3, 0, es_organizador=True)
            else:
                TorneoService.guardar_marcador(p.id, 0, 3, es_organizador=True)

        # Grupo B: resultados más bajos para que Alfa sea líder global
        for p in grupos[1]["partidos"]:
            TorneoService.guardar_marcador(p.id, 1, 1, es_organizador=True)  # Empates

        datos = TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)
        estado = datos["estado_campeon"]

        self.assertEqual(estado["estado"], "CAMPEON_DEFINIDO")
        # Alfa tiene 9 pts, los demás tienen menos
        self.assertEqual(estado["campeon"], "Alfa")

    def test_tabla_unica_varios_grupos(self):
        """Tabla única con múltiples grupos: combina todos los equipos"""
        self.crear_jerarquia(2501, "Tabla2", "tabla_unica")
        
        # Crear 3 grupos
        equipos_b = ["Epsilon", "Zeta", "Eta", "Theta"]
        equipos_c = ["Iota", "Kappa", "Lambda", "Mu"]
        TorneoService.crear_grupo(self.cat_id, self.jornada_id, "Grupo B", equipos_b, es_organizador=True)
        TorneoService.crear_grupo(self.cat_id, self.jornada_id, "Grupo C", equipos_c, es_organizador=True)
        
        # Resultados variados
        datos = TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)
        grupos = datos["grupos"]
        
        # Grupo A: Alfa perfecto (9 pts, DG +9)
        for p in grupos[0]["partidos"]:
            TorneoService.guardar_marcador(p.id, 3, 0, es_organizador=True)
        
        # Grupo B: Epsilon 7 pts (2 victorias, 1 empate)
        resultados_b = [(3, 0), (1, 1), (3, 0), (0, 3), (1, 1), (0, 3)]
        for i, p in enumerate(grupos[1]["partidos"]):
            TorneoService.guardar_marcador(p.id, resultados_b[i][0], resultados_b[i][1], es_organizador=True)
        
        # Grupo C: Iota 6 pts
        for p in grupos[2]["partidos"]:
            TorneoService.guardar_marcador(p.id, 1, 1, es_organizador=True)
        
        datos = TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)
        estado = datos["estado_campeon"]
        
        self.assertEqual(estado["estado"], "CAMPEON_DEFINIDO")
        self.assertEqual(estado["campeon"], "Alfa")


class TestCriteriosDesempate(BaseDB):
    """Pruebas para diferentes criterios de desempate"""

    def test_criterios_combinados(self):
        """Criterios combinados: dg, gf, h2h"""
        self.crear_jerarquia(2603, "Desempate4", "final_lideres", criterios="dg,gf,h2h")
        self.jugar_todos_partidos_grupo([(2, 1), (2, 1), (2, 1), (1, 2), (1, 2), (1, 2)])

        datos = TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)
        tabla = datos["grupos"][0]["tabla"]

        # Debe aplicar criterios en orden
        self.assertEqual(tabla[0].equipo, "Alfa")


class TestPuntosConfigurables(BaseDB):
    """Pruebas para configuración de puntos por victoria/empate"""

    def test_puntos_victoria_5_empate_2(self):
        """Sistema no estándar: 5 pts por victoria, 2 por empate"""
        self.crear_jerarquia(2700, "Puntos5")
        
        from backend.database.repositories import CopaRepository
        CopaRepository.actualizar_puntos(self.copa_id, puntos_victoria=5, puntos_empate=2)
        
        self.jugar_todos_partidos_grupo([(1, 0), (1, 1), (1, 0), (0, 1), (1, 1), (0, 1)])
        
        datos = TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)
        tabla = datos["grupos"][0]["tabla"]
        
        # Alfa: 2 victorias (10 pts) + 1 empate (2 pts) = 12 pts
        self.assertEqual(tabla[0].pts, 12)

    def test_puntos_victoria_2_empate_1(self):
        """Sistema reducido: 2 pts por victoria, 1 por empate"""
        self.crear_jerarquia(2701, "Puntos2")
        
        from backend.database.repositories import CopaRepository
        CopaRepository.actualizar_puntos(self.copa_id, puntos_victoria=2, puntos_empate=1)
        
        self.jugar_todos_partidos_grupo([(1, 0), (1, 1), (1, 0), (0, 1), (1, 1), (0, 1)])
        
        datos = TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)
        tabla = datos["grupos"][0]["tabla"]
        
        # Alfa: 2 victorias (4 pts) + 1 empate (1 pt) = 5 pts
        self.assertEqual(tabla[0].pts, 5)


if __name__ == "__main__":
    unittest.main()
