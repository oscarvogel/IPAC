"""Cubre el cálculo de interés de mora: adaptador, caso de uso y API.

La regla pura ya está cubierta en
`contexts/cobranzas/domain/test_intereses.py`. Acá se prueba lo que sólo se
rompe con base de datos y con HTTP: el saldo que alimenta el cálculo, el
aislamiento por sucursal y los errores que tienen que contestar 400 y no 500.
"""

from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase

from .contexts.cobranzas.application.consultar_intereses import ConsultarIntereses
from .contexts.cobranzas.infrastructure.django_interes_repository import (
    DjangoCuotaInteresReader,
    DjangoTasaInteresRepository,
)
from .models import (
    Alumno,
    AplicacionPago,
    ConceptoCobrable,
    Cuota,
    Pago,
    PerfilUsuario,
    Sucursal,
    TasaInteres,
)

#: Cuota de marzo vencida el día 10, evaluada el 1 de abril: 31 días desde el
#: día 1 del mes, o sea un mes completo de interés.
PERIODO = "2026-03"
VENCIMIENTO = date(2026, 3, 10)
EVALUACION = date(2026, 4, 1)


class BaseIntereses(APITestCase):
    def setUp(self):
        self.posadas = Sucursal.objects.create(codigo="POS", nombre="Posadas")
        self.eldorado = Sucursal.objects.create(codigo="ELD", nombre="Eldorado")

        self.admin = User.objects.create_user("admin", password="admin123")
        PerfilUsuario.objects.create(
            user=self.admin,
            rol=PerfilUsuario.Rol.ADMINISTRACION,
            sucursal=self.posadas,
        )
        self.cajero_eldorado = User.objects.create_user("cajero", password="caja123")
        PerfilUsuario.objects.create(
            user=self.cajero_eldorado,
            rol=PerfilUsuario.Rol.CAJA,
            sucursal=self.eldorado,
        )

        self.alumno = Alumno.objects.create(
            legajo="POS-900",
            nombre="Lucia",
            apellido="Ramirez",
            sucursal=self.posadas,
        )
        self.concepto = ConceptoCobrable.objects.create(
            nombre="Cuota mensual",
            tipo=ConceptoCobrable.Tipo.CUOTA,
            importe=Decimal("10000.00"),
            sucursal=self.posadas,
        )
        self.cuota = self._cuota("POS-901", "10000.00")

    def _cuota(self, legajo, importe, **extra):
        alumno = Alumno.objects.create(
            legajo=legajo, nombre="Alumno", apellido="Prueba", sucursal=self.posadas
        )
        return Cuota.objects.create(
            alumno=alumno,
            concepto=self.concepto,
            sucursal=self.posadas,
            periodo=PERIODO,
            fecha_emision=date(2026, 3, 1),
            fecha_vencimiento=VENCIMIENTO,
            importe=Decimal(importe),
            **extra,
        )

    def _tasa(self, **extra):
        datos = {
            "sucursal": self.posadas,
            "porcentaje_mensual": Decimal("5.500"),
            "vigencia_desde": date(2026, 1, 1),
        }
        datos.update(extra)
        return TasaInteres.objects.create(**datos)


