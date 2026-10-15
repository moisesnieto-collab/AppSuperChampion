from dataclasses import dataclass
from typing import Dict, Any
from datetime import datetime

@dataclass
class Torneo:
    id: int
    nombre: str
    tipo: str  # "Apertura" o "Clausura"
    copa_id: int  # Foreign key a copas
    orden: int = 0
    activo: bool = True
    fecha_inicio: str = None
    fecha_fin: str = None
    modo_campeon: str = "final_lideres"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "tipo": self.tipo,
            "copa_id": self.copa_id,
            "orden": self.orden,
            "activo": self.activo,
            "fecha_inicio": self.fecha_inicio,
            "fecha_fin": self.fecha_fin,
            "modo_campeon": self.modo_campeon,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Torneo":
        return cls(
            id=data.get("id", 0),
            nombre=data.get("nombre", ""),
            tipo=data.get("tipo", ""),
            copa_id=data.get("copa_id", 0),
            orden=data.get("orden", 0),
            activo=bool(data.get("activo", True)),
            fecha_inicio=data.get("fecha_inicio"),
            fecha_fin=data.get("fecha_fin"),
            modo_campeon=data.get("modo_campeon") or "final_lideres",
        )
