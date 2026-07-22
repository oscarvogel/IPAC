# Contrato de refactor del frontend IPAC

> Documento vivo. Define las reglas y la hoja de ruta para dividir
> `frontend/src/App.vue` (1127 lineas) en modulos chicos y mantenibles.
>
> **Ultima actualizacion:** 2026-07-22
> **Rama de trabajo:** `refactor/frontend-modular`
> **Origen:** parte desde `main` con el MVP integrado.

---

## 0. Estado del roadmap

- [x] PR 1 - router + aliases ✅ `7bfd254`
- [x] PR 2 - extract api + auth ✅ `331a3d8`
- [x] PR 3 - extract layout ✅ `ae54133`
- [ ] PR 4 - extract alumnos
- [ ] PR 5 - extract caja
- [ ] PR 6 - extract conceptos
- [ ] PR 7 - extract reportes
- [ ] PR 8 - extract sucursales + dashboard
- [ ] PR 9 - Vitest (opcional)

---

## 1. Proposito

El frontend del MVP esta implementado en un unico archivo `App.vue` que
contiene login, sidebar, cinco modulos y cinco modales. Funciona, pero ya
no escala: cada nueva pantalla, filtro o accion obliga a tocar un mismo
archivo y el riesgo de regresion crece.

Este contrato fija las reglas de arquitectura, la estructura objetivo y
el orden de los PRs para que el frontend crezca sin volverse un
Frankenstein.

---

## 2. Estado al cierre de este contrato

- `main` integro el MVP completo (10 commits de `codex/ipac-inicializacion-mvp`).
- `refactor/frontend-modular` es la rama limpia desde donde se trabaja.
- `frontend/src/App.vue` tiene 1127 lineas y sigue siendo el unico componente.
- El backend NO se toca en este refactor. Cualquier cambio de API va en PR aparte.

---

## 3. Decisiones arquitectonicas cerradas

| Tema | Decision | Por que | Reabrir solo si... |
|---|---|---|---|
| Router | **Si, vue-router 4** | Cada modulo ya es una pantalla; hoy se simula con un `activeModule` ref | — |
| Estado global | **Composables, sin Pinia** | Auth y catalogos se cubren con composables; suma 0kb y un solo concepto | Aparece estado reactivo compartido entre 5+ componentes |
| TypeScript | **No, JS** | Coherente con FEMAG y FASA Desktop | Entra un dev TS-first al equipo |
| UI library | **No, CSS custom** | Ya hay sistema visual propio; meter Vuetify/Element lo rompe | Aparece grilla editable o calendario complejo |
| Validacion de forms | **Manual por ahora** | Forms son simples hoy | Wizard de matricula o generacion masiva de cuotas |
| Testing | **Vitest opcional al final** | Prioridad: paridad funcional primero | Se justifica e2e con Playwright |
| Path aliases | **`@/` apunta a `src/`** | Imports limpios, una sola config en `vite.config.js` | — |
| CSS | **Scoped por componente** + `assets/styles/main.css` global | Evita el mega `style.css` actual | — |
| Print | **`assets/styles/print.css` separado** | El resumen de caja y los recibos imprimen bien | — |

---

## 4. Reglas del juego (no negociables)

1. **Cada `view` es tonta.** Compone componentes. Si una view pasa de ~150 lineas, falta un composable o falta partir un componente.
2. **Logica de negocio solo en composables.** Vistas y componentes hacen `const { total } = useCaja()` y nada mas.
3. **Composables exportan `ref`/`computed`/`function`.** Sin clases, sin stores objetos. Patron Vue 3 puro.
4. **CSS scoped por componente.** El `main.css` solo lleva variables CSS, reset y layout global. Si un componente supera ~250 lineas de estilo, mover a `assets/styles/components/<dominio>.css`.
5. **Imports por alias.** `@/components/...`, `@/composables/...`, `@/lib/...`. Cero `../../../`.
6. **Estados locales para cosas locales.** Si es un toggle de un modal, va como `ref` adentro del componente. No todo merece composable.
7. **Componentes con una sola responsabilidad.** "Lista + detalle + form" en un mismo `.vue` es senial de que hay que partir.
8. **No se mete feature nueva durante el refactor.** Paridad funcional primero. Si aparece una mejora, se anota en `BACKLOG_MVP.md` y se hace en PR aparte.
9. **El backend no se toca.** Si mientras refactorizamos aparece "ya que estoy, ajusto X en el API", se abre PR separado contra `main`.
10. **Un PR = una unidad logica.** Si el PR toca 3 modulos, son 3 PRs.

---

## 5. Estructura objetivo

