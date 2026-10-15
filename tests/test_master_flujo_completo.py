"""Plan de pruebas del flujo Master: Año -> Campeonato -> Copa -> Torneo -> Jornada ->
Categoría -> Grupo -> Marcadores -> VIVO -> Tabla -> Campeón, más permisos y validaciones."""
import os
import shutil
import tempfile
import unittest

from backend.database.schema import inicializar_db
from backend.database.repositories import (
    JornadaRepository, PartidoRepository, GrupoRepository, CategoriaRepository, TorneoRepository,
    ConfiguracionRepository,
)
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
        config.settings.TURSO_URL = os.path.join(cls.dir, "test_master.db")
        config.settings.TURSO_TOKEN = ""
        inicializar_db()

    @classmethod
    def tearDownClass(cls):
        import config.settings
        config.settings.TURSO_URL = cls.original
        shutil.rmtree(cls.dir, ignore_errors=True)

    def crear_jerarquia(self, anio=2200, nombre="Camp"):
        self.anio_id = AnioService.crear_anio(anio, es_master=True)
        self.camp_id = CampeonatoService.crear_campeonato(nombre, self.anio_id, es_master=True)
        self.copa_id = CopaService.crear_copa("Copa A", self.camp_id, color="#1E3A8A", es_master=True)
        self.torneo_id = TorneoService.crear_torneo("Torneo 1", "Copa", self.copa_id, es_master=True)
        self.jornada_id = JornadaRepository.crear(self.torneo_id, "2200-05-01", "Día 1", 1)
        self.cat_id = TorneoService.crear_categoria(self.jornada_id, "7° Básico", es_organizador=True)
        self.grupo_id = TorneoService.crear_grupo(self.cat_id, self.jornada_id, "Grupo A", EQUIPOS,
                                                  es_organizador=True)

    def partidos(self):
        return TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)["grupos"][0]["partidos"]


class TestCrearJerarquiaMaster(BaseDB):
    def test_pines_y_roles(self):
        self.assertEqual(TorneoService.validar_pin(ConfiguracionRepository.obtener_pin_master()), "master")
        self.assertEqual(TorneoService.validar_pin(ConfiguracionRepository.obtener_pin()), "organizador")
        self.assertIsNone(TorneoService.validar_pin("zzz-no"))

    def test_crear_toda_la_jerarquia(self):
        self.crear_jerarquia(2201, "Jerarquía")
        self.assertEqual(TorneoRepository.obtener_por_copa(self.copa_id)[0].id, self.torneo_id)
        self.assertEqual([j.id for j in TorneoService.obtener_jornadas_por_torneo(self.torneo_id)], [self.jornada_id])
        self.assertEqual([c.id for c in TorneoService.obtener_categorias_por_jornada(self.jornada_id)], [self.cat_id])
        self.assertEqual(len(GrupoRepository.obtener_por_categoria_y_jornada(self.cat_id, self.jornada_id)), 1)
        self.assertEqual(CopaService.obtener_copa_por_id(self.copa_id).color, "#1E3A8A")

    def test_cuadrangular_genera_6_partidos(self):
        self.crear_jerarquia(2202, "Cuad")
        self.assertEqual(len(self.partidos()), 6)

    def test_varios_torneos_orden(self):
        self.crear_jerarquia(2203, "Orden")
        t2 = TorneoService.crear_torneo("Torneo 2", "Liga", self.copa_id, orden=5, es_master=True)
        TorneoService.actualizar_orden_torneo(t2, 0, es_master=True)
        self.assertEqual(len(TorneoRepository.obtener_por_copa(self.copa_id)), 2)

    def test_validaciones_categoria_y_grupo(self):
        self.crear_jerarquia(2204, "Valid")
        with self.assertRaises(ValueError):
            TorneoService.crear_categoria(self.jornada_id, "  ", es_organizador=True)
        with self.assertRaises(ValueError):
            TorneoService.crear_categoria(self.jornada_id, "7° básico", es_organizador=True)
        with self.assertRaises(ValueError):
            TorneoService.crear_grupo(self.cat_id, self.jornada_id, "", EQUIPOS, es_organizador=True)
        with self.assertRaises(ValueError):
            TorneoService.crear_grupo(self.cat_id, self.jornada_id, "grupo a", EQUIPOS, es_organizador=True)
        with self.assertRaises(ValueError):
            TorneoService.crear_grupo(self.cat_id, self.jornada_id, "Grupo B", ["Solo"], es_organizador=True)

    def test_editar_grupo_regenera_partidos(self):
        self.crear_jerarquia(2205, "Edit")
        TorneoService.actualizar_grupo(self.grupo_id, ["A", "B", "C", "D"], es_organizador=True)
        self.assertEqual(len(self.partidos()), 6)
        TorneoService.actualizar_grupo(self.grupo_id, ["A", "B", "C"], es_organizador=True)
        self.assertEqual(len(self.partidos()), 0)

    def test_eliminar_en_cascada_y_dependencias(self):
        self.crear_jerarquia(2206, "Elim")
        with self.assertRaises(ValueError):
            CopaService.eliminar_copa(self.copa_id, es_master=True)
        TorneoService.eliminar_grupo(self.grupo_id, es_organizador=True)
        self.assertEqual(TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)["grupos"], [])
        TorneoService.eliminar_categoria(self.cat_id, es_organizador=True)
        self.assertEqual(TorneoService.obtener_categorias_por_jornada(self.jornada_id), [])
        TorneoService.eliminar_torneo(self.torneo_id, es_master=True)
        CopaService.eliminar_copa(self.copa_id, es_master=True)
        CampeonatoService.eliminar_campeonato(self.camp_id, es_master=True)
        AnioService.eliminar_anio(self.anio_id, es_master=True)

    def test_jornada_editar_y_buscar(self):
        self.crear_jerarquia(2207, "Jor")
        JornadaRepository.actualizar(self.jornada_id, "2200-06-01", "Día X", "Cancha", "10:00")
        j = JornadaRepository.obtener_por_id(self.jornada_id)
        self.assertEqual((j.nombre, j.lugar, j.horario), ("Día X", "Cancha", "10:00"))
        self.assertEqual(JornadaRepository.buscar_por_fecha(self.torneo_id, "2200-06-01").id, self.jornada_id)
        n = TorneoService.copiar_categorias_de_ultima_jornada(
            self.torneo_id, JornadaRepository.crear(self.torneo_id, "2200-07-01", "Día 2", 2))
        self.assertEqual(n, 1)


