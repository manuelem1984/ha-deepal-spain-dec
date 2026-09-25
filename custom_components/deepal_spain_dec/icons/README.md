# Iconos personalizados ("dec:")

Paquete de iconos propio para iconos que Material Design Icons (`mdi:`) no
tiene todavía. Se registra en el navegador con la API documentada de Home
Assistant para paquetes de iconos de terceros
(`window.customIconsets`) — ver
<https://developers.home-assistant.io/blog/2020/05/09/custom-iconsets/>.
Una vez registrado, cualquier entidad puede usar el icono con el prefijo
`dec:`, igual que usaríamos `mdi:algo`.

Se sirve directamente desde la propia integración
(`frontend_icons.py`) — no hace falta instalar nada aparte ni añadir
ningún recurso de Lovelace a mano.

## Cómo está organizado

- **`*.svg`** — el SVG de origen de cada icono, tal cual se descarga de
  [Iconify](https://icon-sets.iconify.design/), guardado sin modificar. Es
  la referencia y la prueba de dónde viene cada uno.
- **`dec-icons.js`** — el script que de verdad sirve el navegador. Se
  **genera** a partir de los `.svg` de esta carpeta (extrayendo el `path`
  real, el que tiene `fill="currentColor"` — el otro `<path>` que traen
  estos SVG, con `fill="none"`, es solo un rectángulo invisible de relleno
  y se descarta). No se edita a mano.

## Iconos incluidos

| Nombre (`dec:...`) | Origen | Colección | Licencia |
| --- | --- | --- | --- |
| `steering-wheel-heat` | [Iconify](https://icon-sets.iconify.design/material-symbols/steering-wheel-heat/) | Material Symbols (Google) | Apache 2.0 — sin atribución obligatoria, uso comercial permitido |

## Cómo añadir un icono nuevo

1. Descargar el SVG desde Iconify (botón "SVG" en la página del icono) y
   guardarlo en esta carpeta tal cual, sin modificar.
2. Comprobar la licencia de la colección de origen (se indica en la propia
   página de Iconify) y añadir una fila a la tabla de arriba.
3. Regenerar `dec-icons.js` extrayendo el `d` del `<path>` con
   `fill="currentColor"` de cada SVG (no el de `fill="none"`) y su
   `viewBox`, y añadiéndolo al objeto `icons` del script.
4. Referenciar el icono en la entidad correspondiente como
   `icon="dec:nombre-del-icono"`.
5. Como la URL del script lleva la versión de la integración
   (`?v=<versión>`, ver `frontend_icons.py`), basta con subir de versión
   para que el navegador no se quede con una copia vieja en caché.
