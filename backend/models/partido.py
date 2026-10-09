from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Partido:
    id: int
    grupo_id: int
    categoria_id: int
    dia: str
    equipo_local: str
    equipo_visita: str
    goles_local: int = 0
    goles_visita: int = 0
    jugado: bool = False
    es_definicion: bool = False
    orden: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "grupo_id": self.grupo_id,
            "categoria_id": self.categoria_id,
            "dia": self.dia,
            "equipo_local": self.equipo_local,
            "equipo_visita": self.equipo_visita,
            "goles_local": self.goles_local,
            "goles_visita": self.goles_visita,
            "jugado": self.jugado,
            "es_definicion": self.es_definicion,
            "orden": self.orden,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Partido":
        return cls(
            id=data.get("id", 0),
            grupo_id=data.get("grupo_id", 0),
            categoria_id=data.get("categoria_id", 0),
            dia=data.get("dia", ""),
            equipo_local=data.get("equipo_local", ""),
            equipo_visita=data.get("equipo_visita", ""),
            goles_local=int(data.get("goles_local", 0)),
            goles_visita=int(data.get("goles_visita", 0)),
            jugado=bool(data.get("jugado", False)),
            es_definicion=bool(data.get("es_definicion", False)),
            orden=int(data.get("orden", 0)),
        )
