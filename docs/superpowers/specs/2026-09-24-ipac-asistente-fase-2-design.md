# Asistente IPAC — Fase 2: consultas operativas, base de conocimiento y seguimiento

Fecha: 2026-09-24  
Estado: diseño para revisión  
Rama base: `feat/ipac-chatbot-operativo`  
Alcance: evolución del Asistente IPAC V1 ya desplegable en staging.

## 1. Objetivo

La Fase 2 convierte el asistente actual, que hoy explica procedimientos, en un asistente operacional capaz de:

1. Responder preguntas sobre datos reales de IPAC mediante consultas internas de sólo lectura.
2. Mantener su conocimiento funcional desde una interfaz administrativa, sin recompilar ni desplegar cada vez que cambia un procedimiento.
3. Rechazar explícitamente preguntas ajenas a IPAC en lugar de comportarse como un chatbot general.
4. Registrar las preguntas de IPAC que no pudo responder para que puedan convertirse en nuevo conocimiento.
5. Notificar por email, de forma configurable, las consultas no resueltas relevantes.
6. Mantener las restricciones actuales de rol y sucursal en todas las respuestas.

El asistente no debe inventar importes, alumnos, botones, rutas ni estados. Cuando no disponga de información suficiente debe decirlo de forma explícita.

## 2. Fuera de alcance

Esta fase no permitirá que el asistente modifique datos de negocio. No podrá registrar pagos, generar cuotas, crear alumnos, cerrar caja, anular operaciones ni ejecutar ninguna otra acción transaccional.

Tampoco tendrá acceso a SQL libre, a un intérprete de consultas genérico ni a un ORM expuesto al modelo de IA. MiniMax sólo podrá seleccionar intenciones y herramientas previamente autorizadas por la aplicación.

La API key de IA seguirá siendo una variable de entorno del backend y no será visible ni editable desde el frontend.

## 3. Decisiones principales

### 3.1 Dominio cerrado

El Asistente IPAC sólo responde sobre IPAC y sus procesos administrativos.

Ejemplo fuera de alcance:

> Usuario: ¿Cómo se cura la gripe?  
> Asistente: Mi función está limitada al sistema IPAC. No puedo responder consultas generales sobre salud, noticias u otros temas.

La respuesta fuera de alcance será fija y controlada por la aplicación. No se enviará la pregunta a un generador de respuestas generales.

Las consultas fuera de alcance se registrarán para auditoría del uso del asistente, pero no generarán email por defecto.

### 3.2 Dos fuentes de respuesta

El asistente tendrá dos fuentes autorizadas:

- **Conocimiento funcional**: artículos administrables con procedimientos, pasos, rutas y permisos.
- **Datos vivos**: herramientas internas de sólo lectura que consultan IPAC respetando usuario, rol y sucursal.

MiniMax-M3 se utilizará para interpretar lenguaje natural, clasificar intención y redactar una respuesta basada exclusivamente en el conocimiento o en el resultado de una herramienta. No será fuente de datos de negocio.

### 3.3 Sin SQL generado por IA

El modelo nunca producirá ni ejecutará SQL. Cada consulta de datos reales se resolverá mediante un catálogo cerrado de herramientas implementadas en backend.

El resultado de cada herramienta tendrá un esquema estable y sólo contendrá la información necesaria para contestar la pregunta.

### 3.4 Misma semántica financiera que el sistema

Los cálculos de deuda, vencimiento, pagos y caja no se duplicarán con fórmulas nuevas dentro del chatbot. Se reutilizarán o extraerán los cálculos ya usados por:

- `ReporteResumenView`;
- `DeudoresView.build_queryset`;
- `CajaDiaria.resumen`;
- filtros y reglas actuales de `Pago`, `Cuota` y `AplicacionPago`.

Así, “deuda total” tendrá el mismo significado en el asistente que en los reportes de IPAC: saldo de cuotas no anuladas, descontando aplicaciones activas y considerando descuentos/recargos vigentes.

## 4. Flujo de una pregunta

El flujo será:

