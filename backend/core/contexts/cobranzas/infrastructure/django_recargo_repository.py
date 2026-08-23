from django.db import transaction
from django.utils import timezone

from ....models import Cuota, ReglaRecargo
from ..domain.ajustes_cuota import calcular_ajuste, corresponde_recargo


class DjangoRecargoRepository:
    @transaction.atomic
    def recalcular(self, *, sucursal_ids=None, fecha_evaluacion):
        cuotas = Cuota.objects.select_for_update().filter(
            estado__in=[Cuota.Estado.PENDIENTE, Cuota.Estado.PARCIAL],
        ).select_related("concepto")
        reglas = ReglaRecargo.objects.filter(activo=True).order_by("-concepto_id", "-vigencia_desde", "id")
        if sucursal_ids:
            cuotas = cuotas.filter(sucursal_id__in=sucursal_ids)
            reglas = reglas.filter(sucursal_id__in=sucursal_ids)
        rules_by_branch = {}
        for rule in reglas:
            if rule.vigencia_desde and rule.vigencia_desde > fecha_evaluacion:
                continue
            rules_by_branch.setdefault(rule.sucursal_id, []).append(rule)

        updated = []
        for cuota in cuotas:
            matching = next((
                rule for rule in rules_by_branch.get(cuota.sucursal_id, [])
                if (rule.concepto_id is None or rule.concepto_id == cuota.concepto_id)
                and corresponde_recargo(
                    fecha_vencimiento=cuota.fecha_vencimiento,
                    dias_tolerancia=rule.dias_tolerancia,
                    fecha_evaluacion=fecha_evaluacion,
                )
            ), None)
            if matching is None and cuota.regla_recargo_id is None:
                continue
            expected = calcular_ajuste(
                modalidad=matching.modalidad,
                valor=matching.valor,
                importe_base=cuota.importe - cuota.descuento,
            ) if matching else 0
            if cuota.recargo != expected or cuota.regla_recargo_id != getattr(matching, "id", None):
                cuota.recargo = expected
                cuota.regla_recargo = matching
                cuota.recargo_calculado_en = timezone.now()
                cuota.actualizado = timezone.now()
                updated.append(cuota)
        if updated:
            Cuota.objects.bulk_update(updated, ["recargo", "regla_recargo", "recargo_calculado_en", "actualizado"])
        return {"evaluadas": cuotas.count(), "actualizadas": len(updated)}
