import flet as ft
import unittest
from config.constants import mezclar_color, oscurecer_color, COLOR_TARJETA, COLOR_TARJETA_SEGUNDARIA
from frontend.components.tarjeta_campeon import crear_tarjeta_campeon
from frontend.components.tabla_posiciones import crear_tabla_posiciones
from frontend.components.lista_partidos import crear_lista_partidos
from backend.models.tabla import EstadisticaEquipo
from backend.models.partido import Partido


class TestComponentesColor(unittest.TestCase):
    def test_utilidades_color(self):
        color = "#1E3A8A"
        oscurecido = oscurecer_color(color, 0.30)
        mezclado = mezclar_color(color, 0.22)
        self.assertTrue(oscurecido.startswith("#"))
        self.assertTrue(mezclado.startswith("#"))
        self.assertEqual(len(oscurecido), 7)
        self.assertEqual(len(mezclado), 7)

    def test_tarjeta_campeon_color_copa(self):
        color_copa = "#7F1D1D"
        # Sin color_copa
        c_sin = crear_tarjeta_campeon(
            estado_campeon={"estado": "SIN_DATOS"},
            es_organizador=False
        )
        self.assertEqual(c_sin.bgcolor, COLOR_TARJETA)

        # Con color_copa
        c_con = crear_tarjeta_campeon(
            estado_campeon={"estado": "SIN_DATOS"},
            es_organizador=False,
            color_copa=color_copa
        )
        self.assertEqual(c_con.bgcolor, color_copa)

        # En curso con color_copa
        c_en_curso = crear_tarjeta_campeon(
            estado_campeon={
                "estado": "EN_CURSO",
                "puntero_actual": "Equipo A",
                "partidos_jugados": "2/6",
                "motivo": "Torneo en curso"
            },
            es_organizador=False,
            color_copa=color_copa
        )
        self.assertEqual(c_en_curso.bgcolor, color_copa)

    def test_tabla_posiciones_color_copa(self):
        color_copa = "#065F46"
        stat = EstadisticaEquipo(
            equipo="Equipo Test",
            pj=1,
            pg=1,
            pe=0,
            pp=0,
            gf=2,
            gc=0,
            dg=2,
            pts=3
        )
        # Sin color_copa
        t_sin = crear_tabla_posiciones("Grupo A", [stat])
        self.assertEqual(t_sin.bgcolor, COLOR_TARJETA)

        # Con color_copa
        t_con = crear_tabla_posiciones("Grupo A", [stat], color_copa=color_copa)
        self.assertEqual(t_con.bgcolor, color_copa)

    def test_lista_partidos_color_copa(self):
        color_copa = "#581C87"
        partido = Partido(
            id=1,
            grupo_id=1,
            categoria_id=1,
            fecha_jornada_id=1,
            equipo_local="Equipo A",
            equipo_visita="Equipo B",
            goles_local=2,
            goles_visita=1,
            jugado=1,
            es_definicion=0,
            orden=1
        )
        # Sin color_copa
        lp_sin = crear_lista_partidos(
            grupo_nombre="Grupo A",
            partidos=[partido],
            es_organizador=False,
            on_guardar_marcador=lambda *args: None,
            on_reiniciar_marcador=lambda *args: None
        )
        self.assertIsInstance(lp_sin, ft.Column)  # rediseño: tarjeta SURFACE fija

        # Con color_copa
        lp_con = crear_lista_partidos(
            grupo_nombre="Grupo A",
            partidos=[partido],
            es_organizador=False,
            on_guardar_marcador=lambda *args: None,
            on_reiniciar_marcador=lambda *args: None,
            color_copa=color_copa
        )
        self.assertIsInstance(lp_con, ft.Column)


if __name__ == "__main__":
    unittest.main()


class TestBotonGranFinal(unittest.TestCase):
    def _hay_boton(self, ctrl):
        import flet as ft
        if isinstance(ctrl, ft.FilledButton) and "Gran Final" in str(ctrl.content):
            return True
        hijos = []
        for attr in ("content", "controls"):
            v = getattr(ctrl, attr, None)
            if isinstance(v, list):
                hijos += v
            elif v is not None and not isinstance(v, str):
                hijos.append(v)
        return any(self._hay_boton(h) for h in hijos)

    def test_boton_segun_organizador(self):
        for es_org in (True, False):
            tarjeta = crear_tarjeta_campeon(
                estado_campeon={"estado": "EN_CURSO"},
                es_organizador=es_org,
                on_generar_final=lambda: None,
            )
            self.assertEqual(self._hay_boton(tarjeta), es_org)
