from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class Grupo:
    id: int
    categoria_id: int
    fecha_jornada_id: int
    nombre: str
    equipos: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "categoria_id": self.categoria_id,
            "fecha_jornada_id": self.fecha_jornada_id,
            "nombre": self.nombre,
            "equipos": self.equipos,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Grupo":
        return cls(
            id=data.get("id", 0),
            categoria_id=data.get("categoria_id", 0),
            fecha_jornada_id=data.get("fecha_jornada_id", 0),
            nombre=data.get("nombre", ""),
            equipos=data.get("equipos", []),
        )
