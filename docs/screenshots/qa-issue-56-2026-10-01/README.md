# Issue #56 — el campo de búsqueda de Alumnos ya no se comprime

**Fecha de verificación:** 2026-10-01
**Alcance:** vista `AlumnosView.vue`, toolbar de filtros (`.students-toolbar`), campo de búsqueda.
**Método:** barrido con Playwright 1.62 sobre el build de producción, con la API interceptada y datos de prueba. En cada viewport se escribió un texto largo en el buscador y se midió el ancho del `input` antes y después, además del desbordamiento horizontal del toolbar.

## Causa raíz

`frontend/src/style.css` define `@media (max-width: 2000px)`, que convierte el toolbar en **columna** y los filtros en un **grid de tres columnas**. Por debajo del breakpoint, los chips de filtros activos caen a su propia fila y el campo de búsqueda queda holgado.

Por encima de 2000px el toolbar vuelve a `display: flex` en fila, y los tres hijos (heading, filtros y chips) compiten por el mismo ancho. Como `.students-search-field` no tenía `min-width`, era el elemento que absorbía toda la compresión: a 2001px quedaba en 155px, con el texto tipeado recortado.

## Corrección

Se agrega un bloque `@media (min-width: 2001px)` que replica, para el layout en fila, lo que el layout en columna ya hace bien:

- `flex-wrap: wrap` en `.students-toolbar`, para que los filtros puedan bajar de línea.
- `flex: 0 0 100%` en `.students-filter-chips`, forzando los chips a su propia fila.
- `min-width: 180px` en `.students-search-field`, como defensa para que el campo nunca baje de un ancho legible.

## Mediciones

| Viewport | Antes (sin filtro) | Antes (con filtro) | Después (con filtro) | Recorte |
|---:|---:|---:|---:|:---:|
| 1280 | 632px | 632px | 632px | no |
| 1440 | 706px | 706px | 706px | no |
| 1600 | 794px | 794px | 794px | no |
| 1800 | 923px | 923px | 923px | no |
| 1999 | 1056px | 1056px | 1056px | no |
| 2000 | 1056px | 1056px | 1056px | no |
| 2001 | 230px | **155px** | **238px** | no |
| 2100 | 238px | 172px | 238px | no |
| 2200 | 238px | 190px | 238px | no |
| 2400 | 238px | 224px | 238px | no |
| 2560 | 238px | 238px | 238px | no |
| 3200 | 238px | 238px | 238px | no |

Ningún viewport presenta recorte de texto ni desbordamiento horizontal en el toolbar. El campo mantiene su ancho al activar un filtro en todo el rango.

## Control de no regresión: Deudores

`DeudoresView.vue` comparte la clase base `.students-toolbar` pero la redefine por completo como grid mediante `.debtors-toolbar`, donde `flex-wrap` es inerte. Se verificó la vista en los mismos 12 viewports:

| Viewport | `display` del toolbar | Overflow | Campo de búsqueda |
|---:|:---:|:---:|---:|
| 1280 | grid | no | 220px |
| 2001 | grid | no | 220px |
| 2400 | grid | no | 220px |
| 3200 | grid | no | 220px |

Sin cambios en Deudores.

## Regresión automatizada

`frontend/src/views/AlumnosToolbarLayout.test.js` fija el contrato CSS: existencia del layout columna hasta 2000px, del bloque `min-width: 2001px` con `flex-wrap`, de los chips ocupando la fila completa, y del `min-width` del campo por encima de 150px.

**Limitación:** jsdom no resuelve media queries ni calcula anchos, así que ese test no puede medir píxeles. Verifica que las reglas existan, no que el layout se pinte bien. La verificación de ancho real es la de este documento, con Playwright sobre el build.

## Capturas

- `alumnos-2001-despues-fix.png` — el viewport que antes recortaba texto.
- `alumnos-2400-despues-fix.png` — toolbar en fila, campo estable.
- `deudores-1440-control.png` y `deudores-2400-control.png` — control de no regresión.

Los desplegables se ven truncados ("Todas las su", "Cualquier sit") porque la medición usa catálogos de prueba mínimos, no el padrón real. Es comportamiento del ancho de columna del filtro, no del campo de búsqueda.
