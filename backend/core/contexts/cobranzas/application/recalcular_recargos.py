from dataclasses import dataclass
from datetime import date
from typing import Protocol


class RecargoRepository(Protocol):
    def recalcular(self, *, sucursal_ids=None, fecha_evaluacion: date): ...


@dataclass
class RecalcularRecargos:
    repository: RecargoRepository

    def execute(self, *, sucursal_ids=None, fecha_evaluacion=None):
        return self.repository.recalcular(
            sucursal_ids=sucursal_ids,
            fecha_evaluacion=fecha_evaluacion or date.today(),
        )