```text
Usuario
  ↓
ChatbotMessageView
  ↓
Caso de uso ResponderConsulta
  ↓
normalización + contexto usuario/sucursal
  ↓
¿coincide claramente con un artículo?
  ├─ sí → responder desde Base de conocimiento
  └─ no
       ↓
clasificador de intención
       ↓
scope = out_of_scope
  ├─ sí → respuesta fija + registro
  └─ no
       ↓
intent = read_tool
  ├─ sí → validar argumentos/permisos
  │        ↓
  │      ejecutar herramienta read-only
  │        ↓
  │      redactar respuesta con resultado
  └─ no
       ↓
intent = knowledge_unknown
       ↓
respuesta “no tengo información suficiente”
       ↓
registrar consulta no resuelta
       ↓
notificar según configuración
```

Las coincidencias determinísticas conocidas seguirán funcionando aun si MiniMax no está disponible.

## 5. Contrato de clasificación

Para consultas que no coincidan directamente con un artículo o una regla conocida, el adaptador de IA deberá devolver una estructura validable equivalente a:

```json
{
  "scope": "ipac",
  "intent": "read_tool",
  "tool": "resumen_deuda",
  "arguments": {
    "sucursal": null,
    "alumno": null,
    "desde": null,
    "hasta": null
  }
}
```

Valores permitidos:

- `scope`: `ipac`, `out_of_scope`, `uncertain`.
- `intent`: `knowledge`, `read_tool`, `unknown`.
- `tool`: solamente nombres registrados en el catálogo interno.

El backend validará siempre el resultado antes de ejecutar una herramienta. Un nombre de herramienta o argumento no autorizado se tratará como consulta no resuelta/error de clasificación, nunca como una instrucción ejecutable.

El diseño no dependerá obligatoriamente de function calling nativo del proveedor. El adaptador podrá usar salida estructurada/JSON y validación server-side para mantener compatibilidad con MiniMax-M3 y futuros proveedores.

## 6. Catálogo inicial de herramientas de sólo lectura

### 6.1 `resumen_deuda`

Responde preguntas como:

- “¿Cuánto es la deuda total?”
- “¿Cuánto está vencido?”
- “¿Cuántos alumnos deben?”
- “¿Cuánto deben en Posadas?”

Resultado mínimo:

```json
{
  "scope_label": "Posadas",
  "deuda_total": "1250000.00",
  "deuda_vencida": "810000.00",
  "alumnos_con_deuda": 143,
  "cuotas_pendientes": 325,
  "cuotas_vencidas": 207,
  "as_of": "2026-09-24"
}
```

### 6.2 `estado_cuenta_alumno`

Responde preguntas como:

- “¿Cuánto debe Juan Pérez?”
- “¿Qué cuotas tiene pendientes el legajo 1234?”
- “¿Tiene saldo a favor María Gómez?”

Debe buscar por legajo, nombre/apellido o DNI dentro del alcance permitido. Si hay más de una coincidencia razonable, el asistente pedirá aclaración y no elegirá por su cuenta.

Resultado mínimo:

- alumno y legajo;
- sucursal;
- deuda total;
- deuda vencida;
- cantidad de cuotas pendientes/vencidas;
- saldo a favor;
- fecha del último pago;
- resumen de cuotas relevantes cuando la pregunta lo requiera.

No se devolverán datos personales adicionales si no son necesarios para la respuesta.

### 6.3 `resumen_cobranzas`

Responde:

- “¿Cuánto cobramos hoy?”
- “¿Cuánto se cobró por transferencia?”
- “¿Cuánto cobramos este mes?”

Resultado:

- período;
- alcance;
- total cobrado;
- cantidad de pagos;
- total por medio de pago.

Sólo considera pagos activos, igual que los reportes actuales.

### 6.4 `caja_hoy`

Responde:

- “¿Cómo está mi caja?”
- “¿Cuánto efectivo debería tener?”
- “¿Mi caja está abierta o cerrada?”

Reutiliza la semántica actual de caja: saldo inicial, efectivo esperado, contado, diferencia, retirado y saldo arrastrable cuando correspondan.

Por defecto consulta la caja del usuario actual. Una consulta por otra sucursal sólo se acepta si el perfil tiene alcance global y la semántica del caso de uso permite esa consulta.

### 6.5 `resumen_cuotas`

Responde cantidades e importes de cuotas pendientes, vencidas, pagadas o anuladas por período/sucursal/carrera cuando los filtros estén permitidos.

### 6.6 `resumen_alumnos`

Responde conteos de alumnos por estado, sucursal o carrera/curso.

### 6.7 `buscar_alumno`

Herramienta auxiliar para resolver referencias por nombre, apellido, DNI o legajo. Si encuentra múltiples coincidencias devuelve candidatos mínimos para que el usuario seleccione uno.

