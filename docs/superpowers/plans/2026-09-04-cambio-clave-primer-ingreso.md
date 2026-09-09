# Cambio obligatorio de clave en el primer ingreso — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar cambio obligatorio de clave en el primer ingreso y habilitar de forma segura las cinco cuentas solicitadas en IPAC.

**Architecture:** El comportamiento se incorpora incrementalmente dentro del monolito modular. La bandera vive en `PerfilUsuario`; la operación de cambio se coordina desde `contexts/identidad/application`, la API traduce HTTP y el frontend sólo coordina sesión y presentación. El bloqueo se centraliza en la política de permisos existente para impedir acceso operativo mientras la obligación esté activa.

**Tech Stack:** Django, Django REST Framework, PostgreSQL/SQLite para pruebas, Vue 3, Vite, Vitest, Docker Compose y despliegue controlado por SSH en FASA 189.

---

### Task 1: Backend failing tests for forced password change

**Files:**
- Modify: `backend/core/tests.py`
- Test behavior: model serialization, login response, protected endpoint blocking, password change success/failure, and existing-user regression.

- [ ] **Step 1: Add the failing backend tests**

Add tests that create a user with `PerfilUsuario(debe_cambiar_clave=True)` and assert:

```python
def test_login_reports_password_change_required(self):
    response = self.client.post(
        "/api/auth/login/",
        {"username": "temporal", "password": "Temporal-IPAC-2026!"},
    )
    self.assertEqual(response.status_code, status.HTTP_200_OK)
    self.assertTrue(response.data["debe_cambiar_clave"])

def test_pending_user_cannot_access_operational_endpoint(self):
    self.client.force_authenticate(self.pending_user)
    response = self.client.get("/api/alumnos/")
    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    self.assertEqual(response.data["code"], "password_change_required")

def test_pending_user_can_change_password_and_is_unblocked(self):
    self.client.force_authenticate(self.pending_user)
    response = self.client.post(
        "/api/auth/change-password/",
        {
            "new_password": "Nueva-Clave-IPAC-2026!",
            "new_password_confirmation": "Nueva-Clave-IPAC-2026!",
        },
    )
    self.assertEqual(response.status_code, status.HTTP_200_OK)
    self.pending_user.refresh_from_db()
    self.pending_user.perfil.refresh_from_db()
    self.assertTrue(self.pending_user.check_password("Nueva-Clave-IPAC-2026!"))
    self.assertFalse(self.pending_user.perfil.debe_cambiar_clave)
    self.assertEqual(self.client.get("/api/alumnos/").status_code, status.HTTP_200_OK)

def test_change_password_rejects_mismatch_and_short_password(self):
    self.client.force_authenticate(self.pending_user)
    mismatch = self.client.post(
        "/api/auth/change-password/",
        {"new_password": "Nueva-Clave-IPAC-2026!", "new_password_confirmation": "Otra-Clave"},
    )
    self.assertEqual(mismatch.status_code, status.HTTP_400_BAD_REQUEST)
    short = self.client.post(
        "/api/auth/change-password/",
        {"new_password": "123", "new_password_confirmation": "123"},
    )
    self.assertEqual(short.status_code, status.HTTP_400_BAD_REQUEST)
```

Use the existing `APITestCase` fixtures and add a separate pending user without modifying current test users.

