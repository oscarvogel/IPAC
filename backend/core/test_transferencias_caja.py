from decimal import Decimal

from django.test import SimpleTestCase

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

    def test_rechaza_motivo_vacio(self):
        for motivo in ("", "   "):
            with self.subTest(motivo=motivo):
                solicitud = SolicitudTransferenciaCaja(1, 2, Decimal("10.00"), motivo)
                with self.assertRaises(TransferenciaCajaError):
                    validar_solicitud_transferencia(solicitud)

    def test_acepta_solicitud_valida(self):
        solicitud = SolicitudTransferenciaCaja(1, 2, Decimal("10.00"), "Reubicación")

        self.assertIsNone(validar_solicitud_transferencia(solicitud))
