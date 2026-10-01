"""Pruebas de la reinscripción: generar el año de cuotas desde la matrícula.

Las de dominio y aplicación están en sus módulos, sin Django. Acá se prueba el
adaptador ORM y el contrato HTTP, que es donde aparecen los problemas reales:
enlazado de la cuota, estado de la matrícula y permisos.
"""

from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from core.contexts.cobranzas.application.generar_cuotas import GeneracionCuotasError
from core.contexts.cobranzas.application.reinscripcion_cuotas import (
    GenerarCuotasDeMatricula,
    MatriculaReinscribible,
)
from core.contexts.cobranzas.infrastructure.django_cuota_generator import (
    DjangoCuotaGenerator,
)
from core.models import (
    Alumno,
    CarreraCurso,
    ConceptoCobrable,
    Cuota,
    Matricula,
    PerfilUsuario,
    Sucursal,
    User,
)


class FixturesReinscripcionMixin:
    def _user(self, username, rol, sucursal, todas=False):
        user = User.objects.create_user(username, password="test-password")
        PerfilUsuario.objects.create(
            user=user,
            rol=rol,
            sucursal=sucursal,
            puede_ver_todas_las_sucursales=todas,
        )
        return user

    def _alumno(self, legajo, nombre, apellido):
        return Alumno.objects.create(
            legajo=legajo,
            nombre=nombre,
            apellido=apellido,
            sucursal=self.posadas,
            carrera=self.carrera,
        )


class ReinscripcionAdaptadorTests(FixturesReinscripcionMixin, TestCase):
    def setUp(self):
        self.posadas = Sucursal.objects.create(codigo="POS", nombre="Posadas")
        self.admin = self._user(
            "admin-reinscripcion", PerfilUsuario.Rol.ADMINISTRACION, self.posadas, todas=True
        )
        self.carrera = CarreraCurso.objects.create(
            nombre="Tecnicatura en Sistemas",
            sucursal=self.posadas,
            plan_cuotas=10,
            cuota_programatica=Decimal("62000.00"),
            cuota_extraprogramatica=Decimal("20000.00"),
        )
        self.concepto = ConceptoCobrable.objects.create(
            nombre="Cuota mensual",
            tipo=ConceptoCobrable.Tipo.CUOTA,
            importe=Decimal("82000.00"),
            sucursal=self.posadas,
            carrera=self.carrera,
        )
        self.ana = self._alumno("L-0001", "Ana", "Gomez")
        self.matricula = Matricula.objects.create(
            alumno=self.ana,
            carrera=self.carrera,
            sucursal=self.posadas,
            fecha_inicio="2026-03-01",
        )

    def _dto(self, plan_cuotas=10):
        return MatriculaReinscribible(
            matricula_id=self.matricula.pk,
            alumno_id=self.ana.pk,
            fecha_inicio=self.matricula.fecha_inicio,
            plan_cuotas=plan_cuotas,
        )

    def _reinscribir(self, **kwargs):
        params = {
            "actor": self.admin,
            "matricula": self._dto(),
            "concepto_id": self.concepto.pk,
            "fecha_emision": "2026-02-20",
        }
        params.update(kwargs)
        return GenerarCuotasDeMatricula(DjangoCuotaGenerator()).execute(**params)

    def test_una_reinscripcion_genera_el_ano_del_plan(self):
        resultado = self._reinscribir()

        self.assertEqual(resultado.total_creadas, 10)
        self.assertEqual(
            sorted(Cuota.objects.values_list("periodo", flat=True).distinct()),
            [f"2026-{mes:02d}" for mes in range(3, 13)],
        )

    def test_las_cuotas_quedan_enlazadas_a_la_matricula(self):
        """Era el hueco del modelo: Cuota.matricula existia y nunca se llenaba."""
        self._reinscribir()

        for cuota in Cuota.objects.all():
            self.assertEqual(cuota.matricula_id, self.matricula.pk)

    def test_cada_cuota_hereda_el_desglose_del_catalogo_de_la_carrera(self):
        self._reinscribir()

        cuota = Cuota.objects.get(alumno=self.ana, periodo="2026-03")
        self.assertEqual(cuota.importe_programatico, Decimal("62000.00"))
        self.assertEqual(cuota.importe_extraprogramatica, Decimal("20000.00"))

    def test_reinscribir_de_nuevo_salta_lo_que_ya_existe(self):
        self._reinscribir()
        resultado = self._reinscribir()

        self.assertEqual(resultado.total_creadas, 0)
        self.assertEqual(resultado.total_omitidas, 10)
        self.assertEqual(Cuota.objects.count(), 10)

    def test_rechaza_una_matricula_de_otro_alumno(self):
        bruno = self._alumno("L-0002", "Bruno", "Diaz")
        ajena = Matricula.objects.create(
            alumno=bruno,
            carrera=self.carrera,
            sucursal=self.posadas,
            fecha_inicio="2026-03-01",
        )

        from core.contexts.cobranzas.application.generar_cuotas import (
            GeneracionCuotasError,
        )

        with self.assertRaises(GeneracionCuotasError):
            self._reinscribir(
                matricula=MatriculaReinscribible(
                    matricula_id=ajena.pk,
                    alumno_id=self.ana.pk,
                    fecha_inicio=ajena.fecha_inicio,
                    plan_cuotas=10,
                )
            )
        self.assertEqual(Cuota.objects.count(), 0)

    def test_rechaza_una_matricula_que_no_esta_activa(self):
        from core.contexts.cobranzas.application.generar_cuotas import (
            GeneracionCuotasError,
        )

        self.matricula.estado = Matricula.Estado.ANULADA
        self.matricula.save()

        with self.assertRaises(GeneracionCuotasError) as caso:
            self._reinscribir()

        self.assertIn("activa", str(caso.exception).lower())
        self.assertEqual(Cuota.objects.count(), 0)

    def test_la_cantidad_explicita_manda_sobre_el_plan(self):
        self._reinscribir(cantidad=4)

        self.assertEqual(Cuota.objects.count(), 4)
        self.assertTrue(
            Cuota.objects.filter(periodo__in=["2026-03", "2026-04", "2026-05", "2026-06"]).count() == 4
        )


