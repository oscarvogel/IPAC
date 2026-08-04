<template>
  <Teleport to="body">
    <Transition name="tooltip-fade">
      <div
        v-if="visible"
        id="app-global-tooltip"
        ref="tooltipElement"
        class="app-tooltip"
        role="tooltip"
        :style="position"
      >
        {{ text }}
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'

const visible = ref(false)
const text = ref('')
const tooltipElement = ref(null)
const position = reactive({ top: '0px', left: '0px' })
let activeTarget = null
let previousDescribedBy = ''
let previousTitle = null

function tooltipTarget(node) {
  const target = node?.closest?.('button[aria-label], a[aria-label], [data-tooltip]')
  if (!target) return null
  const explicit = target.dataset.tooltip
  const isIconOnly = !target.textContent.trim()
  return explicit || isIconOnly ? target : null
}

async function show(target) {
  if (!target || target === activeTarget) return
  hide()
  activeTarget = target
  text.value = target.dataset.tooltip || target.getAttribute('aria-label') || ''
  if (!text.value) return

  previousDescribedBy = target.getAttribute('aria-describedby') || ''
  target.setAttribute('aria-describedby', [previousDescribedBy, 'app-global-tooltip'].filter(Boolean).join(' '))
  previousTitle = target.hasAttribute('title') ? target.getAttribute('title') : null
  target.removeAttribute('title')
  visible.value = true
  await nextTick()

  const targetRect = target.getBoundingClientRect()
  const tooltipRect = tooltipElement.value?.getBoundingClientRect()
  if (!tooltipRect) return
  let top = targetRect.top - tooltipRect.height - 9
  if (top < 8) top = targetRect.bottom + 9
  const left = Math.min(
    window.innerWidth - tooltipRect.width - 8,
    Math.max(8, targetRect.left + (targetRect.width - tooltipRect.width) / 2),
  )
  position.top = `${Math.round(top)}px`
  position.left = `${Math.round(left)}px`
}

function hide() {
  if (activeTarget) {
    if (previousDescribedBy) activeTarget.setAttribute('aria-describedby', previousDescribedBy)
    else activeTarget.removeAttribute('aria-describedby')
    if (previousTitle !== null) activeTarget.setAttribute('title', previousTitle)
  }
  activeTarget = null
  previousDescribedBy = ''
  previousTitle = null
  visible.value = false
}

function onPointerOver(event) {
  show(tooltipTarget(event.target))
}

function onPointerOut(event) {
  if (activeTarget && !activeTarget.contains(event.relatedTarget)) hide()
}

function onFocusIn(event) {
  show(tooltipTarget(event.target))
}

function onFocusOut(event) {
  if (activeTarget && !activeTarget.contains(event.relatedTarget)) hide()
}

function onKeydown(event) {
  if (event.key === 'Escape') hide()
}

onMounted(() => {
  document.addEventListener('pointerover', onPointerOver)
  document.addEventListener('pointerout', onPointerOut)
  document.addEventListener('focusin', onFocusIn)
  document.addEventListener('focusout', onFocusOut)
  document.addEventListener('keydown', onKeydown)
  window.addEventListener('scroll', hide, true)
  window.addEventListener('resize', hide)
})

onBeforeUnmount(() => {
  hide()
  document.removeEventListener('pointerover', onPointerOver)
  document.removeEventListener('pointerout', onPointerOut)
  document.removeEventListener('focusin', onFocusIn)
  document.removeEventListener('focusout', onFocusOut)
  document.removeEventListener('keydown', onKeydown)
  window.removeEventListener('scroll', hide, true)
  window.removeEventListener('resize', hide)
})
</script>
