from typing import List, Optional
from backend.models.copa import Copa
from backend.database.repositories import CopaRepository


class CopaService:
    @staticmethod
    def obtener_copas() -> List[Copa]:
        return CopaRepository.obtener_todos()

    @staticmethod
    def obtener_copas_por_campeonato(campeonato_id: int) -> List[Copa]:
        return CopaRepository.obtener_por_campeonato(campeonato_id)

    @staticmethod
    def obtener_copa_por_id(copa_id: int) -> Optional[Copa]:
        return CopaRepository.obtener_por_id(copa_id)

    @staticmethod
    def obtener_copa_activo() -> Optional[Copa]:
        return CopaRepository.obtener_activo()

    @staticmethod
    def crear_copa(nombre: str, campeonato_id: int, orden: int = 0, activo: bool = True, color: Optional[str] = None) -> int:
        return CopaRepository.crear(nombre, campeonato_id, orden, activo, color)

    @staticmethod
    def actualizar_copa_activo(copa_id: int, activo: bool):
        CopaRepository.actualizar_activo(copa_id, activo)

    @staticmethod
    def actualizar_orden_copa(copa_id: int, orden: int):
        CopaRepository.actualizar_orden(copa_id, orden)

    @staticmethod
    def eliminar_copa(copa_id: int):
        # Validar que no tenga torneos asociados
        from backend.database.repositories import TorneoRepository
        torneos = TorneoRepository.obtener_por_copa(copa_id)
        if torneos:
            raise ValueError("No se puede eliminar la copa porque tiene torneos asociados")
        
        CopaRepository.eliminar(copa_id)
