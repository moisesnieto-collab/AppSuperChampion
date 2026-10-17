import unittest

from backend.services.torneo_service import TorneoService
from backend.services import publicador
from scripts import exportar_datos_publicos as exp
from tests.test_master_flujo_completo import BaseDB


class TestJornadaPublica(BaseDB):
    def test_marcar_exige_rol_y_persiste(self):
        self.crear_jerarquia(2500, "JorPub")
        with self.assertRaises(PermissionError):
            TorneoService.marcar_jornada_publica(self.jornada_id, es_organizador=False)
        TorneoService.marcar_jornada_publica(self.jornada_id, es_organizador=True)
        self.assertEqual(TorneoService.obtener_jornada_publica(), self.jornada_id)

    def test_generar_solo_jornada_con_todas_sus_categorias(self):
        self.crear_jerarquia(2501, "JorGen")
        cat2 = TorneoService.crear_categoria(self.jornada_id, "Extra", es_organizador=True)
        datos = exp.generar(self.jornada_id)
        jornadas = [j for c in datos["copas"] for t in c["torneos"] for j in t["jornadas"]]
        self.assertEqual(len(jornadas), 1)
        ids = {c["id"] for c in jornadas[0]["categorias"]}
        self.assertEqual(ids, {self.cat_id, cat2})

    def test_reemplazar_categoria_solo_su_nodo(self):
        doc = {"copas": [{"torneos": [{"jornadas": [{"categorias": [
            {"id": 1, "x": 0}, {"id": 2, "x": 0}]}]}]}]}
        self.assertTrue(publicador.reemplazar_categoria(doc, {"id": 2, "x": 9}))
        cats = doc["copas"][0]["torneos"][0]["jornadas"][0]["categorias"]
        self.assertEqual([c["x"] for c in cats], [0, 9])
        self.assertFalse(publicador.reemplazar_categoria(doc, {"id": 3}))


if __name__ == "__main__":
    unittest.main()