class ReinscripcionApiTests(FixturesReinscripcionMixin, APITestCase):
    def setUp(self):
        self.posadas = Sucursal.objects.create(codigo="POS", nombre="Posadas")
        self.eldorado = Sucursal.objects.create(codigo="ELD", nombre="Eldorado")
        self.admin = self._user(
            "admin-api-reinscripcion",
            PerfilUsuario.Rol.ADMINISTRACION,
            self.posadas,
            todas=True,
        )
        self.tesorero = self._user(
            "tesorero-reinscripcion", PerfilUsuario.Rol.TESORERIA, self.posadas
        )
        self.cajero = self._user(
            "cajero-reinscripcion", PerfilUsuario.Rol.CAJA, self.posadas
        )
        self.carrera = CarreraCurso.objects.create(
            nombre="Tecnicatura en Sistemas",
            sucursal=self.posadas,
            plan_cuotas=10,
            cuota_programatica=Decimal("62000.00"),
            cuota_extraprogramatica=Decimal("20000.00"),
        )
        self.concepto = ConceptoCobrable.objects.create(
            nombre="Cuota mensual",
            tipo=ConceptoCobrable.Tipo.CUOTA,
            importe=Decimal("82000.00"),
            sucursal=self.posadas,
            carrera=self.carrera,
        )
        self.ana = self._alumno("L-0001", "Ana", "Gomez")
        self.matricula = Matricula.objects.create(
            alumno=self.ana,
            carrera=self.carrera,
            sucursal=self.posadas,
            fecha_inicio="2026-03-01",
        )
        self.client.force_authenticate(self.admin)

    def test_plan_cuotas_devuelve_los_periodos_sugeridos(self):
        respuesta = self.client.get(f"/api/matriculas/{self.matricula.pk}/plan-cuotas/")

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["plan_cuotas"], 10)
        self.assertEqual(respuesta.data["periodos"][0], "2026-03")
        self.assertEqual(len(respuesta.data["periodos"]), 10)
        self.assertEqual(respuesta.data["motivo_sin_plan"], "")
        self.assertEqual(
            [c["id"] for c in respuesta.data["conceptos"]], [self.concepto.pk]
        )

    def test_plan_cuotas_explica_cuando_la_carrera_no_tiene_plan(self):
        self.carrera.plan_cuotas = None
        self.carrera.save()

        respuesta = self.client.get(f"/api/matriculas/{self.matricula.pk}/plan-cuotas/")

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["periodos"], [])
        self.assertIn("plan", respuesta.data["motivo_sin_plan"].lower())

    def test_generar_cuotas_crea_el_ano_y_lo_enlaza(self):
        respuesta = self.client.post(
            f"/api/matriculas/{self.matricula.pk}/generar-cuotas/",
            {"concepto": self.concepto.pk, "fecha_emision": "2026-02-20"},
            format="json",
        )

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED, respuesta.data)
        self.assertEqual(respuesta.data["resumen"]["creadas"], 10)
        self.assertEqual(Cuota.objects.filter(matricula=self.matricula).count(), 10)
        self.assertEqual(
            respuesta.data["cuotas"][0]["matricula_estado"], Matricula.Estado.ACTIVA
        )

    def test_generar_cuotas_sin_concepto_responde_400(self):
        respuesta = self.client.post(
            f"/api/matriculas/{self.matricula.pk}/generar-cuotas/",
            {"fecha_emision": "2026-02-20"},
            format="json",
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Cuota.objects.count(), 0)

    def test_reinscribir_de_nuevo_responde_200_con_cero_creadas(self):
        self.client.post(
            f"/api/matriculas/{self.matricula.pk}/generar-cuotas/",
            {"concepto": self.concepto.pk},
            format="json",
        )
        respuesta = self.client.post(
            f"/api/matriculas/{self.matricula.pk}/generar-cuotas/",
            {"concepto": self.concepto.pk},
            format="json",
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["resumen"]["creadas"], 0)
        self.assertEqual(respuesta.data["resumen"]["omitidas"], 10)

    def test_tesoreria_puede_reinscribir(self):
        self.client.force_authenticate(self.tesorero)

        respuesta = self.client.post(
            f"/api/matriculas/{self.matricula.pk}/generar-cuotas/",
            {"concepto": self.concepto.pk},
            format="json",
        )

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED, respuesta.data)

    def test_caja_no_puede_reinscribir_porque_emitir_cuotas_no_es_su_permiso(self):
        """La accion vive en matriculas pero el permiso es el de cobranzas."""
        self.client.force_authenticate(self.cajero)

        respuesta = self.client.post(
            f"/api/matriculas/{self.matricula.pk}/generar-cuotas/",
            {"concepto": self.concepto.pk},
            format="json",
        )

        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Cuota.objects.count(), 0)

    def test_una_cuota_de_matricula_anulada_conserva_el_marcar(self):
        """Anular la matricula no borra lo ya cobrado: lo marca."""
        self.client.post(
            f"/api/matriculas/{self.matricula.pk}/generar-cuotas/",
            {"concepto": self.concepto.pk},
            format="json",
        )
        self.client.post(
            f"/api/matriculas/{self.matricula.pk}/anular/",
            {"motivo": "Se mudo de institucion"},
            format="json",
        )

        cuota = Cuota.objects.filter(matricula=self.matricula).first()
        self.assertIsNotNone(cuota)
        self.assertEqual(cuota.estado, Cuota.Estado.PENDIENTE)

        self.client.force_authenticate(self.admin)
        detalle = self.client.get(f"/api/cuotas/?alumno={self.ana.pk}")
        self.assertEqual(
            detalle.data["results"][0]["matricula_estado"], Matricula.Estado.ANULADA
        )

    def test_la_previsualizacion_puede_filtrar_por_alumno(self):
        bruno = self._alumno("L-0002", "Bruno", "Diaz")

        respuesta = self.client.post(
            "/api/cuotas/evaluar-generacion/",
            {
                "sucursal": self.posadas.pk,
                "carrera": self.carrera.pk,
                "concepto": self.concepto.pk,
                "alumno": self.ana.pk,
                "cantidad": 3,
                "mes_inicial": 3,
                "anio_inicial": 2026,
                "dia_vencimiento": 10,
            },
            format="json",
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["alumnos_encontrados"], 1)
        self.assertEqual(respuesta.data["alumnos_elegibles"], [self.ana.pk])
        self.assertNotIn(bruno.pk, respuesta.data["alumnos_elegibles"])
