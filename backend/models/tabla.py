from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class EstadisticaEquipo:
    equipo: str
    pj: int = 0
    pg: int = 0
    pe: int = 0
    pp: int = 0
    gf: int = 0
    gc: int = 0
    dg: int = 0
    pts: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "equipo": self.equipo,
            "pj": self.pj,
            "pg": self.pg,
            "pe": self.pe,
            "pp": self.pp,
            "gf": self.gf,
            "gc": self.gc,
            "dg": self.dg,
            "pts": self.pts,
        }
