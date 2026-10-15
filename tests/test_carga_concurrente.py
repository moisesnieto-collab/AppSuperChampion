"""Pruebas de carga para evaluar capacidad con 10.000 usuarios concurrentes (Invitados - solo consulta)"""
import os
import shutil
import tempfile
import unittest
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

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
        config.settings.TURSO_URL = os.path.join(cls.dir, "test_carga.db")
        config.settings.TURSO_TOKEN = ""
        inicializar_db()

    @classmethod
    def tearDownClass(cls):
        import config.settings
        config.settings.TURSO_URL = cls.original
        shutil.rmtree(cls.dir, ignore_errors=True)

    def crear_jerarquia_completa(self, anio_base=3000):
        """Crea una jerarquía completa con múltiples categorías y grupos para simular datos reales"""
        self.anio_id = AnioService.crear_anio(anio_base, es_master=True)
        self.camp_id = CampeonatoService.crear_campeonato("Campeonato Carga", self.anio_id, es_master=True)
        self.copa_id = CopaService.crear_copa("Copa Carga", self.camp_id, color="#1E3A8A", es_master=True)
        self.torneo_id = TorneoService.crear_torneo("Torneo Carga", "Copa", self.copa_id, es_master=True)
        
        # Crear múltiples jornadas
        self.jornadas_ids = []
        for i in range(5):
            j_id = JornadaRepository.crear(self.torneo_id, f"2024-05-{i+1:02d}", f"Día {i+1}", i+1)
            self.jornadas_ids.append(j_id)
            
            # Crear múltiples categorías por jornada
            cat_ids = []
            for j in range(10):  # 10 categorías por jornada
                cat_id = TorneoService.crear_categoria(j_id, f"Categoría {j+1}° Básico", es_organizador=True)
                cat_ids.append(cat_id)
                
                # Crear múltiples grupos por categoría
                for k in range(3):  # 3 grupos por categoría
                    equipos = [f"Equipo_{j}_{k}_{m}" for m in range(4)]
                    g_id = TorneoService.crear_grupo(cat_id, j_id, f"Grupo {chr(65+k)}", equipos, es_organizador=True)


