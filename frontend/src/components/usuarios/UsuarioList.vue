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
        <MotionList tag="tbody" data-motion-list="usuarios-desktop" :animate="animate">
          <tr v-for="usuario in paginatedUsuarios" :key="usuario.id" data-motion-item>
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
                  v-if="canEdit && (canManageSuperadmins || usuario.perfil?.rol !== 'superadmin')"
                  type="button"
                  title="Editar usuario"
                  aria-label="Editar usuario"
                  @click="$emit('edit', usuario)"
                >
                  <PencilSquareIcon aria-hidden="true" />
                </button>
                <button
                  v-if="canDeactivate && (canManageSuperadmins || usuario.perfil?.rol !== 'superadmin') && usuario.is_active"
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
        </MotionList>
      </table>

      <MotionList v-if="sortedUsuarios.length" class="mobile-record-list users-mobile-list" data-motion-list="usuarios-mobile" role="list" :animate="animate">
        <article
          v-for="usuario in paginatedUsuarios"
          :key="`mobile-${usuario.id}`"
          data-motion-item
          class="mobile-record-card user-mobile-card"
          role="listitem"
        >
          <header class="mobile-record-head">
            <span class="users-avatar">{{ avatarInitials(usuario) }}</span>
            <span class="mobile-record-title">
              <strong>{{ usuario.username }}</strong>
              <small>{{ fullName(usuario) }}</small>
            </span>
            <MobileActionMenu :label="`Acciones para ${usuario.username}`">
              <button v-if="canEdit && (canManageSuperadmins || usuario.perfil?.rol !== 'superadmin')" type="button" role="menuitem" @click="$emit('edit', usuario)">
                <PencilSquareIcon aria-hidden="true" />
                <span>Editar usuario</span>
              </button>
              <button
                v-if="canDeactivate && (canManageSuperadmins || usuario.perfil?.rol !== 'superadmin') && usuario.is_active"
                type="button"
                class="danger"
                role="menuitem"
                @click="$emit('deactivate', usuario)"
              >
                <NoSymbolIcon aria-hidden="true" />
                <span>Desactivar</span>
              </button>
            </MobileActionMenu>
          </header>

          <a v-if="usuario.email" class="user-mobile-email" :href="`mailto:${usuario.email}`">
            <EnvelopeIcon aria-hidden="true" />
            {{ usuario.email }}
          </a>
          <span v-else class="user-mobile-email is-empty">
            <EnvelopeIcon aria-hidden="true" />
            Sin email
          </span>

          <dl class="mobile-record-meta">
            <div>
              <dt>Rol</dt>
              <dd>
                <component :is="roleIcon(usuario.perfil?.rol)" aria-hidden="true" />
                {{ roleLabel(usuario.perfil?.rol) }}
              </dd>
            </div>
            <div>
              <dt>Sucursal</dt>
              <dd><BuildingStorefrontIcon aria-hidden="true" />{{ usuario.perfil?.sucursal?.nombre || 'Sin sucursal' }}</dd>
            </div>
            <div>
              <dt>Alcance</dt>
              <dd>
                <component
                  :is="usuario.perfil?.puede_ver_todas_las_sucursales ? GlobeAltIcon : MapPinIcon"
                  aria-hidden="true"
                />
                {{ usuario.perfil?.puede_ver_todas_las_sucursales ? 'Todas las sedes' : 'Sede asignada' }}
              </dd>
            </div>
          </dl>

          <footer class="mobile-record-footer">
            <span :class="['users-status', usuario.is_active ? 'active' : 'inactive']">
              <component :is="usuario.is_active ? CheckCircleIcon : PauseCircleIcon" aria-hidden="true" />
              {{ usuario.is_active ? 'Activo' : 'Inactivo' }}
            </span>
          </footer>
        </article>
      </MotionList>

      <nav v-if="sortedUsuarios.length" class="catalog-pagination" aria-label="Paginación de usuarios">
        <label class="catalog-page-size">
          <span>Mostrar</span>
          <select v-model="pageSize" aria-label="Usuarios por página">
            <option v-for="size in pageSizes" :key="size" :value="size">{{ size }}</option>
          </select>
        </label>
        <button type="button" :disabled="page <= 1" @click="goToPage(page - 1)">Anterior</button>
        <span aria-live="polite">Página {{ page }} de {{ totalPages }} · {{ sortedUsuarios.length }} usuarios</span>
        <button type="button" :disabled="page >= totalPages" @click="goToPage(page + 1)">Siguiente</button>
      </nav>

      <div v-if="!sortedUsuarios.length" class="users-empty-state">
        <span><UserGroupIcon aria-hidden="true" /></span>
        <strong>{{ filtered ? 'No encontramos usuarios' : 'Todavía no hay usuarios cargados' }}</strong>
        <p>{{ filtered ? 'Probá cambiando la búsqueda, la sucursal o el rol seleccionado.' : 'Creá el primer acceso para comenzar a administrar permisos.' }}</p>
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
import MobileActionMenu from '@/components/ui/MobileActionMenu.vue'
import { useClientPagination } from '@/composables/useClientPagination'
import MotionList from '@/components/ui/MotionList.vue'

const props = defineProps({
  usuarios: { type: Array, required: true },
  filtered: { type: Boolean, default: false },
  canEdit: { type: Boolean, default: true },
  canDeactivate: { type: Boolean, default: true },
  canManageSuperadmins: { type: Boolean, default: true },
  animate: { type: Boolean, default: true },
})

defineEmits(['edit', 'deactivate'])

const sortedUsuarios = computed(() =>
  [...props.usuarios].sort((a, b) => {
    if (a.is_active !== b.is_active) return a.is_active ? -1 : 1
    return (a.username || '').localeCompare(b.username || '', 'es', { sensitivity: 'base' })
  }),
)

const {
  page,
  pageSize,
  pageSizes,
  totalPages,
  paginatedItems: paginatedUsuarios,
  goToPage,
} = useClientPagination(sortedUsuarios)

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
