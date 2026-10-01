# Cómo probar la rama integrada

Rama a desplegar en Coolify: **`feat/prueba-integrada`**

Trae las tres cosas juntas:

- Pantalla de **Carreras y cursos** (nueva, en Configuración)
- **Desglose programático/extraprogramático** en el recibo
- **Comprobante auditable** de pase y retiro entre cajas

> **El formato del recibo es provisional.** El layout esta hardcodeado en la
> plantilla y se ajusta cuando IPAC mande su modelo. Leer
> `docs/NOTA_FORMATO_RECIBO_PROVISIONAL.md` antes de tocar el recibo.
## Antes de empezar

Entrá con un usuario **Administración** o **Superadmin**. Los demás roles pueden ver la
pantalla de carreras pero no gestionarla.

La migración corre sola al desplegar (agrega cuatro columnas, no toca datos). Si querés
confirmarlo:

```bash
docker compose exec backend python manage.py showmigrations core | tail -3
```

Tiene que decir `[X] 0017_cuota_desglose_movimiento_comprobante`.

---

## Prueba 1 — Pantalla de carreras

1. Entrá a **Configuración → Carreras y cursos**.
2. Arriba debería aparecer un aviso naranja con cuántas carreras están **sin desglose**.
3. Si no hay carreras cargadas, creá una con el botón **Nueva carrera**.
4. En el formulario, andá a **Desglose de la cuota** y cargá:
   - Cuota programática (por ejemplo 62000)
   - Cuota extraprogramática (por ejemplo 20000)
5. Fijate que la **cuota total se calcula sola** y muestra 82000.
6. Ahora tocá la cuota total y poné 90000: tiene que cambiar el cartel a
   "Valor cargado a mano" y avisar que no coincide con la suma.
7. Volvé a 62000 / 20000 y guardá. El aviso de arriba debería bajar el contador.
8. Probá los filtros: buscar, sucursal, tipo (carreras / cursos) y "Solo activas".
9. Probá desactivar una carrera y confirmá.

**Si el total no se calcula solo**, avisame: es la parte más nueva de la pantalla.

## Prueba 2 — Desglose en el recibo

> Ojo: el desglose se congela **cuando se genera la cuota**. Las cuotas que ya existen
> no lo tienen. Hay que generar una nueva.

1. Tomá un alumno matriculado en una carrera que ya tenga el desglose cargado.
2. Generale una cuota nueva (Alumnos → el alumno → generar cuota).
3. Registrá un pago que **cubra la cuota completa**.
4. Abrí el recibo: tiene que aparecer la línea
   **"Parte programática / extraprogramática"** con los dos importes.
5. Imprimilo: la línea tiene que salir también en el PDF, en una sola página.
6. Ahora probá un **pago parcial** de esa misma cuota: el recibo tiene que salir
   **sin** la línea de desglose. Es a propósito, el reparto de un pago parcial todavía
   no está definido.

## Prueba 3 — Comprobante de pase

1. En **Caja**, abrí **Registrar movimiento** y poné tipo **Pase**.
2. Tiene que aparecer el campo **"Recibe el dinero"** con la lista de usuarios de tu
   sucursal.
3. Sin elegir receptor, **no te debe dejar guardar**.
4. Elegí un receptor, guardá, y fijate que el movimiento sale numerado
   (`COM-00000xx`).
5. Ahora hacé lo mismo con tipo **Ingreso** o **Egreso**: el campo de receptor **no**
   aparece y el movimiento **no** se numera. Esto es lo que confirma que no rompí nada
   de lo que ya usaban.

## Prueba 4 — Que no se rompió nada

Como esto se despliega sobre producción, revisá que lo de siempre siga igual:

1. Registrá un pago común y abrí su recibo.
2. Imprimí el recibo de una cuota vieja (sin desglose): una sola página, como antes.
3. Imprimí el resumen de caja: una sola página.
4. Entrá a Alumnos, Deudores, Reportes y Caja y mirá que todo cargue bien.
5. Revisá la consola del navegador: no debería haber errores nuevos.

---

## Problema conocido en esta vuelta

La primera vez que se probó, **Generar cuota** devolvio un error 500 en pantalla
blanca. Ya esta corregido en la rama: si te pasa, actualizá el despliegue a la
misma rama y probá de nuevo.

Para que no vuelva a pasar: si ves un 500 al generar cuotas, es un error del
servidor, no tuyo. Anotá el período y el alumno, avisame, y **no reintentes** a
mano hasta que lo confirme.

## Si algo falla

Mandame: una captura, qué estabas haciendo, tu rol y sucursal, y si aparece algún
código de error copialo tal cual.

Si una operación te deja dudando de si se guardó, **no la repitas**. Prefiero que me
avises y lo reviso yo, para no duplicar un pago.

## Detalle que no es de este cambio

La URL de "Vogel Consultoría" sigue apareciendo en el PDF. Viene del encabezado o pie
que genera el navegador al imprimir, así que desde el sistema no se controla del todo.
Eso es aparte.
