# Transferencias entre cajas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir que administración transfiera efectivo entre dos cajas abiertas autorizadas, con débito y crédito atómicos y evidencia auditable.

**Architecture:** Añadir al contexto lógico Caja y Tesorería un caso de uso de transferencia y un adaptador Django que bloquea las dos cajas, vuelve a validar las reglas y persiste el registro más sus dos movimientos. Exponerlo por una API delgada y una pantalla Vue independiente que no dependa de que el actor tenga caja propia.

**Tech Stack:** Django, Django REST Framework, Django migrations, Vue 3, Vue Router, Vitest.

**Spec:** `docs/superpowers/specs/2026-10-13-transferencias-entre-cajas-design.md`

## Global Constraints

- Solo `superadmin` y `administracion` pueden iniciar transferencias.
- Origen y destino deben ser cajas distintas, abiertas y correspondientes a la fecha operativa actual.
- La persona debe tener alcance autorizado sobre ambas sucursales. Un usuario con alcance limitado opera dentro de su sucursal; el cruce Posadas/Eldorado requiere acceso a ambas.
- El importe representa efectivo físico, debe ser mayor que cero y no puede superar el efectivo esperado disponible en origen.
- El destino se acredita automáticamente al confirmar; no requiere confirmación posterior del cajero receptor.
- El débito, el crédito, la transferencia y su evento de auditoría se guardan en una sola transacción.
- Los movimientos enlazados deben reflejarse en los saldos y cierres existentes: débito como pase de salida y crédito como ingreso de efectivo.
- Las cajas cerradas no se modifican. No se incluye en este alcance anular o editar transferencias ya confirmadas.
- Los modelos existentes en `core.models` siguen en transición; no se presenta el contexto como completamente aislado.

## Review Focus

- Un importe válido justo igual al efectivo esperado de origen se acepta; uno mayor se rechaza bajo bloqueo — Task 2 adapter test.
- Dos solicitudes concurrentes no pueden gastar dos veces el mismo efectivo disponible — Task 2 PostgreSQL concurrency test, alongside the deterministic locking-order adapter test.
- Un actor con alcance de una sucursal no puede consultar ni transferir cajas de otra, aunque envíe sus IDs — Task 3 API test.
- Una caja que se cerró o cambió de fecha entre la consulta y el POST se rechaza sin crear ningún registro — Task 2 adapter test.
- El dueño de la caja no se confunde con el administrador que ejecutó el traspaso — Task 3 evidence/API test and Task 5 detail test.

---

### Task 1: Define pure transfer rules and command

**Files:**
- Create: `backend/core/contexts/caja/domain/transferencia_caja.py`
- Create: `backend/core/contexts/caja/application/transferir_entre_cajas.py`
- Test: `backend/core/test_transferencias_caja.py`

**Interfaces:**
- Produces `SolicitudTransferenciaCaja(origen_id: int, destino_id: int, importe: Decimal, motivo: str)` and `validar_solicitud_transferencia(solicitud) -> None`.
- Produces `TransferirEntreCajas(repository).execute(*, actor, solicitud)`, with repository port method `transferir(*, actor, solicitud) -> object`.

- [ ] **Step 1: Write domain tests** named `test_rechaza_origen_igual_a_destino`, `test_rechaza_importe_cero_o_negativo`, `test_rechaza_motivo_vacio`, and `test_acepta_solicitud_valida`; assert the rejected values raise `TransferenciaCajaError` and valid input passes.
- [ ] **Step 2: Run the domain tests and verify they fail** with the missing domain module or functions.

Run: `.\.venv\Scripts\python.exe backend\manage.py test core.test_transferencias_caja.TransferenciaCajaDominioTests`

Expected: FAIL because the transfer domain and use case do not exist.

- [ ] **Step 3: Implement the pure domain rules and application command/port** in the two new context files; keep imports free of Django, DRF, ORM, and HTTP.
- [ ] **Step 4: Run the domain tests and verify they pass.**

Run: `.\.venv\Scripts\python.exe backend\manage.py test core.test_transferencias_caja.TransferenciaCajaDominioTests`