class SaladoDelAdaptadorTests(BaseIntereses):
    def test_el_saldo_descuenta_lo_ya_pagado(self):
        """Si el interés se calculara sobre el importe original, se cobraría
        interés sobre plata que el alumno ya abonó."""
        cuota = self._cuota("POS-902", "10000.00")
        pago = Pago.objects.create(
            alumno=cuota.alumno,
            sucursal=self.posadas,
            importe=Decimal("4000.00"),
            medio=Pago.Medio.EFECTIVO,
            estado=Pago.Estado.ACTIVO,
        )
        AplicacionPago.objects.create(cuota=cuota, pago=pago, importe=Decimal("4000.00"))

        pendientes = DjangoCuotaInteresReader().cuotas_con_saldo(
            sucursal_ids=[self.posadas.id], fecha_evaluacion=EVALUACION
        )

        saldo = next(c.saldo_pendiente for c in pendientes if c.cuota_id == cuota.id)
        self.assertEqual(saldo, Decimal("6000.00"))

    def test_el_saldo_incluye_el_descuento_y_el_recargo(self):
        cuota = self._cuota(
            "POS-903", "10000.00", descuento=Decimal("2000.00"), recargo=Decimal("500.00")
        )

        pendientes = DjangoCuotaInteresReader().cuotas_con_saldo(
            sucursal_ids=[self.posadas.id], fecha_evaluacion=EVALUACION
        )

        saldo = next(c.saldo_pendiente for c in pendientes if c.cuota_id == cuota.id)
        self.assertEqual(saldo, Decimal("8500.00"))

    def test_una_cuota_pagada_no_entra(self):
        cuota = self._cuota("POS-904", "10000.00")
        pago = Pago.objects.create(
            alumno=cuota.alumno,
            sucursal=self.posadas,
            importe=Decimal("10000.00"),
            medio=Pago.Medio.EFECTIVO,
            estado=Pago.Estado.ACTIVO,
        )
        AplicacionPago.objects.create(cuota=cuota, pago=pago, importe=Decimal("10000.00"))

        pendientes = DjangoCuotaInteresReader().cuotas_con_saldo(
            sucursal_ids=[self.posadas.id], fecha_evaluacion=EVALUACION
        )

        self.assertNotIn(cuota.id, [c.cuota_id for c in pendientes])

    def test_una_lista_de_sucursales_vacia_no_trae_todo(self):
        """`if sucursal_ids:` con `[]` se lee como "sin filtro" y devolvería
        todas las sucursales. Por eso el adaptador compara contra None."""
        pendientes = DjangoCuotaInteresReader().cuotas_con_saldo(
            sucursal_ids=[], fecha_evaluacion=EVALUACION
        )

        self.assertEqual(pendientes, [])


class ProyeccionTests(BaseIntereses):
    def test_calcula_el_interes_de_un_mes(self):
        self._tasa()

        resumen = self._proyectar(EVALUACION)

        cuota = next(d for d in resumen.detalle if d.cuota_id == self.cuota.id)
        self.assertEqual(cuota.dias_interesables, 31)
        self.assertEqual(cuota.importe, Decimal("550.00"))

    def test_el_total_suma_el_interes_de_todas_las_cuotas(self):
        self._tasa()
        self._cuota("POS-905", "10000.00")

        resumen = self._proyectar(EVALUACION)

        self.assertEqual(resumen.cuotas_evaluadas, 2)
        self.assertEqual(resumen.total_interes, Decimal("1100.00"))

    def test_una_cuota_sin_interes_no_cuenta_para_el_total(self):
        self._tasa()
        cuota = self._cuota("POS-906", "10000.00")
        cuota.periodo = "2026-05"
        cuota.save(update_fields=["periodo"])

        resumen = self._proyectar(EVALUACION)

        self.assertEqual(resumen.cuotas_con_interes, 1)
        self.assertEqual(resumen.total_interes, Decimal("550.00"))

    def test_las_cuotas_de_la_sucursal_sin_tasa_quedan_fuera_del_total(self):
        self._tasa()
        # Cuota en la otra sucursal, sin tasa cargada.
        alumno = Alumno.objects.create(
            legajo="ELD-1", nombre="Otro", apellido="Sucursal", sucursal=self.eldorado
        )
        concepto = ConceptoCobrable.objects.create(
            nombre="Cuota Eldorado",
            tipo=ConceptoCobrable.Tipo.CUOTA,
            importe=Decimal("10000.00"),
            sucursal=self.eldorado,
        )
        cuota_eld = Cuota.objects.create(
            alumno=alumno,
            concepto=concepto,
            sucursal=self.eldorado,
            periodo=PERIODO,
            fecha_emision=date(2026, 3, 1),
            fecha_vencimiento=VENCIMIENTO,
            importe=Decimal("10000.00"),
        )

        resumen = self._proyectar(EVALUACION, sucursal_ids=[self.posadas.id, self.eldorado.id])

        self.assertIn(cuota_eld.id, resumen.sin_tasa)
        self.assertEqual(resumen.total_interes, Decimal("550.00"))

    def test_sin_tasa_cargada_falla_con_el_mensaje_que_dice_que_cargue(self):
        from .contexts.cobranzas.application.consultar_intereses import SIN_TASA_CARGA_MSG

        with self.assertRaises(ValueError) as ctx:
            self._proyectar(EVALUACION)

        self.assertEqual(str(ctx.exception), SIN_TASA_CARGA_MSG)

    def test_sin_ninguna_tasa_en_el_alcance_falla(self):
        self._tasa(sucursal=self.eldorado)

        with self.assertRaises(ValueError):
            self._proyectar(EVALUACION)

    def _proyectar(self, fecha, sucursal_ids=None):
        return ConsultarIntereses(
            DjangoTasaInteresRepository(), DjangoCuotaInteresReader()
        ).execute(
            sucursal_ids=[self.posadas.id] if sucursal_ids is None else sucursal_ids,
            fecha_evaluacion=fecha,
        )


