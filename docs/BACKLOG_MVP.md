# Backlog MVP IPAC

## Estado actual

Base ejecutable inicial:

- Login con usuario demo.
- Sucursales Posadas y Eldorado.
- CRM de alumnos con alta, edicion, busqueda y ficha lateral.
- Carreras/cursos y conceptos cobrables iniciales.
- Registro de pagos.
- Estado de cuenta simple por alumno.
- Caja diaria con movimientos, pagos automaticos y cierre con diferencia.
- Backend de matriculas, cuotas, descuentos, recargos, pagos parciales y saldos a favor.
- Docker Compose preparado, pendiente de prueba real en maquina con Docker.

## P0 - Necesario para una demo operativa seria

### Caja diaria - completado

Objetivo: que los pagos registrados alimenten una caja por usuario y sucursal.

Criterios de listo:

- Ver caja del dia por sucursal.
- Registrar ingresos manuales, egresos, retiros y pases.
- Ver pagos del dia dentro de caja.
- Cerrar caja con total esperado, contado y diferencia.
- Impedir o advertir movimientos posteriores a una caja cerrada.

### Conceptos, cuotas y saldos reales - en curso

Objetivo: pasar de saldos demo a deuda calculada con conceptos/cuotas.

Criterios de listo:

- Editar y desactivar conceptos.
- Asociar conceptos a sucursal y carrera/curso.
- Generar cuotas para un alumno o grupo.
- Ver deuda por concepto, pagos aplicados y saldo.
- Soportar pagos a cuenta.

### Recibo de pago - backend completado

Objetivo: que cada pago tenga comprobante util para mostrador.

Criterios de listo:

- Numeracion interna simple.
- Vista imprimible de recibo.
- Datos de alumno, concepto, importe, medio, usuario y sucursal.
- Exportar o imprimir desde el navegador.

Ya disponible en API: numeracion interna inalterable y detalle del comprobante. Pendiente: vista imprimible en el frontend.

## P1 - Necesario para uso interno controlado

### Usuarios y permisos

Objetivo: separar administracion, tesoreria, caja y consulta.

Criterios de listo:

- Alta/edicion de usuarios.
- Rol por usuario.
- Sucursal principal.
- Visibilidad por una o todas las sucursales.
- Permisos minimos por modulo.

### Reportes basicos

Objetivo: responder preguntas operativas sin consultar base de datos.

Criterios de listo:

- Deuda por alumno.
- Deuda por sucursal.
- Pagos por fecha/sucursal/medio.
- Caja diaria y cierres.
- Exportacion basica a Excel/CSV.

### Mejoras CRM alumnos

Objetivo: hacer comoda la operacion diaria.

Criterios de listo:

- Filtros funcionales por estado, deuda, sucursal y carrera.
- Baja/inactivacion de alumno.
- Historial de pagos y acciones.
- Validaciones visibles en formularios.
- Evitar duplicados por DNI/legajo con mensaje claro.

## P2 - Despues de validar el flujo principal

### Migracion de datos

Objetivo: cargar datos reales o anonimizados desde Excel.

Criterios de listo:

- Plantilla esperada de importacion.
- Vista previa de errores.
- Importacion de alumnos, conceptos y saldos iniciales.
- Registro de importaciones realizadas.

### Deploy inicial

Objetivo: publicar una demo estable con Docker Compose.

Criterios de listo:

- Probar Docker Compose en entorno con Docker.
- Definir dominio/host.
- Variables de entorno productivas.
- Backup previo de base de datos.
- Script manual de deploy por SSH.

### Funcionalidades diferidas

- Facturacion ARCA.
- Mercado Pago, QR y conciliacion automatica.
- Portal del alumno o responsable.
- Gestion pedagogica completa.
- Coolify y GitHub Actions.

## Proximo slice recomendado

Completar **cuotas y cuenta corriente real** en el frontend.

El backend ya incorpora matriculas, cuotas por periodo, descuentos, recargos, pagos parciales, aplicaciones de pago y saldos a favor. El siguiente corte debe exponer ese circuito en la ficha del alumno, manteniendo los componentes visuales separados para facilitar el trabajo UX/UI en paralelo.
