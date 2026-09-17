<template>
  <strong>
    <span aria-hidden="true"><span v-if="prefix">{{ prefix }}</span><span ref="visualValue">0</span></span>
    <span class="sr-only">{{ prefix }}{{ accessibleValue }}</span>
  </strong>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { animateCounter } from '@/lib/motion'
import { formatMoney } from '@/lib/formatters'

const props = defineProps({
  value: { type: [Number, String], default: 0 },
  kind: { type: String, default: 'integer' },
  prefix: { type: String, default: '' },
  fractionDigits: { type: Number, default: 2 },
})

const visualValue = ref(null)
let previousValue = 0
let activeTween = null

function numericValue(value) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

function formatValue(value) {
  if (props.kind === 'money') {
    return formatMoney(value, { fractionDigits: props.fractionDigits })
  }
  return formatMoney(Math.round(value))
}

const accessibleValue = computed(() => formatValue(numericValue(props.value)))

function animateValue(value) {
  const nextValue = numericValue(value)
  activeTween?.kill()
  activeTween = animateCounter(visualValue.value, previousValue, nextValue, {
    format: (next) => formatValue(next),
  })
  previousValue = nextValue
}

onMounted(() => {
  animateValue(props.value)
})

watch(
  () => [props.value, props.kind, props.fractionDigits],
  ([nextValue]) => animateValue(nextValue),
)

onBeforeUnmount(() => {
  activeTween?.kill()
})
</script>
