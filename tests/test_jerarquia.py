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
        anio_id = AnioService.crear_anio(2099, es_master=True)
        camp_id = CampeonatoService.crear_campeonato("Camp Test", anio_id, es_master=True)
        copa_id = CopaService.crear_copa("Copa Test", camp_id, es_master=True)

        with self.assertRaises(ValueError):
            AnioService.eliminar_anio(anio_id, es_master=True)
        with self.assertRaises(ValueError):
            CampeonatoService.eliminar_campeonato(camp_id, es_master=True)

        AnioRepository.actualizar(anio_id, 2098)
        self.assertEqual(AnioRepository.obtener_por_id(anio_id).valor, 2098)
        CampeonatoRepository.actualizar(camp_id, "Camp Edit", anio_id)
        self.assertEqual(CampeonatoRepository.obtener_por_id(camp_id).nombre, "Camp Edit")
        CopaRepository.actualizar(copa_id, "Copa Edit", camp_id)
        self.assertEqual(CopaRepository.obtener_por_id(copa_id).nombre, "Copa Edit")

        torneo_id = TorneoService.crear_torneo("T", "Copa", copa_id, es_master=True)
        with self.assertRaises(ValueError):
            CopaService.eliminar_copa(copa_id, es_master=True)
        TorneoService.eliminar_torneo(torneo_id, es_master=True)

        CopaService.eliminar_copa(copa_id, es_master=True)
        CampeonatoService.eliminar_campeonato(camp_id, es_master=True)
        AnioService.eliminar_anio(anio_id, es_master=True)

    def test_jornada_lugar_horario(self):
        anio_id = AnioService.crear_anio(2097, es_master=True)
        camp_id = CampeonatoService.crear_campeonato("C", anio_id, es_master=True)
        copa_id = CopaService.crear_copa("Cp", camp_id, es_master=True)
        torneo_id = TorneoService.crear_torneo("T", "Copa", copa_id, es_master=True)
        jid = JornadaRepository.crear(torneo_id, "2099-01-01", "Día 1", 1, lugar="Estadio", horario="09:30")
        j = JornadaRepository.obtener_por_id(jid)
        self.assertEqual(j.lugar, "Estadio")
        self.assertEqual(j.horario, "09:30")

    def test_permisos(self):
        anio_id = AnioService.crear_anio(2096, es_master=True)
        camp_id = CampeonatoService.crear_campeonato("C", anio_id, es_master=True)
        CampeonatoService.asignar_permiso(camp_id, 7, "master")
        self.assertEqual(CampeonatoService.verificar_permiso_usuario(camp_id, 7), "master")
        with self.assertRaises(ValueError):
            CampeonatoService.asignar_permiso(camp_id, 8, "invalido")
        CampeonatoService.revocar_permiso(camp_id, 7)
        self.assertIsNone(CampeonatoService.verificar_permiso_usuario(camp_id, 7))

    def test_flujo_end_to_end(self):
        anio_id = AnioService.crear_anio(2095, es_master=True)
        camp_id = CampeonatoService.crear_campeonato("E2E", anio_id, es_master=True)
        copa_id = CopaService.crear_copa("Copa E2E", camp_id, es_master=True)
        torneo_id = TorneoService.crear_torneo("T", "Copa", copa_id, es_master=True)
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



class TestRoles(TestJerarquia):
    def test_validar_pin_por_rol(self):
        from backend.database.repositories import ConfiguracionRepository
        self.assertEqual(TorneoService.validar_pin(ConfiguracionRepository.obtener_pin_master()), "master")
        self.assertEqual(TorneoService.validar_pin(ConfiguracionRepository.obtener_pin()), "organizador")
        self.assertIsNone(TorneoService.validar_pin("pin-invalido-xyz"))

    def test_servicios_exigen_master(self):
        with self.assertRaises(PermissionError):
            AnioService.crear_anio(2001)
        with self.assertRaises(PermissionError):
            CampeonatoService.crear_campeonato("X", 1)
        with self.assertRaises(PermissionError):
            CopaService.crear_copa("X", 1)
        with self.assertRaises(PermissionError):
            CopaService.eliminar_copa(1)
        with self.assertRaises(PermissionError):
            TorneoService.crear_torneo("T", "Copa", 1)

if __name__ == "__main__":
    unittest.main()
