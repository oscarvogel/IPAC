"""Pruebas de la generación de cuotas por lote (varios períodos a la vez).

Las de dominio y aplicación están en sus propios módulos, sin Django. Acá se
prueba el adaptador ORM y el contrato HTTP, que es donde aparecen los problemas
reales: bloqueos, duplicados y conteos.
"""

from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from core.contexts.cobranzas.application.generar_cuotas import (
    GenerarCuotas,
)
from core.contexts.cobranzas.infrastructure.django_alumno_elegible_cuota_reader import (
    DjangoAlumnoElegibleCuotaReader,
)
from core.contexts.cobranzas.infrastructure.django_cuota_generator import (
    DjangoCuotaGenerator,
)
from core.models import (
    Alumno,
    CarreraCurso,
    ConceptoCobrable,
    Cuota,
    PerfilUsuario,
    Sucursal,
)
from core.models import User


class FixturesLoteMixin:
    def _user(self, username, rol, sucursal, todas=False):
        user = User.objects.create_user(username, password="test-password")
        PerfilUsuario.objects.create(
            user=user,
            rol=rol,
            sucursal=sucursal,
            puede_ver_todas_las_sucursales=todas,
        )
        return user

    def _alumno(self, legajo, nombre, apellido, carrera=None, sucursal=None):
        return Alumno.objects.create(
            legajo=legajo,
            nombre=nombre,
            apellido=apellido,
            sucursal=sucursal or self.posadas,
            carrera=carrera,
        )


