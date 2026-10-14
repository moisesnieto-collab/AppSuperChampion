from typing import List, Optional
from backend.models.campeonato import Campeonato
from backend.database.repositories import CampeonatoRepository, CampeonatoPermisoRepository


class CampeonatoService:
    @staticmethod
    def obtener_campeonatos() -> List[Campeonato]:
        return CampeonatoRepository.obtener_todos()

    @staticmethod
    def obtener_campeonatos_por_anio(anio_id: int) -> List[Campeonato]:
        return CampeonatoRepository.obtener_por_anio(anio_id)

    @staticmethod
    def obtener_campeonato_por_id(campeonato_id: int) -> Optional[Campeonato]:
        return CampeonatoRepository.obtener_por_id(campeonato_id)

    @staticmethod
    def obtener_campeonato_activo() -> Optional[Campeonato]:
        return CampeonatoRepository.obtener_activo()

    @staticmethod
    def crear_campeonato(nombre: str, anio_id: int, orden: int = 0, activo: bool = True, es_master: bool = False) -> int:
        if not es_master:
            raise PermissionError("Solo el master puede crear campeonatos")
        return CampeonatoRepository.crear(nombre, anio_id, orden, activo)

    @staticmethod
    def actualizar_campeonato_activo(campeonato_id: int, activo: bool):
        CampeonatoRepository.actualizar_activo(campeonato_id, activo)

    @staticmethod
    def actualizar_orden_campeonato(campeonato_id: int, orden: int):
        CampeonatoRepository.actualizar_orden(campeonato_id, orden)

    @staticmethod
    def eliminar_campeonato(campeonato_id: int, es_master: bool = False):
        if not es_master:
            raise PermissionError("Solo el master puede eliminar campeonatos")
        # Validar que no tenga copas asociadas
        from backend.database.repositories import CopaRepository
        copas = CopaRepository.obtener_por_campeonato(campeonato_id)
        if copas:
            raise ValueError("No se puede eliminar el campeonato porque tiene copas asociadas")
        
        CampeonatoRepository.eliminar(campeonato_id)

    @staticmethod
    def asignar_permiso(campeonato_id: int, usuario_id: int, rol: str) -> int:
        # Validar rol
        if rol not in ["organizador", "master"]:
            raise ValueError("Rol debe ser 'organizador' o 'master'")
        
        return CampeonatoPermisoRepository.asignar_permiso(campeonato_id, usuario_id, rol)

    @staticmethod
    def revocar_permiso(campeonato_id: int, usuario_id: int):
        CampeonatoPermisoRepository.revocar_permiso(campeonato_id, usuario_id)

    @staticmethod
    def verificar_permiso_usuario(campeonato_id: int, usuario_id: int) -> Optional[str]:
        return CampeonatoPermisoRepository.verificar_permiso(campeonato_id, usuario_id)

    @staticmethod
    def obtener_permisos_campeonato(campeonato_id: int):
        return CampeonatoPermisoRepository.obtener_por_campeonato(campeonato_id)

    @staticmethod
    def obtener_permisos_usuario(usuario_id: int):
        return CampeonatoPermisoRepository.obtener_por_usuario(usuario_id)
