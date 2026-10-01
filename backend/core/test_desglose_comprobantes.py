"""Pruebas del desglose programatico/extraprogramatico y del comprobante de caja.

Las pruebas de dominio no tocan Django ni la base: son funciones puras.
Las de aplicacion usan un puerto falso. Las de adaptador y API usan Django.
"""

from decimal import Decimal
from unittest import TestCase as UnitTestCase

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from core.contexts.caja.application.registrar_movimiento_caja import (
    RegistrarMovimientoCaja,
    SolicitudMovimientoCaja,
)
from core.contexts.caja.domain.comprobante_caja import (
    ComprobanteCajaError,
    numero_comprobante,
    requiere_comprobante,
    validar_comprobante,
)
from core.contexts.cobranzas.domain.desglose_cuota import (
    DesgloseCuotaError,
    calcular_desglose,
)
from core.models import (
    CajaDiaria,
    CarreraCurso,
    ConceptoCobrable,
    MovimientoCaja,
    Pago,
    PerfilUsuario,
    Sucursal,
)
from core.models import Alumno, Cuota, Matricula


# --------------------------------------------------------------------- dominio


class DesgloseCuotaDominioTests(UnitTestCase):
    def test_reparte_directamente_cuando_el_importe_igual_al_catalogo(self):
        desglose = calcular_desglose(
            importe="82000.00",
            programatico_catalogo="62000.00",
            extraprogramatica_catalogo="20000.00",
        )
        self.assertEqual(desglose.importe_programatico, Decimal("62000.00"))
        self.assertEqual(desglose.importe_extraprogramatica, Decimal("20000.00"))
        self.assertEqual(desglose.total, Decimal("82000.00"))

    def test_prorratea_y_el_reparto_cierra_exacto_con_el_importe_de_la_cuota(self):
        desglose = calcular_desglose(
            importe=Decimal("90000.00"),
            programatico_catalogo="62000.00",
            extraprogramatica_catalogo="20000.00",
        )
        self.assertEqual(desglose.total, Decimal("90000.00"))
        self.assertEqual(
            desglose.importe_extraprogramatica,
            Decimal("90000.00") - desglose.importe_programatico,
        )

    def test_redondea_a_centavo_sin_dejar_el_total_descuadrado(self):
        desglose = calcular_desglose(
            importe=Decimal("10.00"),
            programatico_catalogo="70000.00",
            extraprogramatica_catalogo="30000.00",
        )
        self.assertEqual(desglose.importe_programatico, Decimal("7.00"))
        self.assertEqual(desglose.importe_extraprogramatica, Decimal("3.00"))
        self.assertEqual(desglose.total, Decimal("10.00"))

    def test_sin_catalogo_configurado_no_inventa_un_reparto(self):
        self.assertIsNone(
            calcular_desglose(importe="82000.00", programatico_catalogo=None, extraprogramatica_catalogo=None)
        )
        self.assertIsNone(
            calcular_desglose(importe="82000.00", programatico_catalogo="0", extraprogramatica_catalogo="0")
        )

    def test_rechaza_un_importe_de_cuota_invalido(self):
        with self.assertRaises(DesgloseCuotaError):
            calcular_desglose(importe="0", programatico_catalogo="1.00", extraprogramatica_catalogo="1.00")

    def test_rechaza_un_catalogo_negativo(self):
        with self.assertRaises(DesgloseCuotaError):
            calcular_desglose(
                importe="100.00", programatico_catalogo="-1.00", extraprogramatica_catalogo="101.00"
            )


