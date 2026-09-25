# Iconos personalizados ("dec:")

Desde la v1.3.1b15, la integración sirve su propio paquete de iconos para
casos que Material Design Icons (`mdi:`) no cubre — el primero, un volante
calefactado de verdad (no un volante genérico), para la entidad "Volante
calefactado".

## Por qué así, y no de otra forma

Se valoraron dos caminos antes de decidir este:

1. **Instalar una integración de terceros** que ya trae Iconify conectado
   (por ejemplo, "Custom Icons" de la comunidad) y configurar el icono a
   mano en esa instancia de Home Assistant.
2. **Servir los iconos desde la propia integración**, para que lleguen "de
   serie" a cualquiera que la instale, sin depender de nada más.

Se eligió la opción 2, coherente con cómo está construido el resto del
proyecto: nada de lo básico depende de que el usuario instale algo aparte.

## Cómo funciona técnicamente

Home Assistant tiene una API de frontend documentada para paquetes de
iconos de terceros: `window.customIconsets`. Un script JavaScript pequeño
registra una función que, dado un nombre de icono, devuelve su `path` SVG
(y opcionalmente su `viewBox`). Una vez registrado, cualquier entidad puede
usar ese paquete con `icon: "dec:nombre-del-icono"`, igual que usaría
`mdi:nombre-del-icono`.

- **`custom_components/deepal_spain_dec/icons/`**: los `.svg` de origen
  (descargados tal cual de [Iconify](https://icon-sets.iconify.design/)) y
  el script `dec-icons.js` generado a partir de ellos — ver
  `icons/README.md` para la licencia de cada icono y cómo añadir uno nuevo.
- **`frontend_icons.py`**: registra la ruta estática que sirve esa carpeta
  y añade el script al frontend (`add_extra_js_url`).

### Un detalle importante: dónde se registra, y por qué

El registro se hace desde `async_setup()` (una vez por arranque de Home
Assistant), **nunca desde `async_setup_entry()`**, que también se ejecuta
en cada recarga de la integración (por ejemplo, al cambiar cualquier opción
en Configurar). Registrar la misma ruta estática dos veces en la misma
ejecución lanza `RuntimeError` en las versiones actuales de Home Assistant
("Added route will never be executed, method GET is already registered")
— un fallo real que ya le ha pasado a otras integraciones en esta misma
versión de Home Assistant por registrar la ruta desde el sitio equivocado.
Por eso `frontend_icons.async_register_icons()` también atrapa ese error
concreto como medida extra, por si acaso.

### Caché del navegador

La URL del script incluye la versión de la integración
(`dec-icons.js?v=1.3.1b15`) — así, cuando se publica una beta nueva con un
icono añadido o corregido, el navegador no se queda con una copia vieja
cacheada indefinidamente.

## Iconos disponibles

| Entidad | Icono (encendido / apagado) | Origen |
| --- | --- | --- |
| Volante calefactado (`switch.steering_wheel_heat`) | `dec:steering-wheel-heat` | [Material Symbols](https://icon-sets.iconify.design/material-symbols/steering-wheel-heat/) (Google, Apache 2.0) |
| Luz Intermitente Izquierdo | `dec:arrow-circle-left` / `dec:arrow-circle-left-outline` | [Material Symbols](https://icon-sets.iconify.design/material-symbols/arrow-circle-left/) (Apache 2.0) |
| Luz Intermitente Derecho | `dec:arrow-circle-right` / `dec:arrow-circle-right-outline` | [Material Symbols](https://icon-sets.iconify.design/material-symbols/arrow-circle-right/) (Apache 2.0) |
| Luz de carretera | `dec:car-light-full-on` / `dec:car-light-full-off` | [line-md](https://icon-sets.iconify.design/line-md/car-light-filled/) (MIT) — reconstruido, ver `icons/README.md` |
| Luz de cruce | `dec:car-light-dimmed-on` / `dec:car-light-dimmed-off` | [line-md](https://icon-sets.iconify.design/line-md/car-light-dimmed-filled/) (MIT) — reconstruido |
| Luz de posición | `dec:car-light-parking-on` / `dec:car-light-parking-off` | [line-md](https://icon-sets.iconify.design/line-md/car-light-twotone/) (MIT) — reconstruido |

Los 6 iconos "car-light-\*" **no son una extracción directa** de su SVG de
origen — ese SVG está animado (máscara + SMIL), incompatible con nuestro
formato de icono estático. Son una reconstrucción manual de cómo queda el
icono una vez asentada la animación, verificada renderizando ambas
versiones con un navegador real y comparando las capturas — ver el detalle
completo, y por qué las tres luces (carretera/cruce/posición) tienen un
número de "rayos" distinto a propósito, en `icons/README.md`.

## Cómo añadir un icono nuevo

Ver `icons/README.md` para el procedimiento paso a paso. En resumen:
descargar el SVG de Iconify, anotar su licencia, regenerar `dec-icons.js`
con el `path`/`viewBox` reales (descartando el `<path fill="none">` de
relleno que traen estos SVG), y referenciarlo en la entidad como
`icon="dec:..."`.

## Verificado sin coche real

- El script generado se comprobó con Node.js de verdad (no solo revisado a
  ojo): sintaxis válida, y llamando a
  `window.customIconsets["dec"]("steering-wheel-heat")` se obtiene el
  `path`/`viewBox` correctos; un nombre inexistente devuelve `undefined`.
- `tests/test_frontend_icons.py`: para cada `.svg` de `icons/`, comprueba
  que tiene exactamente un `<path>` visible y que `dec-icons.js` contiene
  una entrada con el `path`/`viewBox` exactos extraídos de ese SVG — y que
  no sobra ninguna entrada sin su SVG correspondiente.
- Pendiente de comprobar en un navegador real que el icono se ve
  correctamente en la entidad "Volante calefactado".