- [ ] **Step 2: Run the focused backend tests and verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe backend\manage.py test core.tests --keepdb
```

Expected: FAIL because the profile field, response flag, endpoint, and permission response do not yet exist.

### Task 2: Persist the identity flag and application use case

**Files:**
- Modify: `backend/core/models.py`
- Create: `backend/core/migrations/0015_perfilusuario_debe_cambiar_clave.py`
- Create: `backend/core/contexts/identidad/__init__.py`
- Create: `backend/core/contexts/identidad/application/__init__.py`
- Create: `backend/core/contexts/identidad/application/cambiar_clave.py`
- Test: `backend/core/tests.py`

- [ ] **Step 1: Add the profile field**

Add to `PerfilUsuario`:

```python
debe_cambiar_clave = models.BooleanField(default=False)
```

The default keeps all existing users usable. Generate migration `0015` from the model without altering existing data.

- [ ] **Step 2: Implement the minimal application operation**

Create `CambiarClave` with one `execute(*, user, profile, new_password)` method. It calls `user.set_password(new_password)`, saves only the password field, sets `profile.debe_cambiar_clave = False`, and saves only the flag and timestamp. Keep this module independent of HTTP/DRF and do not add a new repository abstraction for this single legacy adapter operation.

- [ ] **Step 3: Apply migration and rerun the focused tests**

Run:

```powershell
.\.venv\Scripts\python.exe backend\manage.py migrate
.\.venv\Scripts\python.exe backend\manage.py test core.tests --keepdb
```

Expected: tests still fail only at the not-yet-wired API/policy assertions.

### Task 3: API, serializer, and centralized permission enforcement

**Files:**
- Modify: `backend/core/serializers.py`
- Modify: `backend/core/permissions.py`
- Modify: `backend/core/views.py`
- Modify: `backend/core/urls.py`
- Test: `backend/core/tests.py`

- [ ] **Step 1: Expose the flag without exposing credentials**

Add `debe_cambiar_clave` to `PerfilUsuarioSerializer` as a read-only field. In `UserSerializer.create`, set the flag to `bool(password)` after hashing the supplied password. In `UserSerializer.update`, set it to `True` whenever a new password is supplied. Never include a password or temporary password in serialized output, audit snapshots, or logs.

- [ ] **Step 2: Add change-password validation and endpoint**

Create `ChangePasswordSerializer` with `new_password` and `new_password_confirmation`. Require equality and call Django’s configured `validate_password` for the new value. Add `ChangePasswordView` with `IsAuthenticated`; invoke `CambiarClave` and return `{"debe_cambiar_clave": false}`. `LoginView` adds the flag to its token response. Register `auth/change-password/` before the router URLs.

- [ ] **Step 3: Block operational permissions while pending**

At the start of `RolePermission.has_permission`, after confirming the profile exists, return `False` for `profile.debe_cambiar_clave`. This blocks the existing role-protected operational APIs while leaving `/auth/me/` and `/auth/change-password/` available because they use their own permission classes. Add a consistent DRF exception response with `code=password_change_required` if the current project already normalizes permission errors; otherwise retain the existing 403 response and add the code through a small permission denial handler without touching unrelated endpoints.

- [ ] **Step 4: Run backend tests to verify GREEN**

Run:

```powershell
.\.venv\Scripts\python.exe backend\manage.py check
.\.venv\Scripts\python.exe backend\manage.py test core
```

Expected: all existing and new backend tests pass.

### Task 4: Frontend forced-change flow

**Files:**
- Create: `frontend/src/views/ChangePasswordView.vue`
- Modify: `frontend/src/composables/useAuth.js`
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/views/LoginView.vue`
- Create or modify: `frontend/src/views/ChangePasswordView.test.js`
- Modify: `frontend/src/composables/useAuth.test.js`

- [ ] **Step 1: Add failing frontend tests**

Cover that a successful login with `perfil.debe_cambiar_clave=true` exposes the state, the router sends the user to `/cambiar-clave`, mismatched values show an error without an API call, and a successful change refreshes the current user and navigates to `/dashboard`.

- [ ] **Step 2: Implement the auth composable operation**

Add `changePassword(newPassword, confirmation)` to call `POST /auth/change-password/`, then call `fetchCurrentUser()` so the flag is cleared in memory. Expose a computed/read-only `mustChangePassword` derived from `user.value?.perfil?.debe_cambiar_clave`.

- [ ] **Step 3: Add the standalone route and guard**

Add top-level route `/cambiar-clave` outside `AppShell`. In the guard, hydrate the authenticated user before checking the flag. Redirect pending users to `/cambiar-clave`; redirect users without a pending flag away from that route to `/dashboard`; preserve role checks for all other routes.

- [ ] **Step 4: Implement the blocking screen**