class ComprobanteCajaDominioTests(UnitTestCase):
    def test_pase_y_retiro_exigen_comprobante(self):
        self.assertTrue(requiere_comprobante("pase"))
        self.assertTrue(requiere_comprobante("retiro"))

    def test_los_movimientos_corrientes_no_lo_exigen(self):
        for tipo in ("pago", "ingreso", "egreso", "reverso"):
            self.assertFalse(requiere_comprobante(tipo), tipo)

    def test_numeracion_estable_y_ordenable(self):
        self.assertEqual(numero_comprobante(7), "COM-00000007")
        self.assertLess(numero_comprobante(7), numero_comprobante(70))

    def test_rechaza_pase_sin_quien_recibe(self):
        with self.assertRaises(ComprobanteCajaError):
            validar_comprobante(
                tipo="pase", importe=Decimal("100.00"), descripcion="Pase a Laura", recibido_por_id=None
            )

    def test_rechaza_pase_sin_motivo(self):
        with self.assertRaises(ComprobanteCajaError):
            validar_comprobante(
                tipo="pase", importe=Decimal("100.00"), descripcion="   ", recibido_por_id=3
            )

    def test_rechaza_pase_con_importe_cero(self):
        with self.assertRaises(ComprobanteCajaError):
            validar_comprobante(
                tipo="pase", importe=Decimal("0"), descripcion="Pase a Laura", recibido_por_id=3
            )

    def test_un_ingreso_corriente_no_exige_comprobante(self):
        validar_comprobante(
            tipo="ingreso", importe=Decimal("100.00"), descripcion="Donacion", recibido_por_id=None
        )


# ----------------------------------------------------------------- aplicacion


class FakeMovimientoWriter:
    def __init__(self):
        self.llamadas = []

    def registrar(self, *, actor, solicitud):
        self.llamadas.append((actor, solicitud))
        return solicitud


class RegistrarMovimientoCajaTests(UnitTestCase):
    def setUp(self):
        self.writer = FakeMovimientoWriter()
        self.caso = RegistrarMovimientoCaja(self.writer)

    def _solicitud(self, **cambios):
        base = dict(
            caja_id=1,
            tipo="pase",
            medio="efectivo",
            importe=Decimal("500.00"),
            descripcion="Pase a Laura",
            recibido_por_id=9,
        )
        base.update(cambios)
        return SolicitudMovimientoCaja(**base)

    def test_delega_la_escritura_cuando_el_pase_trae_conformidad(self):
        self.caso.execute(actor="cajero", solicitud=self._solicitud())
        self.assertEqual(len(self.writer.llamadas), 1)

    def test_no_escribe_si_falta_la_conformidad(self):
        with self.assertRaises(ComprobanteCajaError):
            self.caso.execute(actor="cajero", solicitud=self._solicitud(recibido_por_id=None))
        self.assertEqual(self.writer.llamadas, [])

    def test_un_ingreso_corriente_no_necesita_conformidad(self):
        self.caso.execute(
            actor="cajero",
            solicitud=self._solicitud(tipo="ingreso", recibido_por_id=None),
        )
        self.assertEqual(len(self.writer.llamadas), 1)


# ------------------------------------------------------------------ adaptador


class FixturesCajaMixin:
    def _user(self, username, rol, sucursal, todas=False, activo=True):
        user = User.objects.create_user(username, password="test-password")
        PerfilUsuario.objects.create(
            user=user,
            rol=rol,
            sucursal=sucursal,
            puede_ver_todas_las_sucursales=todas,
        )
        if not activo:
            user.is_active = False
            user.save(update_fields=["is_active"])
        return user

    def _caja(self, usuario, sucursal=None):
        return CajaDiaria.objects.create(
            fecha=timezone.localdate(),
            sucursal=sucursal or self.posadas,
            usuario=usuario,
            estado=CajaDiaria.Estado.ABIERTA,
        )


