# Backlog MVP IPAC

## Estado al 26 de septiembre de 2026

IPAC ya implementa el circuito operativo principal de Administración, Tesorería, Caja y Consulta. La información funcional y el alcance se mantienen en un monolito modular: varios modelos Django siguen viviendo en `backend/core/models.py` y los contextos nuevos están en transición.

## Disponible

### Alumnos y trayectoria

- Directorio, búsqueda, ficha, alta/edición, estado y alcance por sucursal.
- Catálogos de carreras/cursos y matrículas.
- Cuenta corriente con cuotas, aplicaciones de pagos, recibos, saldos a favor y anulación autorizada.
- La respuesta de estado de cuenta incluye saldo pendiente, vencido y por vencer; las cuotas anuladas y sin saldo no integran esos importes.

### Conceptos y cobranzas

- Conceptos cobrables, descuentos y recargos.
- Evaluación de elegibilidad y generación individual o masiva de cuotas, con control de sucursal y duplicados.
- Registro manual, automático y como pago a cuenta; aplicación de excedentes y protección frente a caja cerrada, cuota ajena o importe inválido.
- Recibo numerado, consulta/imprenta y anulación trazable.
- La elegibilidad y la generación tienen casos de uso y adaptadores del contexto Cobranzas; los modelos ORM permanecen en `core` durante la transición.

### Caja y Tesorería

- Caja diaria por usuario y sucursal; ingresos, egresos, retiros, pases, movimientos de pago y saldo trasladado.
- Cierre con efectivo esperado, contado y diferencia.
- Historial, detalle, roles y alcance por sucursal; las operaciones sobre cajas ajenas se rechazan.
- El caso de uso de cierre y su adaptador Django ya están separados.

### Reportes y administración

- Dashboard con indicadores existentes y período actual.
- Categorías de reportes: resumen, cobranzas, morosidad, alumnos y caja; filtros y navegación por URL.
- Exportación XLSX de los tipos disponibles. La exportación de Caja aplica fecha, sucursal y usuario dentro del alcance autorizado. Resumen no ofrece un botón de exportación que descargue otro reporte.
- Usuarios, roles y sucursal/permisos configurables.
- Importación de planillas con vista previa y validación.

## Pendiente

### Validación operativa adicional

- Repetir el checklist de recorridos con cada perfil y datos ficticios ante cambios relevantes.
- Completar evaluación manual con lector de pantalla, alto contraste y dispositivos reales. Las pruebas de este slice no certifican WCAG para todo el producto.
- Validar Docker Compose en un equipo/entorno con Docker y revisar backup/restore.

### Evolución arquitectónica

- Extraer gradualmente las reglas y modelos heredados por contexto cuando exista necesidad; no mover tablas en bloque.
- Mantener contratos de API y pruebas de permisos por sucursal al evolucionar los contextos.

### Fuera del MVP acordado

- Facturación ARCA.
- Mercado Pago, QR o conciliación externa.
- Portal del alumno/responsable.
- Gestión pedagógica completa.

## Siguiente acción

Usar [QA_RECORRIDOS_IPAC_2026-09-26.md](QA_RECORRIDOS_IPAC_2026-09-26.md) como checklist de aceptación para los flujos y sus evidencias locales. Registrar hallazgos nuevos allí y revisar este backlog con negocio antes de sumar reglas o métricas.
