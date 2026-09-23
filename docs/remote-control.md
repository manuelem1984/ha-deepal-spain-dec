# Control remoto del vehículo

Inventario de los comandos de control remoto, su estado de implementación y
las comprobaciones pendientes. Sigue el mismo formato que
[`telemetry-parameters.md`](telemetry-parameters.md), pero para el sentido
contrario: escribir en el coche, no leerlo.

- **Vehículo de referencia:** Deepal S05 (VIN `LS6CME0P6TK106840`)
- **Origen de esta información:** el protocolo completo (endpoints, cifrado,
  firma) se reconstruyó comparando con
  [`ha-deepal-alternative`](https://github.com/Sunek0/ha-deepal-alternative),
  otro proyecto open-source que ataca el mismo backend (sus
  `INTL_BASE_URL`/`INTL_CA_BASE_URL` coinciden exactamente con nuestro
  `BASE_URL`/`CA_BASE_URL`, confirmando que es la misma infraestructura).
  Luces, claxon y climatización ya están **confirmados funcionando contra el
  vehículo real** — ver la sección 2.
- **Alcance de esta versión:** solo comandos que **no** requieren el PIN de
  control. Puertas, ventanas y maletero quedan para una fase posterior — ver
  la sección 3.

## 0. Actualización optimista y reintento (desde v1.2.1b6)

`coordinator.async_send_command()` acepta un parámetro `optimistic_update`
(un diccionario `{campo: valor_esperado}`) que, tras un comando correcto:

1. Actualiza la entidad **al momento** con el valor esperado (sin esperar a
   ningún poll) — así la UI responde de inmediato en vez de quedarse en el
   valor viejo varios segundos.
2. Avisa al coche (`control_condition_inquiry`) y lanza hasta 3 reintentos
   de refresco, separados 2 segundos, hasta que un dato real confirme el
   cambio.
3. Si ninguno de los 3 reintentos lo confirma, el valor optimista se queda
   puesto hasta el siguiente ciclo normal de 5 minutos — que lo corregirá
   en cualquier caso, sea confirmando o desmintiendo el cambio.

**Limitación conocida:** no hay marcha atrás automática si el comando falla
en silencio en el lado del servidor (es decir, si Deepal acepta el comando
pero el coche nunca llega a aplicarlo). El valor optimista se mostraría como
correcto durante un rato hasta que el siguiente poll real lo corrija. No se
ha considerado necesario para este primer alcance (climatización, luces,
claxon), pero habrá que revisarlo antes de dar el salto a comandos con PIN
(puertas/ventanas/maletero), donde un estado equivocado importa más.

## 0.1. Renovación silenciosa de sesión en los comandos (desde v1.2.1b8)

**Hallazgo real en pruebas (2026-09-2x):** el claxon falló la primera vez
con `APP_1_1_02_004` (sesión caducada), y funcionó justo después de pulsar
"Actualizar datos del vehículo". La causa: el poll normal de telemetría ya
sabía renovar la sesión sola en silencio (desde la v1.1.0b6), pero los
comandos de control remoto no pasaban por ese mismo mecanismo — si el token
estaba caducado, fallaban directamente pidiendo reautenticar a mano.

Ahora `coordinator._send_command_with_session_retry()` hace lo mismo que ya
hacía el poll: si el comando falla por sesión caducada, intenta renovarla en
silencio con el `refresh_token` guardado y **reintenta el mismo comando una
vez** antes de rendirse. Esto obligó además a cambiar cómo se pasa el
comando a `async_send_command()`: antes se le daba la corrutina ya creada
(`self.api.control_x(...)`), pero una corrutina **no se puede volver a
esperar una segunda vez** en Python — hacía falta pasar una función que la
cree de nuevo cada vez (`lambda: self.api.control_x(...)`) para poder
reintentar.

**Confirmado tras el arreglo:** parpadeo de luces, claxon **y climatización**
funcionan correctamente, comparado además contra la app oficial Changan. El
fallo original del climatizador (`APP_1_1_02_004`) era, en efecto, sesión
caducada — no un problema del payload de `control_air_conditioner`.

## 0.2. Confirmación real del comando y bloqueo de solapamiento (desde v1.2.1b10)

Comparando a fondo con `ha-deepal-alternative` (ver su
`coordinator.py`/`intl.py` reales), se encontraron dos mejoras de robustez
que ellos ya tenían y nosotros no:

**1. Comprobar si el vehículo aceptó el comando de verdad.** Hasta ahora,
tener un `commandId` de vuelta solo significa que **los servidores de
Deepal** aceptaron la petición HTTP — el propio **vehículo** puede rechazarla
después, de forma asíncrona (por ejemplo, si está dormido u ocupado). El
proyecto de referencia consulta un endpoint aparte
(`control/control-result`) tras cada comando para saberlo con certeza; su
código de solución de problemas dice literalmente: *"the car sometimes
refuses every remote command until it has been driven for a few minutes"*.

Ahora `coordinator._async_confirm_command_accepted()` hace lo mismo:

- Llama a `api.get_command_result(vehicle_id, command_id)` — un `POST` **sin
  firmar** (a diferencia de los demás comandos, no necesita el número de
  serie ni la firma RSA — confirmado leyendo su código directamente).
- Clasifica la respuesta por su campo `resultCode`, con la misma tabla que
  usa el proyecto de referencia:

  | `resultCode` | Estado |
  | --- | --- |
  | `0`, `1201` | Éxito |
  | `1015` | Ya estaba hecho |
  | `-1`, `-2` | Fallo |
  | `-100` | Pendiente |
  | (ausente) | Pendiente |
  | cualquier otro | Fallo (por precaución, no se asume éxito) |

- Si el resultado es un fallo, lanza un error claro al usuario en vez de
  dejar que la actualización optimista se quede "colgada" sin explicación —
  y si el mensaje de error contiene `TBOX_` (el patrón que usa el proyecto
  de referencia para "el coche no aceptó el comando"), añade la pista de que
  puede necesitar haberse usado hace poco.
- Si tras 15 segundos sigue sin confirmar ni fallar, se continúa igualmente
  (no bloquea el comando indefinidamente) — el resto del mecanismo de
  actualización optimista (sección 0) sigue siendo el respaldo para ese
  caso.

**2. No solapar comandos que comparten estado.** Si se pulsan dos botones
seguidos (por ejemplo, climatización y calefacción de asiento casi a la
vez), antes se enviaban los dos comandos en paralelo, con el riesgo de que
sus actualizaciones optimistas se pisaran entre sí.

**Verificado sin coche real** (necesita `aiohttp`/Home Assistant, que no
están disponibles en el entorno de desarrollo): con simulaciones a mano de
la función de clasificación (10 casos, incluidos códigos desconocidos y no
numéricos), del bucle de confirmación (6 escenarios: éxito inmediato, "ya
hecho", fallo genérico, fallo `TBOX_` con la pista añadida, pendiente varias
veces antes de confirmar, y pendiente hasta agotar el tiempo).

## 0.3. Cola de comandos con `asyncio.Lock` (desde v1.3.1b4)

La primera versión del punto 2 de arriba usaba una bandera manual
(`_command_in_progress`) que **rechazaba** el segundo comando al instante
con un error visible — molesto si simplemente no habías esperado medio
minuto entre una acción y otra, ya que un comando puede tardar bastante
(hasta ~15s comprobando si el coche lo aceptó, más hasta 6s reintentando
confirmar el cambio).

Ahora es un `asyncio.Lock()` de verdad:

- Los comandos que **comparten estado** (los que usan `optimistic_update` —
  climatización, y desde esta versión también asientos, volante y
  desempañado) se ponen **en cola** y esperan su turno, hasta 30 segundos,
  en vez de fallar al instante. Si de verdad se supera ese tiempo (algo se
  ha quedado atascado), ahí sí se avisa con un error claro.
- Los comandos que **no** tocan ningún dato compartido (parpadear luces,
  claxon, luces+claxon a la vez) **nunca esperan a nada** — se ejecutan de
  inmediato aunque haya otro comando en curso, porque no hay ningún riesgo
  real de que se pisen.

**Verificado con simulaciones** (no con el coche real): confirmado que un
comando sin `optimistic_update` (claxon) no espera a uno que sí lo tiene
(climatización) en curso; que dos comandos que sí comparten estado se
ejecutan en cola, uno tras otro, nunca a la vez; y que si el lock queda
retenido más de 30 segundos, se lanza un error claro en vez de esperar para
siempre.

## 1. Cómo funciona el protocolo de comandos

Cada comando firmado sigue estos pasos:

1. **Pedir el número de serie cifrado del vehículo** (`GET serial-no/get`,
   ahora `api.get_serial_number()`). El servidor lo devuelve cifrado con
   nuestra propia clave pública de login.
2. **Descifrarlo** con la clave privada RSA que ya generamos en el login
   (`CONF_PRIVATE_KEY`, la misma que se usa para el intercambio de claves
   inicial) — `crypto.decrypt_with_private_key()`.
3. **Construir el payload** del comando concreto (p. ej.
   `{"command": "air", "enabled": true, "targetTemp": 220, ...}`) y añadirle
   `seriralNo` (sic — errata del propio fabricante, no nuestra) y
   `vehicleId`.
4. **Firmarlo**: se ordenan alfabéticamente las claves del payload
   (excluyendo `sign`, `class` y `command`), se concatenan como
   `clave=valor&clave=valor...` (booleanos en minúscula, `None` como la
   cadena `"null"`), y se firma ese texto con **RSA-SHA256 (PKCS#1 v1.5)**
   usando la misma clave privada. La firma en base64 se añade al payload
   como campo `sign` — `crypto.sign_command_payload()`.
5. **Enviarlo** por POST a la pasarela principal (`BASE_URL`, no la de CA) y
   leer el `commandId` de la respuesta.

Ninguno de los comandos de esta versión necesita el paso adicional del PIN
de control (que canjea un PIN cifrado por un `rcToken` de corta duración) —
eso solo hace falta para puertas, ventanas y maletero.

## 2. Comandos implementados

| Comando | Entidad HA | Endpoint | ¿PIN? | Estado |
| --- | --- | --- | --- | --- |
| Parpadear luces | `button.parpadear_luces` | `control/flashing-honking` (`type=1`) | No | ✅ Confirmado funcionando (2026-09-2x) |
| Tocar el claxon | `button.tocar_el_claxon` | `control/flashing-honking` (`type=2`) | No | ✅ Confirmado funcionando (2026-09-2x), tras el arreglo de renovación de sesión en v1.2.1b8 |
| Encender/apagar climatización + temperatura de consigna | `climate.climatizacion` | `control/air-conditioner` | No | ✅ Confirmado funcionando (2026-09-2x), comparado contra la app oficial Changan. El fallo inicial (`APP_1_1_02_004`) era sesión caducada, arreglado en v1.2.1b8 |
| Avisar al coche para que reporte datos frescos | (usado internamente tras cada comando, y por el botón "Actualizar datos del vehículo") | `control/condition-inquiry` | No | ✅ Confirmado funcionando (es lo que arregla el token caducado al pulsar "Actualizar") |
| Luces y claxon a la vez | `button.luces_y_claxon_a_la_vez` | `control/flashing-honking` (`type=3`) | No | ⚠️ Sin probar contra el vehículo real (añadido en v1.3.1b3) |
| Calefacción asiento conductor (nivel 0-3) | `number.calefaccion_asiento_conductor` | `control/seats/heat` | No | ⚠️ Sin probar (añadido en v1.3.1b4) |
| Calefacción asiento acompañante (nivel 0-3) | `number.calefaccion_asiento_acompanante` | `control/seats/heat` | No | ⚠️ Sin probar (añadido en v1.3.1b4) |
| Ventilación asiento conductor (nivel 0-3) | `number.ventilacion_asiento_conductor` | `control/seats/wind` | No | ⚠️ Sin probar (añadido en v1.3.1b4) |
| Ventilación asiento acompañante (nivel 0-3) | `number.ventilacion_asiento_acompanante` | `control/seats/wind` | No | ⚠️ Sin probar (añadido en v1.3.1b4) |
| Volante calefactado (on/off) | `switch.volante_calefactado` | `control/steering-wheel/heat` | No | ⚠️ Sin probar (añadido en v1.3.1b4) |
| Desempañado delantero (on/off) | `switch.desempanado_delantero` | `control/defrost` | No | ⚠️ Sin probar (añadido en v1.3.1b4). `ha-deepal-alternative` tiene el método en su cliente pero nunca lo conectó a ninguna entidad — somos los primeros en exponerlo |

### Detalles pendientes de confirmar

- **`targetTemp`**: el payload del comando espera **décimas de grado**
  (`22.5°C` → `225`), a diferencia del campo de telemetría
  `airConditioningSetTemperature`, que ya confirmamos que llega en grados
  directos por MQTT. Son formatos distintos para lectura y escritura — el
  `* 10` parece correcto (el climatizador ya confirmado funcionando lo usa),
  pero no se ha comprobado explícitamente que la temperatura mostrada en la
  app coincida exactamente con la pedida desde Home Assistant grado a
  grado — sería el último detalle fino a confirmar.
- **`windMode`**: fijo a `1` de momento (valor por defecto del proyecto de
  referencia). No se ha investigado qué otros valores acepta ni qué
  representan.
- **`runTime`**: fijo a `30` (minutos, presumiblemente). Sin confirmar.
- Los cuatro valores de `type` en `flashing-honking` según el proyecto de
  referencia: `0` = apagar, `1` = parpadear luces, `2` = claxon, `3` = ambos
  a la vez. Ya usamos los tres (`1`, `2` confirmados; `3` sin probar).
- **Asientos (calefacción/ventilación)**: la escala 0-3 y el hecho de que
  apagar un asiento debe mandar `switch: 0` **sin** el campo de nivel (nunca
  un `0` explícito, el servidor lo rechazaría) están confirmados leyendo el
  código de `ha-deepal-alternative`, pero no probados contra este vehículo.
- **Volante calefactado y desempañado**: payloads simples (`{"open": bool}`
  y `{"enabled": bool}` respectivamente), sin más parámetros que investigar,
  pero tampoco probados todavía.

## 3. Pendiente para una fase posterior (requiere PIN)

No implementado todavía. Necesita además el flujo de canje de PIN
(`security-code/get-status` → `security-code/check-code` → `rcToken`) y
guardar el PIN en la configuración de la integración.

| Comando | Endpoint |
| --- | --- |
| Bloquear/desbloquear puertas | `control/doors` |
| Subir/bajar ventanas | `control/windows` |
| Abrir/cerrar maletero | `control/trunk` |

## 4. Plan de verificación con el vehículo real

1. ~~**Parpadeo de luces**: pulsar el botón con el coche a la vista →
   confirmar visualmente que parpadean las luces exteriores.~~ ✅ Hecho.
2. ~~**Claxon**: igual, con el coche a la vista.~~ ✅ Hecho (tras el arreglo
   de renovación de sesión).
3. ~~**Climatización**: reautenticar la integración a mano una vez, y justo
   después intentar cambiar la temperatura desde Home Assistant. Comparar
   con la app oficial que se enciende y que la temperatura mostrada
   coincide.~~ ✅ Hecho — confirmado funcionando, comparado contra la app
   oficial Changan. Era sesión caducada, resuelto por el arreglo de
   v1.2.1b8.
4. Si algún comando falla con `DeepalCommandNotReady`, comprobar que la
   integración se reautenticó al menos una vez después de que se añadiera
   esta función (las entradas de configuración antiguas no tienen
   `CONF_PRIVATE_KEY` disponible para firmar comandos hasta que se
   reautentiquen).

Actualizar este documento con el resultado de cada prueba, igual que se ha
hecho en `telemetry-parameters.md`.
