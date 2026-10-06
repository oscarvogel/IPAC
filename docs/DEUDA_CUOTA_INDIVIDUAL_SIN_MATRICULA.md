# Deuda tecnica registrada por la QA del PR 61

## Cuota individual sin matricula

**Estado**: no corregido en el PR 61, pendiente de issue propio.

**Sintoma**: una cuota creada por el flujo individual (el boton "Generar
cuota" de la ficha del alumno, `POST /api/cuotas/generar/`) queda con el
campo `matricula` en `null`.

```json
{ "id": 31, "alumno": 286, "matricula": null, "concepto": 7, "periodo": "2026-08" }
```

**Por que no es regresion de este PR**: `Cuota.matricula` existe en el modelo
desde antes y el generador de la generacion individual nunca lo escribio.
El PR 61 solo lo lleno en el camino nuevo, el que dispara la matricula.

**Por que importa igual**: la cuenta corriente de un alumno puede mezclar
cuotas con y sin matricula. El serializer expone `matricula_estado` para
poder marcar en rojo lo que vino de una matricula anulada, y en las cuotas
individuales ese campo queda en `null` aunque su matricula este activa. Un
cobro aplicado sobre una cuota individual no tiene, hoy, el mismo rastro que
uno aplicado sobre una cuota de reinscripcion.

**Que habria que decidir antes de corregirlo**: si la generacion individual
tiene que resolver la matricula activa del alumno y engancharse a ella, o
si el campo debe quedar en `null` por diseño y lo que falta es una forma
distinta de expresar la pertenencia a una cohorte.