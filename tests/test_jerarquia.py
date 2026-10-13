import unittest
import os
import tempfile
import shutil
from backend.database.schema import inicializar_db
from backend.services.anio_service import AnioService
from backend.services.campeonato_service import CampeonatoService
from backend.services.copa_service import CopaService
from backend.services.torneo_service import TorneoService
from backend.database.repositories import (
    AnioRepository, CampeonatoRepository, CopaRepository, JornadaRepository
)


class TestJerarquia(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp()
        import config.settings
        cls.original = config.settings.TURSO_URL
        config.settings.TURSO_URL = os.path.join(cls.dir, "test_jerarquia.db")
        config.settings.TURSO_TOKEN = ""
        inicializar_db()

    @classmethod
    def tearDownClass(cls):
        import config.settings
        config.settings.TURSO_URL = cls.original
        shutil.rmtree(cls.dir, ignore_errors=True)

    def test_crud_y_dependencias(self):
        anio_id = AnioService.crear_anio(2099)
        camp_id = CampeonatoService.crear_campeonato("Camp Test", anio_id)
        copa_id = CopaService.crear_copa("Copa Test", camp_id)

        with self.assertRaises(ValueError):
            AnioService.eliminar_anio(anio_id)
        with self.assertRaises(ValueError):
            CampeonatoService.eliminar_campeonato(camp_id)

        AnioRepository.actualizar(anio_id, 2098)
        self.assertEqual(AnioRepository.obtener_por_id(anio_id).valor, 2098)
        CampeonatoRepository.actualizar(camp_id, "Camp Edit", anio_id)
        self.assertEqual(CampeonatoRepository.obtener_por_id(camp_id).nombre, "Camp Edit")
        CopaRepository.actualizar(copa_id, "Copa Edit", camp_id)
        self.assertEqual(CopaRepository.obtener_por_id(copa_id).nombre, "Copa Edit")

        torneo_id = TorneoService.crear_torneo("T", "Copa", copa_id, es_organizador=True)
        with self.assertRaises(ValueError):
            CopaService.eliminar_copa(copa_id)
        TorneoService.eliminar_torneo(torneo_id, es_organizador=True)

        CopaService.eliminar_copa(copa_id)
        CampeonatoService.eliminar_campeonato(camp_id)
        AnioService.eliminar_anio(anio_id)

    def test_jornada_lugar_horario(self):
        anio_id = AnioService.crear_anio(2097)
        camp_id = CampeonatoService.crear_campeonato("C", anio_id)
        copa_id = CopaService.crear_copa("Cp", camp_id)
        torneo_id = TorneoService.crear_torneo("T", "Copa", copa_id, es_organizador=True)
        jid = JornadaRepository.crear(torneo_id, "2099-01-01", "Día 1", 1, lugar="Estadio", horario="09:30")
        j = JornadaRepository.obtener_por_id(jid)
        self.assertEqual(j.lugar, "Estadio")
        self.assertEqual(j.horario, "09:30")

    def test_permisos(self):
        anio_id = AnioService.crear_anio(2096)
        camp_id = CampeonatoService.crear_campeonato("C", anio_id)
        CampeonatoService.asignar_permiso(camp_id, 7, "master")
        self.assertEqual(CampeonatoService.verificar_permiso_usuario(camp_id, 7), "master")
        with self.assertRaises(ValueError):
            CampeonatoService.asignar_permiso(camp_id, 8, "invalido")
        CampeonatoService.revocar_permiso(camp_id, 7)
        self.assertIsNone(CampeonatoService.verificar_permiso_usuario(camp_id, 7))

    def test_flujo_end_to_end(self):
        anio_id = AnioService.crear_anio(2095)
        camp_id = CampeonatoService.crear_campeonato("E2E", anio_id)
        copa_id = CopaService.crear_copa("Copa E2E", camp_id)
        torneo_id = TorneoService.crear_torneo("T", "Copa", copa_id, es_organizador=True)
        jid = JornadaRepository.crear(torneo_id, "2099-01-01", "Día 1", 1, lugar="Cancha", horario="10:00")
        cat_id = TorneoService.crear_categoria(jid, "Cat E2E", es_organizador=True)
        self.assertEqual(TorneoService.obtener_datos_categoria_dia(cat_id, jid)["grupos"], [])
        TorneoService.crear_grupo(cat_id, jid, "Grupo A", ["A", "B", "C", "D"], es_organizador=True)
        grupos = TorneoService.obtener_datos_categoria_dia(cat_id, jid)["grupos"]
        self.assertEqual(len(grupos), 1)
        partido = grupos[0]["partidos"][0]
        TorneoService.guardar_marcador(partido.id, 2, 1, es_organizador=True)
        CampeonatoService.asignar_permiso(camp_id, 1, "organizador")
        self.assertEqual(CampeonatoService.verificar_permiso_usuario(camp_id, 1), "organizador")

    def test_migracion_integridad_por_defecto(self):
        anio = AnioRepository.obtener_activo()
        self.assertIsNotNone(anio)
        camps = CampeonatoRepository.obtener_por_anio(anio.id)
        self.assertTrue(camps)
        copas = CopaRepository.obtener_por_campeonato(camps[0].id)
        self.assertTrue(copas)


if __name__ == "__main__":
    unittest.main()
