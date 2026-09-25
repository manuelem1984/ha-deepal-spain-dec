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
- **`dec-icons.js`** — el script que de verdad sirve el navegador. Para los
  iconos "simples" (ver tabla) se **genera** a partir del SVG de origen
  (extrayendo el `path` real, el que tiene `fill="currentColor"` — el otro
  `<path>` que traen estos SVG, con `fill="none"`, es solo un rectángulo
  invisible de relleno y se descarta). No se edita a mano.

## Un caso especial: los iconos "car-light-*" (luces)

Los SVG de origen de estos 6 iconos (`line-md`, colección de iconos
**animados**) no son compatibles directamente con nuestro formato: usan una
`<mask>` SVG combinada con animaciones `<animate>` (SMIL) para "dibujarse"
al cargar, mientras que `window.customIconsets` solo admite un `path` plano
y estático — ver el propio SVG de origen para confirmarlo.

Para estos 6, el `path` de `dec-icons.js` es una **reconstrucción manual**
de cómo queda el icono una vez terminada su animación (verificado
renderizando el SVG original con un navegador real y comparando capturas de
pantalla, no solo revisado a ojo):

- Los 3 SVG "on" (`car-light-full-on`, `car-light-dimmed-on`,
  `car-light-parking-on`) comparten la **misma carcasa de luz** (el cuerpo
  del faro) que ya usaba el propio icono de origen — solo cambia el número
  y ángulo de los "rayos" de luz, para que las tres funciones (carretera,
  cruce, posición) se distingan claramente entre sí de un vistazo:
  - `car-light-full-on` (carretera): 4 rayos horizontales.
  - `car-light-dimmed-on` (cruce): 3 rayos diagonales, apuntando hacia
    abajo.
  - `car-light-parking-on` (posición): solo la carcasa, sin rayos — la
    función más "mínima" de las tres.
- Los "rayos" del SVG original son trazos (`stroke`), no formas rellenas;
  como nuestro sistema solo admite un `path` con relleno, se han convertido
  en cápsulas rellenas (rectángulo con extremos redondeados) calculadas a
  partir de las coordenadas y el grosor de trazo (`stroke-width`) reales
  del SVG de origen — no son un simple calco.
- Los 3 SVG "off" comparten la carcasa más una barra diagonal (misma
  técnica de cápsula rellena), en vez de reproducir el tratamiento exacto
  del original (contorno sin relleno + un hueco en la máscara) — más
  sencillo de mantener y perfectamente claro como indicador de "apagado".
- Por lo mismo, no se reproduce el matiz de opacidad reducida del estilo
  "twotone" del SVG de origen de `car-light-parking-*` (nuestro formato no
  admite opacidad por tramo) — se sustituye por la ausencia de rayos, como
  se explica arriba.

Si mañana se quiere afinar el dibujo de estos 6, hay que volver a partir del
SVG de origen guardado en esta misma carpeta y repetir el proceso de
verificación visual — no editar `dec-icons.js` a mano sin comprobarlo.

## Iconos incluidos

| Nombre (`dec:...`) | Origen | Colección | Licencia |
| --- | --- | --- | --- |
| `steering-wheel-heat` | [Iconify](https://icon-sets.iconify.design/material-symbols/steering-wheel-heat/) | Material Symbols (Google) | Apache 2.0 — sin atribución obligatoria, uso comercial permitido |
| `arrow-circle-left` / `arrow-circle-left-outline` | [Iconify](https://icon-sets.iconify.design/material-symbols/arrow-circle-left/) | Material Symbols (Google) | Apache 2.0 |
| `arrow-circle-right` / `arrow-circle-right-outline` | [Iconify](https://icon-sets.iconify.design/material-symbols/arrow-circle-right/) | Material Symbols (Google) | Apache 2.0 |
| `car-light-full-on` / `car-light-full-off` | [Iconify](https://icon-sets.iconify.design/line-md/car-light-filled/) (reconstruido, ver arriba) | line-md (Vjacheslav Trushkin) | MIT — sin atribución obligatoria, uso comercial permitido |
| `car-light-dimmed-on` / `car-light-dimmed-off` | [Iconify](https://icon-sets.iconify.design/line-md/car-light-dimmed-filled/) (reconstruido, ver arriba) | line-md (Vjacheslav Trushkin) | MIT |
| `car-light-parking-on` / `car-light-parking-off` | [Iconify](https://icon-sets.iconify.design/line-md/car-light-twotone/) (reconstruido, ver arriba) | line-md (Vjacheslav Trushkin) | MIT |

## Cómo añadir un icono nuevo

**Caso normal (icono simple, no animado):**

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

**Si el SVG de origen resulta ser animado** (tiene `<mask>`/`<animate>`,
como los "car-light-\*"): no se puede extraer directamente. Hay que
reconstruir el `path` a mano a partir de la geometría del SVG de origen, y
verificarlo **de verdad, con un navegador**, comparando una captura del SVG
original (esperando a que termine la animación) contra una captura de la
reconstrucción — nunca dar por bueno un icono así sin esa comprobación
visual.
