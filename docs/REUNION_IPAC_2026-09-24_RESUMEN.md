# Reunión IPAC — 24/09/2026 20:10 (GMT-03:00)

**Tipo:** revisión técnica con IPAC Instituto
**Asistentes:** José Oscar Vogel, Roman Vogel Corach, IPAC Instituto
**Origen:** transcripción automática de la reunión
**Estado del documento:** referencia. La transcripción original se conserva literal al final, sin editar.

Este documento es el **acta de la reunión** y la fuente de verdad de qué quedó
acordado. Se agrega al repo porque varios compromisos NO están en la lista de
"próximos pasos" y se pierden de vista: están solo en la sección de detalles.

Documentos relacionados:

- `docs/SOLICITUD_ENTREGABLES_IPAC_2026-10-01.md` — lo que le pedimos a IPAC después
- `docs/NOTA_FORMATO_RECIBO_PROVISIONAL.md` — por qué el formato del recibo es provisional
- `docs/GUIA_PRUEBA_RAMA_INTEGRADA.md` — qué probar en la tanda actual

---

## Estado de los próximos pasos (contrastado contra `main` al 01/10/2026)

| # | Próximo paso | Responsable | Estado |
|---|---|---|---|
| 1 | Ajustar interfaz de búsqueda en baja resolución | Oscar | **Hecho** — `0957f92` (cierra issue #56) |
| 2 | Habilitar alta de alumnos: permisos de Laura y Zulma | Oscar | **Bloqueado** — espera la matriz definitiva de permisos del contador (punto 4 del mail del 01/10) |
| 3 | Ajustar transferencias de caja con comprobante digital opcional | Oscar | **Hecho** — `23c173d`, endpoint `GET /api/movimientos-caja/{id}/comprobante/` |
| 4 | Permisos de reportes: consultar movimientos de otras cajas | Oscar | **Hecho** — ver `docs/QA_RECORRIDOS_IPAC_2026-09-26.md` y las capturas de la ronda del 30/09 |
| 5 | Informe detallado de permisos por usuario | Oscar + Roman | **Pendiente** — se pidió a IPAC como punto 4 del mail |
| 6 | **IPAC** envía imagen del modelo de recibo | IPAC | **Pendiente** — punto 2 del mail. Es lo que bloquea el formato |
| 7 | Corregir errores de impresión: páginas en blanco y URL visible | Oscar + Roman | **Mal diagnosticado** — ver abajo |
| 8 | **IPAC** envía formas de pago y política de intereses | IPAC | **Pendiente** — punto 1 del mail. Bloquea intereses y recargos |
| 9 | Configurar desglose programático / extraprogramático | Oscar | **Hecho** — `23c173d` + pantalla de carga en la carrera (`8cc78db`) |

### El punto 7 está mal diagnosticado

La reunión registra dos problemas de impresión. Uno se resolvió, el otro **no es
un bug del sistema**:

- **La URL "Vogel Consultoría" en el pie del PDF** no sale de nuestra plantilla.
  La inyecta el navegador al imprimir (título y URL de la pestaña). Se corrige
  en la configuración de impresión del navegador de la máquina que imprime, no
  en código. Quedó asentado en `docs/NOTA_FORMATO_RECIBO_PROVISIONAL.md`.
- **Las páginas en blanco** no se reprodujeron ni se verificaron nunca contra
  una impresión real. Sigue abierto y **no tiene dueño asignado hoy**.

---

## Compromisos que NO están en la lista de próximos pasos

Estos aparecieron en la discusión y no llegaron a la lista de próximos pasos.
Riesgo de que se pierdan.

| Compromiso | Qué dice la reunión | Estado |
|---|---|---|
| **Numerar las cuotas del 1 al 10** | IPAC necesita identificar claramente el número de cuota. Oscar se compromete a ajustar el sistema | **Parcial** — `CarreraCurso.plan_cuotas` existe (el plan de N cuotas), pero **`Cuota` no tiene campo de número**. La cuota generada no sabe cuál es |
| **Descuentos por convenio (ATE, Crucero del Norte 15% / 20%)** | Aplicar durante la matriculación anual | **Parcial** — el catálogo tiene `cuota_convenio_15` / `cuota_convenio_20` y `Cuota` tiene `descuento` + `tipo_descuento` + `motivo_descuento`, pero el descuento es **manual**, no se calcula del convenio |
| **Reporte de deudas y alumnos activos por curso** | Reportes pedidos por el contador | **Pendiente** — compromiso asumido, sin issue |
| **Reimpresión de comprobantes** | Mantener la reimpresión habilitada por si la impresora falla | **Hecho por construcción** — `Pago.numero_recibo` es estable (`REC-{pk:08d}`), volver a pedir el recibo reimprime el mismo número |
| **Cierre de caja diario** | Recomendación de Oscar para no perder tiquecitos de caja chica | **Recomendación operativa**, no es una tarea de código |

### Requisito que se debe cuidar al integrar ARCA

El Ministerio de Educación pide que el total de la cuota figure desglosado en
programático y extraprogramático, y la reunión lo dice explícitamente: **"tanto
en los recibos como en las facturas oficiales"**.

El desglose ya está resuelto para los recibos. **La factura de ARCA todavía no
lo tiene**, y esa restricción tiene que sobrevivir a la integración con ARCA: el
importe de la factura oficial va a tener que salir del mismo desglose que ya
congela la cuota, no de un cálculo paralelo.

---

## Estado de las acordadas

| Acordada | Estado |
|---|---|
| Comprobante por cada pase o retiro entre cajas | **Hecho** |
| Comprobantes de caja digitales, impresión opcional | **Hecho** |
| Desglose obligatorio programático / extraprogramático | **Hecho en recibo**, pendiente en factura ARCA |
| Registro diario de caja con IA por foto | **Fuera de MVP**, sin fecha |
| Facturación electrónica vía ARCA | **Fuera de MVP**, sin fecha. Ojo con el requisito de desglose de arriba |
| Asistente de consultas integrado | **En curso** — issue #50, PR #51 bloqueado por conflicto de migraciones |

---

## Datos duros que dejaron en la reunión

Anotados acá porque **no están en ningún archivo del sistema** y son
exactamente lo que faltó pedir después:

- Las cuotas **vencen el día 10**, pero los intereses se calculan **desde el día 1
  del mes** si se paga al mes siguiente.
- Tasa mensual aproximada declarada: **entre 5,2% y 5,5%**. Tiene que ser
  parametrizable por fluctuación inflacionaria.
- Recargo del **10% fijo** para medios de pago distintos del efectivo
  (transferencia, débito, crédito, QR, Mercado Pago).
- **Excepciones sin recargo:** tarjeta de crédito de programas como "Ahora
  Estudiantes" y Visa del Banco Macro **en una sola cuota**.
- **Advertencia de Oscar, ratificada en el acta:** aplicar recargo al pago con
  **débito es ilegal** y podría derivar en demandas judiciales. IPAC dijo que
  ya había avisado al contador. **Esto está sin resolver.**
- Pagos en efectivo: hay excepciones operativas con descuento que todavía no
  están especificadas.

El punto 1 del mail del 01/10 pide exactamente estas reglas. Si IPAC devuelve la
planilla, esto es lo que hay que verificar primero, en este orden: **débito**,
excepciones de una cuota, y la base de cálculo de los intereses.

---

## Nota sobre la transcripción

El texto de la reunión se copió **literal**, con sus errores. No se corrigió a
propósito: un acta es evidencia, y un resumen "limpio" no distingue lo que se
acordó de lo que se entendió mal.

Errores de transcripción detectados, para no tomarlos como texto de negocio:

- `modificar el sistema pa sept 24, 2026 ra que cada transferencia` — fecha
  insertada en medio de la frase. El sentido es *"modificar el sistema para que
  cada transferencia"*.
- `comprobante auditable de débito` — por el contexto de la reunión es
  **crédito** (quien Cajero recibe el dinero), no débito.
- `Baile` — es **Baileys** (la librería de WhatsApp).
- `GPT-6 Luna y Astra` — no se pudo identificar el modelo. La mención de Astra
  se relaciona con un problema de conectividad de WhatsApp, no con el sistema.
- `recargos electrónicos` y el resto del texto están limpios.

---

## Transcripción original (literal)

Reunión del 24 sept 2026 a las 20:10 GMT-03:00

### Resumen

Revisión técnica de herramientas y resolución de incidencias con ajustes en permisos.

### Ajustes de interfaz y permisos

Se solucionó el problema de visibilidad en la barra de búsqueda y se otorgaron permisos temporales a los participantes.

### Modificación de procesos de caja

Se acordó modificar el sistema pa sept 24, 2026 ra que cada transferencia genere un comprobante auditable y se discutieron las reglas de recargos electrónicos.

### Automatización e intereses

Se implementará un asistente de consultas y se parametrizará el cálculo automático de intereses por mora según las tasas mensuales.

### Decisiones

**Requiere más debate**

- Parametrización del cálculo automático de intereses. Se debe definir y parametrizar la lógica del cálculo automático de intereses por mora, contemplando las excepciones operativas y la variabilidad de la tasa.
- Configuración de medios de pago y recargos. Se estructurarán en el sistema las distintas formas de pago y sus recargos aplicables, tales como el 10% fijo para medios no en efectivo y las excepciones del programa ahora estudiante.

**Acordada**

- Emisión de comprobantes para movimientos de caja. Se acordó que el sistema genere un comprobante por cada pase o retiro de dinero entre cajas para asegurar su registro formal.
- Impresión opcional para comprobantes de caja. Se estableció que los comprobantes de caja se generen de forma digital con la alternativa de impresión de manera opcional.
- Implementación de registro diario de caja con IA. Se adoptará el registro diario de caja mediante la implementación de captura fotográfica de comprobantes con inteligencia artificial.
- Automatización de factura electrónica mediante ARCA. Se automatizará la emisión de facturas electrónicas integradas mediante web service con ARCA directamente desde el sistema.
- Desglose obligatorio de cuotas programáticas y extraprogramáticas. Se configurarán los comprobantes de cobro para desglosar obligatoriamente los conceptos en programática y extraprogramática según los requerimientos del Ministerio de Educación.

### Próximos pasos

- **[Jose Oscar Vogel]** Ajustar interfaz de búsqueda: Optimizar la visualización de la barra de búsqueda y los botones en pantallas de baja resolución para evitar el solapamiento de elementos.
- **[Jose Oscar Vogel]** Habilitar alta de alumnos: Corregir los permisos de usuario de Laura y Zulma para permitir el registro de nuevos estudiantes en el sistema.
- **[Jose Oscar Vogel]** Ajustar transferencias de caja: Implementar la funcionalidad de pases entre cajas con la generación de un comprobante digital opcional.
- **[Jose Oscar Vogel]** Configurar permisos de reportes: Ajustar las autorizaciones de acceso para permitir la consulta de movimientos en las cajas de otros cajeros desde el módulo de reportes.
- **[Jose Oscar Vogel, Roman Vogel Corach]** Informe de permisos: Realizar un informe detallado sobre los permisos asignados a los diferentes usuarios para avanzar con la configuración del sistema.
- **[IPAC Instituto]** Enviar formato de recibos: Proporcionar una imagen del modelo de recibo actual para que los desarrolladores puedan adecuar el formato en el nuevo sistema.
- **[Jose Oscar Vogel, Roman Vogel Corach]** Corregir errores de impresión: Ajustar el formato de impresión de los recibos para eliminar las páginas en blanco y ocultar la URL de consultoría visible.
- **[IPAC Instituto]** Enviar detalles de pagos e intereses: Entregar un documento o archivo Excel detallando las formas de pago actuales y las políticas de cálculo de intereses.
- **[Jose Oscar Vogel]** Configurar desglose de cuotas: Configurar el sistema para desglosar obligatoriamente el valor total de las cuotas en conceptos programáticos y extraprogramáticos.

### Detalles

**Pruebas del sistema y estado de las herramientas de desarrollo:** En las pasarelas, Jose Oscar Vogel y Roman Vogel Corach discuten el estado de las pruebas del sistema de control y mencionan incidencias técnicas con la plataforma de WhatsApp integrada con Meta y Baile, además de revisar las cuotas de uso de modelos de inteligencia artificial como GPT-6 Luna y Astra. No se toma una decisión formal sobre las herramientas de codificación, pero Jose Oscar Vogel indica que utilizará Astra para resolver los problemas de conectividad de WhatsApp antes del 26 de septiembre.

**Problemas de resolución de pantalla y visibilidad de la barra de búsqueda:** En las pasarelas, IPAC Instituto expone que en pantallas de 14 a 16 pulgadas los botones de interfaz y la lupa de búsqueda de alumnos se amontonan o aparecen deshabilitados en color gris, impidiendo su uso. Jose Oscar Vogel reconoce el error de diseño debido a la resolución y se compromete a ajustar la interfaz para que la lupa sea visible y funcional.

**Gestión de permisos de usuarios y roles administrativos:** En las pasarelas, IPAC Instituto señala que existen diferencias en los permisos asignados a distintas cuentas (como Laura y Zulma), donde ciertas funciones no están habilitadas equitativamente. Jose Oscar Vogel explica que los perfiles actuales se configuraron rápidamente para pruebas y decide otorgar temporalmente permisos de superadministrador a todas las personas participantes para facilitar las evaluaciones, acordando definir los permisos definitivos posteriormente según los requerimientos del contador.

**Funcionamiento y auditoría de los pases y retiros entre cajas:** En las pasarelas, IPAC Instituto explica que el procedimiento habitual consiste en que una persona cajera (como Zulma) retire dinero de la caja de otra (como Laura) para realizar pagos internos de la institución. Jose Oscar Vogel argumenta en contra de este método por motivos de seguridad y falta de un comprobante firmado, indicando que en su experiencia nunca ha visto un sistema con esa lógica. Se acuerda que Jose Oscar Vogel modificará el sistema para que cada transferencia o retiro genere un comprobante auditable de débito con la debida conformidad.

**Opciones de impresión y digitalización de comprobantes:** En las pasarelas, Roman Vogel Corach e IPAC Instituto proponen implementar firmas digitales y la opción de no imprimir para ahorrar papel, manteniendo habilitada la reimpresión por si la impresora presenta fallas. Jose Oscar Vogel acepta esta alternativa para que la emisión de comprobantes en papel sea opcional.

**Visualización de reportes de cajas y cierres de turnos:** En las pasarelas, IPAC Instituto plantea el problema de no poder consultar los movimientos de otras cajas una vez que estas han sido cerradas. Jose Oscar Vogel muestra en pantalla el módulo de reportes de cobranzas por fecha y sucursal, y se compromete a ajustar los permisos para que las personas supervisoras puedan listar y verificar las operaciones de las diferentes cajas de manera integral.

**Asistente integrado en la plataforma para consultas de usuario:** En la pasarela, Jose Oscar Vogel presenta un asistente integrado en el sistema donde las personas usuarias pueden consultar de forma automatizada los pasos para registrar pagos, dar de alta alumnos o realizar cierres de caja, con el fin de agilizar la consulta de procesos. IPAC Instituto valida positivamente la herramienta para reducir la dependencia de reuniones de soporte.

**Pruebas de registro de pagos a cuenta y visualización de saldos:** En las pasarelas, IPAC Instituto realiza una prueba práctica registrando un pago parcial (pago a cuenta) de 10.000 pesos para una alumna, comprobando que el saldo pendiente se actualiza correctamente. Sin embargo, Roman Vogel Corach advierte que al intentar previsualizar el recibo se generan páginas en blanco y aparece texto con enlaces HTTPS, lo cual quedará bajo revisión.

**Generación de cuotas, matrículas y aplicación de convenios:** En las pasarelas, IPAC Instituto detalla la necesidad de identificar claramente el número de cuota (del 1 al 10) y aplicar descuentos por convenios institucionales (como ATE o Crucero del Norte con reducciones del 15% o 20%) durante la matriculación anual. Jose Oscar Vogel debate las opciones entre la generación masiva mensual y la matriculación por cantidad de cuotas elegidas, comprometiéndose a ajustar el sistema y los reportes solicitados por el contador sobre deudas y alumnos activos por curso.

**Gestión histórica de matrículas y control de caja chica:** IPAC Instituto explicó que durante los períodos de mayor inscripción en marzo, el tiempo no bastaba para matricular a los estudiantes en el sistema, lo que obligaba a utilizar planillas de Excel para estimar cantidades y aplazar las matrículas hasta el inicio de las clases. Asimismo, IPAC Instituto detalló que los gastos menores de caja chica (como compras para la mañana y la tarde o papel higiénico) se acumulan y se registran cada quince días o una vez a la semana debido a la cantidad de comprobantes físicos. Ante la duda sobre cómo registrar gastos retroactivos, Jose Oscar Vogel recomendó realizar los cierres de caja de manera diaria para evitar la pérdida de tiquecitos.

**Automatización del registro de caja mediante inteligencia artificial:** Jose Oscar Vogel sugirió mantener la costumbre de cerrar la caja y la conciliación bancaria diariamente, lo cual tomaría entre quince y treinta minutos una vez convertido en hábito. Además, Jose Oscar Vogel indicó que se está trabajando junto a Roman Vogel Corach en el uso de inteligencia artificial para permitir que las personas usuarias suban una fotografía del comprobante y este se registre automáticamente en la caja. IPAC Instituto valoró positivamente esta herramienta para agilizar la carga de datos.

**Metodología y parametrización del cálculo de intereses por mora:** IPAC Instituto planteó la necesidad de que el sistema calcule automáticamente los intereses en lugar de recurrir a una planilla de Excel casera. Se discutió cómo manejar excepciones para pagos en efectivo donde se aplican descuentos. IPAC Instituto explicó que las cuotas vencen el día 10, pero los intereses se calculan desde el día 1 del mes correspondiente si se paga al mes siguiente, aplicando una tasa mensual aproximada de entre 5,2% y 5,5%. Jose Oscar Vogel señaló que dicha tasa debe poder parametrizarse debido a posibles fluctuaciones inflacionarias futuras.

**Recargos aplicados a medios de pago electrónicos y tarjetas:** IPAC Instituto señala que los pagos realizados con medios distintos al efectivo (como transferencias, débitos, créditos, códigos QR y Mercado Pago) tienen un recargo fijo del 10%. Jose Oscar Vogel advirtió que aplicar recargos a los pagos por débito es ilegal y podría derivar en demandas judiciales, ante lo cual IPAC Instituto afirmó haber dado aviso previo al contador. Se aclaró que los pagos con tarjeta de crédito mediante programas como "Ahora Estudiantes" o con tarjetas Visa del Banco Macro en una sola cuota no llevan recargo. Jose Oscar Vogel solicitó que se envíe un documento en planilla de cálculo con todas estas reglas de pago y porcentajes de interés para adaptar el sistema.

**Emisión de facturas electrónicas y desglose obligatorio de cuotas:** IPAC Instituto consultó sobre los comprobantes a emitir para pagos electrónicos, y Jose Oscar Vogel explicó que el sistema se conectará de manera automática con ARCA mediante servicios web para generar la factura electrónica y obtener el código de autorización electrónico sin necesidad de ingresos manuales. Por último, IPAC Instituto indicó que se omitió mencionar un requisito del Ministerio de Educación: el valor total de la cuota (por ejemplo, 82.000 pesos) debe figurar obligatoriamente desglosado en conceptos programáticos y extraprogramáticos tanto en los recibos como en las facturas oficiales.