## 7. Reglas de alcance y permisos

Todas las herramientas partirán de la identidad autenticada. El LLM no podrá elegir ni alterar el alcance efectivo.

Reglas:

- Usuario sin perfil operativo: no puede usar el asistente.
- Usuario con cambio de clave obligatorio: mantiene las restricciones generales del sistema.
- Usuario sin `puede_ver_todas_las_sucursales`: todas las consultas quedan forzadas a su sucursal.
- Usuario con acceso global:
  - si menciona una sucursal válida, se usa esa sucursal;
  - si pregunta por un total sin especificar sucursal, el total abarca todas las sucursales accesibles y la respuesta debe decirlo explícitamente.
- Si se solicita una sucursal fuera del alcance, la herramienta devuelve “sin permiso”; no devuelve datos parciales de esa sucursal.
- Cada respuesta con cifras debe indicar el alcance utilizado: por ejemplo “Posadas”, “Eldorado” o “todas las sucursales”.
- Ninguna herramienta de Fase 2 realiza escrituras sobre alumnos, cuotas, pagos o caja.

## 8. Base de conocimiento editable

### 8.1 Modelo `AsistenteKnowledgeArticle`

Campos:

- `clave`: identificador único estable.
- `titulo`.
- `modulo`: alumnos, cobranzas, cuotas, caja, reportes, configuración, importación u otro.
- `preguntas_equivalentes`: lista de frases/aliases.
- `descripcion`: explicación breve opcional.
- `pasos`: lista ordenada de instrucciones.
- `ruta`: ruta interna opcional.
- `action_label`: texto del botón/deep link opcional.
- `roles_permitidos`: lista de roles para los que el procedimiento es válido.
- `notas`: lista opcional.
- `activo`.
- `orden`.
- `creado_por` y `actualizado_por`.
- timestamps estándar.

Los procedimientos estáticos actuales de `backend/core/chatbot/knowledge.py` se migrarán a esta tabla mediante una migración de datos. Después de esa migración, la base de datos será la fuente de conocimiento en runtime.

### 8.2 Interfaz

Ruta:

`Configuración → Asistente IA`

URL propuesta:

`/configuracion/asistente`

La pantalla tendrá tres secciones:

1. **Base de conocimiento**
2. **Consultas no resueltas**
3. **Notificaciones**

La Base de conocimiento permitirá:

- buscar por título/pregunta;
- filtrar por módulo y estado;
- crear artículo;
- editar;
- activar/desactivar;
- ordenar pasos;
- administrar preguntas equivalentes;
- definir deep link;
- definir roles permitidos.

Guardar un artículo tendrá efecto inmediato en las siguientes conversaciones. No requerirá reiniciar backend ni desplegar.

Superadmin y Administración podrán administrar artículos. Los demás roles sólo consumirán el conocimiento aplicable a su rol.

## 9. Consultas no resueltas

### 9.1 Modelo `AsistenteConsultaNoResuelta`

Cada evento conserva:

- conversación;
- mensaje del usuario;
- usuario;
- sucursal de contexto;
- pregunta original;
- pregunta normalizada;
- categoría;
- intención detectada, si existe;
- herramienta solicitada, si existe;
- respuesta entregada;
- metadata técnica no sensible;
- estado: `pendiente`, `resuelta`, `ignorada`;
- artículo de conocimiento relacionado, opcional;
- resuelto_por;
- resuelto_en;
- notificado_en;
- timestamps.

Categorías:

- `no_documentada`: pregunta válida sobre IPAC sin conocimiento suficiente.
- `sin_datos`: pregunta válida pero no hay datos que permitan contestar.
- `sin_permiso`: intenta acceder a información fuera de su alcance.
- `fuera_de_alcance`: pregunta ajena a IPAC.
- `error_ia`: proveedor no disponible o respuesta inválida.
- `error_herramienta`: fallo inesperado al obtener datos.

Una ambigüedad resolvible —por ejemplo dos alumnos llamados igual— no se considera inicialmente una consulta no resuelta: el bot debe pedir aclaración.

### 9.2 Interfaz administrativa

“Consultas no resueltas” permitirá filtrar por:

- pendiente/resuelta/ignorada;
- categoría;
- fecha;
- usuario;
- sucursal.

Acciones:

- marcar como resuelta;
- ignorar;
- abrir conversación asociada;
- “Crear artículo desde esta pregunta”.

