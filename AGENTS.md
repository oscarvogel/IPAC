# AGENTS.md — Guía de agentes para IPAC

Este documento aplica a todo el repositorio. Define cómo deben trabajar los agentes de IA y las personas que implementen cambios en IPAC.

## Regla obligatoria de arquitectura

Antes de analizar, diseñar o implementar cualquier cambio que afecte dominio, API, persistencia, integraciones o límites entre módulos, el agente DEBE cargar y aplicar la skill `clean-ddd-hexagonal`.

La skill es obligatoria para este repositorio. No se debe sustituir por una interpretación informal de DDD, Clean Architecture o Hexagonal. Si la skill no está disponible, el agente debe detener la implementación arquitectónica, informar el bloqueo y solicitar su instalación o disponibilidad.

La aplicación de la skill debe respetar estas reglas:

- Las dependencias apuntan hacia el dominio: `infrastructure/presentation → application → domain`.
- El dominio no importa Django, DRF, ORM, HTTP, SQL, Vue, almacenamiento ni servicios externos.
- Los controladores, viewsets y componentes de entrada coordinan casos de uso; no ejecutan reglas de negocio ni acceden directamente a repositorios.
- Los puertos declaran necesidades; los adaptadores implementan detalles externos.
- Cada agregado tiene una única raíz y un repositorio por agregado, no un repositorio por tabla.
- Las transacciones deben proteger un agregado. La consistencia entre agregados se resuelve mediante casos de uso, eventos de dominio o integración, según necesidad real.
- CQRS, Event Sourcing, microservicios y un bus de eventos no se agregan por moda: solo después de demostrar una necesidad operativa o de dominio.

## Contexto real del proyecto

IPAC es un sistema de administración, tesorería y cobranzas para las sucursales Posadas y Eldorado.

- Backend actual: Django + Django REST Framework en `backend/`.
- Frontend actual: Vue + Vite en `frontend/`.
- Persistencia prevista: PostgreSQL.
- API: `/api/`, actualmente expuesta desde `backend/core/urls.py`.
- Estado arquitectónico: monolito modular inicial. Los modelos y viewsets existentes viven mayormente en `backend/core`; cualquier evolución debe ser incremental.
- Frontend: módulos existentes para alumnos, caja, conceptos, reportes, sucursales, usuarios y autenticación.
- Documentos funcionales de referencia: `README.md`, `docs/PLAN_INICIAL.md`, `docs/BACKLOG_MVP.md` y `docs/CONTRATO_REFACTOR_FRONTEND.md`.

No se debe afirmar que un contexto ya está completamente aislado cuando todavía comparte `core.models`, viewsets o transacciones con otros contextos. En ese caso se debe documentar como contexto lógico en transición.

## Metodología Bounded Context

Un Bounded Context es un límite semántico, no solamente una carpeta o una tabla. Cada contexto debe tener:

1. Lenguaje ubicuo propio y términos definidos.
2. Modelo de dominio propio, aunque inicialmente se ejecute dentro del mismo monolito.
3. Responsabilidad clara y un equipo/agente dueño.
4. Casos de uso explícitos.
5. Puertos de entrada y salida definidos.
6. Reglas de integración documentadas.
7. Pruebas de sus invariantes y de sus contratos.

### Contextos iniciales de IPAC

Estos límites son la propuesta de trabajo basada en el estado actual del sistema. Deben refinarse con el negocio mediante Event Storming o conversaciones con usuarios antes de introducir reglas nuevas.

| Contexto | Responsabilidad | Modelo actual relacionado | Clasificación inicial |
|---|---|---|---|
| Identidad y Acceso | Autenticación, usuario, rol y permisos | `User`, `PerfilUsuario`, `LoginView`, `CurrentUserView` | Genérico / supporting |
| Organización y Sucursales | Sucursales, estado y alcance operativo | `Sucursal`, visibilidad por sucursal | Supporting |
| Alumnos y Trayectoria Académica | Alumno, carrera/curso y matrícula | `Alumno`, `CarreraCurso`, `Matricula` | Core operativo |
| Conceptos y Cobranzas | Conceptos cobrables, cuotas, pagos, aplicaciones y saldos | `ConceptoCobrable`, `Cuota`, `Pago`, `AplicacionPago` | Core operativo |
| Caja y Tesorería | Caja diaria, movimientos, cierre y diferencia | `CajaDiaria`, `MovimientoCaja` | Core operativo |
| Reportes y Consultas | Consultas operativas, resumen y exportaciones | `ReporteResumenView`, consultas agregadas | Supporting / read side |
| Experiencia Web | Navegación, formularios, estados y presentación | `frontend/src/views`, `components`, `composables` | Presentation |

### Mapa de contexto inicial

