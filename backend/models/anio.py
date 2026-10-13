from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Anio:
    id: int
    valor: int  # Ej: 2024
    orden: int = 0
    activo: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "valor": self.valor,
            "orden": self.orden,
            "activo": self.activo,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Anio":
        return cls(
            id=data.get("id", 0),
            valor=data.get("valor", 0),
            orden=data.get("orden", 0),
            activo=bool(data.get("activo", True)),
        )