class ComprobanteCajaAdaptadorTests(FixturesCajaMixin, TestCase):
    def setUp(self):

        self.posadas = Sucursal.objects.create(codigo="POS", nombre="Posadas")
        self.eldorado = Sucursal.objects.create(codigo="ELD", nombre="Eldorado")
        self.cajero = self._user("cajero-comprobante", PerfilUsuario.Rol.CAJA, self.posadas)
        self.otro_cajero = self._user("otro-comprobante", PerfilUsuario.Rol.CAJA, self.posadas)
        self.caja = self._caja(self.cajero)

    def test_el_pase_se_numera_solo_al_guardarse(self):
        movimiento = MovimientoCaja.objects.create(
            caja=self.caja,
            tipo=MovimientoCaja.Tipo.PASE,
            medio=Pago.Medio.EFECTIVO,
            importe=Decimal("500.00"),
            descripcion="Pase para pagos internos",
            recibido_por=self.otro_cajero,
        )
        movimiento.refresh_from_db()
        self.assertEqual(movimiento.numero_comprobante, f"COM-{movimiento.pk:08d}")

    def test_el_ingreso_no_se_numera(self):
        movimiento = MovimientoCaja.objects.create(
            caja=self.caja,
            tipo=MovimientoCaja.Tipo.INGRESO,
            medio=Pago.Medio.EFECTIVO,
            importe=Decimal("120.00"),
            descripcion="Donacion",
        )
        movimiento.refresh_from_db()
        self.assertIsNone(movimiento.numero_comprobante)

    def test_la_numeracion_no_se_roba_entre_movimientos(self):
        primero = MovimientoCaja.objects.create(
            caja=self.caja,
            tipo=MovimientoCaja.Tipo.RETIRO,
            medio=Pago.Medio.EFECTIVO,
            importe=Decimal("10.00"),
            descripcion="Retiro 1",
            recibido_por=self.otro_cajero,
        )
        segundo = MovimientoCaja.objects.create(
            caja=self.caja,
            tipo=MovimientoCaja.Tipo.RETIRO,
            medio=Pago.Medio.EFECTIVO,
            importe=Decimal("20.00"),
            descripcion="Retiro 2",
            recibido_por=self.otro_cajero,
        )
        self.assertNotEqual(primero.numero_comprobante, segundo.numero_comprobante)


