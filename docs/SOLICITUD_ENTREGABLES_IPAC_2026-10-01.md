Asunto: IPAC — necesitamos 5 definiciones de ustedes para avanzar con pagos, intereses y comprobantes

Hola,

Después de la reunión del 24/09 y de la tanda de pruebas que están haciendo, necesitamos cerrar cinco puntos que no podemos decidir por nuestra cuenta, porque dependen de reglas de negocio y de documentación que tienen ustedes.

Dos de estos cinco son bloqueantes: sin ellos no podemos arrancar el desarrollo.

---

## 1. Planilla con formas de pago y porcentajes (BLOQUEANTE)

Ya lo pidieron en la reunión y es lo que más nos frena. Necesitamos un Excel o documento con:

- Todos los medios de pago que manejan, con el nombre exacto como figura en el recibo.
- El recargo o descuento que aplica a cada uno (en importe fijo o en porcentaje).
- Las excepciones, nombradas una por una. Por ahora conocemos dos: Ahora Estudiantes, y Visa del Banco Macro en una sola cuota, ambos sin recargo.
- Si el recargo del 10% aplica siempre al débito, o si hay algún criterio para distinguirlo.

Sobre esto último: en la reunión se señaló que aplicar recargo al pago con débito puede tener problemas legales. No queremos implementarlo como un parámetro libre sin su confirmación escrita, precisamente para no dejar el sistema con una configuración que después no se pueda usar.

Sin este punto no podemos construir el cálculo de recargo en el momento del pago.

## 2. Imagen del modelo de recibo actual (BLOQUEANTE)

Quedó pendiente que enviaran una foto o imagen del recibo que usan hoy, para adecuar el formato al sistema.

Y aprovecho para avisar algo que salió en la prueba de impresión: en el sistema nuevo ya se imprime una sola página por documento y sin página en blanco, pero la URL de la consultancy sigue apareciendo. Viene del encabezado o pie que genera el navegador al imprimir, así que desde el sistema no la controlamos del todo. Digan si con la imagen de referencia alcanza o si necesitan que la eliminemos de alguna otra manera.

## 3. Tasa de interés y forma de cálculo (BLOQUEANTE)

La idea es calcular los intereses automáticamente y dejar la tasa parametrizable, porque va a cambiar con la inflación. Para implementarlo bien necesitamos:

- La tasa mensual vigente. En la reunión se consolidationó un rango entre 5,2% y 5,5%; necesitamos el número exacto y desde qué fecha rige.
- Desde qué fecha se calcula el interés sobre una cuota. Entendemos que las cuotas vencen el día 10, pero que el interés se cuenta desde el día 1 del mes si se paga al mes siguiente. Confirmar si aplica igual para todas las cuotas.
- Qué pasa con los pagos en efectivo: entendimos que ahí puede haber un descuento. Si es así, ese descuento es comercial, no un interés. ¿Prefieren cargarlo como descuento manual o que el sistema lo calcule?
- Si el interés se suma a la cuota original o se emite como concepto separado. Esto cambia el recibo y también el reporte de deuda.

## 4. Matriz definitiva de permisos

En la reunión activamos permisos de superadministrador de forma temporal para que pudieran probar sin obstáculos. Fue un rodeo, no la solución final.

Para cerrarlo necesitamos:

- Qué roles existen y qué puede hacer cada uno.
- Qué sucursal opera cada persona.
- En particular para Laura y Zulma: qué funciones deben tener habilitadas. El pedido fue que pudieran dar de alta alumnos.
- Si hay personas que no deben ver movimientos de otras cajas.

También quedamos en generar un informe detallado de los permisos que hoy tiene cada usuario. Eso lo preparamos nosotros, pero necesitamos la definición correcta contra la cual compararlo.

## 5. Comprobante de pase entre cajas

Quedamos en que cada pase o retiro de dinero entre cajas debe generar un comprobante auditable, con la conformidad de quien recibe. Antes de construirlo necesitamos:

- Qué datos deben salir en el comprobante (fecha, caja de origen, caja de destino, importe, motivo, nombres de los usuarios).
- Quién firma o conforma: el usuario que recibe, el que entrega, o ambos.
- Si el comprobante se imprime siempre o queda disponible digitalmente para imprimir cuando haga falta. Entendemos que es digital con impresión opcional, pero conviene confirmarlo.
- Si aplica al retiro de cierre de caja o solamente al pase entre cajas de personas distintas.

---

## Si algo se demora

Si alguno de los cinco puntos les lleva más tiempo, con que nos pasen al menos los puntos 1 y 4 ya podemos avanzar en paralelo. Los puntos 3 y 5 podemos arrancarlos con un supuesto por defecto y corregirlo después, siempre que nos confirmen.

Cualquier duda, o si prefieren que lo conversemos en una llamada corta, avísen y coordinamos.

Gracias,

Oscar Vogel
IPAC · vogelconsultoria.com.ar