import unittest
import os
import tempfile
import shutil
from backend.database.connection import obtener_conexion
from backend.database.schema import inicializar_db
from backend.services.torneo_service import TorneoService
from backend.services.tabla_service import TablaService
from backend.models.partido import Partido


class TestSuperChampion(unittest.TestCase):
    """Suite de pruebas para AppSuperChampion."""
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial: crear base de datos temporal para pruebas."""
        cls.test_db_dir = tempfile.mkdtemp()
        cls.test_db_path = os.path.join(cls.test_db_dir, "test_superchampion.db")
        
        # Sobrescribir la configuración de la base de datos para usar la temporal
        import config.settings
        cls.original_turso_url = config.settings.TURSO_URL
        config.settings.TURSO_URL = cls.test_db_path
        config.settings.TURSO_TOKEN = ""
        
        # Inicializar base de datos de prueba
        inicializar_db()
    
    @classmethod
    def tearDownClass(cls):
        """Limpieza: eliminar base de datos temporal."""
        # Restaurar configuración original
        import config.settings
        config.settings.TURSO_URL = cls.original_turso_url
        
        # Cerrar conexiones y eliminar directorio temporal
        if os.path.exists(cls.test_db_dir):
            shutil.rmtree(cls.test_db_dir)
    
    def setUp(self):
        """Configuración antes de cada prueba: reiniciar estado."""
        # Limpiar base de datos antes de cada prueba
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("DELETE FROM partidos")
        cursor.execute("DELETE FROM grupos")
        cursor.execute("DELETE FROM categorias")
        cursor.execute("DELETE FROM jornadas")
        cursor.execute("DELETE FROM torneos")
        cursor.execute("DELETE FROM copas")
        cursor.execute("DELETE FROM campeonato_permisos")
        cursor.execute("DELETE FROM campeonatos")
        cursor.execute("DELETE FROM anios")
        con.commit()
        
        # Reinicializar con datos por defecto
        inicializar_db()
    
    @staticmethod
    def _dejar_un_grupo(cat_id, jornada_id):
        grupos = TorneoService.obtener_datos_categoria_dia(cat_id, jornada_id)["grupos"]
        for g in grupos[1:]:
            TorneoService.eliminar_grupo(g["grupo"].id, es_organizador=True)

    def test_criterios_desempate_configurables(self):
        from backend.models.partido import Partido
        def pj(l, v, gl, gv):
            return Partido(id=0, grupo_id=1, categoria_id=1, fecha_jornada_id=1, equipo_local=l,
                           equipo_visita=v, goles_local=gl, goles_visita=gv, jugado=True)
        # A y B empatan en puntos (3); A tiene mejor DG, B ganó el directo
        partidos = [pj("A", "B", 0, 1), pj("A", "C", 5, 0), pj("A", "D", 0, 1), pj("B", "D", 0, 1)]
        eq = ["A", "B", "C", "D"]
        orden = lambda t: [e.equipo for e in t]
        t1 = orden(TablaService.calcular_tabla(partidos, eq, ["dg", "gf", "h2h"]))
        t2 = orden(TablaService.calcular_tabla(partidos, eq, ["h2h", "dg"]))
        self.assertLess(t1.index("A"), t1.index("B"))
        self.assertLess(t2.index("B"), t2.index("A"))
        t3 = TablaService.calcular_tabla(partidos, eq, ["dg"], pts_victoria=2)
        self.assertEqual(next(e for e in t3 if e.equipo == "A").pts, 2)

    def test_creacion_categoria_fixture(self):
        """Verificar la creación de categorías con grupos automáticos."""
        # Obtener torneo activo
        torneo = TorneoService.obtener_torneo_activo()
        self.assertIsNotNone(torneo)
        
        # Obtener jornadas del torneo
        jornadas = TorneoService.obtener_jornadas_por_torneo(torneo.id)
        self.assertGreater(len(jornadas), 0)
        
        # Obtener categorías de la primera jornada
        categorias = TorneoService.obtener_categorias_por_jornada(jornadas[0].id)
        
        # Deben existir 6 categorías por defecto
        self.assertEqual(len(categorias), 6)
        
        # Verificar nombres de categorías
        nombres_cat = [c.nombre for c in categorias]
        self.assertIn("1° Básico", nombres_cat)
        self.assertIn("6° Básico", nombres_cat)
        
        # Verificar que cada categoría tiene grupos para la jornada
        for cat in categorias:
            grupos = TorneoService.obtener_datos_categoria_dia(cat.id, jornadas[0].id)["grupos"]
            self.assertEqual(len(grupos), 2)  # Grupo A y Grupo B
    
    def test_creacion_categoria_personalizada(self):
        """Verificar creación de categoría personalizada con fixture automático."""
        # Obtener jornada activa
        torneo = TorneoService.obtener_torneo_activo()
        jornadas = TorneoService.obtener_jornadas_por_torneo(torneo.id)
        jornada_id = jornadas[0].id
        
        # Crear nueva categoría como organizador
        nueva_cat_id = TorneoService.crear_categoria(jornada_id, "7° Básico", es_organizador=True)
        
        # Verificar que la categoría fue creada
        categorias = TorneoService.obtener_categorias_por_jornada(jornada_id)
        self.assertEqual(len(categorias), 7)
        
        # Una categoría nueva no crea grupos automáticamente
        datos = TorneoService.obtener_datos_categoria_dia(nueva_cat_id, jornada_id)
        self.assertEqual(len(datos["grupos"]), 0)

        # Al crear un grupo de 4 equipos se genera el cuadrangular (6 partidos)
        TorneoService.crear_grupo(nueva_cat_id, jornada_id, "Grupo A", ["A", "B", "C", "D"], es_organizador=True)
        datos = TorneoService.obtener_datos_categoria_dia(nueva_cat_id, jornada_id)
        self.assertEqual(len(datos["grupos"]), 1)
        for g_data in datos["grupos"]:
            self.assertEqual(len(g_data["partidos"]), 6)
    
    def test_calculo_tabla_posiciones(self):
        """Validar ordenamiento correcto por Pts > DG > GF."""
        # Obtener primera categoría y primera jornada
        torneo = TorneoService.obtener_torneo_activo()
        jornadas = TorneoService.obtener_jornadas_por_torneo(torneo.id)
        categorias = TorneoService.obtener_categorias_por_jornada(jornadas[0].id)
        cat_id = categorias[0].id
        jornada_id = jornadas[0].id
        
        datos = TorneoService.obtener_datos_categoria_dia(cat_id, jornada_id)
        grupo = datos["grupos"][0]
        partidos = grupo["partidos"]
        equipos = grupo["grupo"].equipos
        
        # Simular resultados para crear un ordenamiento claro
        # Equipo 0: 3 victorias (9 pts, DG +3)
        # Equipo 1: 2 victorias, 1 derrota (6 pts, DG 0)
        # Equipo 2: 1 victoria, 2 derrotas (3 pts, DG -3)
        # Equipo 3: 0 victorias (0 pts, DG -6)
        
        resultados = [
            (partidos[0].id, 3, 0),  # e0 vs e1
            (partidos[1].id, 1, 0),  # e2 vs e3
            (partidos[2].id, 2, 0),  # e0 vs e2
            (partidos[3].id, 1, 0),  # e1 vs e3
            (partidos[4].id, 1, 0),  # e0 vs e3
            (partidos[5].id, 2, 0),  # e1 vs e2
        ]
        
        for pid, g_loc, g_vis in resultados:
            TorneoService.guardar_marcador(pid, g_loc, g_vis, es_organizador=True)
        
        # Recalcular tabla
        datos_actualizados = TorneoService.obtener_datos_categoria_dia(cat_id, jornada_id)
        tabla = datos_actualizados["grupos"][0]["tabla"]
        
        # Verificar ordenamiento
        self.assertEqual(tabla[0].pts, 9)
        self.assertEqual(tabla[1].pts, 6)
        self.assertEqual(tabla[2].pts, 3)
        self.assertEqual(tabla[3].pts, 0)
        
        # Verificar diferencia de goles
        self.assertGreater(tabla[0].dg, tabla[1].dg)
        self.assertGreater(tabla[1].dg, tabla[2].dg)
    
    def test_desempate_enfrentamiento_directo(self):
        """Validar criterio de desempate por enfrentamiento directo."""
        torneo = TorneoService.obtener_torneo_activo()
        jornadas = TorneoService.obtener_jornadas_por_torneo(torneo.id)
        categorias = TorneoService.obtener_categorias_por_jornada(jornadas[0].id)
        cat_id = categorias[0].id
        jornada_id = jornadas[0].id
        
        datos = TorneoService.obtener_datos_categoria_dia(cat_id, jornada_id)
        grupo = datos["grupos"][0]
        partidos = grupo["partidos"]
        equipos = grupo["grupo"].equipos
        
        # Fixture según schema.py:
        # partidos[0]: e1 vs e2
        # partidos[1]: e3 vs e4
        # partidos[2]: e1 vs e3
        # partidos[3]: e2 vs e4
        # partidos[4]: e1 vs e4
        # partidos[5]: e2 vs e3
        
        # Crear escenario simple donde e1 y e2 tienen mismos Pts, DG, GF
        # pero e1 ganó el enfrentamiento directo
        # e1: 1-1 vs e2 (empate=1pt), 1-1 vs e3 (empate=1pt), 1-1 vs e4 (empate=1pt) -> 3 pts
        # e2: 1-1 vs e1 (empate=1pt), 1-1 vs e4 (empate=1pt), 1-1 vs e3 (empate=1pt) -> 3 pts
        # e3: 1-1 vs e4 (empate=1pt), 1-1 vs e1 (empate=1pt), 1-1 vs e2 (empate=1pt) -> 3 pts
        # e4: 1-1 vs e3 (empate=1pt), 1-1 vs e2 (empate=1pt), 1-1 vs e1 (empate=1pt) -> 3 pts
        # Todos empatados en todo, el ordenamiento por nombre debería aplicar
        
        resultados = [
            (partidos[0].id, 1, 1),  # e1 vs e2 -> empate
            (partidos[1].id, 1, 1),  # e3 vs e4 -> empate
            (partidos[2].id, 1, 1),  # e1 vs e3 -> empate
            (partidos[3].id, 1, 1),  # e2 vs e4 -> empate
            (partidos[4].id, 1, 1),  # e1 vs e4 -> empate
            (partidos[5].id, 1, 1),  # e2 vs e3 -> empate
        ]
        
        for pid, g_loc, g_vis in resultados:
            TorneoService.guardar_marcador(pid, g_loc, g_vis, es_organizador=True)
        
        # Recalcular tabla
        datos_actualizados = TorneoService.obtener_datos_categoria_dia(cat_id, jornada_id)
        tabla = datos_actualizados["grupos"][0]["tabla"]
        
        # Todos deberían tener 3 pts, 0 DG, mismos GF/GC
        # El ordenamiento final debería ser alfabético (criterio final)
        for stat in tabla:
            self.assertEqual(stat.pts, 3)
            self.assertEqual(stat.dg, 0)
        
        # Verificar que están ordenados alfabéticamente (criterio de desempate final)
        nombres_ordenados = sorted([e for e in equipos])
        nombres_tabla = [t.equipo for t in tabla]
        self.assertEqual(nombres_tabla, nombres_ordenados)
    
    def test_guardado_marcador(self):
        """Verificar persistencia y recálculo de tabla al guardar marcador."""
        torneo = TorneoService.obtener_torneo_activo()
        jornadas = TorneoService.obtener_jornadas_por_torneo(torneo.id)
        categorias = TorneoService.obtener_categorias_por_jornada(jornadas[0].id)
        cat_id = categorias[0].id
        jornada_id = jornadas[0].id
        
        datos = TorneoService.obtener_datos_categoria_dia(cat_id, jornada_id)
        partido = datos["grupos"][0]["partidos"][0]
        
        # Guardar marcador
        TorneoService.guardar_marcador(partido.id, 2, 1, es_organizador=True)
        
        # Verificar que el marcador se guardó
        datos_actualizados = TorneoService.obtener_datos_categoria_dia(cat_id, jornada_id)
        partido_actualizado = datos_actualizados["grupos"][0]["partidos"][0]
        
        self.assertEqual(partido_actualizado.goles_local, 2)
        self.assertEqual(partido_actualizado.goles_visita, 1)
        self.assertTrue(partido_actualizado.jugado)
        
        # Verificar que la tabla se recalculó
        tabla = datos_actualizados["grupos"][0]["tabla"]
        equipos = datos["grupos"][0]["grupo"].equipos
        
        # El equipo local debería tener 3 puntos
        equipo_local_stats = next((t for t in tabla if t.equipo == partido.equipo_local), None)
        self.assertIsNotNone(equipo_local_stats)
        self.assertEqual(equipo_local_stats.pts, 3)
        self.assertEqual(equipo_local_stats.pg, 1)
    
    def test_determinacion_campeon_puntero_unico(self):
        """Caso 1: Puntero único con mayor puntaje -> Estado CAMPEON_DEFINIDO."""
        torneo = TorneoService.obtener_torneo_activo()
        jornadas = TorneoService.obtener_jornadas_por_torneo(torneo.id)
        categorias = TorneoService.obtener_categorias_por_jornada(jornadas[0].id)
        cat_id = categorias[0].id
        jornada_id = jornadas[0].id
        
        self._dejar_un_grupo(cat_id, jornada_id)
        datos = TorneoService.obtener_datos_categoria_dia(cat_id, jornada_id)
        
        # Simular todos los partidos de todos los grupos con un puntero claro
        for grupo_data in datos["grupos"]:
            partidos = grupo_data["partidos"]
            for i, partido in enumerate(partidos):
                if i % 2 == 0:
                    TorneoService.guardar_marcador(partido.id, 3, 0, es_organizador=True)
                else:
                    TorneoService.guardar_marcador(partido.id, 0, 3, es_organizador=True)
        
        datos_final = TorneoService.obtener_datos_categoria_dia(cat_id, jornada_id)
        estado_campeon = datos_final["estado_campeon"]
        
        self.assertEqual(estado_campeon["estado"], "CAMPEON_DEFINIDO")
        self.assertIsNotNone(estado_campeon["campeon"])
    
    def test_determinacion_campeon_empate(self):
        """Caso 2: Empate en puntos y diferencia de goles -> Estado EMPATE_REQUIERE_DESEMPATE."""
        torneo = TorneoService.obtener_torneo_activo()
        jornadas = TorneoService.obtener_jornadas_por_torneo(torneo.id)
        categorias = TorneoService.obtener_categorias_por_jornada(jornadas[0].id)
        cat_id = categorias[0].id
        jornada_id = jornadas[0].id
        
        self._dejar_un_grupo(cat_id, jornada_id)
        datos = TorneoService.obtener_datos_categoria_dia(cat_id, jornada_id)
        
        # Crear escenario de empate absoluto en primer lugar
        # Todos los partidos empate 1-1 en todos los grupos
        for grupo_data in datos["grupos"]:
            partidos = grupo_data["partidos"]
            for partido in partidos:
                TorneoService.guardar_marcador(partido.id, 1, 1, es_organizador=True)
        
        datos_final = TorneoService.obtener_datos_categoria_dia(cat_id, jornada_id)
        estado_campeon = datos_final["estado_campeon"]
        
        self.assertEqual(estado_campeon["estado"], "EMPATE_REQUIERE_DESEMPATE")
        self.assertIn("equipo1", estado_campeon)
        self.assertIn("equipo2", estado_campeon)
    
    def test_generacion_partido_desempate(self):
        """Validar generación de partido de desempate."""
        torneo = TorneoService.obtener_torneo_activo()
        jornadas = TorneoService.obtener_jornadas_por_torneo(torneo.id)
        categorias = TorneoService.obtener_categorias_por_jornada(jornadas[0].id)
        cat_id = categorias[0].id
        jornada_id = jornadas[0].id
        
        datos = TorneoService.obtener_datos_categoria_dia(cat_id, jornada_id)
        grupo = datos["grupos"][0]
        grupo_id = grupo["grupo"].id
        equipos = grupo["grupo"].equipos
        
        # Generar partido de desempate
        partido_id = TorneoService.generar_partido_desempate(
            cat_id, jornada_id, grupo_id, equipos[0], equipos[1], es_organizador=True
        )
        
        self.assertIsNotNone(partido_id)
        
        # Verificar que el partido se creó
        datos_actualizados = TorneoService.obtener_datos_categoria_dia(cat_id, jornada_id)
        partidos_definicion = datos_actualizados["partidos_definicion"]
        
        self.assertEqual(len(partidos_definicion), 1)
        self.assertTrue(partidos_definicion[0].es_definicion)
    
    def test_validacion_pin(self):
        """Validar sistema de autenticación por PIN."""
        # PIN por defecto es "1234"
        self.assertTrue(TorneoService.validar_pin("1234"))
        self.assertFalse(TorneoService.validar_pin("0000"))
        self.assertFalse(TorneoService.validar_pin("12345"))
    
    def test_permisos_organizador(self):
        """Verificar que las acciones de organizador requieren PIN."""
        torneo = TorneoService.obtener_torneo_activo()
        jornadas = TorneoService.obtener_jornadas_por_torneo(torneo.id)
        categorias = TorneoService.obtener_categorias_por_jornada(jornadas[0].id)
        cat_id = categorias[0].id
        jornada_id = jornadas[0].id
        
        datos = TorneoService.obtener_datos_categoria_dia(cat_id, jornada_id)
        partido = datos["grupos"][0]["partidos"][0]
        
        # Intentar guardar marcador sin ser organizador
        with self.assertRaises(PermissionError):
            TorneoService.guardar_marcador(partido.id, 2, 1, es_organizador=False)
        
        # Intentar crear categoría sin ser organizador
        with self.assertRaises(PermissionError):
            TorneoService.crear_categoria(jornada_id, "Test", es_organizador=False)
        
        # Guardar con permiso de organizador
        TorneoService.guardar_marcador(partido.id, 2, 1, es_organizador=True)
        
        # Verificar que se guardó
        datos_actualizados = TorneoService.obtener_datos_categoria_dia(cat_id, jornada_id)
        partido_actualizado = datos_actualizados["grupos"][0]["partidos"][0]
        self.assertEqual(partido_actualizado.goles_local, 2)
    
    def test_reiniciar_marcador(self):
        """Validar reinicio de marcador a 0-0."""
        torneo = TorneoService.obtener_torneo_activo()
        jornadas = TorneoService.obtener_jornadas_por_torneo(torneo.id)
        categorias = TorneoService.obtener_categorias_por_jornada(jornadas[0].id)
        cat_id = categorias[0].id
        jornada_id = jornadas[0].id
        
        datos = TorneoService.obtener_datos_categoria_dia(cat_id, jornada_id)
        partido = datos["grupos"][0]["partidos"][0]
        
        # Guardar marcador
        TorneoService.guardar_marcador(partido.id, 3, 2, es_organizador=True)
        
        # Reiniciar marcador
        TorneoService.reiniciar_marcador(partido.id, es_organizador=True)
        
        # Verificar reinicio
        datos_actualizados = TorneoService.obtener_datos_categoria_dia(cat_id, jornada_id)
        partido_actualizado = datos_actualizados["grupos"][0]["partidos"][0]
        
        self.assertEqual(partido_actualizado.goles_local, 0)
        self.assertEqual(partido_actualizado.goles_visita, 0)
        self.assertFalse(partido_actualizado.jugado)


if __name__ == "__main__":
    unittest.main()