class TestPermisos(BaseDB):
    def test_sin_master_u_organizador_se_bloquea(self):
        self.crear_jerarquia(2210, "Perm")
        pid = self.partidos()[0].id
        with self.assertRaises(PermissionError):
            TorneoService.guardar_marcador(pid, 1, 0)
        with self.assertRaises(PermissionError):
            TorneoService.reiniciar_marcador(pid)
        with self.assertRaises(PermissionError):
            TorneoService.actualizar_en_vivo(pid, True, "10:00")
        with self.assertRaises(PermissionError):
            TorneoService.crear_categoria(self.jornada_id, "X")
        with self.assertRaises(PermissionError):
            TorneoService.crear_grupo(self.cat_id, self.jornada_id, "Z", EQUIPOS)
        with self.assertRaises(PermissionError):
            TorneoService.eliminar_grupo(self.grupo_id)
        with self.assertRaises(PermissionError):
            TorneoService.eliminar_torneo(self.torneo_id)
        with self.assertRaises(PermissionError):
            AnioService.crear_anio(2999)
        with self.assertRaises(PermissionError):
            TorneoService.generar_final_dia2(self.cat_id, self.jornada_id)


class TestMarcadoresYVivo(BaseDB):
    def test_guardar_y_reiniciar_marcador(self):
        self.crear_jerarquia(2220, "Marc")
        p = self.partidos()[0]
        self.assertFalse(p.jugado)
        TorneoService.guardar_marcador(p.id, 3, 1, es_organizador=True)
        p = PartidoRepository.obtener_por_id(p.id)
        self.assertEqual((p.goles_local, p.goles_visita, p.jugado), (3, 1, True))
        TorneoService.reiniciar_marcador(p.id, es_organizador=True)
        p = PartidoRepository.obtener_por_id(p.id)
        self.assertEqual((p.goles_local, p.goles_visita, p.jugado), (0, 0, False))

    def test_goles_negativos_rechazados(self):
        self.crear_jerarquia(2221, "Neg")
        with self.assertRaises(ValueError):
            TorneoService.guardar_marcador(self.partidos()[0].id, -1, 0, es_organizador=True)

    def test_habilitar_y_deshabilitar_vivo_con_hora(self):
        self.crear_jerarquia(2222, "Vivo")
        pid = self.partidos()[0].id
        TorneoService.actualizar_en_vivo(pid, True, "15:30", es_organizador=True)
        p = PartidoRepository.obtener_por_id(pid)
        self.assertTrue(p.en_vivo)
        self.assertEqual(p.hora, "15:30")
        TorneoService.actualizar_en_vivo(pid, False, "15:30", es_organizador=True)
        self.assertFalse(PartidoRepository.obtener_por_id(pid).en_vivo)

    def test_hora_invalida(self):
        self.crear_jerarquia(2223, "Hora")
        pid = self.partidos()[0].id
        for mala in ("25:99", "abc", "1530"):
            with self.assertRaises(ValueError):
                TorneoService.actualizar_en_vivo(pid, True, mala, es_organizador=True)
        TorneoService.actualizar_en_vivo(pid, True, "", es_organizador=True)

    def test_vivo_aparece_en_datos_y_no_altera_marcador(self):
        self.crear_jerarquia(2224, "VivoDatos")
        pid = self.partidos()[0].id
        TorneoService.guardar_marcador(pid, 2, 2, es_organizador=True)
        TorneoService.actualizar_en_vivo(pid, True, "09:00", es_organizador=True)
        p = next(x for x in self.partidos() if x.id == pid)
        self.assertTrue(p.en_vivo)
        self.assertEqual((p.goles_local, p.goles_visita), (2, 2))


