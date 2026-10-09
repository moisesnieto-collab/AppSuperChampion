from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class Grupo:
    id: int
    categoria_id: int
    dia: str
    nombre: str
    equipos: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "categoria_id": self.categoria_id,
            "dia": self.dia,
            "nombre": self.nombre,
            "equipos": self.equipos,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Grupo":
        return cls(
            id=data.get("id", 0),
            categoria_id=data.get("categoria_id", 0),
            dia=data.get("dia", ""),
            nombre=data.get("nombre", ""),
            equipos=data.get("equipos", []),
        )