Expected: PASS.

- [ ] **Step 5: Commit** the domain, application, and tests.

### Task 2: Persist an atomic transfer and its paired movements

**Files:**
- Modify: `backend/core/models.py`
- Create: generated migration after the current `0017_cuota_desglose_movimiento_comprobante.py`
- Create: `backend/core/contexts/caja/infrastructure/django_transferencia_caja_repository.py`
- Modify: `backend/core/test_transferencias_caja.py`

**Interfaces:**
- Produces model `TransferenciaCaja` with unique `numero_comprobante` (`TRF-` plus the ID padded to eight digits), origin and destination `CajaDiaria`, actor, positive amount, required reason (maximum 180 characters), and creation timestamp.
- Adds nullable `MovimientoCaja.transferencia` relation so the two existing ledger entries point to the same transfer.
- Produces `DjangoTransferenciaCajaRepository.transferir(*, actor, solicitud) -> TransferenciaCaja`.

- [ ] **Step 1: Write adapter tests** named `test_guarda_pase_y_entrada_en_una_transferencia`, `test_bloquea_ambas_cajas_en_orden_de_id`, `test_rechaza_caja_cerrada_o_fecha_distinta_sin_escrituras`, `test_rechaza_importe_superior_al_efectivo_esperado`, `test_acepta_importe_igual_al_efectivo_esperado`, and `test_error_al_guardar_el_destino_revierte_la_operacion`; add `TransferenciaCajaConcurrenciaTests.test_dos_transferencias_concurrentes_no_sobrepasan_efectivo_origen` using separate database connections on PostgreSQL. Assert linked movement types/amounts, stable ascending lock order for both caja IDs, no partial rows, and unchanged totals on rejection; the concurrency test must assert that only one simultaneous transfer succeeds when the source holds exactly one transfer amount.
- [ ] **Step 2: Run the adapter tests and verify they fail** because the persistence model and adapter are missing.

Run: `.\.venv\Scripts\python.exe backend\manage.py test core.test_transferencias_caja.TransferenciaCajaAdaptadorTests core.test_transferencias_caja.TransferenciaCajaConcurrenciaTests`

Expected: FAIL because the model and adapter do not exist.

- [ ] **Step 3: Add the transfer model and migration.** The transfer record is the immutable evidence root; both cash movements use `medio=efectivo`, source `tipo=pase`, destination `tipo=ingreso`, and the same transfer relation. Generate the migration with `.\.venv\Scripts\python.exe backend\manage.py makemigrations core`.
- [ ] **Step 4: Implement the transactional Django adapter.** Lock the two caja rows in ascending primary-key order; reload movements while locked; validate both are open for `timezone.localdate()` and the source expected cash covers the requested amount; create the transfer and both movements within one `transaction.atomic` boundary. Set the existing `recibido_por` field on the source `pase` to the destination caja's user as the named custodian; this does not create a separate confirmation step. On an injected persistence error, all records must roll back.
- [ ] **Step 5: Run the adapter tests and verify they pass.**

Run: `.\.venv\Scripts\python.exe backend\manage.py test core.test_transferencias_caja.TransferenciaCajaAdaptadorTests core.test_transferencias_caja.TransferenciaCajaConcurrenciaTests`

Expected: PASS, including no partial write when a leg fails. Run the concurrency test against PostgreSQL; skip it on SQLite because SQLite does not implement row-level `SELECT FOR UPDATE` locks.

- [ ] **Step 6: Commit** the model, migration, adapter, and tests.

### Task 3: Expose scoped API and audit evidence

**Files:**
- Create: `backend/core/contexts/caja/presentation/__init__.py`
- Create: `backend/core/contexts/caja/presentation/http/__init__.py`
- Create: `backend/core/contexts/caja/presentation/http/transferencias_caja.py`
- Modify: `backend/core/contexts/caja/infrastructure/django_transferencia_caja_repository.py`
- Modify: `backend/core/urls.py`
- Modify: `backend/core/test_transferencias_caja.py`