```
frontend/
├── public/
├── src/
│   ├── main.js                  bootstrap, registra router, importa css
│   ├── App.vue                  shell minimal: <RouterView /> + toaster
│   ├── router/
│   │   └── index.js             rutas + guard de auth
│   ├── lib/
│   │   ├── api.js               fetch wrapper con token + errores
│   │   ├── constants.js         medios de pago, tipos, estados
│   │   └── formatters.js        formatMoney, formatDate, formatLegajo
│   ├── composables/
│   │   ├── useAuth.js           login, logout, current user, persistencia token
│   │   ├── useCatalogos.js      sucursales, carreras, conceptos (compartido)
│   │   ├── useAlumnos.js        CRUD + busqueda + estado de cuenta
│   │   ├── usePagos.js          alta de pago + recibo
│   │   ├── useCaja.js           caja del dia + movimientos + cierre + totales
│   │   ├── useReportes.js       filtros + resumen + export CSV
│   │   └── useToast.js          mensajes globales exito/error
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppShell.vue     wrapper con grid principal
│   │   │   ├── AppSidebar.vue   nav + footer usuario
│   │   │   └── AppTopbar.vue    titulo + busqueda global + acciones
│   │   ├── ui/                  primitivos (solo si se usan 3+ veces)
│   │   │   ├── AppButton.vue
│   │   │   ├── AppModal.vue
│   │   │   └── AppTable.vue
│   │   ├── alumnos/
│   │   │   ├── AlumnoList.vue
│   │   │   ├── AlumnoDetail.vue
│   │   │   ├── AlumnoForm.vue
│   │   │   ├── PagoForm.vue
│   │   │   └── EstadoCuentaModal.vue
│   │   ├── caja/
│   │   │   ├── CajaHero.vue
│   │   │   ├── CajaMovimientos.vue
│   │   │   ├── MovimientoForm.vue
│   │   │   └── CerrarCajaModal.vue
│   │   ├── conceptos/
│   │   │   ├── ConceptoList.vue
│   │   │   └── ConceptoForm.vue
│   │   ├── reportes/
│   │   │   ├── ReporteFiltros.vue
│   │   │   ├── ReporteResumen.vue
│   │   │   └── PagosListado.vue
│   │   └── sucursales/
│   │       └── SucursalList.vue
│   ├── views/
│   │   ├── LoginView.vue
│   │   ├── DashboardView.vue
│   │   ├── AlumnosView.vue
│   │   ├── CajaView.vue
│   │   ├── ConceptosView.vue
│   │   ├── ReportesView.vue
│   │   └── SucursalesView.vue
│   └── assets/
│       └── styles/
│           ├── main.css         variables, reset, layout
│           ├── print.css        reglas de impresion (caja, recibos)
│           └── components/      estilos por dominio si crecen
├── package.json
├── vite.config.js               con alias @/ -> src/
└── index.html
```

---

## 6. Roadmap de PRs

Cada PR deja la app funcionando. Paridad funcional primero, mejoras despues.

### PR 1 - `chore(frontend): add vue-router and path aliases` ✅
- Instala `vue-router@4`.
- Configura `@/` en `vite.config.js`.
- Crea `src/router/index.js` con las rutas (placeholders que renderizan `<h1>Modulo X</h1>`).
- `App.vue` se reduce a `<RouterView />` + toaster.
- Mantiene el login gate provisorio.
- **Resultado:** app funciona con URLs (`/login`, `/alumnos`, etc.) pero los modulos son placeholders.
- **Cerrado en commit `7bfd254` sobre `refactor/pr1-router-aliases`.**

### PR 2 - `refactor(frontend): extract api client and auth composable` ✅
- `src/lib/api.js` - fetch wrapper, token header, normalizacion de errores.
- `src/lib/formatters.js` - `formatMoney`, `formatDate`, `formatDateTime`.
- `src/composables/useAuth.js` - login/logout/me, persistencia en localStorage.
- `src/composables/useToast.js` - mensajes globales.
- `src/views/LoginView.vue` - mueve el form de login.
- `App.vue` queda en ~30 lineas: shell + toaster + router guard.
- **Resultado:** login funciona desde `/login`, redirect a `/alumnos` tras exito.
- **Cerrado en commit `331a3d8` sobre `refactor/pr2-api-auth`.**

### PR 3 - `refactor(frontend): extract layout components` ✅
- `AppShell.vue`, `AppSidebar.vue`, `AppTopbar.vue`.
- `App.vue` queda en ~10 lineas.
- Sidebar usa `<router-link>` pero las views siguen siendo placeholders.
- **Resultado:** layout limpio, navegacion con URL real, modulos siguen como placeholders.
- **Cerrado en commit `ae54133` sobre `refactor/pr3-layout`.** Patrón parent route: `/` envuelve con AppShell, los 5 modulos son children; `/login` y 404 quedan top-level.

