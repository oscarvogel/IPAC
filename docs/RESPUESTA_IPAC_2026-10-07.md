# Respuesta de IPAC a las 5 preguntas — 07/10/2026

Documento de referencia. Traduce cada punto del mail del 01/10/2026 a **qué se
respondió**, **qué falta** y **qué se puede construir hoy con lo que hay**.

- Origen: respuesta de IPAC Instituto, recibida el 07/10/2026 (conservada en
  `docs/SISTEMA vogel.docx`).
- Foto del recibo: `docs/RECIBO_MODELO_ACTUAL_IPAC.png`.
- Acta de la reunión del 24/09/2026: `docs/REUNION_IPAC_2026-09-24_RESUMEN.md`.

---

## Semáforo

| Punto | Qué era | Estado | Qué falta |
|---|---|---|---|
| 1 | Formas de pago y porcentajes | 🟡 Contestado a medias | importe del recargo, sentido de "jueves y viernes" |
| 2 | Foto del recibo | 🟢 **Resuelto** | — (llegó la foto, ver abajo) |
| 3 | Tasa y forma de cálculo del interés | 🟡 Contestado a medias | número exacto de la tasa, base de cálculo |
| 4 | Matriz definitiva de permisos | 🟢 **Contestado** | — |
| 5 | Comprobante de pase entre cajas | 🟢 **Contestado** | — |

IPAC habilitó avanzar con los puntos 3 y 5 *"con un supuesto por defecto y
corregirlo después, siempre que nos confirmen"*.

---

## Punto 1 — Formas de pago y porcentajes

### Lo que respondió

| Dato | Respuesta de IPAC |
|---|---|
| Medios de pago | Condición de venta (contado), factura ARCA (factura electrónica), tarjeta de débito, tarjeta de crédito, cheque, transferencia bancaria, QR, otra, medio de pago electrónico MP |
| Recargo | **Importe fijo** (no porcentaje) |
| Descuento por convenio | 15% o 20% según convenio, aplicado **separando programática de extraprogramática** |
| Excepciones sin recargo | Ahora Estudiantes; Visa del Banco Macro en una sola cuota |
| A qué medios se aplica el recargo | "Siempre", y se registra bajo el concepto **Otros conceptos educativos** |

### Lo que falta y hay que devolver

1. **El importe del recargo.** Dijeron "importe fijo" pero no dieron el monto.
   El acta del 24/09 decía 10%. Si es importe fijo, ¿cuál es la suma? Si el 10%
   era en realidad un porcentaje, hay que corregirlo.
2. **El sentido de "jueves y viernes".** Escribieron *"los días del ahora
   estudiante con visa crédito no se aplica el recargo del 10% — jueves y
   viernes"*. ¿La excepción **solo** aplica jueves y viernes, o aplica siempre y
   jueves/viernes es un extra? Choca con la línea anterior, donde la describen
   sin condición de día.
3. **El recargo al débito.** Ver la sección "Riesgo legal" más abajo.

### Riesgo legal: el recargo al débito

El acta de la reunión del 24/09/2026 deja asentado que **aplicar recargo al pago
con débito es ilegal** y podría derivar en demandas judiciales. La respuesta del
07/10 dice *"el recargo se aplica siempre"* a débito, crédito, QR y MP.

**Decisión tomada: el recargo de débito queda parametrizable y desactivado por
omisión**, hasta que IPAC confirme por escrito. Un interés o recargo mal aplicado
se devuelve con nota de crédito o con demanda; una configuración que se pueda
apagar no deja al Sistema en un estado insostenible.

### Impacto en el código

`Pago.Medio` hoy tiene cinco valores (`efectivo`, `transferencia`, `mercado_pago`,
`tarjeta`, `otro`) y hay que llevar los nueve nombres exactos del recibo. Ojo: la
lista que mandaron mezcla **dos dimensiones** — forma de comprobante (recibo /
factura ARCA) y medio de pago (contado, débito, crédito, cheque, transferencia,
QR, otra, MP). Recomendación: catálogo `MedioPago` con un atributo
`exige_comprobante_fiscal`.

Las excepciones necesitan modelo nuevo: **"Ahora Estudiantes"** es un programa de
tarjeta, no un medio, y **"Visa Banco Macro en una sola cuota"** depende de la
cantidad de cuotas.

---

## Punto 2 — Foto del recibo: resuelto

Llegó la foto (`docs/RECIBO_MODELO_ACTUAL_IPAC.png`). Qué fija:

- **Recibo con "Documento de válido como Factura"**, numerado `N° 0001-000102013`.
- Marca de **DUPLICADO** con casillero.
- Datos del instituto: CUIT 33-79609544-8, *Ing. Brutos: EXENTO*, inicio de
  actividades 04/10/2022.
- **Condiciones de Venta: Contado / Cuenta corriente** — es una casilla del
  recibo, no un medio de pago. Confirma la lectura del punto 1.
