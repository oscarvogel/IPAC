<template>
  <section class="settings-view">
    <header class="settings-header">
      <p class="eyebrow">Administración del sistema</p>
      <p>Catálogos, accesos y herramientas que definen cómo funciona IPAC.</p>
    </header>

    <div class="settings-grid">
      <RouterLink v-for="item in items" :key="item.to" :to="item.to" class="settings-card">
        <span class="settings-card-icon"><component :is="item.icon" aria-hidden="true" /></span>
        <span>
          <strong>{{ item.title }}</strong>
          <small>{{ item.description }}</small>
        </span>
        <ChevronRightIcon aria-hidden="true" />
      </RouterLink>
    </div>
  </section>
</template>

<script setup>
import {
  ArrowUpTrayIcon,
  BuildingOffice2Icon,
  ChevronRightIcon,
  ClipboardDocumentCheckIcon,
  ReceiptPercentIcon,
  TagIcon,
  UserGroupIcon,
} from '@heroicons/vue/24/outline'

const items = [
  { to: '/sucursales', title: 'Sucursales', description: 'Sedes y alcance operativo.', icon: BuildingOffice2Icon },
  { to: '/conceptos', title: 'Conceptos cobrables', description: 'Aranceles disponibles para cuotas y matrículas.', icon: TagIcon },
  { to: '/ajustes-cuotas', title: 'Descuentos y recargos', description: 'Beneficios autorizados y reglas automáticas de mora.', icon: ReceiptPercentIcon },
  { to: '/usuarios', title: 'Usuarios y permisos', description: 'Roles, sucursales y acceso al sistema.', icon: UserGroupIcon },
  { to: '/importaciones', title: 'Importar datos', description: 'Plantillas y carga controlada desde Excel o CSV.', icon: ArrowUpTrayIcon },
  { to: '/auditoria', title: 'Auditoría', description: 'Historial de cambios administrativos y financieros.', icon: ClipboardDocumentCheckIcon },
]
</script>

<style scoped>
.settings-view { display: grid; gap: 1.5rem; }
.settings-header h1 { margin: .2rem 0 .35rem; font-size: clamp(1.75rem, 4vw, 2.5rem); }
.settings-header > p:last-child { margin: 0; color: var(--color-text-secondary); }
.settings-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr)); gap: 1rem; }
.settings-card { display: grid; grid-template-columns: 3rem 1fr 1.25rem; align-items: center; gap: 1rem; min-height: 7.5rem; padding: 1.15rem; border: 1px solid var(--color-border); border-radius: 1rem; background: var(--color-surface); color: var(--color-text-primary); text-decoration: none; box-shadow: var(--shadow-card); }
.settings-card:hover, .settings-card:focus-visible { border-color: var(--color-primary); transform: translateY(-1px); }
.settings-card-icon { display: grid; place-items: center; width: 3rem; height: 3rem; border-radius: .9rem; background: var(--primary-soft); color: var(--primary); }
.settings-card-icon svg, .settings-card > svg { width: 1.35rem; }
.settings-card span:nth-child(2) { display: grid; gap: .35rem; }
.settings-card small { color: var(--color-text-secondary); line-height: 1.4; }
</style>