class TestCargaLecturasConcurrentes(BaseDB):
    """Pruebas de carga para lecturas concurrentes (usuarios invitados)"""

    def test_100_lecturas_concurrentes(self):
        """Simula 100 usuarios consultando datos simultáneamente"""
        self.crear_jerarquia_completa(anio_base=3100)
        
        def consulta_usuario(user_id):
            """Simula un usuario invitado consultando datos"""
            try:
                # Consulta típica de un usuario: obtener datos de categoría y jornada
                cat_id = 1  # Primera categoría
                jornada_id = self.jornadas_ids[0]
                datos = TorneoService.obtener_datos_categoria_dia(cat_id, jornada_id)
                return {"user_id": user_id, "success": True, "grupos": len(datos["grupos"])}
            except Exception as e:
                return {"user_id": user_id, "success": False, "error": str(e)}

        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(consulta_usuario, i) for i in range(100)]
            results = [f.result() for f in as_completed(futures)]
        
        elapsed = time.time() - start_time
        
        exitosos = sum(1 for r in results if r["success"])
        print(f"\n100 usuarios concurrentes: {exitosos}/100 exitosos en {elapsed:.2f}s")
        
        self.assertEqual(exitosos, 100, "Todas las consultas deben ser exitosas")
        self.assertLess(elapsed, 5, "100 consultas deben completarse en menos de 5 segundos")

    def test_1000_lecturas_concurrentes(self):
        """Simula 1.000 usuarios consultando datos simultáneamente"""
        self.crear_jerarquia_completa(anio_base=3200)
        
        def consulta_usuario(user_id):
            """Simula un usuario invitado consultando datos"""
            try:
                # Rotar entre diferentes jornadas y categorías
                jornada_idx = user_id % len(self.jornadas_ids)
                jornada_id = self.jornadas_ids[jornada_idx]
                cat_id = (user_id % 10) + 1  # 10 categorías
                
                datos = TorneoService.obtener_datos_categoria_dia(cat_id, jornada_id)
                return {"user_id": user_id, "success": True}
            except Exception as e:
                return {"user_id": user_id, "success": False, "error": str(e)}

        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=200) as executor:
            futures = [executor.submit(consulta_usuario, i) for i in range(1000)]
            results = [f.result() for f in as_completed(futures)]
        
        elapsed = time.time() - start_time
        
        exitosos = sum(1 for r in results if r["success"])
        print(f"\n1.000 usuarios concurrentes: {exitosos}/1.000 exitosos en {elapsed:.2f}s")
        
        self.assertGreaterEqual(exitosos, 995, "Al menos 99.5% de las consultas deben ser exitosas")
        self.assertLess(elapsed, 30, "1.000 consultas deben completarse en menos de 30 segundos")

    def test_10000_lecturas_escalonadas(self):
        """Simula 10.000 usuarios en lotes escalonados (más realista)"""
        self.crear_jerarquia_completa(anio_base=3300)
        
        def consulta_usuario(user_id):
            """Simula un usuario invitado consultando datos"""
            try:
                jornada_idx = user_id % len(self.jornadas_ids)
                jornada_id = self.jornadas_ids[jornada_idx]
                cat_id = (user_id % 10) + 1
                
                datos = TorneoService.obtener_datos_categoria_dia(cat_id, jornada_id)
                return {"user_id": user_id, "success": True}
            except Exception as e:
                return {"user_id": user_id, "success": False, "error": str(e)}

        total_usuarios = 10000
        lote_size = 500  # Procesar en lotes de 500
        resultados_totales = []
        tiempo_total = 0
        
        for lote in range(0, total_usuarios, lote_size):
            lote_inicio = lote
            lote_fin = min(lote + lote_size, total_usuarios)
            usuarios_lote = list(range(lote_inicio, lote_fin))
            
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=100) as executor:
                futures = [executor.submit(consulta_usuario, u) for u in usuarios_lote]
                resultados_lote = [f.result() for f in as_completed(futures)]
            
            elapsed_lote = time.time() - start_time
            tiempo_total += elapsed_lote
            resultados_totales.extend(resultados_lote)
            
            exitosos_lote = sum(1 for r in resultados_lote if r["success"])
            print(f"Lote {lote_inicio}-{lote_fin}: {exitosos_lote}/{len(resultados_lote)} exitosos en {elapsed_lote:.2f}s")
        
        exitosos_total = sum(1 for r in resultados_totales if r["success"])
        print(f"\n10.000 usuarios escalonados: {exitosos_total}/{total_usuarios} exitosos en {tiempo_total:.2f}s total")
        
        self.assertGreaterEqual(exitosos_total, 9950, "Al menos 99.5% de las consultas deben ser exitosas")
        self.assertLess(tiempo_total, 300, "10.000 consultas escalonadas deben completarse en menos de 5 minutos")

    def test_consultas_complejas(self):
        """Simula consultas más complejas (tablas, múltiples categorías)"""
        self.crear_jerarquia_completa(anio_base=3400)
        
        def consulta_compleja(user_id):
            """Simula un usuario navegando por múltiples vistas"""
            try:
                # Consultar múltiples jornadas
                for jornada_id in self.jornadas_ids[:3]:
                    for cat_id in range(1, 4):
                        datos = TorneoService.obtener_datos_categoria_dia(cat_id, jornada_id)
                
                return {"user_id": user_id, "success": True}
            except Exception as e:
                return {"user_id": user_id, "success": False, "error": str(e)}

        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(consulta_compleja, i) for i in range(200)]
            results = [f.result() for f in as_completed(futures)]
        
        elapsed = time.time() - start_time
        
        exitosos = sum(1 for r in results if r["success"])
        print(f"\n200 consultas complejas: {exitosos}/200 exitosos en {elapsed:.2f}s")
        
        self.assertGreaterEqual(exitosos, 195, "Al menos 97.5% de las consultas complejas deben ser exitosas")


class TestAnalisisArquitectura(BaseDB):
    """Análisis de arquitectura para escalabilidad"""

    def test_analisis_conexion_db(self):
        """Analiza el comportamiento de conexiones a la base de datos"""
        self.crear_jerarquia_completa()
        
        from backend.database.connection import obtener_conexion
        
        # Probar múltiples conexiones desde diferentes threads
        def conexion_thread(thread_id):
            try:
                con = obtener_conexion()
                cursor = con.cursor()
                cursor.execute("SELECT COUNT(*) FROM partidos")
                count = cursor.fetchone()[0]
                return {"thread_id": thread_id, "count": count, "success": True}
            except Exception as e:
                return {"thread_id": thread_id, "success": False, "error": str(e)}
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(conexion_thread, i) for i in range(50)]
            results = [f.result() for f in as_completed(futures)]
        
        exitosos = sum(1 for r in results if r["success"])
        print(f"\n50 conexiones concurrentes: {exitosos}/50 exitosos")
        
        self.assertEqual(exitosos, 50, "Todas las conexiones deben ser exitosas")

    def test_rendimiento_queries(self):
        """Mide el rendimiento de queries típicas"""
        self.crear_jerarquia_completa(anio_base=3500)
        
        # Query simple: obtener partidos
        start = time.time()
        for _ in range(100):
            PartidoRepository.obtener_por_categoria_y_jornada(1, self.jornadas_ids[0])
        elapsed = time.time() - start
        print(f"\n100 queries simples: {elapsed:.3f}s ({100/elapsed:.1f} queries/s)")
        
        # Query compleja: obtener datos completos
        start = time.time()
        for _ in range(100):
            TorneoService.obtener_datos_categoria_dia(1, self.jornadas_ids[0])
        elapsed = time.time() - start
        print(f"100 queries complejas: {elapsed:.3f}s ({100/elapsed:.1f} queries/s)")
        
        # Queries deben ser razonablemente rápidas
        self.assertGreater(100/elapsed, 10, "Queries simples deben ser > 10/s")


if __name__ == "__main__":
    unittest.main(verbosity=2)
