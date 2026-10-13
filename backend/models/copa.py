from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class Copa:
    id: int
    nombre: str
    campeonato_id: int  # Foreign key a campeonatos
    orden: int = 0
    activo: bool = True
    color: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "campeonato_id": self.campeonato_id,
            "orden": self.orden,
            "activo": self.activo,
            "color": self.color,
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
        )
