from dataclasses import dataclass
from typing import Protocol


class AuditoriaRepository(Protocol):
    def guardar(self, **evento): ...


@dataclass
class RegistrarEventoAuditoria:
    repository: AuditoriaRepository

    def execute(
        self,
        *,
        usuario,
        modulo,
        accion,
        entidad,
        entidad_id,
        sucursal=None,
        descripcion="",
        valores_anteriores=None,
        valores_nuevos=None,
        metadata=None,
    ):
        if not modulo or not accion or not entidad or entidad_id is None:
            raise ValueError("El evento de auditoría requiere módulo, acción, entidad e identificador.")
        return self.repository.guardar(
            usuario=usuario,
            sucursal=sucursal,
            modulo=modulo,
            accion=accion,
            entidad=entidad,
            entidad_id=str(entidad_id),
            descripcion=descripcion,
            valores_anteriores=valores_anteriores or {},
            valores_nuevos=valores_nuevos or {},
            metadata=metadata or {},
        )
