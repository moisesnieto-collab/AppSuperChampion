from dataclasses import dataclass
from typing import Dict, Any
from datetime import datetime

@dataclass
class Torneo:
    id: int
    nombre: str
    tipo: str  # "Apertura" o "Clausura"
    anio: int
    activo: bool = True
    fecha_inicio: str = None
    fecha_fin: str = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "tipo": self.tipo,
            "anio": self.anio,
            "activo": self.activo,
            "fecha_inicio": self.fecha_inicio,
            "fecha_fin": self.fecha_fin,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Torneo":
        return cls(
            id=data.get("id", 0),
            nombre=data.get("nombre", ""),
            tipo=data.get("tipo", ""),
            anio=data.get("anio", datetime.now().year),
            activo=bool(data.get("activo", True)),
            fecha_inicio=data.get("fecha_inicio"),
            fecha_fin=data.get("fecha_fin"),
        )
