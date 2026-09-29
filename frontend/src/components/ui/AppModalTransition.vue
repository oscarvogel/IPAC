<template>
  <Transition
    :css="false"
    @enter="enter"
    @leave="leave"
  >
    <slot v-if="open" />
  </Transition>
</template>

<script setup>
import { animateDialogEnter, animateDialogLeave } from '@/lib/motion'

defineProps({
  open: { type: Boolean, default: false },
})

function enter(element, done) {
  animateDialogEnter(element, done)
}

function leave(element, done) {
  animateDialogLeave(element, done)
}
</script>
