<template>
  <section class="page-state access-denied-state" aria-labelledby="access-denied-title">
    <div class="page-state-icon" aria-hidden="true">!</div>
    <p class="eyebrow">Acceso restringido</p>
    <h1 id="access-denied-title">No tenés permisos para ver esta sección</h1>
    <p>Tu rol actual no permite realizar esta operación. Si necesitás acceso, consultá a un administrador.</p>
    <button type="button" class="primary-button" @click="goDashboard">Volver al dashboard</button>
  </section>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function goDashboard() {
  router.push('/dashboard')
}
</script>
