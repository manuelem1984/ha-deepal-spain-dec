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

## 5. Pendiente: comandos con PIN

No implementado. Requiere guardar el PIN de control en las opciones de la
integración y canjearlo en cada comando
(`security-code/get-status` → `security-code/check-code` → `rcToken`).

| Comando | Endpoint | Estado |
| --- | --- | --- |
| Bloquear / desbloquear puertas | `control/doors` | ❌ |
| Subir / bajar ventanillas | `control/windows` | ❌ |
| Abrir / cerrar maletero | `control/trunk` | ❌ |

Recomendación para cuando se implemente: crear el PIN con la **misma cuenta** que
usa Home Assistant (la secundaria). Para ello, en la app oficial, con esa cuenta,
intenta bajar una ventanilla: la app pedirá crear el PIN.

## 6. Pruebas pendientes con el coche real

- [ ] Luces y claxon a la vez.
- [ ] Calefacción y ventilación de asientos (encender, cambiar nivel, apagar).
- [ ] Volante calefactado y desempañado.
- [ ] Temperatura de la climatización grado a grado frente a la app oficial.
