# Task 1 — Reglas y comando de transferencia entre cajas

## Alcance

- Contexto: Caja y Tesorería, en transición dentro del monolito modular existente.
- Actor: actor autenticado recibido por el caso de uso.
- Comando: solicitar transferencia desde una caja de origen hacia una caja de destino por un importe y motivo.
- Resultado: el puerto de persistencia ejecuta la transferencia y devuelve su resultado.
- Invariantes cubiertas: origen y destino distintos; importe mayor que cero; motivo no vacío.

## Cambios

- `backend/core/contexts/caja/domain/transferencia_caja.py`: solicitud inmutable, error de dominio y validación sin dependencias externas.
- `backend/core/contexts/caja/application/transferir_entre_cajas.py`: comando que valida la solicitud antes de delegar en el puerto `transferir`.
- `backend/core/test_transferencias_caja.py`: cuatro pruebas de dominio solicitadas y una prueba adicional para `NaN` e infinitos.

## Enfoque arquitectónico

La dependencia apunta desde aplicación hacia dominio. El puerto está definido en aplicación y no conoce el adaptador. Dominio y aplicación no importan Django, DRF, ORM ni HTTP. La ejecución atómica y las reglas relacionadas con estado de caja quedan a cargo del adaptador/implementación posterior; esta tarea solo define las reglas indicadas en el brief y el contrato del comando.

## Verificación

- TDD RED inicial (`/tmp/ipac-transferencias-venv/bin/python backend/manage.py test core.test_transferencias_caja.TransferenciaCajaDominioTests`): falló como esperado con `ModuleNotFoundError: No module named 'core.contexts.caja.domain.transferencia_caja'`.
- TDD GREEN inicial (mismo comando): `Ran 4 tests ... OK`.
- TDD RED de la corrección (`/tmp/ipac-transferencias-venv/bin/python backend/manage.py test core.test_transferencias_caja.TransferenciaCajaDominioTests.test_rechaza_importe_no_finito`): un `NaN` produjo `decimal.InvalidOperation` y `Infinity` fue aceptado; luego se corrigió para elevar `TransferenciaCajaError`.
- `core.test_transferencias_caja.TransferenciaCajaDominioTests`: 5 pruebas aprobadas tras la corrección.
- `git diff --check`: aprobado.
- Revisión de imports del dominio y aplicación: sin dependencias Django/DRF/ORM/HTTP.

## Deuda y límites

No se implementó adaptador ni persistencia, autorización, transacción, validación del estado de las cajas, ni pruebas de aplicación; quedan fuera de Task 1. El repositorio ya contiene archivos no rastreados preexistentes y fueron preservados.

## Seguimiento: importes no finitos

Se añadió una validación `Decimal.is_finite()` antes de comparar con cero. `NaN`, `Infinity` y `-Infinity` ahora se rechazan con `TransferenciaCajaError`, sin permitir que una comparación inválida exponga `decimal.InvalidOperation`.

Comando de verificación en WSL:

```text
/tmp/ipac-transferencias-venv/bin/python backend/manage.py test core.test_transferencias_caja.TransferenciaCajaDominioTests
```

Salida relevante:

```text
.....
Ran 5 tests in 0.001s
OK
Found 5 test(s).
System check identified no issues (0 silenced).
```

Diff check:

```text
git diff --check
```

Salida: vacía (código de salida 0).