class GenerarLoteAdaptadorTests(FixturesLoteMixin, TestCase):
    def setUp(self):
        self.posadas = Sucursal.objects.create(codigo="POS", nombre="Posadas")
        self.admin = self._user(
            "admin-lote", PerfilUsuario.Rol.ADMINISTRACION, self.posadas, todas=True
        )
        self.carrera = CarreraCurso.objects.create(
            nombre="Tecnicatura en Sistemas",
            sucursal=self.posadas,
            cuota_programatica=Decimal("62000.00"),
            cuota_extraprogramatica=Decimal("20000.00"),
            cuota_total=Decimal("82000.00"),
        )
        self.concepto = ConceptoCobrable.objects.create(
            nombre="Cuota mensual",
            tipo=ConceptoCobrable.Tipo.CUOTA,
            importe=Decimal("82000.00"),
            sucursal=self.posadas,
            carrera=self.carrera,
        )
        self.ana = self._alumno("L-0001", "Ana", "Gomez", self.carrera)
        self.bruno = self._alumno("L-0002", "Bruno", "Diaz", self.carrera)

    def _generar(self, alumnos, **extra):
        payload = {
            "alumnos": [a.pk for a in alumnos],
            "concepto": self.concepto.pk,
            "fecha_emision": "2026-03-01",
            "descuento": "0",
            "recargo": "0",
        }
        payload.update(extra)
        return GenerarCuotas(DjangoCuotaGenerator()).execute(
            actor=self.admin, payload=payload
        )

    # ------------------------------------------------------------------ lote

    def test_genera_una_cuota_por_alumno_y_por_periodo(self):
        resultado = self._generar(
            [self.ana, self.bruno],
            cantidad=3,
            mes_inicial=3,
            anio_inicial=2026,
            dia_vencimiento=10,
        )

        self.assertEqual(resultado.total_creadas, 6)
        self.assertEqual(resultado.total_omitidas, 0)
        # order_by() sin argumentos limpia el ordering del Meta: con
        # DISTINCT, PostgreSQL rechaza que se ordene por columnas que no
        # estan en la lista de seleccion.
        periodos = Cuota.objects.order_by().values_list("periodo", flat=True).distinct()
        self.assertEqual(sorted(periodos), ["2026-03", "2026-04", "2026-05"])

    def test_cada_periodo_vence_el_dia_indicado_de_su_mes(self):
        self._generar(
            [self.ana], cantidad=3, mes_inicial=3, anio_inicial=2026, dia_vencimiento=10
        )

        vencimientos = {
            c.periodo: c.fecha_vencimiento.isoformat()
            for c in Cuota.objects.filter(alumno=self.ana)
        }
        self.assertEqual(
            vencimientos,
            {
                "2026-03": "2026-03-10",
                "2026-04": "2026-04-10",
                "2026-05": "2026-05-10",
            },
        )

    def test_el_lote_atraviesa_el_cambio_de_anio(self):
        self._generar(
            [self.ana], cantidad=3, mes_inicial=11, anio_inicial=2026, dia_vencimiento=10
        )

        self.assertEqual(
            sorted(Cuota.objects.filter(alumno=self.ana).values_list("periodo", flat=True)),
            ["2026-11", "2026-12", "2027-01"],
        )

    def test_el_desglose_se_congela_en_todas_las_cuotas_del_lote(self):
        self._generar(
            [self.ana], cantidad=3, mes_inicial=3, anio_inicial=2026, dia_vencimiento=10
        )

        for cuota in Cuota.objects.filter(alumno=self.ana):
            self.assertEqual(cuota.importe_programatico, Decimal("62000.00"))
            self.assertEqual(cuota.importe_extraprogramatica, Decimal("20000.00"))

    def test_cambiar_el_catalogo_no_altera_un_lote_ya_generado(self):
        self._generar(
            [self.ana], cantidad=1, mes_inicial=3, anio_inicial=2026, dia_vencimiento=10
        )
        self.carrera.cuota_programatica = Decimal("40000.00")
        self.carrera.cuota_extraprogramatica = Decimal("40000.00")
        self.carrera.save()

        cuota = Cuota.objects.get(alumno=self.ana)
        self.assertEqual(cuota.importe_programatico, Decimal("62000.00"))

    # ------------------------------------------------------------- existentes

    def test_genera_solo_las_cuotas_que_faltan_y_reporta_las_omitidas(self):
        self._generar(
            [self.ana, self.bruno],
            cantidad=3,
            mes_inicial=3,
            anio_inicial=2026,
            dia_vencimiento=10,
        )
        Cuota.objects.filter(alumno=self.ana, periodo="2026-03").delete()

        resultado = self._generar(
            [self.ana, self.bruno],
            cantidad=3,
            mes_inicial=3,
            anio_inicial=2026,
            dia_vencimiento=10,
        )

        # A Ana se le borró 2026-03, así que solo le falta esa: se genera 1.
        # Bruno ya tenía las 3, así que no se le genera ninguna.
        self.assertEqual(resultado.total_creadas, 1)
        self.assertEqual(resultado.total_omitidas, 5)
        omitidas_de_ana = [o for o in resultado.omitidas if o["alumno_id"] == self.ana.pk]
        self.assertEqual(
            sorted(o["periodo"] for o in omitidas_de_ana), ["2026-04", "2026-05"]
        )

    def test_repetir_el_mismo_lote_no_crea_duplicados_ni_falla(self):
        for _ in range(2):
            resultado = self._generar(
                [self.ana],
                cantidad=3,
                mes_inicial=3,
                anio_inicial=2026,
                dia_vencimiento=10,
            )

        self.assertEqual(resultado.total_creadas, 0)
        self.assertEqual(resultado.total_omitidas, 3)
        self.assertEqual(Cuota.objects.filter(alumno=self.ana).count(), 3)

    def test_omitir_una_cuota_ya_creada_no_rompe_el_resto_del_lote(self):
        self._generar(
            [self.ana], cantidad=1, mes_inicial=3, anio_inicial=2026, dia_vencimiento=10
        )

        resultado = self._generar(
            [self.ana], cantidad=3, mes_inicial=3, anio_inicial=2026, dia_vencimiento=10
        )

        self.assertEqual(resultado.total_creadas, 2)
        self.assertEqual(
            sorted(Cuota.objects.filter(alumno=self.ana).values_list("periodo", flat=True)),
            ["2026-03", "2026-04", "2026-05"],
        )

    # -------------------------------------------------------- compatibilidad

    def test_el_periodo_unico_sigue_generando_una_sola_cuota(self):
        resultado = self._generar(
            [self.ana],
            periodo="2026-10",
            fecha_vencimiento="2026-10-15",
        )

        self.assertEqual(resultado.total_creadas, 1)
        cuota = Cuota.objects.get(alumno=self.ana)
        self.assertEqual(cuota.periodo, "2026-10")
        self.assertEqual(cuota.fecha_vencimiento.isoformat(), "2026-10-15")

    def test_un_alumno_de_otra_sucursal_rechaza_todo_el_lote(self):
        eldorado = Sucursal.objects.create(codigo="ELD", nombre="Eldorado")
        ajena = self._alumno("L-0003", "Carla", "Mendez", sucursal=eldorado)
        self.admin.perfil.sucursal = self.posadas
        self.admin.perfil.save()

        from core.contexts.cobranzas.application.generar_cuotas import (
            GeneracionCuotasError,
        )

        with self.assertRaises(GeneracionCuotasError):
            self._generar(
                [self.ana, ajena],
                cantidad=3,
                mes_inicial=3,
                anio_inicial=2026,
                dia_vencimiento=10,
            )

        # La operacion es atomica: no queda ninguna cuota a medias.
        self.assertEqual(Cuota.objects.count(), 0)


