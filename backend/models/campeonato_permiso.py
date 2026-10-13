from dataclasses import dataclass
from typing import Dict, Any
from datetime import datetime

@dataclass
class CampeonatoPermiso:
    id: int
    campeonato_id: int
    usuario_id: int
    rol: str  # "organizador" o "master"
    fecha_asignacion: str = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "campeonato_id": self.campeonato_id,
            "usuario_id": self.usuario_id,
            "rol": self.rol,
            "fecha_asignacion": self.fecha_asignacion,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CampeonatoPermiso":
        return cls(
            id=data.get("id", 0),
            campeonato_id=data.get("campeonato_id", 0),
            usuario_id=data.get("usuario_id", 0),
            rol=data.get("rol", ""),
            fecha_asignacion=data.get("fecha_asignacion", datetime.now().isoformat()),
        )