class ComprobanteCajaApiTests(FixturesCajaMixin, APITestCase):
    def setUp(self):

        self.posadas = Sucursal.objects.create(codigo="POS", nombre="Posadas")
        self.eldorado = Sucursal.objects.create(codigo="ELD", nombre="Eldorado")
        self.cajero = self._user("cajero-api", PerfilUsuario.Rol.CAJA, self.posadas)
        self.receptor = self._user("receptor-api", PerfilUsuario.Rol.CAJA, self.posadas)
        self.cajero_eldorado = self._user("cajero-eld", PerfilUsuario.Rol.CAJA, self.eldorado)
        self.consulta = self._user("consulta-api", PerfilUsuario.Rol.CONSULTA, self.posadas)
        self.caja = self._caja(self.cajero)

    def test_el_api_rechaza_el_pase_sin_conformidad(self):
        self.client.force_authenticate(self.cajero)
        respuesta = self.client.post(
            "/api/movimientos-caja/",
            {
                "caja": self.caja.pk,
                "tipo": MovimientoCaja.Tipo.PASE,
                "medio": Pago.Medio.EFECTIVO,
                "importe": "500.00",
                "descripcion": "Pase para pagos internos",
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_el_api_registra_el_pase_con_comprobante(self):
        self.client.force_authenticate(self.cajero)
        respuesta = self.client.post(
            "/api/movimientos-caja/",
            {
                "caja": self.caja.pk,
                "tipo": MovimientoCaja.Tipo.PASE,
                "medio": Pago.Medio.EFECTIVO,
                "importe": "500.00",
                "descripcion": "Pase para pagos internos",
                "recibido_por": self.receptor.pk,
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertTrue(respuesta.data["numero_comprobante"].startswith("COM-"))
        self.assertEqual(respuesta.data["recibido_por"], self.receptor.pk)
        self.assertEqual(respuesta.data["recibido_por_nombre"], self.receptor.username)

    def test_el_api_rechaza_un_receptor_inactivo(self):
        inactivo = self._user("inactivo-api", PerfilUsuario.Rol.CAJA, self.posadas, activo=False)
        self.client.force_authenticate(self.cajero)
        respuesta = self.client.post(
            "/api/movimientos-caja/",
            {
                "caja": self.caja.pk,
                "tipo": MovimientoCaja.Tipo.PASE,
                "medio": Pago.Medio.EFECTIVO,
                "importe": "500.00",
                "descripcion": "Pase para pagos internos",
                "recibido_por": inactivo.pk,
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_el_api_sigue_aceptando_ingresos_sin_conformidad(self):
        self.client.force_authenticate(self.cajero)
        respuesta = self.client.post(
            "/api/movimientos-caja/",
            {
                "caja": self.caja.pk,
                "tipo": MovimientoCaja.Tipo.INGRESO,
                "medio": Pago.Medio.EFECTIVO,
                "importe": "120.00",
                "descripcion": "Donacion",
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(respuesta.data["numero_comprobante"])

    def test_el_comprobante_se_puede_consultar_como_documento_digital(self):
        self.client.force_authenticate(self.cajero)
        creado = self.client.post(
            "/api/movimientos-caja/",
            {
                "caja": self.caja.pk,
                "tipo": MovimientoCaja.Tipo.PASE,
                "medio": Pago.Medio.EFECTIVO,
                "importe": "500.00",
                "descripcion": "Pase para pagos internos",
                "recibido_por": self.receptor.pk,
            },
            format="json",
        )
        documento = self.client.get(f"/api/movimientos-caja/{creado.data['id']}/comprobante/")
        self.assertEqual(documento.status_code, status.HTTP_200_OK)
        self.assertEqual(documento.data["numero"], creado.data["numero_comprobante"])
        self.assertTrue(documento.data["requiere_comprobante"])

    def test_un_cajero_no_abre_el_comprobante_de_la_caja_de_otro(self):
        movimiento = MovimientoCaja.objects.create(
            caja=self._caja(self.receptor),
            tipo=MovimientoCaja.Tipo.RETIRO,
            medio=Pago.Medio.EFECTIVO,
            importe=Decimal("50.00"),
            descripcion="Retiro",
            recibido_por=self.receptor,
        )
        self.client.force_authenticate(self.cajero)
        respuesta = self.client.get(f"/api/movimientos-caja/{movimiento.pk}/comprobante/")
        self.assertIn(respuesta.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND))

    def test_consulta_no_lista_movimientos(self):
        movimiento = MovimientoCaja.objects.create(
            caja=self.caja,
            tipo=MovimientoCaja.Tipo.INGRESO,
            medio=Pago.Medio.EFECTIVO,
            importe=Decimal("120.00"),
            descripcion="Donacion",
        )
        self.client.force_authenticate(self.consulta)
        respuesta = self.client.get(f"/api/movimientos-caja/{movimiento.pk}/comprobante/")
        self.assertIn(respuesta.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND))

    def test_receptores_devuelve_la_sucursal_del_usuario_y_no_otra(self):
        self.client.force_authenticate(self.cajero)
        respuesta = self.client.get("/api/cajas/receptores/")
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in respuesta.data]
        self.assertIn(self.cajero.pk, ids)
        self.assertIn(self.receptor.pk, ids)
        self.assertNotIn(self.cajero_eldorado.pk, ids)

    def test_receptores_para_administracion_alcanza_a_todas_las_sucursales(self):
        admin = self._user("admin-receptores", PerfilUsuario.Rol.ADMINISTRACION, self.posadas, todas=True)
        self.client.force_authenticate(admin)
        respuesta = self.client.get("/api/cajas/receptores/")
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in respuesta.data]
        self.assertIn(self.cajero_eldorado.pk, ids)

    def test_consulta_no_puede_ver_los_receptores(self):
        self.client.force_authenticate(self.consulta)
        respuesta = self.client.get("/api/cajas/receptores/")
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)


# ------------------------------------------------------------------- desglose


class DesgloseCuotaApiTests(FixturesCajaMixin, APITestCase):
    def setUp(self):

        self.posadas = Sucursal.objects.create(codigo="POS", nombre="Posadas")
        self.admin = self._user("admin-desglose", PerfilUsuario.Rol.ADMINISTRACION, self.posadas, todas=True)
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
        self.alumno = Alumno.objects.create(
            legajo="L-0001",
            nombre="Ana",
            apellido="Gomez",
            sucursal=self.posadas,
            carrera=self.carrera,
        )

    def _generar(self, **extra):
        payload = {
            "alumnos": [self.alumno.pk],
            "concepto": self.concepto.pk,
            "periodo": "2026-10",
            "fecha_emision": "2026-10-01",
            "fecha_vencimiento": "2026-10-10",
            "descuento": "0",
            "recargo": "0",
        }
        payload.update(extra)
        self.client.force_authenticate(self.admin)
        return self.client.post("/api/cuotas/generar/", payload, format="json")

    def test_la_generacion_congela_el_desglose_del_catalogo(self):
        respuesta = self._generar()
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        cuota = Cuota.objects.get(alumno=self.alumno, periodo="2026-10")
        self.assertEqual(cuota.importe_programatico, Decimal("62000.00"))
        self.assertEqual(cuota.importe_extraprogramatica, Decimal("20000.00"))
        self.assertTrue(cuota.desglose_disponible)

    def test_un_cambio_de_precio_del_catalogo_no_altera_las_cuotas_emitidas(self):
        self._generar()
        self.carrera.cuota_programatica = Decimal("70000.00")
        self.carrera.cuota_extraprogramatica = Decimal("20000.00")
        self.carrera.save()
        cuota = Cuota.objects.get(alumno=self.alumno, periodo="2026-10")
        self.assertEqual(cuota.importe_programatico, Decimal("62000.00"))
        self.assertEqual(cuota.importe_extraprogramatica, Decimal("20000.00"))

    def test_la_matricula_activa_manda_sobre_la_carrera_de_la_ficha(self):
        otra_carrera = CarreraCurso.objects.create(
            nombre="Curso de diseno",
            sucursal=self.posadas,
            cuota_programatica=Decimal("30000.00"),
            cuota_extraprogramatica=Decimal("10000.00"),
        )
        Matricula.objects.create(
            alumno=self.alumno,
            carrera=otra_carrera,
            sucursal=self.posadas,
            fecha_inicio="2026-08-01",
        )
        self._generar()
        cuota = Cuota.objects.get(alumno=self.alumno, periodo="2026-10")
        # La cuota vale 82000 (importe del concepto) y el catalogo de la carrera
        # matriculada reparte 30000/10000, o sea 75/25. Se aplica el mismo reparto
        # al importe de la cuota: 82000 * 0,75 = 61500 y el resto 20500.
        # Lo relevante es que manda la carrera de la matricula y no la de la
        # ficha, que habria dado 62000/20000.
        self.assertEqual(cuota.importe_programatico, Decimal("61500.00"))
        self.assertEqual(cuota.importe_extraprogramatica, Decimal("20500.00"))
        self.assertEqual(
            cuota.importe_programatico + cuota.importe_extraprogramatica, cuota.importe
        )

    def test_sin_carrera_la_cuota_queda_sin_desglose(self):
        self.alumno.carrera = None
        self.alumno.save(update_fields=["carrera"])
        respuesta = self._generar()
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        cuota = Cuota.objects.get(alumno=self.alumno, periodo="2026-10")
        self.assertFalse(cuota.desglose_disponible)
        self.assertIsNone(cuota.importe_programatico)

    def test_el_recibo_muestra_el_desglose_de_la_cuota_totalmente_cubierta(self):
        cuota_id = self._generar().data[0]["id"]
        self.client.force_authenticate(self.admin)
        respuesta = self.client.post(
            "/api/pagos/cobrar/",
            {
                "alumno": self.alumno.pk,
                "importe": "82000.00",
                "medio": Pago.Medio.EFECTIVO,
                "aplicaciones": [{"cuota_id": cuota_id, "importe": "82000.00"}],
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        recibo = self.client.get(f"/api/pagos/{respuesta.data['id']}/recibo/")
        self.assertEqual(recibo.status_code, status.HTTP_200_OK)
        linea = recibo.data["aplicaciones"][0]
        self.assertTrue(linea["desglose_completo"])
        self.assertEqual(Decimal(linea["importe_programatico"]), Decimal("62000.00"))
        self.assertEqual(Decimal(linea["importe_extraprogramatica"]), Decimal("20000.00"))

    def test_el_recibo_no_inventa_el_reparto_de_un_pago_parcial(self):
        cuota_id = self._generar().data[0]["id"]
        self.client.force_authenticate(self.admin)
        respuesta = self.client.post(
            "/api/pagos/cobrar/",
            {
                "alumno": self.alumno.pk,
                "importe": "10000.00",
                "medio": Pago.Medio.EFECTIVO,
                "aplicaciones": [{"cuota_id": cuota_id, "importe": "10000.00"}],
            },
            format="json",
        )
        recibo = self.client.get(f"/api/pagos/{respuesta.data['id']}/recibo/")
        linea = recibo.data["aplicaciones"][0]
        self.assertFalse(linea["desglose_completo"])
        self.assertIsNone(linea["importe_programatico"])
