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

Planificacion inicial. Todavia no hay implementacion de backend, frontend, Docker ni deploy.

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
