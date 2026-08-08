# Design QA — menú de sesión de IPAC

- Source visual truth path: captura adjunta por el usuario en la conversación actual.
- Implementation screenshot path: no disponible; el navegador integrado no está conectado en esta sesión.
- Source crop: sidebar móvil/estrecha, aproximadamente 273 × 323 px.
- Intended comparison viewport: misma anchura visible de sidebar y estado expandido.
- State: usuario administrador autenticado, menú de sesión abierto.

## Full-view comparison evidence

La captura de origen muestra tres problemas visibles: el botón de opciones desborda su columna, el panel blanco aparece separado de la tarjeta de usuario y la acción “Gestionar usuarios” pierde contraste. El código fue corregido, pero falta una captura renderizada posterior para hacer una comparación visual válida.

## Focused-region comparison evidence

El análisis se concentró en la tarjeta inferior de usuario. No se evaluaron otras regiones porque el cambio está limitado a este componente.

## Required fidelity surfaces

- Fonts and typography: se mantiene Inter y la jerarquía existente; sin cambios de fuente.
- Spacing and layout rhythm: la columna de acciones ahora reserva 34 px para un control de 32 px y el detalle se integra dentro de la tarjeta.
- Colors and visual tokens: el detalle usa la paleta azul de la sidebar y contraste blanco; se eliminaron los estilos heredados que apagaban la acción.
- Image quality and asset fidelity: no hay recursos raster nuevos; todos los iconos continúan siendo Heroicons.
- Copy and content: se eliminó la identidad duplicada y se conservan rol, sucursal, alcance y acceso a usuarios.

## Findings

- [P2] Verificación visual posterior bloqueada.
  - Location: `AppSidebar`, menú de sesión expandido.
  - Evidence: las pruebas y el build pasan, pero no existe una captura renderizada posterior en esta sesión.
  - Impact: no puede confirmarse visualmente el resultado final en el mismo viewport de la referencia.
  - Fix: recargar la aplicación, abrir el menú y capturar la misma región para una comparación final.

## Comparison history

- Pass 1: se identificaron desborde del botón, panel desconectado, contenido duplicado y contraste insuficiente.
- Fixes: columna ampliada, selectores CSS con especificidad correcta, panel integrado y paleta oscura coherente.
- Pass 2: bloqueado por falta de navegador para capturar la implementación corregida.

## Implementation checklist

- [x] Corregir ancho de la columna del botón.
- [x] Evitar que estilos heredados anulen controles del footer.
- [x] Integrar los detalles en la tarjeta de usuario.
- [x] Eliminar contenido duplicado.
- [x] Mantener navegación y cierre con Escape.
- [ ] Capturar y comparar el estado expandido corregido.

final result: blocked
