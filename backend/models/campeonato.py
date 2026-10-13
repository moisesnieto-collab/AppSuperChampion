from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Campeonato:
    id: int
    nombre: str
    anio_id: int  # Foreign key a anios
    orden: int = 0
    activo: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "anio_id": self.anio_id,
            "orden": self.orden,
            "activo": self.activo,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Campeonato":
        return cls(
            id=data.get("id", 0),
            nombre=data.get("nombre", ""),
            anio_id=data.get("anio_id", 0),
            orden=data.get("orden", 0),
            activo=bool(data.get("activo", True)),
        )
