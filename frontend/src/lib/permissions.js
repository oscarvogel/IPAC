export const ROLES = Object.freeze({
  SUPERADMIN: 'superadmin',
  ADMINISTRACION: 'administracion',
  TESORERIA: 'tesoreria',
  CAJA: 'caja',
  CONSULTA: 'consulta',
})

const ROLE_CAPABILITIES = Object.freeze({
  superadmin: ['manage-users', 'manage-alumnos', 'register-payments', 'void-payments', 'manage-fees', 'manage-concepts', 'manage-branches', 'operate-cash', 'import-data'],
  administracion: ['manage-users', 'manage-alumnos', 'register-payments', 'manage-fees', 'manage-concepts', 'manage-branches', 'operate-cash', 'import-data'],
  tesoreria: ['register-payments', 'void-payments', 'manage-fees', 'operate-cash'],
  caja: ['register-payments', 'operate-cash'],
  consulta: [],
})

export function roleOf(user) {
  return typeof user === 'string' ? user : user?.perfil?.rol || ''
}

export function can(user, capability) {
  return ROLE_CAPABILITIES[roleOf(user)]?.includes(capability) || false
}

export function canManageUsers(user) {
  return can(user, 'manage-users')
}

export function canViewRoute(user, roles = []) {
  return !roles.length || roles.includes(roleOf(user))
}
