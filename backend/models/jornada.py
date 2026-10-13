from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Jornada:
    id: int
    torneo_id: int
    fecha: str
    nombre: str
    orden: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "torneo_id": self.torneo_id,
            "fecha": self.fecha,
            "nombre": self.nombre,
            "orden": self.orden,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Jornada":
        return cls(
            id=data.get("id", 0),
            torneo_id=data.get("torneo_id", 0),
            fecha=data.get("fecha", ""),
            nombre=data.get("nombre", ""),
            orden=data.get("orden", 1),
        )