class LectorElegiblesAdaptadorTests(FixturesLoteMixin, TestCase):
    def setUp(self):
        self.posadas = Sucursal.objects.create(codigo="POS", nombre="Posadas")
        self.admin = self._user(
            "admin-lector", PerfilUsuario.Rol.ADMINISTRACION, self.posadas, todas=True
        )
        self.carrera = CarreraCurso.objects.create(
            nombre="Enfermeria", sucursal=self.posadas
        )
        self.concepto = ConceptoCobrable.objects.create(
            nombre="Cuota mensual",
            tipo=ConceptoCobrable.Tipo.CUOTA,
            importe=Decimal("10000.00"),
            sucursal=self.posadas,
            carrera=self.carrera,
        )
        self.ana = self._alumno("L-0001", "Ana", "Gomez", self.carrera)

    def test_informa_los_periodos_que_el_alumno_ya_tiene(self):
        GenerarCuotas(DjangoCuotaGenerator()).execute(
            actor=self.admin,
            payload={
                "alumnos": [self.ana.pk],
                "concepto": self.concepto.pk,
                "fecha_emision": "2026-03-01",
                "cantidad": 2,
                "mes_inicial": 3,
                "anio_inicial": 2026,
                "dia_vencimiento": 10,
            },
        )

        candidatos = DjangoAlumnoElegibleCuotaReader().obtener_candidatos(
            actor=self.admin,
            sucursal_id=self.posadas.pk,
            carrera_id=self.carrera.pk,
            concepto_id=self.concepto.pk,
            periodos=["2026-03", "2026-04", "2026-05"],
        )

        self.assertEqual(len(candidatos), 1)
        self.assertEqual(candidatos[0]["periodos_existentes"], ["2026-03", "2026-04"])

    def test_ignora_las_cuotas_de_otro_concepto(self):
        otro = ConceptoCobrable.objects.create(
            nombre="Matricula",
            tipo=ConceptoCobrable.Tipo.MATRICULA,
            importe=Decimal("5000.00"),
            sucursal=self.posadas,
            carrera=self.carrera,
        )
        GenerarCuotas(DjangoCuotaGenerator()).execute(
            actor=self.admin,
            payload={
                "alumnos": [self.ana.pk],
                "concepto": otro.pk,
                "fecha_emision": "2026-03-01",
                "periodo": "2026-03",
                "fecha_vencimiento": "2026-03-10",
            },
        )

        candidatos = DjangoAlumnoElegibleCuotaReader().obtener_candidatos(
            actor=self.admin,
            sucursal_id=self.posadas.pk,
            carrera_id=self.carrera.pk,
            concepto_id=self.concepto.pk,
            periodos=["2026-03"],
        )

        self.assertEqual(candidatos[0]["periodos_existentes"], [])


