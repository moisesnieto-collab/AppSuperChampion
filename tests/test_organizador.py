"""Pruebas del rol Organizador: qué puede y qué no puede hacer (lógica y selector de UI)."""
import types
import unittest

from backend.database.repositories import PartidoRepository
from backend.services.anio_service import AnioService
from backend.services.campeonato_service import CampeonatoService
from backend.services.copa_service import CopaService
from backend.services.torneo_service import TorneoService
from tests.test_master_flujo_completo import BaseDB, EQUIPOS


def tooltips(ctrl, acc=None):
    """Recolecta recursivamente los tooltips de un árbol de controles Flet."""
    acc = [] if acc is None else acc
    tip = getattr(ctrl, "tooltip", None)
    if isinstance(tip, str):
        acc.append(tip)
    for attr in ("controls", "items"):
        for sub in getattr(ctrl, attr, None) or []:
            tooltips(sub, acc)
    sub = getattr(ctrl, "content", None)
    if sub is not None and not isinstance(sub, str):
        tooltips(sub, acc)
    return acc


class TestOrganizadorLogica(BaseDB):
    def test_no_puede_crear_ni_eliminar_nivel_master(self):
        self.crear_jerarquia(2300, "OrgMaster")
        with self.assertRaises(PermissionError):
            AnioService.crear_anio(2301, es_master=False)
        with self.assertRaises(PermissionError):
            CampeonatoService.crear_campeonato("X", self.anio_id, es_master=False)
        with self.assertRaises(PermissionError):
            CopaService.crear_copa("X", self.camp_id, es_master=False)
        with self.assertRaises(PermissionError):
            TorneoService.crear_torneo("X", "Copa", self.copa_id, es_master=False)
        with self.assertRaises(PermissionError):
            TorneoService.eliminar_torneo(self.torneo_id, es_master=False)
        with self.assertRaises(PermissionError):
            TorneoService.actualizar_orden_torneo(self.torneo_id, 3, es_master=False)

    def test_puede_gestionar_categorias_grupos(self):
        self.crear_jerarquia(2301, "OrgGest")
        cat2 = TorneoService.crear_categoria(self.jornada_id, "8° Básico", es_organizador=True)
        g2 = TorneoService.crear_grupo(cat2, self.jornada_id, "Grupo A", EQUIPOS, es_organizador=True)
        TorneoService.actualizar_grupo(g2, ["A", "B", "C", "D"], es_organizador=True)
        TorneoService.eliminar_grupo(g2, es_organizador=True)
        TorneoService.eliminar_categoria(cat2, es_organizador=True)
        self.assertEqual([c.id for c in TorneoService.obtener_categorias_por_jornada(self.jornada_id)], [self.cat_id])

    def test_programacion_no_cambia_estado(self):
        self.crear_jerarquia(2399, "OrgProg")
        pid = self.partidos()[0].id
        antes = PartidoRepository.obtener_por_id(pid)
        TorneoService.actualizar_programacion(pid, "15:30", "Cancha 1", es_organizador=True)
        p = PartidoRepository.obtener_por_id(pid)
        self.assertEqual((p.hora, p.cancha), ("15:30", "Cancha 1"))
        self.assertEqual((p.jugado, p.en_vivo, p.goles_local, p.goles_visita),
                         (antes.jugado, antes.en_vivo, antes.goles_local, antes.goles_visita))
        with self.assertRaises(PermissionError):
            TorneoService.actualizar_programacion(pid, "15:30", "C", es_organizador=False)
        with self.assertRaises(ValueError):
            TorneoService.actualizar_programacion(pid, "99:99", "C", es_organizador=True)

    def test_puede_marcadores_vivo_y_reinicio(self):
        self.crear_jerarquia(2302, "OrgMarc")
        pid = self.partidos()[0].id
        TorneoService.guardar_marcador(pid, 2, 1, es_organizador=True)
        TorneoService.actualizar_en_vivo(pid, True, "11:15", es_organizador=True)
        p = PartidoRepository.obtener_por_id(pid)
        self.assertEqual((p.goles_local, p.goles_visita, p.en_vivo, p.hora), (2, 1, True, "11:15"))
        with self.assertRaises(ValueError):
            TorneoService.actualizar_en_vivo(pid, True, "99:99", es_organizador=True)
        TorneoService.reiniciar_marcador(pid, es_organizador=True)
        self.assertFalse(PartidoRepository.obtener_por_id(pid).jugado)

    def test_puede_desempate_y_final(self):
        self.crear_jerarquia(2303, "OrgFinal")
        pid = TorneoService.generar_partido_desempate(
            self.cat_id, self.jornada_id, self.grupo_id, "Alfa", "Beta", es_organizador=True)
        self.assertTrue(pid)
        self.assertFalse(TorneoService.generar_final_dia2(self.cat_id, self.jornada_id, es_organizador=True))

    def test_consulta_no_puede_nada(self):
        self.crear_jerarquia(2304, "Consulta")
        with self.assertRaises(PermissionError):
            TorneoService.crear_categoria(self.jornada_id, "Y")
        with self.assertRaises(PermissionError):
            TorneoService.guardar_marcador(self.partidos()[0].id, 1, 1)


class TestOrganizadorSelectorUI(BaseDB):
    def construir(self, rol, org=True, admin=True):
        from frontend.components.selector_categoria import crear_selector_categoria_y_dia
        estado = {
            "anio_activo_id": self.anio_id, "campeonato_activo_id": self.camp_id,
            "copa_activa_id": self.copa_id, "torneo_activo_id": self.torneo_id,
            "jornada_activa_id": self.jornada_id, "categoria_activa_id": self.cat_id,
            "es_organizador": org, "modo_admin": admin, "rol": rol,
        }
        page = types.SimpleNamespace(bgcolor=None, overlay=[], update=lambda: None)
        sel = crear_selector_categoria_y_dia(estado, page, [], [], lambda: None, vista="campeonato",
                                             on_crear_grupo=lambda *a: None, on_editar_grupo=lambda *a: None,
                                             on_eliminar_grupo=lambda *a: None, on_crear_jornada=lambda *a: None,
                                             on_eliminar_jornada=lambda *a: None, on_buscar_jornada=lambda *a: None)
        return tooltips(sel)

    def test_organizador_ve_herramientas_propias_pero_no_de_master(self):
        self.crear_jerarquia(2310, "UIOrg")
        tips = self.construir("organizador")
        for esperado in ("Nueva categoría", "Eliminar categoría", "Nueva jornada", "Buscar jornada",
                         "Eliminar jornada", "Nuevo grupo"):
            self.assertIn(esperado, tips)
        for prohibido in ("Nueva copa", "Editar copa", "Eliminar copa", "Nuevo torneo",
                          "Eliminar torneo", "Editar", "Administrar"):
            self.assertNotIn(prohibido, tips)

    def test_master_ve_ademas_herramientas_de_jerarquia(self):
        self.crear_jerarquia(2311, "UIMaster")
        tips = self.construir("master")
        for esperado in ("Nueva copa", "Nuevo torneo", "Nueva categoría", "Nuevo grupo"):
            self.assertIn(esperado, tips)

    def test_sin_modo_admin_o_sin_pin_no_hay_herramientas(self):
        self.crear_jerarquia(2312, "UIConsulta")
        for org, admin in ((True, False), (False, True), (False, False)):
            tips = self.construir("organizador", org, admin)
            self.assertNotIn("Nueva categoría", tips)
            self.assertNotIn("Nuevo grupo", tips)
            self.assertNotIn("Nueva jornada", tips)


if __name__ == "__main__":
    unittest.main()
