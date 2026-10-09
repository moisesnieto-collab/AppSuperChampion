from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Categoria:
    id: int
    nombre: str
    orden: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "orden": self.orden,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Categoria":
        return cls(
            id=data.get("id", 0),
            nombre=data.get("nombre", ""),
            orden=data.get("orden", 1),
        )
