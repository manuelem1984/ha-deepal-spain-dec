# Control remoto

Comandos que la integración puede enviar al coche, cómo funcionan por dentro y
qué falta por hacer. Para los datos que se **leen** del coche ver
[`telemetry-parameters.md`](telemetry-parameters.md).

- **Vehículo de referencia:** Deepal S05 España.
- **Alcance actual:** solo comandos que **no** necesitan el PIN de control remoto.
  Puertas, ventanillas y maletero quedan para una fase posterior (sección 5).
- **Origen:** el protocolo (endpoints, cifrado y firma) se reconstruyó por
  ingeniería inversa de la app oficial, contrastado con material de referencia
  sobre el mismo backend. Luces, claxon y climatización están confirmados con el
  coche real.

## Leyenda

| Símbolo | Significado |
| --- | --- |
| ✅ | Comprobado con el coche real |
| ⚠️ | Implementado, pendiente de comprobar con el coche real |
| ❌ | No implementado |

---

## 1. Comandos disponibles

| Comando | Entidad | Endpoint | Estado |
| --- | --- | --- | --- |
| Parpadear luces | `button.…_parpadear_luces` | `control/flashing-honking` (`type=1`) | ✅ |
| Tocar el claxon | `button.…_tocar_el_claxon` | `control/flashing-honking` (`type=2`) | ✅ |
| Luces y claxon a la vez | `button.…_luces_y_claxon_a_la_vez` | `control/flashing-honking` (`type=3`) | ⚠️ |
| Climatización: encender/apagar y temperatura | `climate.…_climatizacion` | `control/air-conditioner` | ✅ (comparado con la app oficial) |
| Calefacción asiento conductor / acompañante (0-3) | `number.…_calefaccion_asiento_*` | `control/seats/heat` | ⚠️ |
| Ventilación asiento conductor / acompañante (0-3) | `number.…_ventilacion_asiento_*` | `control/seats/wind` | ⚠️ |
| Volante calefactado (on/off) | `switch.…_volante_calefactado` | `control/steering-wheel/heat` | ⚠️ |
| Desempañado delantero (on/off) | `switch.…_desempanado_delantero` | `control/defrost` | ⚠️ |
| Pedir datos frescos al coche | botón *Actualizar datos del vehículo* y uso interno tras cada comando | `control/condition-inquiry` | ✅ |

Todos los endpoints cuelgan de `/intl-app-gw/intl-app-car-control/api/`.

### Detalles de cada payload

- **Climatización:** `targetTemp` va en **décimas de grado** (`22.5 °C` → `225`),
  al contrario que la lectura, que llega en grados. `windMode` está fijo a `1` y
  `runTime` a `30` (minutos, presumiblemente); no se ha investigado qué otros
  valores aceptan.
- **Luces/claxon:** `type` = `0` apagar, `1` luces, `2` claxon, `3` ambos.
- **Asientos:** conductor = `masterSwitch`/`masterLevel`, acompañante =
  `copilotSwitch`/`copilotLevel`, nivel 0-3. Para **apagar** se manda
  `switch: 0` **sin** el campo de nivel: un nivel `0` explícito lo rechaza el
  servidor.
- **Volante calefactado:** `{"open": true|false}`.
- **Desempañado:** `{"enabled": true|false}`.

---

## 2. Cómo se envía un comando

1. **Número de serie cifrado:** `GET serial-no/get` (`api.get_serial_number()`).
   El servidor lo devuelve cifrado con nuestra clave pública de login.
2. **Descifrado** con la clave privada RSA generada al iniciar sesión
   (`CONF_PRIVATE_KEY`) — `crypto.decrypt_with_private_key()`.
3. **Payload:** los datos del comando más `seriralNo` (sic, errata del fabricante)
   y `vehicleId`.
