# IPAC

Sistema web de administracion, tesoreria y cobranzas para IPAC Posadas y Eldorado.

## Objetivo

El proyecto busca reemplazar una operatoria administrativa local por una plataforma web centralizada, accesible desde ambas sucursales, con control de alumnos, cuotas, pagos, caja y reportes.

La primera version se enfocara en administracion, tesoreria y cobranzas. La gestion pedagogica, el portal del alumno y las integraciones externas quedaran para etapas posteriores.

## Stack previsto

- Backend: Django + Django REST Framework.
- Frontend: Vue + Vite.
- Base de datos: PostgreSQL en produccion.
- Deploy previsto: Docker Compose con script manual por SSH.

## Estado del proyecto

Base ejecutable inicial en desarrollo:

- Backend Django + Django REST Framework en `backend/`.
- Frontend Vue + Vite en `frontend/`.
- Docker Compose preparado para PostgreSQL, backend y frontend.
- Primer flujo funcional: login, sucursales, alumnos, carreras/cursos y conceptos cobrables.

## Alcance inicial previsto

- Usuarios, roles y visibilidad por sucursal.
- Sucursales Posadas y Eldorado.
- Alumnos, carreras/cursos y conceptos cobrables.
- Matricula y generacion de cuotas.
- Descuentos, recargos, pagos y pagos a cuenta.
- Estado de cuenta del alumno.
- Caja por usuario y sucursal.
- Recibos, exportaciones y reportes basicos.

## Documentacion

- [Plan inicial](docs/PLAN_INICIAL.md)
- [Backlog MVP](docs/BACKLOG_MVP.md)

## Desarrollo local

### Backend

En Windows usar `py` y el entorno virtual local:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r backend\requirements.txt
.\.venv\Scripts\python.exe backend\manage.py migrate
.\.venv\Scripts\python.exe backend\manage.py seed_initial_data
.\.venv\Scripts\python.exe backend\manage.py createsuperuser
.\.venv\Scripts\python.exe backend\manage.py runserver 0.0.0.0:8000
```

El backend expone la API bajo `http://localhost:8000/api/` y acepta CORS local para `localhost` y `127.0.0.1`.
El seed crea un usuario inicial `admin` / `admin123` salvo que se ajusten `IPAC_SEED_ADMIN_USERNAME` e `IPAC_SEED_ADMIN_PASSWORD`.

### Frontend

```powershell
npm --prefix frontend --strict-ssl=false install
npm --prefix frontend run dev
```

El frontend usa `VITE_API_BASE_URL`; ver `frontend/.env.example`.

### Tests y checks

```powershell
.\.venv\Scripts\python.exe backend\manage.py test core
.\.venv\Scripts\python.exe backend\manage.py check
npm --prefix frontend run build
```

### Importación de alumnos, carreras y cursos

Desde la pantalla `Administración → Cargar datos`, un usuario de Administración puede descargar las plantillas CSV y cargar archivos `.csv` o `.xlsx`. La carga es idempotente, deduplica alumnos por DNI o legajo y devuelve advertencias para datos incompletos o inconsistentes.

También se puede ejecutar desde consola:

```powershell
.\.venv\Scripts\python.exe backend\manage.py import_ipac_excel ".\CARRERAS Y CURSOS 2026.xlsx" --sucursal POS
.\.venv\Scripts\python.exe backend\manage.py import_ipac_excel ".\Alumnos IPAC- Posadas.xlsx" --sucursal POS
```

Las columnas esperadas están documentadas en [docs/plantillas/README.md](docs/plantillas/README.md).

## Docker Compose

Docker no esta disponible actualmente en esta maquina, pero el repo queda preparado para:

```powershell
docker compose up --build
```

Servicios previstos:

- `db`: PostgreSQL con volumen persistente.
- `backend`: Django/DRF + migraciones + seed inicial.
- `frontend`: Vue compilado y servido por Nginx.

Copiar los `.env.example` antes de un despliegue real y ajustar claves, hosts, CORS y credenciales.