“Crear artículo desde esta pregunta” abre el formulario de conocimiento precargando la pregunta como alias y vinculando el nuevo artículo con el evento. Al guardar, el evento puede marcarse resuelto.

No se borrará el historial original.

## 10. Notificaciones por email

### 10.1 Configuración funcional

Modelo singleton `AsistenteConfig`:

- `email_habilitado`;
- `modo_email`: `desactivado`, `inmediato`, `diario`;
- `destinatarios`: lista de emails;
- `incluir_fuera_de_alcance`: default `false`;
- `hora_resumen_diario`: default `18:00`;
- `ultimo_resumen_exitoso_en`;
- `actualizado_por`.

Superadmin podrá cambiar notificaciones. Administración podrá ver la configuración pero no cambiar destinatarios ni modo de envío.

SMTP seguirá configurándose por variables de entorno de Django; las credenciales no se guardarán en la base ni se mostrarán en la UI.

### 10.2 Modo inmediato

Al crear una consulta no resuelta se enviará email cuando:

- la notificación esté habilitada;
- la categoría sea `no_documentada`, `sin_datos`, `error_ia` o `error_herramienta`;
- existan destinatarios.

`fuera_de_alcance` sólo se notifica si `incluir_fuera_de_alcance=true`.

Un error de email no debe impedir la respuesta del chatbot. El evento queda guardado y sin `notificado_en` para permitir reintento.

### 10.3 Resumen diario

Se implementará un comando de gestión idempotente, por ejemplo:

`python manage.py enviar_resumen_asistente`

El deployment programará ese comando en Coolify a la hora definida. El comando enviará los eventos pendientes de notificación desde el último resumen exitoso y, tras un envío correcto, marcará `notificado_en`.

Si no hay eventos relevantes, no envía correo.

## 11. Arquitectura propuesta

El nuevo código de backend se organizará como un contexto de asistente:

```text
backend/core/contexts/asistente/
  domain/
    intents.py
    scope.py
    tool_result.py
  application/
    responder_consulta.py
    clasificar_consulta.py
    ejecutar_herramienta.py
    gestionar_conocimiento.py
    registrar_no_resuelta.py
    notificar_no_resueltas.py
  infrastructure/
    django_knowledge_repository.py
    django_assistant_repository.py
    django_reporting_gateway.py
    minimax_provider.py
    django_email_notifier.py
  presentation/
    views.py
    serializers.py
```

El código actual de `core/chatbot` quedará como fachada compatible con los endpoints V1 mientras la lógica se traslada al contexto.

Dependencias:

```text
presentation → application → domain
infrastructure ─────────────→ domain/application ports
```

Los adaptadores Django conocen ORM, email y settings. La lógica de decisión del asistente no debe depender de DRF ni de detalles de MiniMax.

## 12. Contratos internos

### 12.1 `AIIntentClassifier`

Entrada:

- pregunta;
- últimas interacciones relevantes;
- catálogo permitido de intenciones/herramientas;
- contexto no sensible de rol/sucursal.

Salida validada:

- scope;
- intent;
- tool;
- arguments.

### 12.2 `ReadToolRegistry`

Responsabilidades:

- registrar sólo herramientas aprobadas;
- validar nombre y argumentos;
- resolver el alcance efectivo desde el usuario;
- ejecutar el caso de uso;
- devolver `ToolResult`.

No acepta código, SQL, nombres de modelo ni expresiones arbitrarias proporcionadas por la IA.

### 12.3 `KnowledgeRepository`

Responsabilidades:

- buscar artículos activos;
- filtrar por rol;
- resolver aliases;
- entregar contenido estructurado para respuesta;
- permitir CRUD sólo a administradores autorizados.

## 13. API HTTP

Se mantienen los endpoints de conversación existentes.

Nuevos endpoints administrativos propuestos:

```text
GET/POST   /api/asistente/conocimiento/
GET/PATCH  /api/asistente/conocimiento/{id}/
POST       /api/asistente/conocimiento/{id}/activar/
POST       /api/asistente/conocimiento/{id}/desactivar/

GET         /api/asistente/no-resueltas/
PATCH       /api/asistente/no-resueltas/{id}/
POST        /api/asistente/no-resueltas/{id}/resolver/
POST        /api/asistente/no-resueltas/{id}/ignorar/
POST        /api/asistente/no-resueltas/{id}/crear-articulo/

GET/PATCH   /api/asistente/configuracion/
```