Create a desktop/mobile-accessible form with two password inputs, clear instructions, submit loading state, validation, normalized API error, and no operational navigation. On success route to the dashboard. Do not persist the temporary or new password in application state beyond the request.

- [ ] **Step 5: Run frontend tests and build**

Run:

```powershell
npm --prefix frontend run test -- --run
npm --prefix frontend run build
```

Expected: all tests pass and the Vite build completes.

### Task 5: Full local verification and controlled production deployment

**Files:**
- Review only: `docs/DEPLOY_PRODUCCION.md`, `scripts/deploy-production.sh`, `docker-compose.yml`
- No credentials or `.env` files may be committed or copied from the local checkout.

- [ ] **Step 1: Run repository verification**

Run:

```powershell
git diff --check
.\.venv\Scripts\python.exe backend\manage.py check
.\.venv\Scripts\python.exe backend\manage.py test core
npm --prefix frontend run build
```

- [ ] **Step 2: Verify remote target and current state**

Use SSH to `fasa_189` and confirm the IPAC checkout path, current branch/commit, running Compose services, and database container. Confirm the existing `.env` and named volumes will be preserved. Stop if the remote target is not FASA 189 or if the current checkout diverges.

- [ ] **Step 3: Create a PostgreSQL backup before deployment**

Create a timestamped custom-format dump from the running IPAC PostgreSQL container on FASA 189, record file size and SHA-256, and confirm the dump command succeeded. Do not use `docker compose down -v` or recreate volumes.

- [ ] **Step 4: Deploy the verified commit**

Fast-forward the remote checkout only after the target check, run the repository’s production deploy script, and monitor migrations/container recreation. Preserve remote `.env`, PostgreSQL volume, and media volume.

- [ ] **Step 5: Verify the live application before account creation**

Require all of: migration `0015` applied, backend `check` passes in the container, backend health response, frontend health response, public HTTPS home, and visible login page. If any fails, stop before creating users.

### Task 6: Create and verify the five requested users

**Users and payload policy:**

| Username | Name | Role | Global access | Branch |
|---|---|---|---:|---|
| `mario.osten` | Osten Mario Ruben | `superadmin` | yes | Posadas |
| `claudio.rodriguez` | Rodriguez Aguero Claudio | `superadmin` | yes | Posadas |
| `zulma.rodriguez` | Rodriguez Zulma | `administracion` | yes | Posadas |
| `laura.acosta` | Acosta Laura | `tesoreria` | yes | Posadas |
| `gerardo.casco` | Casco Gerardo | `caja` | no | Posadas |

- [ ] **Step 1: Generate temporary credentials locally**

Generate one strong temporary password per user with a cryptographically secure generator. Keep them only in the current secure task context; never write them to the repository, browser storage, logs, or audit fields.

- [ ] **Step 2: Confirm no duplicate usernames on the live directory**

Read the live user directory and stop if any proposed username already exists. Do not overwrite or deactivate an existing account without a separate instruction.

- [ ] **Step 3: Create the accounts through the live admin UI/API**

Create each account with `is_active=true`, the mapped role/scope, Posadas, and its temporary password. The backend must set `debe_cambiar_clave=true` automatically. Do not send email from the system.

- [ ] **Step 4: Verify the live directory and forced-change behavior**

Confirm all five rows show the intended role, scope, branch, and active state. Perform a controlled login check for at least one account, verify redirection to `/cambiar-clave`, verify operational access is blocked before the change, and complete the change with a separate test password. Do not change all five real users’ passwords during verification.

- [ ] **Step 5: Prepare the reply email**

Draft a Spanish response listing the five usernames, their role/scope, the temporary-key procedure, and a placeholder for each temporary key. Do not send it because the request is to provide the email for answering, not to transmit credentials.

### Task 7: Final review and handoff

- [ ] **Step 1: Review the diff and status**

Confirm only intended tracked files changed, unrelated untracked files remain untouched, and `git diff --check` is clean.

- [ ] **Step 2: Report evidence and limitations**

Separate automated tests, live deployment evidence, and user-visible browser evidence. State explicitly whether all five first-login flows were individually tested and whether any email was sent.
