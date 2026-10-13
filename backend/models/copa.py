from dataclasses import dataclass
from typing import Dict, Any, Optional

MODO_CAMPEON_DEFECTO = "final_lideres"
CRITERIOS_DEFECTO = "dg,gf,h2h,pg,gc"

MODOS_CAMPEON = {
    "final_lideres": "Final entre líderes de grupo (1° vs 1°; con 3+ grupos, los 2 mejores líderes)",
    "liguilla_lideres": "Liguilla de líderes (todos contra todos entre los líderes de grupo)",
    "tabla_unica": "Líder de la tabla general (sin final)",
}

CRITERIOS_DESEMPATE = {
    "dg": "Diferencia de goles",
    "pg": "Partidos ganados",
    "h2h": "Resultado entre ellos (enfrentamiento directo)",
    "dg_h2h": "Diferencia de goles entre ellos",
    "gf": "Goles a favor",
    "gc": "Goles en contra (menos es mejor)",
}


@dataclass
class Copa:
    id: int
    nombre: str
    campeonato_id: int  # Foreign key a campeonatos
    orden: int = 0
    activo: bool = True
    color: Optional[str] = None
    modo_campeon: str = MODO_CAMPEON_DEFECTO
    criterios_desempate: str = CRITERIOS_DEFECTO
    puntos_victoria: int = 3
    puntos_empate: int = 1

    def lista_criterios(self):
        return [c for c in (self.criterios_desempate or "").split(",") if c in CRITERIOS_DESEMPATE]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "campeonato_id": self.campeonato_id,
            "orden": self.orden,
            "activo": self.activo,
            "color": self.color,
            "modo_campeon": self.modo_campeon,
            "criterios_desempate": self.criterios_desempate,
            "puntos_victoria": self.puntos_victoria,
            "puntos_empate": self.puntos_empate,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Copa":
        return cls(
            id=data.get("id", 0),
            nombre=data.get("nombre", ""),
            campeonato_id=data.get("campeonato_id", 0),
            orden=data.get("orden", 0),
            activo=bool(data.get("activo", True)),
            color=data.get("color"),
            modo_campeon=data.get("modo_campeon") or MODO_CAMPEON_DEFECTO,
            criterios_desempate=data.get("criterios_desempate") or CRITERIOS_DEFECTO,
            puntos_victoria=data.get("puntos_victoria", 3),
            puntos_empate=data.get("puntos_empate", 1),
        )