4. **Firma:** se ordenan alfabéticamente las claves (sin `sign`, `class` ni
   `command`), se unen como `clave=valor&clave=valor…` (booleanos en minúscula,
   `None` como `"null"`) y se firma con **RSA-SHA256 (PKCS#1 v1.5)**. La firma en
   base64 va en el campo `sign` — `crypto.sign_command_payload()`.
5. **Envío** por POST a la pasarela principal (`BASE_URL`). La respuesta trae un
   `commandId`.

> Si un comando falla con `DeepalCommandNotReady`, reautentica la integración una
> vez: las instalaciones antiguas no tenían guardada la clave privada necesaria
> para firmar.

---

## 3. Qué pasa después de enviar el comando

Todo esto vive en `coordinator.async_send_command()`.

### Renovación silenciosa de la sesión

Si el comando falla por sesión caducada (`APP_1_1_02_004`), se renueva la sesión
con el `refresh_token` guardado y se **reintenta una vez**. Por eso los comandos se
pasan como función (`lambda: self.api.control_x(...)`) y no como corrutina ya
creada: una corrutina no se puede esperar dos veces.

### Confirmación de que el coche lo aceptó

Tener un `commandId` solo significa que **el servidor** aceptó la petición; el
**coche** puede rechazarla después (por ejemplo, si está dormido). Durante hasta
15 s se consulta `control/control-result` (POST sin firma) y se clasifica su
`resultCode`:

| `resultCode` | Resultado |
| --- | --- |
| `0`, `1201` | Éxito |
| `1015` | Ya estaba hecho |
| `-1`, `-2` | Fallo |
| `-100` o ausente | Pendiente (se sigue esperando) |
| cualquier otro | Fallo (por precaución) |

Si falla, se muestra un error claro. Si el mensaje contiene `TBOX_`, se añade la
pista de que el coche a veces rechaza comandos hasta que se ha usado un rato. Si a
los 15 s sigue pendiente, se continúa sin bloquear.

### Actualización optimista

Los comandos que cambian un estado visible pasan `optimistic_update`
(`{campo: valor_esperado}`):

1. La entidad cambia **al momento** al valor esperado.
2. Se pide al coche que reporte (`condition-inquiry`) y se reintenta la lectura
   hasta 3 veces, cada 2 s, hasta confirmar el cambio.
3. Si no se confirma, el valor optimista se mantiene hasta la siguiente lectura
   normal (5 min), que lo confirma o lo corrige.

**Limitación:** si el servidor acepta el comando pero el coche no lo aplica, el
valor optimista puede verse un rato hasta la siguiente lectura. Habrá que revisarlo
antes de añadir puertas y maletero, donde un estado equivocado importa más.

### Cola de comandos

- Los comandos con `optimistic_update` (clima, asientos, volante, desempañado)
  **esperan su turno** con un `asyncio.Lock` (máximo 30 s) para que sus
  actualizaciones no se pisen.
- Luces, claxon y luces+claxon **no esperan** a nada: no tocan ningún estado.

---

## 4. Lectura fiable de asientos y volante

El MQTT no refleja el estado real de la calefacción/ventilación de asientos, el
volante ni el desempañado: guarda el último nivel configurado, esté encendido o no.
Se comprobó con dos capturas reales, apagando el asiento entre ambas.

Por eso, tras cada lectura MQTT, `coordinator._async_overlay_condition()` pide un
endpoint REST de "estado del vehículo" (el mismo que usa la app oficial) y
**sustituye solo esos 6 datos**:

| Dato | MQTT (reserva) | REST (el que se usa) |
| --- | --- | --- |
| Calefacción asiento | `driverSeatHeatStatus` (0-6 ÷ 2) | `seat.leftFront.heatStatus` (0-3) |
| Ventilación asiento | `driverSeatAirStatus` | `seat.leftFront.ventStatus` |
| Volante calefactado | `steeringWheelHeating` | `vehicleStatus.steeringWheelHeater` |
| Desempañado | `frontDefrostStatus` | `hvac.defrostStatus` |

(El acompañante usa `rightFront`.) Si la llamada falla, se queda el valor del MQTT
hasta la siguiente lectura. Justo después de un comando, esta lectura puede llegar
antes de que el coche aplique el cambio y revertirlo unos segundos.

---

## 5. Comandos con PIN (puertas, ventanillas, maletero)

Implementado en v1.3.1, tras una ronda de análisis y diseño conjunto sobre cómo
integra esto otro proyecto de referencia para este mismo backend, y sobre cómo
evitar que una pulsación accidental deje el coche abierto o con una ventanilla
bajada.

### 5.1. El bloque es opcional y viene desactivado por defecto

Todo esto se configura en **Opciones** de la integración:

- **PIN de control remoto habilitado** — interruptor maestro, desactivado por
  defecto. Mientras esté así, no existe ninguna entidad de puertas, ventanillas
  ni maletero, ni el candado de armado.
- **Para activarlo hace falta introducir el PIN y que se verifique en ese mismo
  momento** contra el servidor de Deepal (`check_control_code`). Si el PIN es
  incorrecto o hay demasiados intentos fallidos, la activación se rechaza — no
  se guarda como activado ni aparece ninguna entidad hasta que la verificación
  pase. El campo se muestra enmascarado (tipo contraseña).
- **El PIN debe haberse creado antes desde la app oficial**, con la misma
  cuenta con la que Home Assistant inicia sesión (normalmente la secundaria).
  Para crearlo: en la app, con esa cuenta, intenta bajar una ventanilla — la
  app pedirá crear el PIN. Un PIN creado con otra cuenta es rechazado por el
  servidor.

### 5.2. El intercambio PIN → `rcToken`

Mismo mecanismo que usan otros proyectos para este backend, confirmado
funcionando en nuestras propias simulaciones (`tests/test_api.py`):

1. `get_security_code_status()` — consulta cuántos intentos de PIN quedan
   (`retryQuantity`) **antes de intentar nada**. Si no queda ninguno, se
   rechaza localmente en vez de arriesgarse a un bloqueo peor.
2. `check_control_code(pin)` — cifra el PIN con la misma clave pública que se
   usa para email/teléfono al iniciar sesión, y lo manda al servidor. La
   respuesta trae un `rcToken`.

Ese `rcToken`:

- **Se guarda y se reutiliza** en varios comandos seguidos — no se pide un PIN
  nuevo cada vez.
- **Se renueva solo si el servidor lo rechaza** (comparado con un `rcToken`
  reutilizado, no uno recién obtenido): se descarta, se pide uno nuevo con el
  PIN guardado, y se reintenta el comando una vez.
- **Entra dentro de la firma RSA del comando**, junto con el resto del
  payload — no es un paso aparte.

### 5.3. Opción A / Opción B — la protección contra pulsaciones accidentales

Una confirmación tipo "¿estás seguro?" en el propio dashboard de Lovelace
**no protege de verdad**: solo cubre esa tarjeta concreta, no una
automatización, un asistente de voz, ni otro dashboard sin esa confirmación.
La protección real tiene que vivir en el propio código, en el mismo sitio por
donde pasan todos los comandos (`coordinator.async_send_command`).

- **Opción A — No segura**: los comandos se ejecutan directamente al
  pulsarlos, sin ningún paso intermedio.
- **Opción B — Segura**: hace falta "armar" primero, como un mando de garaje.
  - Entidad `lock` (no `switch`) llamada **"Desbloqueo Acciones PIN"** —
    ganamos gratis los iconos `mdi:lock`/`mdi:lock-open`, y si algún día se
    conecta esta integración a un asistente de voz, Google ya exige su propio
    PIN de 4 dígitos para desbloquear cualquier `lock` por voz.
  - Al desbloquearlo, queda armado durante una **ventana de tiempo
    configurable** (10 / 20 / 30 / 60 segundos — 30 por defecto), dentro de la
    cual se pueden ejecutar varias acciones seguidas (no solo una).
  - Pasado ese tiempo, se bloquea solo (`async_call_later`, cancelado y
    reiniciado si se vuelve a armar antes de que expire).
  - **Siempre arranca bloqueado** al iniciar o recargar Home Assistant — nunca
    se recuerda armado de una sesión a otra.
  - Aviso al desbloquear: configurable, **desactivado por defecto**.
  - Esta entidad solo existe si se elige la Opción B; con la Opción A no
    aparece.
  - La comprobación de si está armado (`_is_command_blocked_by_arming`, ver
    `coordinator.py`) se hace en el propio `async_send_command`, así que
    protege igual venga el comando de un botón, una automatización o un
    asistente de voz — probado con 6 casos en `tests/test_coordinator.py`.

### 5.4. Comandos y entidades

| Comando | Endpoint | Entidad | Estado |
| --- | --- | --- | --- |
| Bloquear / desbloquear puertas | `control/doors` | `lock.bloqueo_de_puertas` | ⚠️ payload cruzado con otra implementación, sin confirmar contra el coche real |
| Abrir / cerrar maletero | `control/trunk` | `cover.maletero` | ⚠️ ídem |
| Subir / bajar ventanillas (×4) | `control/windows` | `cover.ventanilla_*` (4) | ⚠️ forma exacta del payload por posición de ventanilla **sin confirmar** — ver nota abajo |

Todas requieren `require_rc_token=True` en `_signed_command` y, en Opción B,
`requires_arming=True` en `async_send_command`.

Las nuevas entidades `lock`/`cover` conviven con los `binary_sensor` de
solo lectura que ya existían para puertas/ventanillas/maletero desde
v1.3.1b13 — no se ha quitado nada para evitar un cambio incompatible. Queda
anotado en `docs/roadmap.md` como posible limpieza futura.

**Nota sobre `control_windows`**: a diferencia de puertas y maletero, no se ha
podido confirmar el nombre exacto de los campos que espera el servidor para
cada ventanilla. La implementación actual manda un campo booleano por
posición (`leftFront`, `rightFront`, `leftRear`, `rightRear`), siguiendo la
misma convención de nombres que ya usa esta API en otros sitios (asientos,
neumáticos) — es una hipótesis razonada, no un dato confirmado.

## 6. Pruebas pendientes con el coche real

- [ ] Luces y claxon a la vez.
- [ ] Calefacción y ventilación de asientos (encender, cambiar nivel, apagar).
- [ ] Volante calefactado y desempañado.
- [ ] Temperatura de la climatización grado a grado frente a la app oficial.
- [ ] Bloquear/desbloquear puertas (`lock.bloqueo_de_puertas`).
- [ ] Abrir/cerrar maletero (`cover.maletero`).
- [ ] Subir/bajar cada ventanilla — y confirmar si el nombre de campo por
      posición (`leftFront`, etc.) es correcto o el servidor lo rechaza.
- [ ] Opción B: confirmar que el rebloqueo automático ocurre exactamente al
      cumplirse la duración configurada, y que varias acciones seguidas
      dentro de la ventana funcionan sin tener que rearmar entre medias.
- [ ] Confirmar que un PIN creado con la cuenta correcta se verifica bien
      desde el formulario de Opciones, y que uno incorrecto (o creado con
      otra cuenta) se rechaza con el mensaje esperado.