```text
Identidad y Acceso ──define alcance──> Organización y Sucursales
          │                                      │
          ├──────────── autorización ───────────┼──> Alumnos y Trayectoria
          │                                      │          │
          │                                      └──────────┘
          │                                                 │
          └──────────────── autorización ───────────────> Cobranzas

Alumnos y Trayectoria ──IDs/snapshots publicados──> Cobranzas
Cobranzas ──PagoRegistrado / PagoAplicado──> Caja y Tesorería
Todos los contextos operativos ──consultas/contratos──> Reportes
Contextos de backend ──API estable──> Experiencia Web
```

Reglas del mapa:

- `Pago` pertenece semánticamente a Cobranzas. Caja consume el hecho de que un pago fue registrado y crea su movimiento correspondiente; no debe duplicar la regla de cobro.
- Los contextos no deben importar modelos internos de otro contexto para ejecutar su lógica. Se usan IDs, DTOs, puertos o eventos de integración.
- Si una integración externa futura usa un modelo diferente, debe existir un Anti-Corruption Layer (ACL) dentro del adaptador del contexto que lo consume.
- `shared` solo puede contener tipos realmente compartidos y estables, por ejemplo identificadores, dinero o rangos de fecha. No es un lugar para esconder reglas de negocio ni modelos Django.
- Reportes puede leer modelos/proyecciones optimizadas, pero no debe convertirse en dueño de las reglas transaccionales.

## Agentes especializados

Los siguientes son roles lógicos. Para una tarea concreta se activa el menor conjunto necesario; todos deben respetar la regla obligatoria de `clean-ddd-hexagonal`.

### 1. Agente coordinador de dominio

Responsable de aclarar el objetivo, identificar el Bounded Context afectado, mantener el mapa de contexto y detectar cambios de lenguaje ubicuo.

- Antes de codificar, registra el contexto, actor, comando, resultado y reglas involucradas.
- Evita mezclar cambios de dos contextos en un mismo caso de uso sin justificar la relación.
- Define si una dependencia es Partnership, Customer-Supplier, Published Language, Conformist o ACL.
- Señala decisiones pendientes del negocio como preguntas, no como supuestos silenciosos.
- Rechaza una nueva abstracción si no resuelve una complejidad real.

### 2. Agente guardián de Clean/Hexagonal y SOLID

Responsable de revisar estructura, dependencias y calidad de diseño.

- Verifica que `domain` sea independiente de Django y DRF.
- Exige casos de uso en `application` entre la entrada HTTP y el dominio.
- Revisa que los puertos sean pequeños y orientados a la necesidad del caso de uso.
- Detecta clases o módulos con demasiadas responsabilidades, dependencias concretas y lógica duplicada.
- Mantiene la composición de dependencias en el borde de la aplicación.
- No convierte SOLID en una proliferación de interfaces: una abstracción debe tener consumidores y una razón de cambio clara.

### 3. Agente de Identidad y Acceso

Dueño de autenticación, sesión/token, usuario, rol, permisos y políticas de visibilidad.

- Protege las invariantes de acceso por sucursal y de roles (`superadmin`, `administracion`, `tesoreria`, `caja`, `consulta`).
- Separa identidad de autorización: conocer al usuario no implica decidir qué puede operar.
- Expone una política/puerto de autorización para que otros contextos no dependan directamente de `PerfilUsuario`.
- Nunca acepta sucursal o alcance enviado por el cliente sin validarlo contra el usuario autenticado.
- Prueba acceso permitido, denegado y aislamiento entre sucursales.

### 4. Agente de Organización y Sucursales

Dueño del catálogo y ciclo de vida de Posadas, Eldorado y futuras sucursales.

- Define qué significa que una sucursal esté activa y quién puede verla u operarla.
- Evita que cada contexto replique una política distinta de sucursal.
- Publica contratos de lectura o IDs; no entrega sus modelos internos como dependencia.
- Mantiene las reglas de pertenencia de alumnos, conceptos, carreras, cuotas y cajas.

### 5. Agente de Alumnos y Trayectoria Académica

Dueño de alumno, estado, datos identificatorios, carrera/curso y matrícula.

- Modela comportamientos de negocio, no simples setters de estados.
- Protege unicidad de DNI/legajo y las reglas de matrícula activa por carrera.
- Distingue alumno, carrera/curso y matrícula aunque inicialmente compartan tablas o app Django.
- Publica únicamente la información que Cobranzas necesite para operar, preferentemente por IDs y DTOs.
- No calcula saldos ni modifica cajas.

### 6. Agente de Conceptos y Cobranzas

Dueño de conceptos cobrables, generación de cuotas, descuentos, recargos, pagos, aplicaciones, recibos y saldos.