### PR 4 - `refactor(frontend): extract alumnos module`
- `useAlumnos.js`, `useCatalogos.js`.
- `AlumnosView.vue` + `AlumnoList.vue` + `AlumnoDetail.vue` + `AlumnoForm.vue` + `PagoForm.vue` + `EstadoCuentaModal.vue`.
- **Este es el PR mas grande.** Conviene partirlo en commits chicos: lista -> detail -> form -> modales.
- **Resultado:** pantalla de alumnos funciona identica a antes, en 6 archivos chicos.

### PR 5 - `refactor(frontend): extract caja module`
- `useCaja.js` con la logica de totales.
- `CajaView.vue` + 4 subcomponentes.
- `print.css` con las reglas de impresion.
- **Resultado:** caja, movimientos y cierre funcionan. Resumen imprimible sigue OK.

### PR 6 - `refactor(frontend): extract conceptos module`
- `useConceptos.js` + `ConceptosView.vue` + 2 subcomponentes.
- **Resultado:** alta, edicion y desactivacion de conceptos funciona como antes.

### PR 7 - `refactor(frontend): extract reportes module`
- `useReportes.js` + 3 subcomponentes.
- **Resultado:** listado filtrable + export CSV funcionan.

### PR 8 - `refactor(frontend): extract sucursales module + dashboard`
- `SucursalList.vue` + `SucursalesView.vue`.
- `DashboardView.vue` con los KPIs actuales.
- `/` redirige a `/dashboard`.
- **Resultado:** 5 modulos navegables + dashboard inicial.

### PR 9 (opcional) - `test(frontend): add Vitest setup`
- Instala `vitest` + `@vue/test-utils`.
- Tests para: `useAuth`, `useCaja.totales`, `formatters`.
- Configura `npm test` y dejalo listo para CI.

---

## 7. Convenciones

- **Conventional Commits en espanol**, mismo patron que el resto del repo
  (`feat(frontend): ...`, `refactor(frontend): ...`, `chore(frontend): ...`).
- **Un PR = uno o varios commits chicos relacionados.** Evitar un commit
  gigante con 50 archivos cambiados.
- **No merge a `main` sin verificar paridad funcional manual.** Antes de
  mergear cada PR, abrir la app localmente y probar login + el modulo
  tocado end-to-end.
- **El contrato se actualiza con cada PR.** Al cerrar un item de la
  seccion 6, marcarlo con `[x]` y commitear el cambio en el mismo PR o
  en un micro-commit de docs.
- **Mensajes de commit con cuerpo cuando el cambio no es obvio.** El
  `que` va en el titulo, el `por que` en el cuerpo.

---

## 8. Como retomar (si pasan semanas)

1. Leer este contrato de arriba a abajo.
2. Mirar la seccion 6: el primer checkbox sin tildar es el PR que sigue.
3. `git checkout refactor/frontend-modular` y `git pull`.
4. Crear la rama del PR desde aca: `git checkout -b refactor/pr-N-<slug>`.
5. Al terminar, mergear a `refactor/frontend-modular` y tildar el
   checkbox del contrato en un commit aparte.

Si el contrato quedo desactualizado (alguien lo dejo de lado), la
senial visible es que `App.vue` sigue grande o que aparecieron archivos
`.vue` fuera de la estructura de la seccion 5. Eso es la alerta para
"re-sincronizar" antes de seguir.

---

## 9. Fuera de alcance (no se hace en este refactor)

- Tests e2e con Playwright.
- Migrar a TypeScript.
- Migrar a Pinia (solo si aparece dolor real).
- Agregar UI library (Vuetify, Element, PrimeVue).
- i18n (single-tenant en espanol).
- Dashboard con charts reales (esperar datos reales de IPAC).
- Mejoras de UX que no sean refactor (filtros nuevos, baja de alumnos, etc).
- Cambios al backend.
- Deploy o cambios de Docker.

---

## 10. Riesgos conocidos

- **PR 4 (alumnos) es el de mayor superficie.** Si el diff supera ~600
  lineas, partirlo. La regla: lista primero, detail despues, form al
  final, modales al cierre.
- **`useAuth` debe estar listo antes de PR 4.** Si no, los componentes
  de alumnos van a terminar haciendo fetch a mano con `token`
  importado y queda inconsistente.
- **El CSS de `print` vive en `print.css`.** Moverlo mal hace que el
  resumen de caja deje de imprimirse. Verificar con Ctrl+P en la
  pantalla de caja antes de cerrar el PR 5.
- **No tocar la API.** Si surge "ya que estamos, ajusto X", PR aparte.
- **No meter features nuevas.** Paridad funcional primero. Mejora despues.
