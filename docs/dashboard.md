# Panel "DEC - Vehículos"

Desde la v1.3.1b7, la integración registra su propio panel en la barra
lateral de Home Assistant — sin JavaScript ni frontend a medida: es un
dashboard de Lovelace normal, en modo YAML, que la propia integración
escribe en disco y engancha al menú.

## Cómo funciona

- **`dashboard.async_register_panel()`**: registra el panel una sola vez,
  usando `frontend.async_register_built_in_panel` con `component_name:
  lovelace` y `config: {mode: yaml, filename: ...}`. Se llama tanto desde
  `async_setup()` (arranque normal de Home Assistant) como desde
  `async_setup_entry()` (por si se añade la integración en caliente, sin
  reiniciar) — es seguro llamarlo más de una vez: Home Assistant lanza
  `ValueError` si ya está registrado, y simplemente lo ignoramos.
- **`dashboard.async_write_dashboard()`**: (re)escribe el archivo YAML
  completo, recorriendo **todas** las entradas de configuración cargadas de
  este dominio — no solo la que se acaba de dar de alta o de baja — así que
  el dashboard refleja siempre todos los vehículos configurados, sin
  importar el orden en que se hayan cargado. Se llama al configurar una
  entrada, al desinstalarla, y una vez vacío al arrancar Home Assistant (por
  si el panel se abre antes de que termine de cargar ninguna entrada).

## Diseño actual (v1.3.1b8)

- **Nombre en el menú**: "DEC - Vehículos"
- **Icono**: `mdi:car` (provisional — pendiente de sustituir por el emblema
  Deepal cuando lo tengamos preparado en el formato adecuado)
- **Una pestaña por vehículo configurado**, titulada con su **VIN**. No es
  el diseño final: nos gustaría mostrar un apodo/pseudónimo del vehículo en
  su lugar, pero no hemos encontrado todavía un endpoint que lo exponga —
  ver `docs/roadmap.md`.
- **Una única tarjeta por pestaña** (tipo `markdown`), con:
  - **Título**: combina marca, modelo, versión y color —
    `Deepal S05 <versión> <color>` — donde "Deepal" y "S05" son siempre
    fijos, y la versión/color se leen de lo configurado en Opciones
    (`config_flow.DeepalSpainOptionsFlow`). Si no se ha configurado ninguno
    de los dos, se muestra solo "Deepal S05".
  - **Indicador de batería** (desde v1.3.1b8), alineado a la derecha:
    porcentaje en texto seguido de un icono de batería, ambos coloreados
    según el nivel (rojo por debajo del 10%, amarillo entre el 10% y el
    30%, verde por encima del 30%), con el propio icono cambiando de forma
    en pasos de 10 (`mdi:battery-outline`, `mdi:battery-10`, ...,
    `mdi:battery`), igual que hace Home Assistant con sus propios sensores
    de batería. Construido como una plantilla Jinja dentro del contenido de
    la tarjeta (`dashboard._general_card()`), ya que un `markdown` es la
    forma más flexible de mezclar un icono con estilo condicional dentro
    del mismo recuadro que el título, en vez de una tarjeta aparte. El
    `entity_id` real del sensor de batería de cada vehículo se busca en el
    registro de entidades por su `unique_id` (`dashboard._battery_entity_id()`),
    ya que el usuario puede haberlo renombrado. Si la entidad todavía no
    existe (arranque en curso), el indicador simplemente no se incluye esa
    vez, en vez de dejar una plantilla rota.
- **Todo lo demás queda vacío a propósito** — es una beta deliberadamente
  incompleta; el resto de tarjetas (vehículo, neumáticos, carga,
  climatización/confort, otros) se van añadiendo en betas sucesivas — ver
  `docs/roadmap.md` para el diseño completo acordado.

## Decisiones de diseño pendientes de resolver

Estas preguntas surgieron al diseñar el dashboard completo y siguen abiertas
para las próximas betas:

- **Selector de unidad de presión/temperatura**: Home Assistant ya permite
  cambiar la unidad de cada sensor individualmente desde sus propios
  ajustes de entidad. Un selector único que afecte a la vez a todas las
  tarjetas del dashboard necesitaría un `input_select` (helper) más
  plantillas Jinja en cada tarjeta que lo consulten — es diseño de
  dashboard, no algo que la integración resuelva con una opción.
- **Presión de neumáticos "calculada"** (🟢 si las 4 están dentro de rango):
  pendiente de decidir si vive como plantilla dentro del propio dashboard, o
  como una entidad nueva (`binary_sensor`) en la integración.
- **Potencia de carga en kW**: no la tenemos mapeada; pendiente de investigar
  si el MQTT la trae con otro nombre de campo.
- **Bloquear/desbloquear como acción rápida**: no implementado todavía — es
  el bloque grande de comandos con PIN que seguimos aplazando.
