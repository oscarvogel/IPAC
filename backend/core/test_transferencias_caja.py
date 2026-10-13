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


class TransferenciaCajaApiTests(TestCase):
    def setUp(self):
        from rest_framework.test import APIClient
        from .models import PerfilUsuario

        self.client = APIClient()
        self.posadas = Sucursal.objects.create(codigo="TP", nombre="Posadas transferencias API")
        self.eldorado = Sucursal.objects.create(codigo="TE", nombre="Eldorado transferencias API")
        self.actor = User.objects.create_user(username="administrador-api")
        PerfilUsuario.objects.create(
            user=self.actor, sucursal=self.posadas, rol="administracion",
            puede_ver_todas_las_sucursales=True,
        )
        self.cajero_origen = User.objects.create_user(username="cajero-origen-api")
        self.cajero_destino = User.objects.create_user(username="cajero-destino-api")
        self.origen = CajaDiaria.objects.create(
            fecha=timezone.localdate(), sucursal=self.posadas, usuario=self.cajero_origen,
            saldo_inicial=Decimal("100.00"),
        )
        self.destino = CajaDiaria.objects.create(
            fecha=timezone.localdate(), sucursal=self.eldorado, usuario=self.cajero_destino,
            saldo_inicial=Decimal("20.00"),
        )
        self.local = CajaDiaria.objects.create(
            fecha=timezone.localdate(), sucursal=self.posadas, usuario=self.actor,
            saldo_inicial=Decimal("10.00"),
        )
        # Administración puede operar sin tener una caja propia.
        self.local.usuario = User.objects.create_user(username="otro-cajero-api")
        self.local.save()
        self.client.force_authenticate(self.actor)
        self.url = "/api/transferencias-caja/"
        self.payload = {
            "origen_id": self.origen.pk, "destino_id": self.destino.pk,
            "importe": "30.00", "motivo": "Refuerzo de efectivo",
        }

    def cambiar_perfil(self, **cambios):
        from .models import PerfilUsuario
        PerfilUsuario.objects.filter(user=self.actor).update(**cambios)
        self.actor = User.objects.get(pk=self.actor.pk)
        self.client.force_authenticate(self.actor)

    def test_admin_global_puede_transferir_entre_sucursales(self):
        for rol in ("administracion", "superadmin"):
            with self.subTest(rol=rol):
                self.cambiar_perfil(rol=rol)
                cajas = self.client.get(self.url + "cajas-abiertas/")
                self.assertEqual(cajas.status_code, 200)
                self.assertEqual({c["id"] for c in cajas.data}, {self.origen.pk, self.destino.pk, self.local.pk})
                respuesta = self.client.post(self.url, self.payload, format="json")
                self.assertEqual(respuesta.status_code, 201)
                self.assertEqual(respuesta.data["origen"]["sucursal"], self.posadas.pk)
                self.assertEqual(respuesta.data["destino"]["sucursal"], self.eldorado.pk)
        self.assertEqual(TransferenciaCaja.objects.count(), 2)
        self.assertEqual(MovimientoCaja.objects.count(), 4)
        self.assertEqual(self.origen.total_esperado, Decimal("40.00"))
        self.assertEqual(self.destino.total_esperado, Decimal("80.00"))

    def test_admin_limitado_no_consulta_ni_transfiere_fuera_de_su_sucursal(self):
        transferencia_externa = DjangoTransferenciaCajaRepository().transferir(
            actor=self.actor, solicitud=SolicitudTransferenciaCaja(
                self.origen.pk, self.destino.pk, Decimal("10.00"), "Entre sucursales",
            ),
        )
        transferencia_local = DjangoTransferenciaCajaRepository().transferir(
            actor=self.actor, solicitud=SolicitudTransferenciaCaja(
                self.origen.pk, self.local.pk, Decimal("10.00"), "Dentro de sucursal",
            ),
        )
        for rol in ("administracion", "superadmin"):
            with self.subTest(rol=rol):
                self.cambiar_perfil(rol=rol, puede_ver_todas_las_sucursales=False)
                cajas = self.client.get(self.url + "cajas-abiertas/", {"sucursal": self.eldorado.pk})
                self.assertEqual(cajas.status_code, 200)
                self.assertEqual({c["id"] for c in cajas.data}, {self.origen.pk, self.local.pk})
                historial = self.client.get(self.url)
                self.assertEqual(historial.status_code, 200)
                self.assertEqual([t["id"] for t in historial.data], [transferencia_local.pk])
                self.assertNotIn(transferencia_externa.pk, [t["id"] for t in historial.data])
                for caja_id in (self.destino.pk, 999999):
                    for campo in ("origen_id", "destino_id"):
                        payload = dict(self.payload, origen_id=self.origen.pk, destino_id=self.local.pk)
                        payload[campo] = caja_id
                        respuesta = self.client.post(self.url, payload, format="json")
                        self.assertEqual(respuesta.status_code, 404)
                        self.assertEqual(respuesta.data["detail"], "Caja no disponible.")
        self.assertEqual(TransferenciaCaja.objects.count(), 2)
        self.assertEqual(MovimientoCaja.objects.count(), 4)

    def test_solo_administracion_y_superadmin_pueden_transferir(self):
        for rol in ("tesoreria", "caja", "consulta"):
            with self.subTest(rol=rol):
                self.cambiar_perfil(rol=rol)
                respuesta = self.client.post(self.url, self.payload, format="json")
                self.assertEqual(respuesta.status_code, 403)
                self.assertEqual(self.client.get(self.url).status_code, 403)
                self.assertEqual(self.client.get(self.url + "cajas-abiertas/").status_code, 403)
        self.assertEqual(TransferenciaCaja.objects.count(), 0)
        self.assertEqual(MovimientoCaja.objects.count(), 0)

    def test_respuesta_identifica_actor_y_los_dos_movimientos(self):
        from .models import EventoAuditoria
        payload = dict(self.payload, actor=self.cajero_destino.pk, actor_id=self.cajero_destino.pk)
        respuesta = self.client.post(self.url, payload, format="json")
        self.assertEqual(respuesta.status_code, 201)
        evidencia = respuesta.data
        transferencia = TransferenciaCaja.objects.get(pk=evidencia["id"])
        self.assertEqual(evidencia["actor"]["id"], self.actor.pk)
        self.assertEqual(evidencia["actor"]["username"], self.actor.username)
        self.assertEqual(evidencia["numero_comprobante"], transferencia.numero_comprobante)
        self.assertTrue(evidencia["creado"])
        self.assertEqual(evidencia["importe"], "30.00")
        self.assertEqual(evidencia["motivo"], "Refuerzo de efectivo")
        self.assertEqual(evidencia["origen"]["id"], self.origen.pk)
        self.assertEqual(evidencia["destino"]["id"], self.destino.pk)
        self.assertEqual(evidencia["origen"]["usuario"], self.cajero_origen.pk)
        self.assertEqual(evidencia["destino"]["usuario"], self.cajero_destino.pk)
        self.assertEqual(evidencia["movimiento_origen_id"], transferencia.movimientos.get(caja=self.origen).pk)
        self.assertEqual(evidencia["movimiento_destino_id"], transferencia.movimientos.get(caja=self.destino).pk)
        self.assertNotEqual(evidencia["movimiento_origen_id"], evidencia["movimiento_destino_id"])
        evento = EventoAuditoria.objects.get(entidad="core.TransferenciaCaja", entidad_id=str(transferencia.pk))
        self.assertEqual(EventoAuditoria.objects.count(), 1)
        self.assertEqual(evento.usuario_id, self.actor.pk)
        self.assertEqual(evento.modulo, "caja")
        self.assertEqual(evento.accion, "transferencia")
        for campo in ("origen_id", "destino_id", "actor_id", "importe", "motivo", "numero_comprobante",
                      "movimiento_origen_id", "movimiento_destino_id", "creado"):
            self.assertIn(campo, evento.valores_nuevos)
        self.assertEqual(evento.valores_nuevos["actor_id"], self.actor.pk)
        self.assertEqual(evento.valores_nuevos["origen_id"], self.origen.pk)
        self.assertEqual(evento.valores_nuevos["destino_id"], self.destino.pk)
        self.assertEqual(evento.valores_nuevos["importe"], "30.00")
        historial = self.client.get(self.url)
        self.assertEqual(historial.status_code, 200)
        self.assertEqual(historial.data[0], evidencia)

    def test_cajas_operables_solo_abiertas_del_dia_e_historial_conserva_evidencia(self):
        transferencia = DjangoTransferenciaCajaRepository().transferir(
            actor=self.actor, solicitud=SolicitudTransferenciaCaja(
                self.origen.pk, self.destino.pk, Decimal("10.00"), "Evidencia anterior",
            ),
        )
        CajaDiaria.objects.filter(pk=self.origen.pk).update(
            fecha=timezone.localdate() - timedelta(days=1), estado=CajaDiaria.Estado.CERRADA,
        )
        CajaDiaria.objects.filter(pk=self.destino.pk).update(
            fecha=timezone.localdate() + timedelta(days=1),
        )
        cajas = self.client.get(self.url + "cajas-abiertas/")
        self.assertEqual(cajas.status_code, 200)
        self.assertEqual([c["id"] for c in cajas.data], [self.local.pk])
        historial = self.client.get(self.url)
        self.assertEqual(historial.status_code, 200)
        self.assertEqual([t["id"] for t in historial.data], [transferencia.pk])
        for caja_id in (self.origen.pk, self.destino.pk):
            respuesta = self.client.post(
                self.url, dict(self.payload, origen_id=self.local.pk, destino_id=caja_id), format="json",
            )
            self.assertEqual(respuesta.status_code, 404)
            self.assertEqual(respuesta.data["detail"], "Caja no disponible.")
        self.assertEqual(TransferenciaCaja.objects.count(), 1)
        self.assertEqual(MovimientoCaja.objects.count(), 2)

    def test_fallo_de_auditoria_revierte_transferencia_y_ambos_movimientos(self):
        from .models import EventoAuditoria
        from .contexts.auditoria.infrastructure.django_auditoria_repository import DjangoAuditoriaRepository

        with patch.object(DjangoAuditoriaRepository, "guardar", side_effect=RuntimeError("Auditoría indisponible")):
            with self.assertRaisesMessage(RuntimeError, "Auditoría indisponible"):
                self.client.post(self.url, self.payload, format="json")
        self.assertEqual(TransferenciaCaja.objects.count(), 0)
        self.assertEqual(MovimientoCaja.objects.count(), 0)
        self.assertEqual(EventoAuditoria.objects.count(), 0)
        self.assertEqual(self.origen.total_esperado, Decimal("100.00"))
        self.assertEqual(self.destino.total_esperado, Decimal("20.00"))

    def test_rechaza_importes_invalidos_saldo_insuficiente_y_cajas_iguales_sin_escrituras(self):
        for cambios in (
            {"importe": "0"}, {"importe": "-1"}, {"importe": "NaN"},
            {"importe": "100.01"}, {"importe": "1.001"},
            {"motivo": ""}, {"motivo": "x" * 181},
            {"destino_id": self.origen.pk},
        ):
            with self.subTest(cambios=cambios):
                respuesta = self.client.post(self.url, dict(self.payload, **cambios), format="json")
                self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(TransferenciaCaja.objects.count(), 0)
        self.assertEqual(MovimientoCaja.objects.count(), 0)

    def test_anonimo_sin_perfil_o_clave_pendiente_no_opera(self):
        from rest_framework.test import APIClient

        self.assertEqual(APIClient().post(self.url, self.payload, format="json").status_code, 401)
        self.client.force_authenticate(self.cajero_origen)
        self.assertEqual(self.client.post(self.url, self.payload, format="json").status_code, 403)
        self.cambiar_perfil(debe_cambiar_clave=True)
        self.assertEqual(self.client.post(self.url, self.payload, format="json").status_code, 403)
        self.assertEqual(TransferenciaCaja.objects.count(), 0)
        self.assertEqual(MovimientoCaja.objects.count(), 0)
