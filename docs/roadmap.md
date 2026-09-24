# Roadmap hacia la siguiente versión estable

Lista de trabajo para ir implementando en sucesivas betas a partir de la
v1.3.0. Se van tachando conforme se completan; cuando esté todo, se publica
la siguiente versión estable.

- [x] Menú de configuración para elegir versión y color del Deepal S05
      (v1.3.1b2: 10 fotos, Pro/Max/Max AWD × 5 colores oficiales)
- [x] Arreglar las etiquetas del formulario de Opciones, que mostraban las
      claves internas (`vehicle_trim`, `vehicle_color`) en vez de "Versión"
      y "Color" — faltaban las traducciones (v1.3.1b3) — ✅ **verificado
      en real**: el menú ya sale traducido correctamente
- [x] Añadir un botón "luces + claxon a la vez" (`FLASH_HONK_FLASH_BEE`,
      `type=3`) (v1.3.1b3) — ⚠️ **pendiente de probar contra el vehículo
      real** (pendiente para la tarde)
- [x] **Implementado** — 4 comandos más sin PIN de control (6 entidades:
      2 `number` de calefacción + 2 `number` de ventilación + 2 `switch`),
      confirmados leyendo el código real de `ha-deepal-alternative`
      (`deepal_sdk/deepal/intl.py` y `endpoints.py`) (v1.3.1b4) —
      ⚠️ **pendiente de probar contra el vehículo real**:

      | Comando | Endpoint | Payload | Entidad HA |
      | --- | --- | --- | --- |
      | Calefacción asiento conductor (nivel 0-3) | `control/seats/heat` | `masterSwitch`/`masterLevel` | `number.calefaccion_asiento_conductor` |
      | Calefacción asiento pasajero (nivel 0-3) | `control/seats/heat` | `copilotSwitch`/`copilotLevel` | `number.calefaccion_asiento_acompanante` |
      | Ventilación asiento conductor (nivel 0-3) | `control/seats/wind` | `masterSwitch`/`masterLevel` | `number.ventilacion_asiento_conductor` |
      | Ventilación asiento pasajero (nivel 0-3) | `control/seats/wind` | `copilotSwitch`/`copilotLevel` | `number.ventilacion_asiento_acompanante` |
      | Volante calefactado (on/off) | `control/steering-wheel/heat` | `{"open": true/false}` | `switch.volante_calefactado` |
      | Desempañado delantero (on/off) | `control/defrost` | `{"enabled": true/false}` | `switch.desempanado_delantero` |

      Detalle importante confirmado en su código (probado por ellos contra
      el coche real): para **apagar** un asiento hay que mandar
      `switch: 0` **sin** enviar el campo de nivel — si se manda un nivel
      `0` explícito, el servidor lo rechaza. Ninguno de los 6 necesita PIN
      (`require_rc_token=False` en su cliente). El desempañado
      (`control_defrost`) existe en su SDK pero **ellos nunca lo conectaron
      a ninguna entidad** — somos los primeros en exponerlo de verdad. Se
      ha añadido también la lectura por telemetría de estos 6 campos
      (antes solo eran candidatas sin mapear), con la misma escala (0-6 en
      bruto ÷ 2 = nivel 0-3) usada por `ha-deepal-alternative` para su
      propio análisis MQTT — cross-referenciada, no confirmada todavía con
      este vehículo.

      **Seguimiento (v1.3.1b6)**: probado contra el vehículo real, la
      *lectura* de estos 4 campos (calefacción/ventilación de asientos,
      volante calefactado) resultó no ser fiable por MQTT — ver la tarea de
      abajo. La *escritura* (los comandos de esta tabla) sigue sin
      confirmar contra el vehículo real.