**Interfaces:**
- `GET /api/transferencias-caja/cajas-abiertas/` returns only current-day open cajas inside the actor's authorized branch scope, including caja ID, branch, cashier, and expected cash.
- `POST /api/transferencias-caja/` accepts `origen_id`, `destino_id`, `importe`, `motivo`; actor identity comes only from authentication.
- `GET /api/transferencias-caja/` returns recent transfer evidence limited to the branches the actor may view.
- A successful POST response includes transfer ID/reference, timestamp, actor, source/destination summaries, amount, reason, and both movement IDs.

- [ ] **Step 1: Write API tests** named `test_admin_global_puede_transferir_entre_sucursales`, `test_admin_limitado_no_consulta_ni_transfiere_fuera_de_su_sucursal`, `test_solo_administracion_y_superadmin_pueden_transferir`, and `test_respuesta_identifica_actor_y_los_dos_movimientos`; assert status codes, scope filtering, and complete evidence.
- [ ] **Step 2: Run the API tests and verify they fail** because the transfer routes do not exist.

Run: `.\.venv\Scripts\python.exe backend\manage.py test core.test_transferencias_caja.TransferenciaCajaApiTests`

Expected: FAIL because the transfer API routes do not exist.

- [ ] **Step 3: Implement thin HTTP adapters and URL routes.** Enforce admin roles; derive allowed branch IDs from the authenticated profile; validate both caja IDs against those authorized open cajas before invoking the use case. Expose the authenticated actor as the transfer executor.
- [ ] **Step 4: Extend the transfer repository's atomic transaction to record one Caja audit event** through the existing `RegistrarEventoAuditoria` application contract and `DjangoAuditoriaRepository` adapter; include origin, destination, amount, reason, actor, and transfer reference in evidence. A failure to write the audit event must roll back the transfer and both ledger entries.
- [ ] **Step 5: Run the API tests and verify they pass.**

Run: `.\.venv\Scripts\python.exe backend\manage.py test core.test_transferencias_caja.TransferenciaCajaApiTests`

Expected: PASS; unauthorized IDs are not disclosed and no rejected request creates a transfer.

- [ ] **Step 6: Commit** the HTTP adapter, routes, audit integration, and tests.

### Task 4: Build the independent transfer screen