- Mantiene invariantes: cuota no duplicada por alumno/concepto/período, importes válidos, aplicación no superior al saldo y estados coherentes.
- Modela operaciones como `generarCuotas`, `registrarPago`, `aplicarPago` y `anularCuota`, no como actualización arbitraria de `estado`.
- Mantiene la numeración y los datos del recibo dentro de este contexto.
- Usa transacciones para la consistencia del agregado; no abre una transacción que abarque indiscriminadamente caja, alumnos y reportes.
- Emite contratos de integración para que Caja reaccione sin duplicar la lógica de cobranzas.

### 7. Agente de Caja y Tesorería

Dueño de caja diaria, movimientos, ingresos, egresos, retiros, pases, cierre, total esperado y diferencia.

- Define cuándo una caja está abierta o cerrada y qué operaciones se permiten en cada estado.
- Valida que un movimiento de pago tenga origen y trazabilidad, sin volver a decidir si el pago era válido.
- Hace explícita la idempotencia al consumir `PagoRegistrado`.
- Protege el cierre con una política de autorización y registra la diferencia.
- No consulta ni muta directamente la lógica interna de Cuota o Pago.

### 8. Agente de Reportes y Consultas

Dueño de reportes de deuda, pagos, cajas, sucursales y exportaciones.

- Separa consultas de lectura de comandos que cambian estado.
- Define DTOs de reporte estables y filtros validados (`desde`, `hasta`, sucursal, medio).
- Respeta la autorización y el alcance de sucursal del usuario.
- No coloca reglas transaccionales en `ReporteResumenView` ni en serializers de presentación.
- Puede evolucionar a proyecciones/read models cuando el volumen lo justifique, sin introducir CQRS prematuramente.

### 9. Agente de API e Integración

Dueño de endpoints DRF, serializers, versionado de contratos, adaptadores, ACL y composición de dependencias.

- Mantiene viewsets y APIViews delgados: autenticación de entrada, DTO, invocación del caso de uso y respuesta.
- Traduce errores de dominio a respuestas HTTP consistentes sin filtrar detalles de infraestructura.
- No permite que un serializer sea el lugar principal de las reglas de negocio.
- Documenta cambios incompatibles y mantiene compatibilidad cuando sea posible.
- Usa ACL para importaciones Excel, pasarelas de pago, ARCA, Mercado Pago u otros sistemas externos futuros.

### 10. Agente de Frontend por contexto

Dueño de la experiencia Vue sin mezclar reglas de dominio del backend con presentación.

- Organiza vistas, componentes y composables por capacidad/contexto: `alumnos`, `caja`, `conceptos`, `reportes`, `sucursales`, `usuarios`.
- Mantiene las views delgadas y deja coordinación de API/estado en composables o servicios.
- Consume contratos de API; no reconstruye en JavaScript reglas de saldo, autorización o cierre de caja como fuente de verdad.
- Mantiene componentes con una sola responsabilidad, CSS scoped y alias `@/`, conforme a `docs/CONTRATO_REFACTOR_FRONTEND.md`.
- Conserva accesibilidad, estados de carga/error/vacío y navegación por teclado en cada flujo modificado.

### 11. Agente de pruebas y arquitectura

Responsable de convertir invariantes y límites en evidencia verificable.

- Tests unitarios del dominio sin Django, base de datos ni HTTP.
- Tests de aplicación con puertos falsos o mocks mínimos.
- Tests de integración de adaptadores y API con Django/DRF.
- Tests de contrato para endpoints y eventos publicados.
- Tests de autorización y aislamiento entre sucursales.
- Tests frontend con Vitest para composables, componentes y estados de interacción.
- Revisa dependencias prohibidas y regresiones antes de aprobar el cambio.

## Estructura objetivo para evolución incremental

No se debe mover todo el backend en una sola operación. Para código nuevo o refactorizado, usar el contexto como primera carpeta:

```text
backend/core/contexts/<contexto>/
├── domain/
│   ├── entities/          # entidades y raíces de agregado
│   ├── value_objects/     # objetos inmutables
│   ├── events/            # eventos de dominio, en pasado
│   ├── repositories/      # puertos de persistencia por agregado
│   └── services/          # lógica que no pertenece a una entidad
├── application/
│   ├── commands/queries/  # DTOs de entrada
│   ├── use_cases/         # casos de uso
│   └── ports/             # puertos de entrada/salida
├── infrastructure/
│   ├── persistence/       # adaptadores ORM/repositorios
│   ├── messaging/         # publicación/consumo de eventos
│   └── external/          # ACLs e integraciones externas
└── presentation/
    └── http/              # serializers, viewsets y mapeo HTTP
```

Durante la transición, el código existente en `backend/core/models.py`, `serializers.py` y `views.py` puede permanecer operativo. El agente debe evitar mezclar una extracción arquitectónica con una funcionalidad no relacionada y dejar claro qué parte sigue siendo legado compartido.

