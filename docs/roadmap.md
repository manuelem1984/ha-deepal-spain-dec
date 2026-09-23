# Roadmap hacia la siguiente versión estable

Lista de trabajo para ir implementando en sucesivas betas a partir de la
v1.3.0. Se van tachando conforme se completan; cuando esté todo, se publica
la siguiente versión estable.

- [x] Menú de configuración para elegir versión y color del Deepal S05
      (v1.3.1b2: 10 fotos, Pro/Max/Max AWD × 5 colores oficiales)
- [x] Arreglar las etiquetas del formulario de Opciones, que mostraban las
      claves internas (`vehicle_trim`, `vehicle_color`) en vez de "Versión"
      y "Color" — faltaban las traducciones (v1.3.1b3)
- [x] Añadir un botón "luces + claxon a la vez" (`FLASH_HONK_FLASH_BEE`,
      `type=3`) (v1.3.1b3)
- [ ] **Investigado, pendiente de implementar** — 4 comandos más sin PIN de
      control, confirmados leyendo el código real de `ha-deepal-alternative`
      (`deepal_sdk/deepal/intl.py` y `endpoints.py`):

      | Comando | Endpoint | Payload | Entidad HA propuesta |
      | --- | --- | --- | --- |
      | Calefacción asiento conductor (nivel 0-3) | `control/seats/heat` | `masterSwitch`/`masterLevel` | `number` |
      | Calefacción asiento pasajero (nivel 0-3) | `control/seats/heat` | `copilotSwitch`/`copilotLevel` | `number` |
      | Ventilación asiento conductor (nivel 0-3) | `control/seats/wind` | `masterSwitch`/`masterLevel` | `number` |
      | Ventilación asiento pasajero (nivel 0-3) | `control/seats/wind` | `copilotSwitch`/`copilotLevel` | `number` |
      | Volante calefactado (on/off) | `control/steering-wheel/heat` | `{"open": true/false}` | `switch` |
      | Desempañado delantero (on/off) | `control/defrost` | `{"enabled": true/false}` | `switch` |

      Detalle importante confirmado en su código (probado por ellos contra
      el coche real): para **apagar** un asiento hay que mandar
      `switch: 0` **sin** enviar el campo de nivel — si se manda un nivel
      `0` explícito, el servidor lo rechaza. Ninguno de los 6 necesita PIN
      (`require_rc_token=False` en su cliente). El desempañado
      (`control_defrost`) existe en su SDK pero **ellos nunca lo conectaron
      a ninguna entidad** — seríamos los primeros en exponerlo de verdad.
- [ ] Arreglar el error al enviar varias acciones de control seguidas
      (sustituir la bandera manual de "comando en curso" por un
      `asyncio.Lock()`, para que la segunda acción espere en cola en vez de
      fallar con un error visible; limitar la cola solo a los comandos que
      de verdad comparten estado — por ahora, climatización — dejando
      luces/claxon libres de solapamiento real)
- [ ] Confirmar `windMode` y `runTime` del comando de climatización (siguen
      fijos a valores por defecto, sin investigar qué otros valores acepta
      cada uno)
- [ ] Multiidioma y multipaís (desplegable de país en el config flow,
      método de login según país, traducciones de la propia integración)
- [ ] Comandos de control con PIN (puertas, ventanas, maletero — el bloque
      grande que llevamos aplazando)
- [ ] **Última tarea de esta lista**: diseñar una Card para el coche, con
      la foto, los comandos sin PIN y los comandos con PIN todos juntos