class TestTablaYCampeon(BaseDB):
    def test_tabla_refleja_resultados(self):
        self.crear_jerarquia(2230, "Tabla")
        p = self.partidos()[0]
        TorneoService.guardar_marcador(p.id, 4, 0, es_organizador=True)
        tabla = TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)["grupos"][0]["tabla"]
        self.assertEqual(tabla[0].equipo, p.equipo_local)
        self.assertEqual((tabla[0].pts, tabla[0].pj, tabla[0].dg), (3, 1, 4))

    def test_empate_da_un_punto(self):
        self.crear_jerarquia(2231, "Empate")
        p = self.partidos()[0]
        TorneoService.guardar_marcador(p.id, 1, 1, es_organizador=True)
        tabla = TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)["grupos"][0]["tabla"]
        por_equipo = {t.equipo: t for t in tabla}
        self.assertEqual(por_equipo[p.equipo_local].pts, 1)
        self.assertEqual(por_equipo[p.equipo_visita].pts, 1)

    def test_torneo_completo_define_estado_campeon(self):
        self.crear_jerarquia(2232, "Campeon")
        for i, p in enumerate(self.partidos()):
            TorneoService.guardar_marcador(p.id, i + 1, 0, es_organizador=True)
        datos = TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)
        self.assertIsInstance(datos["estado_campeon"], dict)
        self.assertTrue(all(p.jugado for p in datos["grupos"][0]["partidos"]))

    def test_desempate(self):
        self.crear_jerarquia(2233, "Desempate")
        pid = TorneoService.generar_partido_desempate(
            self.cat_id, self.jornada_id, self.grupo_id, "Alfa", "Beta", es_organizador=True)
        datos = TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)
        self.assertIn(pid, [p.id for p in datos["partidos_definicion"]])

    def test_final_requiere_dos_grupos(self):
        self.crear_jerarquia(2234, "Final")
        self.assertFalse(TorneoService.generar_final_dia2(self.cat_id, self.jornada_id, es_organizador=True))
        g2 = TorneoService.crear_grupo(self.cat_id, self.jornada_id, "Grupo B", ["E", "F", "G", "H"],
                                       es_organizador=True)
        self.assertTrue(g2)
        for g in TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)["grupos"]:
            for p in g["partidos"]:
                TorneoService.guardar_marcador(p.id, 1, 0, es_organizador=True)
        TorneoService.generar_final_dia2(self.cat_id, self.jornada_id, es_organizador=True)


class TestInterfazMaster(BaseDB):
    """Construye los componentes de UI con datos reales (sin ejecutar la app)."""

    def test_lista_partidos_modo_master_y_consulta(self):
        from frontend.components.lista_partidos import crear_lista_partidos
        self.crear_jerarquia(2240, "UI")
        ps = self.partidos()
        TorneoService.actualizar_en_vivo(ps[0].id, True, "10:00", es_organizador=True)
        ps = self.partidos()
        for es_org in (True, False):
            c = crear_lista_partidos("Grupo A", ps, es_org, lambda *a: None, lambda *a: None)
            self.assertIsNotNone(c)

    def test_tabla_posiciones_se_construye(self):
        from frontend.components.tabla_posiciones import crear_tabla_posiciones
        self.crear_jerarquia(2241, "UITabla")
        g = TorneoService.obtener_datos_categoria_dia(self.cat_id, self.jornada_id)["grupos"][0]
        for compacto in (True, False):
            self.assertIsNotNone(crear_tabla_posiciones("Grupo A", g["tabla"], compacto=compacto))

    def test_fecha_sin_hora(self):
        from frontend.components.vista_rediseno import fecha_sin_hora
        self.assertEqual(fecha_sin_hora("2026-09-27T03:00:00+00:00"), "27-09-2026")
        self.assertEqual(fecha_sin_hora("2026-09-27"), "27-09-2026")


if __name__ == "__main__":
    unittest.main()