- [x] **Arreglada la lectura no fiable de asientos y volante (v1.3.1b6)**:
      confirmado con dos volcados de diagnósticos reales que el MQTT no
      refleja el estado actual de calefacción/ventilación de asientos ni del
      volante calefactado (parece guardar solo "el último nivel
      configurado", encendido o no). Sustituido por un segundo endpoint
      REST más fiable — ver "0.4. Lectura fiable de asientos y volante" en
      `remote-control.md`. Verificado con simulaciones (20 casos en total);
      pendiente de confirmar contra el vehículo real.
- [ ] Comparar la marca de tiempo (`lastUpdatedAt`) de este nuevo endpoint
      de asientos/volante contra la del MQTT, para no sustituir un dato
      fresco por uno más antiguo — de momento se sustituye siempre que la
      llamada tenga éxito, sin comparar frescura entre ambas fuentes.
- [ ] Investigar si ese mismo endpoint (el de asientos/volante) también
      sirve para recuperar temperatura exterior y temperatura por
      neumático — los retiramos porque el MQTT nunca los manda, pero este
      endpoint parece incluirlos también.
- [x] Arreglar el error al enviar varias acciones de control seguidas —
      sustituida la bandera manual de "comando en curso" por un
      `asyncio.Lock()` con timeout de 30s (v1.3.1b4). Solo los comandos que
      comparten estado (los que usan `optimistic_update`: climatización,
      asientos, volante, desempañado) esperan en cola; luces/claxon/luces+
      claxon nunca esperan a nada. ⚠️ **Pendiente de probar contra el
      vehículo real** — verificado hasta ahora solo con simulaciones.
- [ ] Confirmar `windMode` y `runTime` del comando de climatización (siguen
      fijos a valores por defecto, sin investigar qué otros valores acepta
      cada uno)
- [ ] Multiidioma y multipaís (desplegable de país en el config flow,
      método de login según país, traducciones de la propia integración)
- [ ] Comandos de control con PIN (puertas, ventanas, maletero — el bloque
      grande que llevamos aplazando)
- [ ] **Última tarea de esta lista**: Panel "DEC - Vehículos" — dashboard
      Lovelace propio en la barra lateral (no requiere JavaScript ni
      frontend a medida, ver `docs/dashboard.md`). Diseño acordado:
      - Nombre: "DEC - Vehículos". Icono: `mdi:car` por ahora (pendiente el
        emblema Deepal más adelante).
      - Una pestaña por vehículo, titulada con su VIN (pendiente de
        sustituir por un apodo/pseudónimo si encontramos el endpoint que lo
        exponga).
      - Icono de configuración en la pestaña con selector de unidad de
        presión/temperatura (pendiente de diseño — ver "Decisiones de
        diseño pendientes" en `docs/dashboard.md`).
      - Máximo 3 secciones en horizontal por pestaña.
      - **Tarjeta 1 (General)** — [x] título hecho en v1.3.1b7
        ("Deepal S05 &lt;versión&gt; &lt;color&gt;"); [x] indicador de
        batería (porcentaje + icono variable en pasos de 10%, en rojo si
        &lt;10%, amarillo 10-30%, verde &gt;30%) añadido en v1.3.1b8,
        alineado a la derecha del título. Pendiente: resto del estado
        (cargando/enchufado, kilometraje, conectado/última actualización) y
        acciones rápidas (actualizar, climatizador; bloquear/desbloquear
        solo cuando exista el bloque de PIN).
      - **Tarjeta 2 (🚗 Vehículo)**: VIN, kilometraje, estado del motor, y
        una presión de neumáticos "calculada" (🟢 si las 4 están dentro de
        rango — pendiente de decidir si es plantilla de dashboard o
        entidad nueva).
      - **Tarjeta 3 (🛞 Neumáticos)**: las 4 presiones, en la unidad
        seleccionada.
      - **Tarjeta 4 (🔋 Carga/Batería)**: estado, batería %, corriente,
        potencia en kW (pendiente de investigar si el MQTT la trae con
        otro nombre), tiempo restante.
      - **Tarjeta 5 (🌡️ Climatizador y Confort)**: controles del
        climatizador, temperatura/humedad interior, controles de
        calefacción/ventilación de ambos asientos.
      - **Tarjeta 6 (Otros)**: control de desempañado.