class TasaInteresApiTests(BaseIntereses):
    def test_proyectar_devuelve_el_total(self):
        self._tasa()
        self.client.force_authenticate(user=self.admin)

        respuesta = self.client.get("/api/tasas-interes/proyectar/?fecha_evaluacion=" + EVALUACION.isoformat())

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data["total_interes"], "550.00")
        self.assertEqual(respuesta.data["cuotas_evaluadas"], 1)

    def test_una_fecha_invalida_responde_400_y_no_500(self):
        self._tasa()
        self.client.force_authenticate(user=self.admin)

        respuesta = self.client.get("/api/tasas-interes/proyectar/?fecha_evaluacion=2026-13-45")

        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("fecha_evaluacion", respuesta.data)

    def test_sin_tasa_cargada_responde_400(self):
        self.client.force_authenticate(user=self.admin)

        respuesta = self.client.get("/api/tasas-interes/proyectar/", format="json")

        self.assertEqual(respuesta.status_code, 400)

    def test_la_proyeccion_no_escribe_interest_en_las_cuotas(self):
        """Nada de esto se persiste todavía: IPAC no respondió si el interés
        se suma a la cuota o va como concepto separado."""
        self._tasa()
        self.client.force_authenticate(user=self.admin)

        self.client.get("/api/tasas-interes/proyectar/", format="json")

        self.cuota.refresh_from_db()
        self.assertEqual(self.cuota.recargo, Decimal("0.00"))

    def test_un_cajero_no_puede_cargar_una_tasa(self):
        self.client.force_authenticate(user=self.cajero_eldorado)

        respuesta = self.client.post(
            "/api/tasas-interes/",
            {
                "sucursal": self.eldorado.id,
                "porcentaje_mensual": "9.000",
                "vigencia_desde": "2026-01-01",
            },
            format="json",
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_el_cajero_que_proyecta_solo_ve_su_sucursal(self):
        self._tasa()
        concepto = ConceptoCobrable.objects.create(
            nombre="Cuota Eldorado",
            tipo=ConceptoCobrable.Tipo.CUOTA,
            importe=Decimal("10000.00"),
            sucursal=self.eldorado,
        )
        alumno = Alumno.objects.create(
            legajo="ELD-2", nombre="Otro", apellido="Sucursal", sucursal=self.eldorado
        )
        cuota_eld = Cuota.objects.create(
            alumno=alumno,
            concepto=concepto,
            sucursal=self.eldorado,
            periodo=PERIODO,
            fecha_emision=date(2026, 3, 1),
            fecha_vencimiento=VENCIMIENTO,
            importe=Decimal("10000.00"),
        )
        TasaInteres.objects.create(
            sucursal=self.eldorado,
            porcentaje_mensual=Decimal("5.500"),
            vigencia_desde=date(2026, 1, 1),
        )
        self.client.force_authenticate(user=self.cajero_eldorado)

        respuesta = self.client.get("/api/tasas-interes/proyectar/", format="json")

        self.assertEqual(respuesta.status_code, 200)
        ids = [d["cuota_id"] for d in respuesta.data["detalle"]]
        self.assertIn(cuota_eld.id, ids)
        self.assertNotIn(self.cuota.id, ids)

    def test_una_vigencia_invertida_responde_400(self):
        self.client.force_authenticate(user=self.admin)

        respuesta = self.client.post(
            "/api/tasas-interes/",
            {
                "sucursal": self.posadas.id,
                "porcentaje_mensual": "5.500",
                "vigencia_desde": "2026-06-01",
                "vigencia_hasta": "2026-01-01",
            },
            format="json",
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_crea_una_tasa_con_vigencia(self):
        self.client.force_authenticate(user=self.admin)

        respuesta = self.client.post(
            "/api/tasas-interes/",
            {
                "sucursal": self.posadas.id,
                "porcentaje_mensual": "5.200",
                "vigencia_desde": "2026-10-01",
                "descripcion": "Tasa vigente acordada con el contador",
            },
            format="json",
        )

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.data["porcentaje_mensual"], "5.200")
        self.assertEqual(respuesta.data["base_calculo"], "dia_1_del_mes")
        self.assertEqual(respuesta.data["unidad_calculo"], "meses")
        self.assertTrue(
            TasaInteres.objects.filter(
                sucursal=self.posadas, vigencia_desde=date(2026, 10, 1)
            ).exists()
        )


class VariasVigenciasTests(BaseIntereses):
    def test_cada_vigencia_usa_su_propia_tasa(self):
        """5,5% hasta el 31/03 y 9% desde el 01/04. Una cuota de enero ya tiene
        interés acumulado en marzo; una de marzo todavía no tiene nada en
        marzo, y desde el 01/04 se le aplica la tasa nueva."""
        self._tasa(
            porcentaje_mensual=Decimal("5.500"),
            vigencia_desde=date(2026, 1, 1),
            vigencia_hasta=date(2026, 3, 31),
        )
        TasaInteres.objects.create(
            sucursal=self.posadas,
            porcentaje_mensual=Decimal("9.000"),
            vigencia_desde=date(2026, 4, 1),
        )
        cuota_enero = self._cuota("POS-910", "10000.00")
        cuota_enero.periodo = "2026-01"
        cuota_enero.fecha_vencimiento = date(2026, 1, 10)
        cuota_enero.save(update_fields=["periodo", "fecha_vencimiento"])

        # 15/03: la cuota de enero acumula 73 días, o sea dos meses enteros a
        # la tasa vieja. La de marzo todavía está dentro de su mes: cero.
        marzo = self._proyectar(date(2026, 3, 15))
        enero = next(d for d in marzo.detalle if d.cuota_id == cuota_enero.id)
        marzo_mio = next(d for d in marzo.detalle if d.cuota_id == self.cuota.id)
        self.assertEqual(enero.importe, Decimal("1100.00"))
        self.assertEqual(marzo_mio.importe, Decimal("0.00"))

    def test_la_tasa_nueva_rige_desde_su_propio_dia(self):
        """Con vigencia_desde 01/04, ese mismo día ya se cobra la nueva. Si
        arrancara al día siguiente, un pago del 01/04 quedaría con la tasa
        vieja sin que nadie lo note."""
        self._tasa(porcentaje_mensual=Decimal("5.500"))
        TasaInteres.objects.create(
            sucursal=self.posadas,
            porcentaje_mensual=Decimal("9.000"),
            vigencia_desde=date(2026, 4, 1),
        )

        resumen = self._proyectar(date(2026, 4, 1))

        self.assertEqual(resumen.total_interes, Decimal("900.00"))

    def _proyectar(self, fecha):
        return ConsultarIntereses(
            DjangoTasaInteresRepository(), DjangoCuotaInteresReader()
        ).execute(
            sucursal_ids=[self.posadas.id], fecha_evaluacion=fecha
        )