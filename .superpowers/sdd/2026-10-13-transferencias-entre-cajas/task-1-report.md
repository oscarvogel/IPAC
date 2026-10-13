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
- `backend/core/test_transferencias_caja.py`: cuatro pruebas de dominio solicitadas.

## Enfoque arquitectónico

La dependencia apunta desde aplicación hacia dominio. El puerto está definido en aplicación y no conoce el adaptador. Dominio y aplicación no importan Django, DRF, ORM ni HTTP. La ejecución atómica y las reglas relacionadas con estado de caja quedan a cargo del adaptador/implementación posterior; esta tarea solo define las reglas indicadas en el brief y el contrato del comando.

## Verificación

- TDD: la primera ejecución falló al no existir el módulo de dominio.
- `core.test_transferencias_caja.TransferenciaCajaDominioTests`: 4 pruebas aprobadas.
- `git diff --check`: aprobado.
- Revisión de imports del dominio y aplicación: sin dependencias Django/DRF/ORM/HTTP.

## Deuda y límites

No se implementó adaptador ni persistencia, autorización, transacción, validación del estado de las cajas, ni pruebas de aplicación; quedan fuera de Task 1. El repositorio ya contiene archivos no rastreados preexistentes y fueron preservados.
