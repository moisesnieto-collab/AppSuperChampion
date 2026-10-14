from typing import List, Optional
from backend.models.anio import Anio
from backend.database.repositories import AnioRepository


class AnioService:
    @staticmethod
    def obtener_anios() -> List[Anio]:
        return AnioRepository.obtener_todos()

    @staticmethod
    def obtener_anio_por_id(anio_id: int) -> Optional[Anio]:
        return AnioRepository.obtener_por_id(anio_id)

    @staticmethod
    def obtener_anio_activo() -> Optional[Anio]:
        return AnioRepository.obtener_activo()

    @staticmethod
    def crear_anio(valor: int, orden: int = 0, activo: bool = True, es_master: bool = False) -> int:
        if not es_master:
            raise PermissionError("Solo el master puede crear años")
        # Validar que el año no exista
        anios_existentes = AnioRepository.obtener_todos()
        for anio in anios_existentes:
            if anio.valor == valor:
                raise ValueError(f"El año {valor} ya existe")
        
        return AnioRepository.crear(valor, orden, activo)

    @staticmethod
    def actualizar_anio_activo(anio_id: int, activo: bool):
        AnioRepository.actualizar_activo(anio_id, activo)

    @staticmethod
    def actualizar_orden_anio(anio_id: int, orden: int):
        AnioRepository.actualizar_orden(anio_id, orden)

    @staticmethod
    def eliminar_anio(anio_id: int, es_master: bool = False):
        if not es_master:
            raise PermissionError("Solo el master puede eliminar años")
        # Validar que no tenga campeonatos asociados
        from backend.database.repositories import CampeonatoRepository
        campeonatos = CampeonatoRepository.obtener_por_anio(anio_id)
        if campeonatos:
            raise ValueError("No se puede eliminar el año porque tiene campeonatos asociados")
        
        AnioRepository.eliminar(anio_id)
