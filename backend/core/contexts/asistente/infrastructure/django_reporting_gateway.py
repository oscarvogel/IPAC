from datetime import date
from decimal import Decimal, InvalidOperation

from django.db.models import (
    Count,
    DecimalField,
    ExpressionWrapper,
    F,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce
from django.utils import timezone

from core.models import (
    Alumno,
    AplicacionPago,
    CajaDiaria,
    Cuota,
    Pago,
    Sucursal,
)

from ..domain.models import ToolContext, ToolResult


class ToolForbidden(Exception):
    pass


class ToolNoData(Exception):
    pass


MONEY_FIELD = DecimalField(max_digits=14, decimal_places=2)


class DjangoReportingGateway:
    def _result(self, *, status, data, scope_label, as_of=None):
        return ToolResult(
            status=status,
            data=data,
            scope_label=scope_label,
            as_of=str(as_of or timezone.localdate()),
        )

    def _branch_name(self, branch_id):
        return (
            Sucursal.objects.filter(pk=branch_id)
            .values_list("nombre", flat=True)
            .first()
            or f"Sucursal {branch_id}"
        )

    def _scope_branch_ids(
        self,
        context: ToolContext,
        requested_id=None,
        requested_name=None,
    ):
        requested_name = str(requested_name or "").strip()

        if not context.global_access:
            branch = Sucursal.objects.filter(pk=context.sucursal_id).first()
            if not branch:
                raise ToolNoData()
            if requested_id not in (None, "") and int(requested_id) != context.sucursal_id:
                raise ToolForbidden()
            if requested_name and requested_name.casefold() not in {
                branch.nombre.casefold(),
                branch.codigo.casefold(),
            }:
                raise ToolForbidden()
            return [branch.id], branch.nombre

        if requested_id not in (None, ""):
            branch = Sucursal.objects.filter(pk=requested_id).first()
            if not branch:
                raise ToolNoData()
            return [branch.id], branch.nombre

        if requested_name:
            branch = Sucursal.objects.filter(
                Q(nombre__iexact=requested_name) | Q(codigo__iexact=requested_name)
            ).first()
            if not branch:
                raise ToolNoData()
            return [branch.id], branch.nombre

        ids = list(
            Sucursal.objects.order_by("id").values_list("id", flat=True)
        )
        if not ids:
            raise ToolNoData()
        return ids, "Todas las sucursales"

    def _with_scope(
        self,
        context,
        callback,
        *,
        requested_id=None,
        requested_name=None,
    ):
        try:
            ids, label = self._scope_branch_ids(
                context,
                requested_id=requested_id,
                requested_name=requested_name,
            )
        except ToolForbidden:
            return self._result(status="forbidden", data={}, scope_label="Sin acceso")
        except ToolNoData:
            return self._result(status="no_data", data={}, scope_label="Sin datos")
        return callback(ids, label)

    def _fees_with_balance(self, branch_ids):
        paid = (
            AplicacionPago.objects.filter(cuota_id=OuterRef("pk"), activa=True)
            .values("cuota_id")
            .annotate(total=Sum("importe"))
            .values("total")[:1]
        )
        return (
            Cuota.objects.filter(sucursal_id__in=branch_ids)
            .exclude(estado=Cuota.Estado.ANULADA)
            .annotate(
                saldo_calculado=ExpressionWrapper(
                    F("importe")
                    - F("descuento")
                    + F("recargo")
                    - Coalesce(
                        Subquery(
                            paid,
                            output_field=DecimalField(
                                max_digits=12,
                                decimal_places=2,
                            ),
                        ),
                        Value(Decimal("0")),
                        output_field=MONEY_FIELD,
                    ),
                    output_field=MONEY_FIELD,
                )
            )
        )

    def resumen_deuda(self, *, context, sucursal_id=None, sucursal=None):
        def execute(ids, label):
            fees = self._fees_with_balance(ids).filter(saldo_calculado__gt=0)
            today = timezone.localdate()
            total = fees.aggregate(total=Sum("saldo_calculado"))["total"] or Decimal("0")
            overdue = (
                fees.filter(fecha_vencimiento__lt=today)
                .aggregate(total=Sum("saldo_calculado"))["total"]
                or Decimal("0")
            )
            return self._result(
                status="ok",
                scope_label=label,
                data={
                    "deuda_total": total,
                    "deuda_vencida": overdue,
                    "alumnos_con_deuda": fees.values("alumno_id").distinct().count(),
                    "cuotas_pendientes": fees.count(),
                    "cuotas_vencidas": fees.filter(fecha_vencimiento__lt=today).count(),
                },
            )

        return self._with_scope(context, execute, requested_id=sucursal_id, requested_name=sucursal)

    def _student_candidates(self, branch_ids, *, alumno_id=None, search=None):
        qs = Alumno.objects.filter(sucursal_id__in=branch_ids).select_related("sucursal")
        if alumno_id not in (None, ""):
            return list(qs.filter(pk=alumno_id)[:2])

        terms = [term for term in str(search or "").strip().split() if term]
        if not terms:
            return []
        for term in terms:
            qs = qs.filter(
                Q(nombre__icontains=term)
                | Q(apellido__icontains=term)
                | Q(dni__icontains=term)
                | Q(legajo__icontains=term)
            )
        return list(qs.order_by("apellido", "nombre", "id")[:6])

    @staticmethod
    def _candidate(student):
        return {
            "id": student.id,
            "nombre": f"{student.apellido}, {student.nombre}",
            "legajo": student.legajo,
            "sucursal": student.sucursal.nombre,
        }

    def estado_cuenta_alumno(self, *, context, alumno_id=None, search=None):
        def execute(ids, label):
            students = self._student_candidates(
                ids,
                alumno_id=alumno_id,
                search=search,
            )
            if not students:
                return self._result(status="no_data", data={}, scope_label=label)
            if len(students) > 1:
                return self._result(
                    status="ambiguous",
                    scope_label=label,
                    data={"candidates": [self._candidate(student) for student in students]},
                )

            student = students[0]
            fees = self._fees_with_balance([student.sucursal_id]).filter(
                alumno_id=student.id,
                saldo_calculado__gt=0,
            )
            today = timezone.localdate()
            debt = fees.aggregate(total=Sum("saldo_calculado"))["total"] or Decimal("0")
            overdue = (
                fees.filter(fecha_vencimiento__lt=today)
                .aggregate(total=Sum("saldo_calculado"))["total"]
                or Decimal("0")
            )
            payments = Pago.objects.filter(
                alumno=student,
                estado=Pago.Estado.ACTIVO,
            ).prefetch_related("aplicaciones")
            credit = sum((payment.saldo_a_favor for payment in payments), Decimal("0"))
            last_payment = payments.order_by("-fecha", "-id").values_list("fecha", flat=True).first()
            return self._result(
                status="ok",
                scope_label=student.sucursal.nombre,
                data={
                    "alumno": self._candidate(student),
                    "deuda_total": debt,
                    "deuda_vencida": overdue,
                    "cuotas_pendientes": fees.count(),
                    "cuotas_vencidas": fees.filter(fecha_vencimiento__lt=today).count(),
                    "saldo_a_favor": credit,
                    "fecha_ultimo_pago": last_payment.isoformat() if last_payment else None,
                },
            )

        return self._with_scope(context, execute)

    def resumen_cobranzas(
        self,
        *,
        context,
        sucursal_id=None,
        sucursal=None,
        desde=None,
        hasta=None,
        medio=None,
    ):
        def execute(ids, label):
            try:
                start = date.fromisoformat(desde) if desde else timezone.localdate()
                end = date.fromisoformat(hasta) if hasta else start
            except (TypeError, ValueError):
                return self._result(status="invalid", data={}, scope_label=label)
            if start > end:
                return self._result(status="invalid", data={}, scope_label=label)

            payments = Pago.objects.filter(
                sucursal_id__in=ids,
                estado=Pago.Estado.ACTIVO,
                fecha__range=(start, end),
            )
            if medio:
                payments = payments.filter(medio=medio)
            if not payments.exists():
                return self._result(
                    status="no_data",
                    data={},
                    scope_label=label,
                    as_of=end,
                )
            totals = {
                key: payments.filter(medio=key).aggregate(total=Sum("importe"))["total"]
                or Decimal("0")
                for key, _ in Pago.Medio.choices
            }
            return self._result(
                status="ok",
                scope_label=label,
                as_of=end,
                data={
                    "desde": start.isoformat(),
                    "hasta": end.isoformat(),
                    "total_cobrado": payments.aggregate(total=Sum("importe"))["total"]
                    or Decimal("0"),
                    "cantidad_pagos": payments.count(),
                    "por_medio": totals,
                },
            )

        return self._with_scope(context, execute, requested_id=sucursal_id, requested_name=sucursal)

    def caja_hoy(self, *, context, sucursal_id=None, sucursal=None):
        def execute(ids, label):
            requested_branch = ids[0] if len(ids) == 1 else context.sucursal_id
            if requested_branch not in ids:
                return self._result(status="forbidden", data={}, scope_label="Sin acceso")
            caja = (
                CajaDiaria.objects.filter(
                    fecha=timezone.localdate(),
                    sucursal_id=requested_branch,
                    usuario_id=context.user_id,
                )
                .prefetch_related("movimientos")
                .first()
            )
            if not caja:
                return self._result(status="no_data", data={}, scope_label=self._branch_name(requested_branch))
            resumen = caja.resumen
            return self._result(
                status="ok",
                scope_label=self._branch_name(requested_branch),
                data={
                    "estado": caja.estado,
                    "saldo_inicial": caja.saldo_inicial,
                    "efectivo_esperado": resumen.efectivo_esperado,
                    "total_contado": caja.total_contado,
                    "diferencia": caja.diferencia,
                    "importe_retirado": caja.importe_retirado,
                    "saldo_arrastrable": caja.saldo_arrastrable,
                },
            )

        return self._with_scope(context, execute, requested_id=sucursal_id, requested_name=sucursal)

    def resumen_cuotas(
        self,
        *,
        context,
        sucursal_id=None,
        sucursal=None,
        periodo=None,
        estado=None,
    ):
        def execute(ids, label):
            fees = self._fees_with_balance(ids)
            if periodo:
                fees = fees.filter(periodo=periodo)
            if estado:
                fees = fees.filter(estado=estado)
            if not fees.exists():
                return self._result(status="no_data", data={}, scope_label=label)
            positive = fees.filter(saldo_calculado__gt=0)
            return self._result(
                status="ok",
                scope_label=label,
                data={
                    "cantidad": fees.count(),
                    "con_saldo": positive.count(),
                    "saldo_pendiente": positive.aggregate(total=Sum("saldo_calculado"))["total"]
                    or Decimal("0"),
                },
            )

        return self._with_scope(context, execute, requested_id=sucursal_id, requested_name=sucursal)

    def resumen_alumnos(
        self,
        *,
        context,
        sucursal_id=None,
        sucursal=None,
        estado=None,
        carrera_id=None,
    ):
        def execute(ids, label):
            students = Alumno.objects.filter(sucursal_id__in=ids)
            if estado:
                students = students.filter(estado=estado)
            if carrera_id:
                students = students.filter(carrera_id=carrera_id)
            if not students.exists():
                return self._result(status="no_data", data={}, scope_label=label)
            return self._result(
                status="ok",
                scope_label=label,
                data={
                    "cantidad": students.count(),
                    "por_estado": {
                        key: students.filter(estado=key).count()
                        for key, _ in Alumno.Estado.choices
                    },
                },
            )

        return self._with_scope(context, execute, requested_id=sucursal_id, requested_name=sucursal)

    def buscar_alumno(self, *, context, search):
        def execute(ids, label):
            students = self._student_candidates(ids, search=search)
            if not students:
                return self._result(status="no_data", data={}, scope_label=label)
            return self._result(
                status="ok" if len(students) == 1 else "ambiguous",
                scope_label=label,
                data={"candidates": [self._candidate(student) for student in students]},
            )

        return self._with_scope(context, execute)
