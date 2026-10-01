<template>
  <details v-if="contenido && permitido" class="context-help">
    <summary>{{ contenido.titulo }} · Ayuda</summary>
    <ol><li v-for="paso in pasos" :key="paso">{{ paso }}</li></ol>
    <p v-if="modo">Opción elegida: {{ { automatico: 'aplicar a las cuotas más antiguas', manual: 'elegir las cuotas', cuenta: 'conservar como saldo a favor' }[modo] }}.</p>
    <p><strong>Ejemplo:</strong> {{ sinPeriodo ? 'Guardá el listado actual de una sucursal para consultarlo con los mismos filtros desde otro equipo.' : contenido.ejemplo }}</p>
    <ul><li v-for="termino in terminos" :key="termino">{{ termino }}</li></ul>
  </details>
</template>
<script setup>
import { computed } from 'vue'
import { guias } from '@/content/guias'
import { useAuth } from '@/composables/useAuth'
const props = defineProps({ guia: { type: String, required: true }, modo: { type: String, default: '' }, seccion: { type: String, default: '' } })
const auth = useAuth()
const contenido = computed(() => guias.find(item => item.id === props.guia))
const permitido = computed(() => !contenido.value?.permiso || auth.can(contenido.value.permiso))
const sinPeriodo = computed(() => props.guia === 'reportes' && ['alumnos', 'morosidad'].includes(props.seccion))
const pasos = computed(() => sinPeriodo.value ? ['Elegí la sucursal y pulsá Aplicar.', 'Este listado refleja el estado actual. Exportá el resultado o abrí la pantalla correspondiente para más filtros.', 'Guardá la consulta actual como favorita para reutilizarla desde otro equipo.'] : contenido.value?.pasos || [])
const terminos = computed(() => {
  const items = contenido.value?.terminos || []
  if (props.guia !== 'reportes') return items
  const role = auth.user?.value?.perfil?.rol
  const scope = role === 'consulta' ? 'Tu perfil puede consultar los resúmenes agregados de cajas.' : role === 'caja' ? 'Tu perfil puede consultar sus propias cajas y movimientos en el historial.' : 'Podés consultar cajas de otros cajeros dentro de tus sucursales autorizadas.'
  return [...items.slice(0, -1), scope]
})
</script>
<style scoped>
.context-help{padding:.7rem 1rem;border:1px solid var(--border);border-radius:.7rem;background:var(--surface-soft);color:var(--text-primary);margin-bottom:1rem;font-size:.9rem;line-height:1.6}.context-help summary{min-height:28px;cursor:pointer;font-weight:700;color:var(--primary)}.context-help summary:focus-visible{outline:3px solid var(--primary);outline-offset:3px}.context-help li+li{margin-top:.35rem}.context-help p{margin:.8rem 0}
</style>
