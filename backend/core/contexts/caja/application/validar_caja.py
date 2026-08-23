from ....models import CajaDiaria


CAJA_CERRADA_MESSAGE = "La caja del día está cerrada. No se pueden registrar nuevas cobranzas."


class CajaCerradaError(ValueError):
    """Raised when an operation attempts to mutate a closed daily cashbox."""


def asegurar_caja_abierta(caja):
    if caja.estado == CajaDiaria.Estado.CERRADA:
        raise CajaCerradaError(CAJA_CERRADA_MESSAGE)
    return caja
