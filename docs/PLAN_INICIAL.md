# Plan Inicial IPAC

## Resumen

Inicializar el proyecto IPAC como una aplicacion web administrativa para IPAC Posadas y Eldorado, orientada a administracion, tesoreria y cobranzas.

Por ahora este repositorio contiene solo documentacion inicial. No se crea todavia backend, frontend, Docker, scripts ni estructura de aplicacion.

## Stack acordado

- Backend: Django + Django REST Framework.
- Frontend: Vue + Vite.
- Base de datos: PostgreSQL para produccion.
- Deploy previsto: Docker Compose con script manual por SSH.

## Alcance MVP

La primera version funcional debera cubrir:

- Usuarios con roles y visibilidad por sucursal.
- Sucursales Posadas y Eldorado.
- Alumnos con datos de contacto, estado y sucursal.
- Carreras/cursos y conceptos cobrables.
- Matricula y generacion de cuotas.
- Descuentos por convenio y recargos.
- Registro de pagos, pagos a cuenta y saldos.
- Estado de cuenta del alumno.
- Caja por usuario y sucursal.
- Ingresos, egresos, retiros, pases, cierres y arqueos.
- Recibos y exportaciones basicas a Excel/PDF.
- Reportes basicos de deuda, caja y pagos.

## Estrategia Docker y deploy futura

La implementacion debera prepararse para correr completa con Docker Compose.

Servicios previstos:

- Backend Django/DRF.
- Frontend Vue servido por Nginx o equivalente.
- PostgreSQL con volumen persistente.
- Volumen persistente para archivos media si el sistema los requiere.

Deploy previsto:

- Script manual por SSH en el servidor.
- Pull del repositorio.
- Backup previo de base de datos cuando corresponda.
- Build de imagenes.
- Levantado con `docker compose`.
- Migraciones Django.
- Verificacion de estado de contenedores.

Coolify y GitHub Actions quedan diferidos hasta definir servidor, credenciales y necesidades reales de operacion.

## Funcionalidades diferidas

- Facturacion ARCA.
- Mercado Pago, QR y conciliacion automatica.
- Portal del alumno o responsable.
- Gestion pedagogica/académica completa.
- Migracion completa desde Excel hasta recibir datos reales o anonimizados.
- Automatizacion de deploy con GitHub Actions.
- Administracion visual de deploy con Coolify.

## Supuestos

- El sistema sera web y centralizado para ambas sucursales.
- El desarrollo priorizara administracion, tesoreria y cobranzas.
- PostgreSQL sera la base productiva recomendada.
- Docker Compose sera el camino inicial de operacion y deploy.
- La propuesta comercial vigente queda como referencia externa y no se sube al repositorio en este paso.

## Proximos pasos

1. Confirmar datos reales o anonimizados de alumnos, cuotas, pagos y conceptos.
2. Definir usuarios iniciales, roles y permisos por sucursal.
3. Inicializar backend Django/DRF.
4. Inicializar frontend Vue/Vite.
5. Agregar Docker Compose para desarrollo y produccion.
6. Construir el primer flujo funcional: login, sucursales, alumnos y conceptos base.