- Fila de condición impositiva: *Rec. Inscripto / Exento / Conv. Final / Reg.
  Monotributo / Monot. Social / No Responsable / Monot. Eventual*.
- En el recorte no entra la parte de **forma de pago**: si hace falta el detalle
  de medios, hay que pedir una foto del tramo inferior.

Lo que sigue pendiente es del lado nuestro: adecuar el formato. Ver
[`NOTA_FORMATO_RECIBO_PROVISIONAL.md`](NOTA_FORMATO_RECIBO_PROVISIONAL.md).

---

## Punto 3 — Tasa y forma de cálculo del interés

### Lo que confirmó IPAC

- La tasa mensual es **parametrizable**, porque va a cambiar con la inflación.
- El interés **no se cuenta desde la fecha de vencimiento**: se cuenta desde el
  **día 1 del mes**. Textual: *"las cuotas vencen el día 10, pero el interés se
  cuenta desde el día 1 del mes si se paga al mes siguiente"*.
- **Aplica igual para todas las cuotas.**
- El descuento por convenio (15%/20%) lo calcula el sistema, no se carga a mano.

### Lo que falta

1. **El número exacto de la tasa y desde qué fecha rige.** En la reunión se
   consolidationó un rango de **5,2% a 5,5%**. Mandaron una foto de la planilla
   manual por WhatsApp, que no está en el repo. **No se cargó ninguna tasa por
   omisión**: el sistema calcula, pero el número lo tiene que confirmar IPAC.
2. **Si el interés se suma a la cuota o se emite como concepto separado.** No
   contestaron. Por eso la primera entrega **calcula e informa pero no escribe**.

### Supuestos por defecto

Documentados en `backend/core/contexts/cobranzas/domain/intereses.py` y fijados
por tests. Si la planilla dice otra cosa, se cambian las constantes, no el cálculo.

| # | Supuesto | Por qué | Cómo se revierte |
|---|---|---|---|
| 1 | El interés **no** arranca al vencer: recién cuando la cuota pasa de su mes. Una cuota de marzo vencía el 10 y se paga el 25 → sin interés. | Es la lectura literal de *"si se paga al mes siguiente"*. Con la base desde el vencimiento, el 25/03 pagaría 15 días. | `PoliticaInteres(base_calculo=BASE_DESDE_VENCIMIENTO)` |
| 2 | Se cobran **meses completos**, no días prorrateados (59 días = 1 mes, no 2). | Lectura literal de "tasa mensual", y es la que menos cobra al alumno. | `PoliticaInteres(unidad_calculo=UNIDAD_DIAS)` |
| 3 | Interés **simple**: dos meses son el doble exacto de un mes, sin capitalización. | Es lo que se entiende por "tasa mensual" en un institute. | — |
| 4 | La base es el **saldo pendiente** (`importe - descuento + recargo - pagado`). | Cobrar interés sobre plata ya abonada es un reclamo seguro. | — |

### Lo entregado

| Capa | Dónde |
|---|---|
| Regla pura | `contexts/cobranzas/domain/intereses.py` |
| Tests de la regla | `contexts/cobranzas/domain/test_intereses.py` (34) |
| Tasa parametrizable | `core.TasaInteres` + migración `0018_tasa_interes` |
| Caso de uso (informa, no escribe) | `application/consultar_intereses.py` |
| Adaptadores de lectura | `infrastructure/django_interes_repository.py` |
| API | `GET /api/tasas-interes/` (administrar) y `GET /api/tasas-interes/proyectar/?fecha_evaluacion=AAAA-MM-DD` |
| Pantalla | `Descuentos y recargos` → tercera tarjeta **Interés de las cuotas** (`AjustesCuotasView.vue`) |
| Tests de integración y API | `core/test_intereses.py` (20) |
| Tests de componente | `AjustesCuotasInteres.test.js` (9) |
| Datos de prueba local | `manage.py crear_datos_prueba_intereses` |

`proyectar` va por **GET y no POST** a propósito: no escribe nada, y como POST
caía en `write_roles` (sólo administración) el rol `caja` recibía un 403 sin
poder ver el interés de la cuota que le toca cobrar. Separa consultas de
lectura de comandos que cambian estado.

### Tests de dominio que no se ejecutaban

Al agregar `domain/__init__.py` y `infrastructure/__init__.py` aparecieron en la
suite **57 tests que llevaban tiempo sin correr**: 23 de `test_planificacion_cuotas`,
1 de `test_exportar_cajas` y 33 de `test_intereses`. Sin `__init__.py` la carpeta es
un *namespace package* y el descubrimiento de `manage.py test core` no entra
dentro. Eran justamente los tests puros de dominio, los que fijan las reglas de
negocio: pasaban "en verde" porque nadie los ejecutaba.

---

## Punto 4 — Matriz definitiva de permisos

