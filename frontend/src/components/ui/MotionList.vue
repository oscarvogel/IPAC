<template>
  <TransitionGroup
    ref="transitionGroup"
    v-bind="$attrs"
    :tag="props.tag"
    :css="false"
    @enter="enter"
    @leave="leave"
  >
    <slot />
  </TransitionGroup>
</template>

<script setup>
import { onBeforeUpdate, onUpdated, ref } from 'vue'
import {
  animateFlipState,
  animateListEnter,
  animateListLeave,
  animateToastEnter,
  animateToastLeave,
  captureFlipState,
} from '@/lib/motion'

defineOptions({ inheritAttrs: false })

const transitionGroup = ref(null)
let pendingFlipState = null

function element() {
  return transitionGroup.value?.$el || transitionGroup.value
}

function items() {
  return element()?.querySelectorAll?.('[data-motion-item]') || []
}

const props = defineProps({
  tag: { type: String, default: 'div' },
  variant: { type: String, default: 'list' },
  animate: { type: Boolean, default: true },
})

function enter(item, done) {
  if (!props.animate) return done()
  if (props.variant === 'toast') return animateToastEnter(item, done)
  animateListEnter(item, done)
}

function leave(item, done) {
  if (!props.animate) return done()
  if (props.variant === 'toast') return animateToastLeave(item, done)
  animateListLeave(item, done)
}

onBeforeUpdate(() => {
  if (!props.animate) {
    pendingFlipState = null
    return
  }
  pendingFlipState = captureFlipState(items())
})

onUpdated(() => {
  if (!pendingFlipState) return
  const state = pendingFlipState
  pendingFlipState = null
  if (!props.animate) return
  animateFlipState(state, items())
})
</script>
