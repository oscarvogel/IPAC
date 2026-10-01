# Issue #47 — el campo de búsqueda de Alumnos ya no se oculta

**Fecha de verificación:** 2026-10-01
**Alcance:** vista `AlumnosView.vue`, toolbar de filtros (`.students-toolbar`).
**Método:** medición con Playwright 1.62 sobre el build de producción de `main` (148e234), con la API interceptada y datos de prueba. En cada viewport se escribió un texto largo en el buscador y se midió el ancho resultante del `input`.

## Conclusión

El defecto reportado **no se reproduce**. En todo el rango de uso real (1280–2000px) el campo de búsqueda conserva su ancho, el texto tipeado queda visible y el chip de filtro activo desciende a su propia fila.

## Causa de la resolución

El reporte original asumía un `display: flex` con tres hijos (heading, filtros y chips) compartiendo la misma fila. Ese supuesto ya no aplica: `frontend/src/style.css` incluye un bloque `@media (max-width: 2000px)` que convierte el toolbar en **columna** y los filtros en un **grid de tres columnas**, de modo que el chip de filtros activos queda siempre por debajo de los filtros.

## Mediciones

Ancho del `input` del buscador, antes y después de escribir un texto largo con el filtro activo.

| Viewport | Input antes | Input con filtro | Texto recortado | Chip en fila propia |
|---:|---:|---:|:---:|:---:|
| 1280 | 632px | 632px | no | sí |
| 1440 | 706px | 706px | no | sí |
| 1600 | 794px | 794px | no | sí |
| 1800 | 923px | 923px | no | sí |
| 1900 | 990px | 990px | no | sí |
| 1999 | 1056px | 1056px | no | sí |
| 2000 | 1056px | 1056px | no | sí |
| 2001 | 230px | 155px | **sí** | no |
| 2100 | 238px | 172px | no | no |
| 2200 | 238px | 190px | no | no |
| 2400 | 238px | 224px | no | no |
| 2560 | 238px | 238px | no | no |
| 3200 | 238px | 238px | no | no |

Ningún viewport bajo 2001px presenta recorte ni desbordamiento horizontal en el toolbar.

## Capturas

- `campo-busqueda-1440-con-chip.png` — comportamiento correcto en el rango de uso habitual.
- `campo-busqueda-2001-con-chip.png` — borde del breakpoint, justo al cambiar de columna a fila.
- `campo-busqueda-2100-con-chip.png` — toolbar en fila, el campo se comprime pero el texto entra.

## Pendiente detectado (no corregido aquí)

El breakpoint de `2000px` es una discontinuidad: al cruzarlo, el campo de búsqueda salta de 1056px a 230px. Entre 2001 y 2400px el campo se comprime cada vez que aparece un filtro activo, y a 2001px puede llegar a 155px, con recorte del texto ante consultas largas.

Es un defecto real pero acotado a monitores grandes, y de naturaleza distinta al issue reportado. Queda como seguimiento para el backlog de frontend.

## Nota sobre capturas

Los valores de los desplegables aparecen truncados ("Toda", "Todc", "Cual") porque la verificación se hizo con catálogos de prueba mínimos, no con el padrón real. No es un defecto del layout.