### Lo que dijo IPAC

| Persona | Rol | Puede |
|---|---|---|
| Ruben Ostén — directivo | ve todo | ambas sedes |
| Claudio Rodríguez Agüero — directivo | ve todo | ambas sedes |
| Zulma | administración | carreras/cursos/diplomaturas, alta y matrícula de alumnos, situaciones, todos los usuarios, movimientos de cajas, caja diaria |
| Laura | administración | **todo lo mismo que Zulma** |
| Casco Gerardo | caja | **sólo cobros de cuotas y su caja diaria** |

- **Sucursal por ahora: sólo Posadas** para Zulma, Laura y Gerardo.
- Casco Gerardo **sólo puede ver el movimiento de su caja**.

### Impacto

Es lo que destrababa el punto 2 de los próximos pasos de la reunión del 24/09
(*"Habilitar alta de alumnos: permisos de Laura y Zulma"*), que estaba
**bloqueado** esperando esta matriz. También alcanza para el informe detallado
de permisos por usuario que quedó pendiente.

El alta de alumnos **ya estaba habilitada en código** para el rol `administracion`:
el bloqueo era que esas personas tenían `superadmin` de prueba en vez del rol que
les corresponde. Es configuración, no código.

### Lo entregado

| Capa | Dónde |
|---|---|
| Regla "el rol caja sólo ve la suya" | `core/access_scope.py` → `scoped_cajas_for_user` |
| Informe y aplicación de la matriz | `manage.py configurar_matriz_permisos` |
| Tests de la matriz | `core/test_matriz_permisos.py` (17) |

```
python manage.py configurar_matriz_permisos             # informe
python manage.py configurar_matriz_permisos --aplicar   # asigna los roles
```

El comando **no crea usuarios**: las personas se dan de alta desde Usuarios y
permisos, que pide la contraseña y la valida. Sólo asigna rol y alcance.

#### Fuga de cajas que encontró la matriz

IPAC lo subrayo dos veces en la respuesta: *"Casco Gerardo solo puede ver los movimientos de su caja"*.
Estaba escrita a mano en **dos** lugares y sólo uno la tenía:

- El listado de cajas filtraba por `usuario`. **Correcto.**
- El **reporte exportable de cajas** filtraba sólo por sucursal. Gerardo podía
  exportar las cajas de todos los demás de Posadas, y además **ampliar el filtro
  pasando el id de otro usuario por query string**.
- El **resumen** contaba las cajas de la sucursal: Gerardo veía "3 abiertas"
  aunque tuviera una sola.

La regla ahora vive en un solo lugar, `scoped_cajas_for_user`, que el listado, el
reporte y el resumen llaman. Verificado en el navegador: el historial de Gerardo
muestra **1 caja** y el resumen **1 abierta**.

#### Decisión pendiente sobre los directivos

Ruben Ostén y Claudio Rodríguez Agüero quedan como `superadmin` con alcance
global, porque es el único rol que hoy ve ambas sedes. **Eso les permite
también administrar usuarios y crear otros superadmins.**

Si IPAC quiere gente que **vea** todo pero no **administre** usuarios, hace falta
un rol nuevo; no conviene resolverlo empujando gente a `superadmin`, que fue
justo el rodeo que la reunión del 24/09 Humor rechazó.

#### Qué sigue abierto

Gerardo ve los **pagos** de todos los cajeros de su sucursal, aunque no vea sus
cajas. Puede ser lo correcto —necesita saber si una cuota ya fue paga para no
cobrar dos veces— pero es una interpretación de qué significa "su caja". Queda
para confirmar con IPAC.

---

## Punto 5 — Comprobante de pase entre cajas

IPAC confirmó los cinco puntos: datos completos (fecha, caja origen, caja destino,
importe, motivo, nombres, número continuo), **conformidad de ambos**,
digital con impresión opcional, y **aplica también al saldo de cierre de caja**.

### Estado real en el código

| Punto | Estado |
|---|---|
| Comprobante por pase y retiro | **Hecho** — `contexts/caja/domain/comprobante_caja.py` |
| Número continuo | **Hecho** — `COM-{id:08d}` |
| Conformidad de quien recibe | **Hecho** — `MovimientoCaja.recibido_por` |
| Digital con impresión opcional | **Hecho** — `GET /api/movimientos-caja/{id}/comprobante/` |
| **Conformidad de quien entrega** | **Falta** — sólo existe `recibido_por` |
| **Saldo de cierre de caja** | **Falta** — `requiere_comprobante` cubre `pase` y `retiro`, no el cierre |

---

## Nada de esto resuelve

- La **URL "Vogel Consultoría"** en el pie impreso no sale de nuestra plantilla:
  la inyecta el navegador. Se corrige en la configuración de impresión de la
  máquina que imprime.
- Las **páginas en blanco** nunca se reprodujeron contra una impresión real y no
  tienen dueño asignado.