# Nota: el formato del recibo es provisional

**Estado:** provisional. Cierra cuando IPAC entregue su modelo de recibo.
**Fecha de la nota:** 2026-10-01
**Pedido que la bloquea:** punto 2 de `docs/SOLICITUD_ENTREGABLES_IPAC_2026-10-01.md`

Esta nota va junto a `docs/GUIA_PRUEBA_RAMA_INTEGRADA.md` porque las dos cosas
se releen juntas cuando IPAC mande el modelo. La guia sirve para probar; esta
sirve para saber **que se puede tocar y que no** cuando llegue la maqueta final.

---

## Que esta provisional y que no

El layout del recibo esta **hardcodeado** en
`frontend/src/components/ui/ReciboPrintView.vue`. El orden de las secciones,
los titulos literales y que datos del alumno van son decisions nuestras, no
del cliente. En cuanto IPAC mande su modelo, esa maqueta se reemplaza.

**No hay que tocar** cuando llegue el modelo (esto sale de los datos y ya esta
correcto):

| Elemento | Origen |
|---|---|
| Importe de cada aplicacion | `AplicacionPago.importe` |
| Desglose programatico / extraprogramatico | `Cuota.importe_programatico` / `importe_extraprogramatica` |
| Alumno y legajo | `Alumno` |
| Medio de pago | `Pago.medio` |
| Fecha del pago | `Pago.fecha` |
| Total del pago | `Pago.importe` |
| Saldo pendiente posterior | calculado por el backend en el action `recibo` |
| Observacion y motivo de anulacion | `Pago.observacion` / `Pago.motivo_anulacion` |
| Usuario emisor | `Pago.usuario_nombre` |
| Sucursal, numero de recibo, fecha de emision | `Pago` / recibo |

## Unico requisito externo abierto

**La posicion de la linea de desglose.** Hoy se imprime como una sub-linea
dentro de la fila de la cuota:

```text
| Concepto              | Periodo   | Importe      |
| Matricula 2026        | 2026-08   | $ 50.000,00  |
|   Parte programatica / extraprogramatica | $ 40.000,00 / $ 10.000,00 |
```

Cuando llegue el modelo puede tener que ir:

- arriba del detalle, como fila propia,
- en un bloque separado debajo de la tabla,
- o al pie, como resumen.

Es la unica decision de maquetado que hoy no tenemos por escrito. Cualquier
otra diferencia entre nuestro recibo y el de IPAC la resolvemos por
consenso en la reunion, no por interpretacion.

## Sobre el encabezado del PDF

El PDF que sale al imprimir muestra **"Vogel Consultoria" en el encabezado y
en el pie**. Eso lo injecta el navegador, no el sistema: es el titulo y la
URL de la pestana desde la que se lanzo la impresion. No hay nada que cambiar
en el codigo para sacarlo. Si molesta, la via correcta es configurar el
encabezado y pie en la config de impresion del navegador de la maquina que
imprime, no tocar la plantilla.

## Que pedirle a IPAC ademas

Ademas del modelo, conviene pedirle que el-envie **en PDF y no como captura**.
Con el PDF se puede leer el modelo original y no se pierde el papel. El mismo
pedido esta en el punto 2 del mail del 01/10/2026.

## Como se ajusta cuando llegue

1. Aplicar el modelo sobre `ReciboPrintView.vue`, empezando por la posicion
   de la linea de desglose.
2. No tocar los bindings de datos: si un valor no coincide con el modelo, es
   un bug de datos, no un ajuste de formato.
3. Correr la suite de frontend (`npm --prefix frontend test`) y la prueba 2 de
   `docs/GUIA_PRUEBA_RAMA_INTEGRADA.md`.
4. Reempluir esta nota por una que diga que el formato quedo confirmado, o
   eliminarla si ya no aplica.