class GenerarLoteApiTests(FixturesLoteMixin, APITestCase):
    def setUp(self):
        self.posadas = Sucursal.objects.create(codigo="POS", nombre="Posadas")
        self.admin = self._user(
            "admin-api-lote", PerfilUsuario.Rol.ADMINISTRACION, self.posadas, todas=True
        )
        self.carrera = CarreraCurso.objects.create(
            nombre="Tecnicatura en Sistemas",
            sucursal=self.posadas,
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
        self.ana = self._alumno("L-0001", "Ana", "Gomez", self.carrera)
        self.bruno = self._alumno("L-0002", "Bruno", "Diaz", self.carrera)
        self.client.force_authenticate(self.admin)

    def _payload_lote(self, **extra):
        payload = {
            "alumnos": [self.ana.pk, self.bruno.pk],
            "concepto": self.concepto.pk,
            "fecha_emision": "2026-03-01",
            "cantidad": 4,
            "mes_inicial": 3,
            "anio_inicial": 2026,
            "dia_vencimiento": 10,
        }
        payload.update(extra)
        return payload

    def test_evaluar_devuelve_los_periodos_del_lote_y_lo_que_falta(self):
        respuesta = self.client.post(
            "/api/cuotas/evaluar-generacion/",
            {
                "sucursal": self.posadas.pk,
                "carrera": self.carrera.pk,
                "concepto": self.concepto.pk,
                "cantidad": 4,
                "mes_inicial": 3,
                "anio_inicial": 2026,
                "dia_vencimiento": 10,
            },
            format="json",
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["cantidad_periodos"], 4)
        self.assertEqual(respuesta.data["cuotas_a_generar"], 8)
        # El detalle viene ordenado por apellido, no por id.
        self.assertEqual(
            sorted(respuesta.data["alumnos_elegibles"]), sorted([self.ana.pk, self.bruno.pk])
        )
        self.assertEqual(
            respuesta.data["periodos"],
            ["2026-03", "2026-04", "2026-05", "2026-06"],
        )
        self.assertEqual(respuesta.data["detalle_alumnos"][0]["faltantes"], respuesta.data["periodos"])

    def test_generar_devuelve_las_cuotas_y_el_resumen(self):
        respuesta = self.client.post(
            "/api/cuotas/generar/", self._payload_lote(), format="json"
        )

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data["resumen"]["creadas"], 8)
        self.assertEqual(respuesta.data["resumen"]["omitidas"], 0)
        self.assertEqual(len(respuesta.data["cuotas"]), 8)

    def test_correr_el_mismo_lote_de_nuevo_responde_200_con_cero_creadas(self):
        self.client.post("/api/cuotas/generar/", self._payload_lote(), format="json")

        respuesta = self.client.post(
            "/api/cuotas/generar/", self._payload_lote(), format="json"
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["resumen"]["creadas"], 0)
        self.assertEqual(respuesta.data["resumen"]["omitidas"], 8)
        self.assertEqual(Cuota.objects.count(), 8)

    def test_un_lote_imposible_responde_400(self):
        respuesta = self.client.post(
            "/api/cuotas/generar/",
            self._payload_lote(cantidad=0),
            format="json",
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cantidad", respuesta.data["detail"].lower())

    def test_evaluar_un_lote_imposible_responde_400(self):
        respuesta = self.client.post(
            "/api/cuotas/evaluar-generacion/",
            {
                "sucursal": self.posadas.pk,
                "concepto": self.concepto.pk,
                "cantidad": 4,
                "mes_inicial": 2,
                "anio_inicial": 2026,
                "dia_vencimiento": 31,
            },
            format="json",
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_evaluar_sigue_aceptando_el_periodo_unico(self):
        respuesta = self.client.post(
            "/api/cuotas/evaluar-generacion/",
            {
                "sucursal": self.posadas.pk,
                "concepto": self.concepto.pk,
                "periodo": "2026-10",
                "fecha_vencimiento": "2026-10-10",
            },
            format="json",
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["periodos"], ["2026-10"])
        self.assertEqual(respuesta.data["cuotas_a_generar"], 2)