**Files:**
- Create: `frontend/src/views/TransferenciasCajaView.vue`
- Create: `frontend/src/composables/useTransferenciasCaja.js`
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/components/layout/AppSidebar.vue`
- Create: `frontend/src/views/TransferenciasCajaView.test.js`

**Interfaces:**
- `useTransferenciasCaja()` exposes `cajasAbiertas`, `transferencias`, `loading`, `error`, `load()`, and `transferir({ origen_id, destino_id, importe, motivo })`.
- Route `/caja/transferencias` is restricted to `superadmin` and `administracion` and does not load `/cajas/hoy/` for the current actor.

- [ ] **Step 1: Write view tests** named `test_admin_sin_caja_propia_puede_cargar_transferencias`, `test_exige_origen_destino_importe_y_motivo`, `test_no_permite_seleccionar_la_misma_caja`, and `test_actualiza_historial_y_muestra_comprobante_al_confirmar`; mock only the composable/API boundary.
- [ ] **Step 2: Run the view tests and verify they fail** because the view and composable do not exist.

Run: `npm --prefix frontend run test -- src/views/TransferenciasCajaView.test.js`

Expected: FAIL because the transfer view does not exist.

- [ ] **Step 3: Implement the composable and view.** Load open caixas and recent transfers independently of the actor's own box; present source/destination, amount, and reason; show a confirmation summary before POST; refresh the history and show the returned transfer reference after success; render loading, empty, and error states accessibly.
- [ ] **Step 4: Add the restricted route and Caja sidebar entry.** Keep the new screen separate from the current daily cash workflow.
- [ ] **Step 5: Run the view tests and verify they pass.**

Run: `npm --prefix frontend run test -- src/views/TransferenciasCajaView.test.js`

Expected: PASS, including the actor-without-own-box flow.

- [ ] **Step 6: Commit** the view, composable, navigation, and tests.

### Task 5: Show transfer evidence from both caja ledgers

**Files:**
- Modify: `backend/core/serializers.py`
- Modify: `backend/core/test_transferencias_caja.py`
- Modify: `frontend/src/components/ui/OperacionDetalle.vue`
- Modify: `frontend/src/components/ui/OperacionDetalle.test.js`
- Modify: `frontend/src/components/caja/CajaMovimientos.vue` only if a transfer reference needs a visible row label/search token.
- Modify: `frontend/src/views/ReportesView.vue` only if the history movement detail DTO requires additional mapping.

**Interfaces:**
- Movement response adds a read-only transfer summary with transfer reference, counterpart caja/branch/cashier, reason, and executor; permissions remain inherited from the caja/movement query scope.
- `OperacionDetalle` displays these fields for both source and destination movements without changing payment receipt behavior.

- [ ] **Step 1: Write backend serialization test** named `test_movimiento_transferencia_expone_resumen_del_otro_caja_y_ejecutor` and detail tests named `test_muestra_comprobante_origen_destino_y_ejecutor` and `test_movimiento_sin_transferencia_conserva_detalle_actual`; assert the API exposes the counterpart and executor, evidence appears for transfer movements, and ordinary operations do not show placeholder transfer fields.
- [ ] **Step 2: Run the frontend detail test and verify it fails** because the transfer summary is not rendered.

Run: `npm --prefix frontend run test -- src/components/ui/OperacionDetalle.test.js`

Expected: FAIL because the transfer summary is not rendered.

- [ ] **Step 3: Run the backend serialization test and verify it fails** because the movement serializer does not expose the transfer summary.

Run: `.\.venv\Scripts\python.exe backend\manage.py test core.test_transferencias_caja.TransferenciaCajaSerializerTests`

Expected: FAIL because the read-only transfer summary is not serialized.

- [ ] **Step 4: Add the read-only transfer summary to movement serialization** and render it in `OperacionDetalle`; keep source/destination as existing movement signs/types and preserve normal details for all other operations.
- [ ] **Step 5: Run detail tests and the backend transfer API tests.**

Run: `npm --prefix frontend run test -- src/components/ui/OperacionDetalle.test.js`

Expected: PASS.

Run: `.\.venv\Scripts\python.exe backend\manage.py test core.test_transferencias_caja`

Expected: PASS.

- [ ] **Step 6: Commit** the serializer, detail view, and tests.

### Task 6: Verify the integrated feature

**Files:**
- Verify the full changeset; modify only files required to fix failures.

- [ ] **Step 1: Run backend checks and the complete relevant backend suite.**

Run: `.\.venv\Scripts\python.exe backend\manage.py check`

Expected: `System check identified no issues`.

Run: `.\.venv\Scripts\python.exe backend\manage.py test core.test_transferencias_caja core.test_desglose_comprobantes`

Expected: PASS.

- [ ] **Step 2: Run the frontend suite and production build.**

Run: `npm --prefix frontend run test`

Expected: PASS.

Run: `npm --prefix frontend run build`

Expected: Vite exits successfully and produces the frontend bundle.

- [ ] **Step 3: Run migration and whitespace checks.**

Run: `.\.venv\Scripts\python.exe backend\manage.py makemigrations --check --dry-run`

Expected: no model changes missing from migrations.

Run: `git diff --check`

Expected: no whitespace errors.

- [ ] **Step 4: Review authorization, inward dependencies, and the final diff.** Confirm a limited-scope administrator cannot infer or affect another branch's caja, two linked movements and one audit record commit or roll back together, and every transfer can be traced from either caja movement.

## Execution notes

- Keep unrelated user-owned untracked files out of commits.
- Do not move legacy models or introduce a broker, CQRS, or a broad `shared` abstraction.
- The feature's database transaction intentionally covers the transfer aggregate and its two cash ledger entries because the approved invariant requires both sides to exist together.
- Report automated checks separately from visual and production validation.