Las herramientas read-only no se expondrán como API genérica para MiniMax. Se invocarán dentro del backend mediante casos de uso.

## 14. Auditoría

Se conserva `ChatbotMessage` como historial de conversación por usuario.

Además:

- cada consulta no resuelta se registra en `AsistenteConsultaNoResuelta`;
- altas, cambios, activaciones y bajas lógicas de artículos generan `EventoAuditoria`;
- cambios de configuración de notificaciones generan `EventoAuditoria`;
- resolver/ignorar una consulta genera `EventoAuditoria`;
- no se registran API keys ni secretos en auditoría o metadata.

No se duplicará cada respuesta satisfactoria en `EventoAuditoria`, porque el historial de conversación ya cubre ese caso y evitará inflar la auditoría general.

## 15. Mensajes controlados

### Pregunta de IPAC resuelta con datos

> La deuda pendiente es de $1.250.000, de los cuales $810.000 están vencidos. Hay 143 alumnos con saldo pendiente. Alcance: Posadas. Datos al 24/09/2026.

### Pregunta válida sin conocimiento

> No tengo información suficiente para responder esa consulta de forma confiable. La registré para que pueda incorporarse a mi base de conocimiento.

### Sin permiso

> Esa consulta requiere información de una sucursal a la que tu usuario no tiene acceso.

### Fuera de alcance

> Mi función está limitada al sistema IPAC. No puedo responder consultas generales sobre salud, noticias u otros temas.

### Error temporal de IA

> No pude interpretar esa consulta en este momento. La registré para revisión. Las consultas conocidas del sistema siguen disponibles.

El sistema no deberá decir “la registré” si por un error de persistencia el registro no pudo crearse.

## 16. Manejo de errores

- Si MiniMax falla pero existe match determinístico de conocimiento o herramienta: se responde sin depender de MiniMax.
- Si MiniMax falla y la consulta necesita clasificación: se responde con error temporal y se registra `error_ia`.
- Si una herramienta falla: no se entrega un número parcial ni inventado; se registra `error_herramienta`.
- Si no hay datos: se responde “no hay datos disponibles para ese alcance/período”, no cero salvo que la herramienta pueda demostrar que el valor correcto es cero.
- Si el alumno es ambiguo: se presentan candidatos mínimos y se solicita selección.
- Si falla el email: no afecta la conversación.
- Si la base de conocimiento está vacía: las herramientas de datos pueden seguir funcionando y las preguntas procedimentales desconocidas se registran.

## 17. Seguridad

- API key de IA sólo en backend.
- Nada de SQL generado.
- Nada de ejecución dinámica de Python.
- Catálogo de herramientas allowlist.
- Argumentos validados con esquemas.
- Alcance de sucursal resuelto server-side.
- Sin herramientas de escritura en Fase 2.
- La IA no recibe datasets completos: sólo resultados mínimos de la herramienta necesaria.
- Las respuestas nunca amplían los permisos del usuario.
- Las entradas de Base de conocimiento son texto/estructura administrativa; no pueden introducir herramientas nuevas ni permisos nuevos.
- Toda ruta/deep link del conocimiento debe ser una ruta interna permitida.

## 18. Migraciones

La rama ya contiene la migración `0016_chatbotconversation_chatbotmessage`.

La Fase 2 agregará migraciones posteriores para:

- `AsistenteKnowledgeArticle`;
- `AsistenteConsultaNoResuelta`;
- `AsistenteConfig`;
- relaciones e índices.

Se incluirá una data migration que copie los procedimientos actuales de `PROCEDURES` a `AsistenteKnowledgeArticle`. Los valores se congelarán dentro de la migración; no se importará código mutable de runtime desde la migración.

Después de completar esa migración, runtime consultará la base de conocimiento persistida y no el diccionario estático.

## 19. Índices y volumen

Índices mínimos:

- artículo: `activo`, `modulo`, `clave`;
- no resuelta: `estado + creado`, `categoria + creado`, `usuario + creado`, `sucursal + creado`, `pregunta_normalizada`;
- conversación: se conserva el índice natural por usuario/conversación.

La lista administrativa será paginada desde backend.

## 20. Pruebas

### Backend

Se deberán cubrir al menos:

- match de artículo persistido;
- artículo desactivado deja de responder;
- cambio de artículo toma efecto sin reinicio;
- filtro de artículo por rol;
- deuda total igual a la semántica de reportes;
- deuda vencida;
- saldo de alumno;
- alumno ambiguo;
- cobranzas por período y medio;
- caja del usuario;
- usuario restringido no ve otra sucursal;
- usuario global puede obtener total global y filtro por sucursal;
- intento de herramienta no registrada es rechazado;
- pregunta fuera de alcance no obtiene respuesta general de MiniMax;
- pregunta válida desconocida crea consulta no resuelta;
- error de MiniMax crea `error_ia`;
- error de herramienta crea `error_herramienta`;
- email inmediato según categorías;
- fuera de alcance no envía email por defecto;
- fallo SMTP no rompe respuesta;
- CRUD de conocimiento sólo para roles permitidos;
- configuración de email sólo editable por Superadmin;
- no exposición de API key.

### Frontend

Se cubrirá:

- tarjeta “Asistente IA” en Configuración;
- acceso por rol;
- listado/filtros de artículos;
- alta/edición/activar/desactivar;
- listado/filtros de no resueltas;
- crear artículo desde una consulta;
- marcar resuelta/ignorada;
- configuración de notificaciones;
- comportamiento responsive.

### Regresión

La suite existente completa deberá continuar verde. El pipeline seguirá ejecutando:

- `python backend/manage.py check`;
- `python backend/manage.py makemigrations --check --dry-run`;
- tests backend;
- tests frontend;
- build frontend.

## 21. Criterios de aceptación

La fase se considera apta para staging cuando se cumplan todos estos casos:

1. Un usuario restringido pregunta “¿cuánto es la deuda total?” y recibe el importe real exclusivamente de su sucursal, con el alcance visible.
2. Un usuario global hace la misma pregunta y recibe el total de todas las sucursales accesibles, identificado como global.
3. “¿Cuánto debe <alumno>?” usa datos reales y pide aclaración si el nombre es ambiguo.
4. “¿Cuánto cobramos hoy?” devuelve total real y puede desglosar por medio.
5. “¿Cómo está mi caja?” devuelve el estado real de la caja del usuario.
6. “¿Cómo se cura la gripe?” recibe únicamente el mensaje de fuera de alcance.
7. Una pregunta válida sobre IPAC sin respuesta queda visible en “Consultas no resueltas”.
8. Desde esa consulta se puede crear un artículo y, desde la siguiente pregunta equivalente, el asistente ya responde con el nuevo conocimiento.
9. Un artículo puede desactivarse sin borrarse y deja de participar del matching inmediatamente.
10. Las consultas relevantes no resueltas pueden generar email según configuración.
11. Las preguntas fuera de alcance no generan email por defecto.
12. Ninguna pregunta del asistente modifica datos de alumnos, cuotas, pagos o caja.
13. Un usuario nunca puede obtener datos de una sucursal que no tenga autorizada.
14. La API key no aparece en respuestas API, HTML, JavaScript ni configuración visible.
15. La CI completa queda verde sobre el commit que se despliegue a staging.

## 22. Despliegue y compatibilidad

La Fase 2 se desarrollará sobre una rama separada derivada de `feat/ipac-chatbot-operativo`.

El despliegue seguirá usando el compose actual, que ejecuta `python manage.py migrate` antes de Gunicorn.

La configuración MiniMax existente se conserva:

```env
IPAC_AI_ENABLED=1
IPAC_AI_PROVIDER=minimax
IPAC_AI_API_KEY=<secreto>
IPAC_AI_MODEL=MiniMax-M3
IPAC_AI_BASE_URL=https://api.minimax.io/v1/chat/completions
IPAC_AI_TIMEOUT_SECONDS=30
```

Para email se agregarán las variables SMTP estándar necesarias en backend. Las credenciales SMTP se gestionarán únicamente en el entorno de despliegue.

El PR de Fase 1 permanecerá separado hasta decidir la estrategia final de integración. No se mergeará a `main` como parte de escribir esta especificación.

## 23. Decisión sobre la skill de arquitectura

Por instrucción explícita del usuario para esta etapa, esta especificación y la posterior implementación no dependen de ejecutar `clean-ddd-hexagonal` en ChatGPT. La validación de esa skill se realizará localmente por el usuario al bajar la rama.

Aun así, el diseño mantiene los límites `domain/application/infrastructure/presentation` ya presentes en el repositorio para reducir acoplamiento y facilitar esa validación local posterior.
