from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from core.models import (
    Alumno,
    AplicacionPago,
    ConceptoCobrable,
    Cuota,
    Pago,
    PerfilUsuario,
    Sucursal,
)


class AssistantReadToolsTests(TestCase):
    def setUp(self):
        self.posadas = Sucursal.objects.create(codigo="POS-T", nombre="Posadas Tools")
        self.eldorado = Sucursal.objects.create(codigo="ELD-T", nombre="Eldorado Tools")

        self.restricted = User.objects.create_user(username="tool-pos", password="secret")
        PerfilUsuario.objects.create(
            user=self.restricted,
            rol=PerfilUsuario.Rol.ADMINISTRACION,
            sucursal=self.posadas,
            puede_ver_todas_las_sucursales=False,
        )
        self.global_user = User.objects.create_user(username="tool-global", password="secret")
        PerfilUsuario.objects.create(
            user=self.global_user,
            rol=PerfilUsuario.Rol.SUPERADMIN,
            sucursal=self.posadas,
            puede_ver_todas_las_sucursales=True,
        )

        self.concept_pos = ConceptoCobrable.objects.create(
            nombre="Cuota Tools POS",
            tipo=ConceptoCobrable.Tipo.CUOTA,
            importe=Decimal("1000"),
            sucursal=self.posadas,
        )
        self.concept_eld = ConceptoCobrable.objects.create(
            nombre="Cuota Tools ELD",
            tipo=ConceptoCobrable.Tipo.CUOTA,
            importe=Decimal("500"),
            sucursal=self.eldorado,
        )
        self.student_pos = Alumno.objects.create(
            legajo="T-POS-1",
            nombre="Juan",
            apellido="Perez",
            sucursal=self.posadas,
        )
        self.student_eld = Alumno.objects.create(
            legajo="T-ELD-1",
            nombre="Juan",
            apellido="Perez",
            sucursal=self.eldorado,
        )
        today = timezone.localdate()
        self.fee_pos = Cuota.objects.create(
            alumno=self.student_pos,
            concepto=self.concept_pos,
            sucursal=self.posadas,
            periodo="2026-09",
            fecha_emision=today,
            fecha_vencimiento=today,
            importe=Decimal("1000"),
            descuento=Decimal("100"),
        )
        self.fee_eld = Cuota.objects.create(
            alumno=self.student_eld,
            concepto=self.concept_eld,
            sucursal=self.eldorado,
            periodo="2026-09",
            fecha_emision=today,
            fecha_vencimiento=today,
            importe=Decimal("500"),
        )
        payment = Pago.objects.create(
            alumno=self.student_pos,
            sucursal=self.posadas,
            importe=Decimal("200"),
            medio=Pago.Medio.EFECTIVO,
        )
        AplicacionPago.objects.create(
            pago=payment,
            cuota=self.fee_pos,
            importe=Decimal("200"),
            activa=True,
        )

    def _registry(self):
        try:
            from core.contexts.asistente.application.tools import ReadToolRegistry
            from core.contexts.asistente.infrastructure.django_reporting_gateway import (
                DjangoReportingGateway,
            )
        except ImportError as exc:
            self.fail(f"Debe existir el registro de herramientas read-only: {exc}")
        return ReadToolRegistry(DjangoReportingGateway())

    def _context(self, user):
        from core.contexts.asistente.domain.models import ToolContext

        profile = user.perfil
        return ToolContext(
            user_id=user.id,
            role=profile.rol,
            sucursal_id=profile.sucursal_id,
            global_access=profile.puede_ver_todas_las_sucursales,
        )

    def test_restricted_user_total_debt_is_only_own_branch(self):
        result = self._registry().execute("resumen_deuda", {}, self._context(self.restricted))
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.scope_label, "Posadas Tools")
        self.assertEqual(result.data["deuda_total"], Decimal("700.00"))

    def test_global_user_total_debt_is_all_accessible_branches(self):
        result = self._registry().execute("resumen_deuda", {}, self._context(self.global_user))
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.scope_label, "Todas las sucursales")
        self.assertEqual(result.data["deuda_total"], Decimal("1200.00"))

    def test_global_user_can_filter_debt_by_branch_name(self):
        result = self._registry().execute(
            "resumen_deuda",
            {"sucursal": "Eldorado Tools"},
            self._context(self.global_user),
        )
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.scope_label, "Eldorado Tools")
        self.assertEqual(result.data["deuda_total"], Decimal("500.00"))

    def test_restricted_user_cannot_request_other_branch_by_name(self):
        result = self._registry().execute(
            "resumen_deuda",
            {"sucursal": "Eldorado Tools"},
            self._context(self.restricted),
        )
        self.assertEqual(result.status, "forbidden")

    def test_requested_forbidden_branch_is_denied(self):
        result = self._registry().execute(
            "resumen_deuda",
            {"sucursal_id": self.eldorado.id},
            self._context(self.restricted),
        )
        self.assertEqual(result.status, "forbidden")
        self.assertEqual(result.data, {})

    def test_list_debtors_returns_real_students_and_balances(self):
        result = self._registry().execute(
            "alumnos_con_deuda",
            {},
            self._context(self.global_user),
        )

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.scope_label, "Todas las sucursales")
        self.assertEqual(result.data["total_alumnos"], 2)
        self.assertEqual(result.data["deuda_total"], Decimal("1200.00"))
        rows = result.data["alumnos"]
        self.assertEqual(
            [
                (row["legajo"], row["deuda_total"])
                for row in rows
            ],
            [
                ("T-POS-1", Decimal("700.00")),
                ("T-ELD-1", Decimal("500.00")),
            ],
        )
        self.assertEqual(
            set(rows[0]),
            {
                "id",
                "nombre",
                "legajo",
                "sucursal",
                "deuda_total",
                "deuda_vencida",
            },
        )

    def test_multiple_students_same_name_returns_ambiguous(self):
        result = self._registry().execute(
            "estado_cuenta_alumno",
            {"search": "Juan Perez"},
            self._context(self.global_user),
        )
        self.assertEqual(result.status, "ambiguous")
        self.assertEqual(len(result.data["candidates"]), 2)
        self.assertEqual(
            set(result.data["candidates"][0]),
            {"id", "nombre", "legajo", "sucursal"},
        )

    def test_no_dataset_is_not_reported_as_zero(self):
        result = self._registry().execute(
            "resumen_cobranzas",
            {"desde": "2099-01-01", "hasta": "2099-01-01"},
            self._context(self.restricted),
        )
        self.assertEqual(result.status, "no_data")

    def test_registry_rejects_arbitrary_tool_or_sql(self):
        from core.contexts.asistente.application.tools import UnknownTool

        with self.assertRaises(UnknownTool):
            self._registry().execute(
                "django_sql",
                {"query": "DELETE FROM core_pago"},
                self._context(self.global_user),
            )
