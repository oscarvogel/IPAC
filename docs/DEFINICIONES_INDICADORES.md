# Definiciones de indicadores de IPAC

Estas son las fórmulas implementadas actualmente por `/api/reportes/resumen/`. Se documentan para conservar su significado antes de proponer métricas nuevas.

| Indicador | Definición actual |
|---|---|
| Cobranzas del período | Suma de pagos activos cuya fecha cae entre `desde` y `hasta`, dentro de sucursales autorizadas. El filtro de medio/usuario también afecta esta suma. |
| Cobranzas de hoy | Subconjunto de las cobranzas anteriores con fecha igual a la fecha local del servidor. |
| Cobranzas por medio y sucursal | Desglose de los pagos activos que cumplen el alcance, período y filtros seleccionados. |
| Deuda pendiente | Suma del saldo de cuotas no anuladas de las sucursales autorizadas. No se limita al período de fechas del reporte. |
| Alumnos con deuda | Cantidad de alumnos distintos con al menos una cuota no anulada y saldo positivo. No filtra el estado académico del alumno. |
| Cuotas vencidas | Cantidad de cuotas no anuladas con saldo positivo y vencimiento anterior a la fecha local (`fecha_vencimiento < hoy`). |
| Saldo a favor | Saldo sin aplicar de pagos activos en las sucursales autorizadas. No se limita por fechas, medio o usuario. |
| Saldo neto | Deuda pendiente menos saldo a favor. Un resultado negativo representa saldo a favor neto. |
| Cajas abiertas/cerradas | Cantidad de cajas con fecha dentro del período consultado y sucursal autorizada, agrupadas por estado. |
| Diferencia acumulada de caja | Suma de `total contado - efectivo esperado` para cajas cerradas dentro del período y sucursal autorizada. |

`desde` por defecto es el primer día del mes local actual y `hasta` es hoy. El filtro de sucursal no puede ampliar el alcance del usuario. Los cambios de semántica requieren actualización de este documento y de los contratos/tests asociados.