Para frontend se mantiene la estructura existente y se agrupa por contexto cuando corresponda:

```text
frontend/src/
├── views/
├── components/<contexto>/
├── composables/use<Contexto>.js
├── lib/api.js              # adaptador HTTP, no reglas de negocio
└── components/ui/          # primitivas realmente reutilizadas
```

## SOLID aplicado a IPAC

### S — Single Responsibility

Una clase, función, view, composable o componente debe tener un motivo principal de cambio. Un viewset no debe validar reglas, persistir, publicar eventos y formatear el dominio al mismo tiempo.

### O — Open/Closed

Las nuevas formas de pago, exportadores o políticas de reporte deben poder agregarse mediante estrategias/puertos cuando exista variación real, sin editar una cadena de condicionales central. No se abstraen variaciones hipotéticas.

### L — Liskov Substitution

Un adaptador de repositorio, proveedor de exportación o política de autorización debe cumplir el contrato completo de su puerto, incluyendo errores, límites e idempotencia. No se aceptan implementaciones que devuelvan datos parciales fingiendo ser equivalentes.

### I — Interface Segregation

Los casos de uso dependen de puertos mínimos, por ejemplo `AlumnoReader`, `PagoRepository` o `CajaWriter`, en lugar de una interfaz gigante con todo el CRUD del sistema.

### D — Dependency Inversion

El dominio y la aplicación dependen de abstracciones propias. Django, PostgreSQL, DRF, fetch y proveedores externos son detalles reemplazables implementados en infraestructura o presentación.

## Flujo obligatorio de trabajo

1. Leer este `AGENTS.md`, la skill `clean-ddd-hexagonal` y la documentación funcional relevante.
2. Revisar el estado real del código, tests, rutas, modelos, contratos y rama antes de proponer una solución.
3. Identificar contexto, subdominio, lenguaje ubicuo, agregado e invariantes afectados.
4. Escribir o actualizar el caso de uso y sus puertos antes de conectar ORM, HTTP o UI.
5. Implementar el dominio sin infraestructura; después la aplicación; finalmente los adaptadores.
6. Validar integraciones entre contextos mediante DTOs, eventos o ACL. No importar modelos internos por comodidad.
7. Mantener cambios pequeños y trazables. Una unidad lógica por PR/commit.
8. Ejecutar las pruebas proporcionales al cambio y separar evidencia automatizada de validación visual o de producción.
9. Revisar `git diff --check`, dependencias hacia afuera y regresiones de autorización.
10. Informar explícitamente qué se verificó, qué quedó pendiente y qué deuda arquitectónica se mantuvo por compatibilidad.

## Definition of Done

Un cambio no se considera terminado si no cumple, según corresponda:

- Contexto y dueño identificados.
- Lenguaje ubicuo y reglas/invariantes documentados.
- Caso de uso explícito y entrada HTTP/UI delgada.
- Dependencias hacia adentro y puertos pequeños.
- Sin acceso directo de controladores a repositorios.
- Sin reglas de negocio en serializers, templates o componentes Vue.
- Pruebas de dominio/aplicación y de integración cuando se modifique un adaptador.
- Autorización por rol y sucursal cubierta.
- Contratos de API/eventos actualizados si cambiaron.
- `python backend/manage.py check`, tests relevantes, build frontend y `git diff --check` ejecutados cuando apliquen.
- Limitaciones de la evidencia declaradas: un test o build no demuestra por sí solo la aceptación visual en navegador ni el comportamiento del entorno productivo.

## Prohibiciones

- No crear un `GodService`, `GodViewSet`, `GodComposable` o módulo compartido sin límites.
- No agregar `shared` como cajón de sastre.
- No usar el ORM como modelo de dominio por defecto en código nuevo.
- No llamar repositorios desde views, componentes o serializers.
- No duplicar una entidad entre contextos sin documentar la traducción y la propiedad de cada modelo.
- No hacer cambios de base de datos, API o backend dentro de un trabajo declarado exclusivamente frontend.
- No introducir CQRS, Event Sourcing, microservicios o un framework nuevo sin decisión explícita y evidencia de necesidad.
- No marcar una tarea como completa basándose solo en archivos creados: se debe verificar el código y los checks que correspondan.

## Comandos de verificación habituales

Desde la raíz del repositorio, usando el entorno local cuando esté disponible:

```powershell
.\.venv\Scripts\python.exe backend\manage.py check
.\.venv\Scripts\python.exe backend\manage.py test core
npm --prefix frontend run build
git diff --check
```

Los comandos se adaptan al alcance del cambio. Si una dependencia o servicio no está disponible, el agente debe informarlo y no presentar la validación como completa.
