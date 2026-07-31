<template>
  <section class="users-list-card border-border bg-surface">
    <header class="users-list-head">
      <div class="users-list-title">
        <span class="users-list-icon">
          <IdentificationIcon aria-hidden="true" />
        </span>
        <div>
          <p class="eyebrow">Directorio interno</p>
          <h2>Usuarios del sistema</h2>
          <p>Perfiles habilitados para acceder al CRM.</p>
        </div>
      </div>
      <span class="users-list-count">
        {{ sortedUsuarios.length }} {{ sortedUsuarios.length === 1 ? 'usuario' : 'usuarios' }}
      </span>
    </header>

    <div class="users-table-wrap">
      <table class="users-table">
        <thead>
          <tr>
            <th>Usuario</th>
            <th>Email</th>
            <th>Rol</th>
            <th>Sucursal</th>
            <th>Alcance</th>
            <th>Estado</th>
            <th><span class="sr-only">Acciones</span></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="usuario in sortedUsuarios" :key="usuario.id">
            <td>
              <div class="users-identity-cell">
                <span class="users-avatar">{{ avatarInitials(usuario) }}</span>
                <span>
                  <strong>{{ usuario.username }}</strong>
                  <small>{{ fullName(usuario) }}</small>
                </span>
              </div>
            </td>
            <td>
              <span class="users-email">
                <EnvelopeIcon aria-hidden="true" />
                {{ usuario.email || 'Sin email' }}
              </span>
            </td>
            <td>
              <span :class="['users-role-badge', `role-${usuario.perfil?.rol || 'consulta'}`]">
                <component :is="roleIcon(usuario.perfil?.rol)" aria-hidden="true" />
                {{ roleLabel(usuario.perfil?.rol) }}
              </span>
            </td>
            <td>
              <span class="users-branch">
                <BuildingStorefrontIcon aria-hidden="true" />
                {{ usuario.perfil?.sucursal?.nombre || 'Sin sucursal' }}
              </span>
            </td>
            <td>
              <span :class="['users-scope', { global: usuario.perfil?.puede_ver_todas_las_sucursales }]">
                <component
                  :is="usuario.perfil?.puede_ver_todas_las_sucursales ? GlobeAltIcon : MapPinIcon"
                  aria-hidden="true"
                />
                {{ usuario.perfil?.puede_ver_todas_las_sucursales ? 'Todas las sedes' : 'Sede asignada' }}
              </span>
            </td>
            <td>
              <span :class="['users-status', usuario.is_active ? 'active' : 'inactive']">
                <component :is="usuario.is_active ? CheckCircleIcon : PauseCircleIcon" aria-hidden="true" />
                {{ usuario.is_active ? 'Activo' : 'Inactivo' }}
              </span>
            </td>
            <td>
              <div class="users-row-actions">
                <button
                  type="button"
                  title="Editar usuario"
                  aria-label="Editar usuario"
                  @click="$emit('edit', usuario)"
                >
                  <PencilSquareIcon aria-hidden="true" />
                </button>
                <button
                  v-if="usuario.is_active"
                  type="button"
                  class="deactivate"
                  title="Desactivar usuario"
                  aria-label="Desactivar usuario"
                  @click="$emit('deactivate', usuario)"
                >
                  <NoSymbolIcon aria-hidden="true" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="!sortedUsuarios.length" class="users-empty-state">
        <span><UserGroupIcon aria-hidden="true" /></span>
        <strong>No encontramos usuarios</strong>
        <p>Probá cambiando la búsqueda, la sucursal o el rol seleccionado.</p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import {
  BanknotesIcon,
  BuildingStorefrontIcon,
  CheckCircleIcon,
  ClipboardDocumentCheckIcon,
  EnvelopeIcon,
  EyeIcon,
  GlobeAltIcon,
  IdentificationIcon,
  KeyIcon,
  MapPinIcon,
  NoSymbolIcon,
  PauseCircleIcon,
  PencilSquareIcon,
  ShieldCheckIcon,
  UserGroupIcon,
} from '@heroicons/vue/24/outline'

const props = defineProps({
  usuarios: { type: Array, required: true },
})

defineEmits(['edit', 'deactivate'])

const sortedUsuarios = computed(() =>
  [...props.usuarios].sort((a, b) => {
    if (a.is_active !== b.is_active) return a.is_active ? -1 : 1
    return (a.username || '').localeCompare(b.username || '', 'es', { sensitivity: 'base' })
  }),
)

function fullName(usuario) {
  return [usuario.first_name, usuario.last_name].filter(Boolean).join(' ') || 'Sin nombre registrado'
}

function avatarInitials(usuario) {
  const first = (usuario.first_name || '').trim()
  const last = (usuario.last_name || '').trim()
  if (first || last) return `${first.slice(0, 1)}${last.slice(0, 1)}`.toUpperCase()
  return (usuario.username || '?').slice(0, 2).toUpperCase()
}

function roleLabel(role) {
  const labels = {
    superadmin: 'Superadmin',
    administracion: 'Administración',
    tesoreria: 'Tesorería',
    caja: 'Caja',
    consulta: 'Consulta',
  }
  return labels[role] || role || 'Consulta'
}

function roleIcon(role) {
  const icons = {
    superadmin: ShieldCheckIcon,
    administracion: KeyIcon,
    tesoreria: BanknotesIcon,
    caja: ClipboardDocumentCheckIcon,
    consulta: EyeIcon,
  }
  return icons[role] || EyeIcon
}
</script>
