from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import close_old_connections, connection, connections
from django.test import SimpleTestCase, TestCase, TransactionTestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from .contexts.caja.infrastructure.django_transferencia_caja_repository import (
    DjangoTransferenciaCajaRepository,
)
from .models import CajaDiaria, MovimientoCaja, Pago, Sucursal, TransferenciaCaja


from .contexts.caja.domain.transferencia_caja import (
    SolicitudTransferenciaCaja,
    TransferenciaCajaError,
    validar_solicitud_transferencia,
)


class TransferenciaCajaDominioTests(SimpleTestCase):
    def test_rechaza_origen_igual_a_destino(self):
        solicitud = SolicitudTransferenciaCaja(1, 1, Decimal("10.00"), "Reubicación")

        with self.assertRaises(TransferenciaCajaError):
            validar_solicitud_transferencia(solicitud)

    def test_rechaza_importe_cero_o_negativo(self):
        for importe in (Decimal("0"), Decimal("-0.01")):
            with self.subTest(importe=importe):
                solicitud = SolicitudTransferenciaCaja(1, 2, importe, "Reubicación")
                with self.assertRaises(TransferenciaCajaError):
                    validar_solicitud_transferencia(solicitud)

    def test_rechaza_importe_no_finito(self):
        for importe in (Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")):
            with self.subTest(importe=importe):
                solicitud = SolicitudTransferenciaCaja(1, 2, importe, "Reubicación")
                with self.assertRaises(TransferenciaCajaError):
                    validar_solicitud_transferencia(solicitud)

    def test_rechaza_motivo_vacio(self):
        for motivo in ("", "   "):
            with self.subTest(motivo=motivo):
                solicitud = SolicitudTransferenciaCaja(1, 2, Decimal("10.00"), motivo)
                with self.assertRaises(TransferenciaCajaError):
                    validar_solicitud_transferencia(solicitud)

    def test_acepta_solicitud_valida(self):
        solicitud = SolicitudTransferenciaCaja(1, 2, Decimal("10.00"), "Reubicación")

        self.assertIsNone(validar_solicitud_transferencia(solicitud))


class TransferenciaCajaFixture:
    def setUp(self):
        super().setUp()
        self.actor = User.objects.create_user(username="administracion-transferencias")
        self.cajero = User.objects.create_user(username="cajero-destino-transferencias")
        sucursal = Sucursal.objects.create(codigo="TRF", nombre="Sucursal transferencias")
        self.origen = CajaDiaria.objects.create(
            fecha=timezone.localdate(), sucursal=sucursal, usuario=self.actor,
            saldo_inicial=Decimal("100.00"),
        )
        self.destino = CajaDiaria.objects.create(
            fecha=timezone.localdate(), sucursal=sucursal, usuario=self.cajero,
            saldo_inicial=Decimal("20.00"),
        )
        self.repository = DjangoTransferenciaCajaRepository()

    def solicitud(self, importe="30.00", *, origen=None, destino=None):
        return SolicitudTransferenciaCaja(
            (origen or self.origen).pk, (destino or self.destino).pk,
            Decimal(importe), "Refuerzo de efectivo",
        )

    def assert_sin_escrituras(self, *, movimientos=0, origen="100.00", destino="20.00"):
        self.assertEqual(TransferenciaCaja.objects.count(), 0)
        self.assertEqual(MovimientoCaja.objects.count(), movimientos)
        self.assertEqual(self.origen.total_esperado, Decimal(origen))
        self.assertEqual(self.destino.total_esperado, Decimal(destino))


class TransferenciaCajaAdaptadorTests(TransferenciaCajaFixture, TestCase):
    def test_guarda_pase_y_entrada_en_una_transferencia(self):
        transferencia = self.repository.transferir(actor=self.actor, solicitud=self.solicitud())

        transferencia.refresh_from_db()
        self.assertEqual(transferencia.origen_id, self.origen.pk)
        self.assertEqual(transferencia.destino_id, self.destino.pk)
        self.assertEqual(transferencia.actor_id, self.actor.pk)
        self.assertEqual(transferencia.importe, Decimal("30.00"))
        self.assertEqual(transferencia.motivo, "Refuerzo de efectivo")
        self.assertIsNotNone(transferencia.creado)
        self.assertEqual(transferencia.numero_comprobante, f"TRF-{transferencia.pk:08d}")
        self.assertEqual(transferencia.movimientos.count(), 2)
        salida = transferencia.movimientos.get(caja=self.origen)
        entrada = transferencia.movimientos.get(caja=self.destino)
        self.assertEqual(salida.tipo, MovimientoCaja.Tipo.PASE)
        self.assertEqual(entrada.tipo, MovimientoCaja.Tipo.INGRESO)
        self.assertEqual(salida.recibido_por_id, self.cajero.pk)
        for movimiento in (salida, entrada):
            self.assertEqual(movimiento.importe, transferencia.importe)
            self.assertEqual(movimiento.medio, Pago.Medio.EFECTIVO)
            self.assertEqual(movimiento.descripcion, transferencia.motivo)
        self.assertEqual(salida.signed_amount, -transferencia.importe)
        self.assertEqual(entrada.signed_amount, transferencia.importe)
        self.assertEqual(self.origen.total_esperado, Decimal("70.00"))
        self.assertEqual(self.destino.total_esperado, Decimal("50.00"))

    def test_transferencia_persistida_no_permite_mutacion(self):
        transferencia = self.repository.transferir(actor=self.actor, solicitud=self.solicitud())
        evidencia = TransferenciaCaja.objects.values().get(pk=transferencia.pk)
        partidas = list(transferencia.movimientos.order_by("pk").values())

        transferencia.importe = Decimal("80.00")
        transferencia.motivo = "Motivo alterado"
        transferencia.numero_comprobante = "TRF-ALTERADO"
        with self.assertRaises(TransferenciaCajaError):
            transferencia.save()

        self.assertEqual(TransferenciaCaja.objects.values().get(pk=transferencia.pk), evidencia)
        self.assertEqual(list(transferencia.movimientos.order_by("pk").values()), partidas)
        self.assertEqual(self.origen.total_esperado, Decimal("70.00"))
        self.assertEqual(self.destino.total_esperado, Decimal("50.00"))

    def test_transferencia_persistida_no_permite_save_con_instancia_reconstruida(self):
        transferencia = self.repository.transferir(actor=self.actor, solicitud=self.solicitud())
        evidencia = TransferenciaCaja.objects.values().get(pk=transferencia.pk)
        reconstruida = TransferenciaCaja(
            pk=transferencia.pk, origen=self.origen, destino=self.destino, actor=self.actor,
            importe=Decimal("80.00"), motivo="Motivo alterado", creado=transferencia.creado,
        )
        with self.assertRaises(TransferenciaCajaError):
            reconstruida.save()
        self.assertEqual(TransferenciaCaja.objects.values().get(pk=transferencia.pk), evidencia)

    def test_transferencia_persistida_no_permite_delete(self):
        transferencia = self.repository.transferir(actor=self.actor, solicitud=self.solicitud())
        evidencia = TransferenciaCaja.objects.values().get(pk=transferencia.pk)
        partidas = list(transferencia.movimientos.order_by("pk").values())
        with self.assertRaises(TransferenciaCajaError):
            transferencia.delete()
        self.assertEqual(TransferenciaCaja.objects.values().get(pk=transferencia.pk), evidencia)
        self.assertEqual(list(transferencia.movimientos.order_by("pk").values()), partidas)

    def test_bloquea_ambas_cajas_en_orden_de_id(self):
        # Invertir las cajas fuerza un orden distinto al indicado por el comando.
        with CaptureQueriesContext(connection) as queries:
            self.repository.transferir(
                actor=self.actor,
                solicitud=self.solicitud("10.00", origen=self.destino, destino=self.origen),
            )
        consultas_cajas = [
            consulta["sql"] for consulta in queries.captured_queries
            if consulta["sql"].startswith("SELECT") and "FROM \"core_cajadiaria\"" in consulta["sql"]
        ]
        self.assertEqual(len(consultas_cajas), 1)
        consulta = consultas_cajas[0]
        self.assertIn("ORDER BY \"core_cajadiaria\".\"id\" ASC", consulta)
        self.assertIn(f"IN ({self.origen.pk}, {self.destino.pk})", consulta)
        if connection.features.has_select_for_update:
            self.assertIn("FOR UPDATE", consulta)

    def test_rechaza_caja_cerrada_o_fecha_distinta_sin_escrituras(self):
        for caja in (self.origen, self.destino):
            for cambios in (
                {"estado": CajaDiaria.Estado.CERRADA},
                {"fecha": timezone.localdate() - timedelta(days=1)},
                {"fecha": timezone.localdate() + timedelta(days=1)},
            ):
                with self.subTest(caja=caja.pk, cambios=cambios):
                    CajaDiaria.objects.filter(pk=caja.pk).update(**cambios)
                    with self.assertRaises(TransferenciaCajaError):
                        self.repository.transferir(actor=self.actor, solicitud=self.solicitud())
                    self.assert_sin_escrituras()
                    CajaDiaria.objects.filter(pk=caja.pk).update(
                        estado=CajaDiaria.Estado.ABIERTA, fecha=timezone.localdate(),
                    )

    def test_rechaza_importe_superior_al_efectivo_esperado(self):
        MovimientoCaja.objects.create(
            caja=self.origen, tipo=MovimientoCaja.Tipo.EGRESO,
            medio=Pago.Medio.EFECTIVO, importe=Decimal("40.00"),
        )
        MovimientoCaja.objects.create(
            caja=self.origen, tipo=MovimientoCaja.Tipo.INGRESO,
            medio=Pago.Medio.TRANSFERENCIA, importe=Decimal("500.00"),
        )
        with self.assertRaises(TransferenciaCajaError):
            self.repository.transferir(actor=self.actor, solicitud=self.solicitud("60.01"))
        self.assert_sin_escrituras(movimientos=2, origen="60.00")

    def test_acepta_importe_igual_al_efectivo_esperado(self):
        self.repository.transferir(actor=self.actor, solicitud=self.solicitud("100.00"))
        self.assertEqual(self.origen.total_esperado, Decimal("0.00"))
        self.assertEqual(self.destino.total_esperado, Decimal("120.00"))
        self.assertEqual(TransferenciaCaja.objects.count(), 1)
        self.assertEqual(MovimientoCaja.objects.count(), 2)

    def test_error_al_guardar_el_destino_revierte_la_operacion(self):
        guardar_movimiento = MovimientoCaja.save

        def fallar_destino(movimiento, *args, **kwargs):
            if movimiento.caja_id == self.destino.pk:
                raise RuntimeError("Fallo de persistencia de la entrada")
            return guardar_movimiento(movimiento, *args, **kwargs)

        with patch.object(MovimientoCaja, "save", new=fallar_destino):
            with self.assertRaisesMessage(RuntimeError, "Fallo de persistencia de la entrada"):
                self.repository.transferir(actor=self.actor, solicitud=self.solicitud())
        self.assert_sin_escrituras()


@skipUnless(
    connection.vendor == "postgresql" and connection.features.has_select_for_update,
    "La concurrencia requiere PostgreSQL y bloqueos SELECT FOR UPDATE; SQLite no los implementa.",
)
class TransferenciaCajaConcurrenciaTests(TransferenciaCajaFixture, TransactionTestCase):
    def test_dos_transferencias_concurrentes_no_sobrepasan_efectivo_origen(self):
        barrera = Barrier(2)
        solicitud = self.solicitud("100.00")
        actor_id = self.actor.pk

        def transferir():
            close_old_connections()
            conexion = connections["default"]
            try:
                with conexion.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    conexion_id = cursor.fetchone()[0]
                    cursor.execute("SET lock_timeout = 5000")
                    cursor.execute("SET statement_timeout = 10000")
                actor = User.objects.get(pk=actor_id)

                def sincronizar_bloqueos(execute, sql, params, many, context):
                    if "FOR UPDATE" in sql and "core_cajadiaria" in sql:
                        barrera.wait(timeout=5)
                    return execute(sql, params, many, context)

                with conexion.execute_wrapper(sincronizar_bloqueos):
                    try:
                        DjangoTransferenciaCajaRepository().transferir(actor=actor, solicitud=solicitud)
                        return conexion_id, "confirmada"
                    except TransferenciaCajaError:
                        return conexion_id, "rechazada"
            finally:
                conexion.close()

        with ThreadPoolExecutor(max_workers=2) as executor:
            resultados = list(executor.map(lambda _: transferir(), range(2)))
        self.assertEqual(len({conexion_id for conexion_id, _ in resultados}), 2)
        self.assertCountEqual([estado for _, estado in resultados], ["confirmada", "rechazada"])
        self.assertEqual(TransferenciaCaja.objects.count(), 1)
        self.assertEqual(MovimientoCaja.objects.count(), 2)
        self.assertEqual(self.origen.total_esperado, Decimal("0.00"))
        self.assertEqual(self.destino.total_esperado, Decimal("120.00"))
