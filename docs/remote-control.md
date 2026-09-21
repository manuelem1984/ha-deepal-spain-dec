# Control remoto del vehículo

Inventario de los comandos de control remoto, su estado de implementación y
las comprobaciones pendientes. Sigue el mismo formato que
[`telemetry-parameters.md`](telemetry-parameters.md), pero para el sentido
contrario: escribir en el coche, no leerlo.

- **Vehículo de referencia:** Deepal S05 (VIN `LS6CME0P6TK106840`)
- **Origen de esta información:** ninguno de estos comandos se ha probado
  todavía contra el vehículo real. El protocolo completo (endpoints,
  cifrado, firma) se ha reconstruido comparando con
  [`ha-deepal-alternative`](https://github.com/dbarreiro/ha-deepal-alternative),
  otro proyecto open-source que ataca el mismo backend (sus
  `INTL_BASE_URL`/`INTL_CA_BASE_URL` coinciden exactamente con nuestro
  `BASE_URL`/`CA_BASE_URL`, confirmando que es la misma infraestructura).
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

## 2. Comandos implementados en v1.2.1b2

| Comando | Entidad HA | Endpoint | ¿PIN? | Estado |
| --- | --- | --- | --- | --- |
| Encender/apagar climatización + temperatura de consigna | `climate.climatizacion` | `control/air-conditioner` | No | ⚠️ Sin probar |
| Parpadear luces | `button.parpadear_luces` | `control/flashing-honking` (`type=1`) | No | ⚠️ Sin probar |
| Tocar el claxon | `button.tocar_el_claxon` | `control/flashing-honking` (`type=2`) | No | ⚠️ Sin probar |
| Avisar al coche para que reporte datos frescos | (usado internamente tras cada comando, y por el botón "Actualizar datos del vehículo") | `control/condition-inquiry` | No | ⚠️ Sin probar |

### Detalles pendientes de confirmar

- **`targetTemp`**: el payload del comando espera **décimas de grado**
  (`22.5°C` → `225`), a diferencia del campo de telemetría
  `airConditioningSetTemperature`, que ya confirmamos que llega en grados
  directos por MQTT. Son formatos distintos para lectura y escritura — hay
  que confirmar que el `* 10` es correcto para nuestro vehículo.
- **`windMode`**: fijo a `1` de momento (valor por defecto del proyecto de
  referencia). No se ha investigado qué otros valores acepta ni qué
  representan.
- **`runTime`**: fijo a `30` (minutos, presumiblemente). Sin confirmar.
- Los cuatro valores de `type` en `flashing-honking` según el proyecto de
  referencia: `0` = apagar, `1` = parpadear luces, `2` = claxon, `3` = ambos
  a la vez. Solo usamos `1` y `2` por ahora; `3` queda para más adelante.

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

Antes de dar esto por bueno, hace falta probar cada comando una vez y
comparar con la app oficial:

1. **Climatización**: encenderla desde Home Assistant a una temperatura
   concreta (p. ej. 21°C) → comprobar en la app oficial que se enciende y
   que la temperatura mostrada coincide. Repetir apagándola.
2. **Parpadeo de luces**: pulsar el botón con el coche a la vista →
   confirmar visualmente que parpadean las luces exteriores.
3. **Claxon**: igual, con el coche a la vista (¡avisar a quien esté cerca!).
4. Si alguno falla con `DeepalCommandNotReady`, comprobar que la
   integración se reautenticó al menos una vez después de que se añadiera
   esta función (las entradas de configuración antiguas no tienen
   `CONF_PRIVATE_KEY` disponible para firmar comandos hasta que se
   reautentiquen).

Actualizar este documento con el resultado de cada prueba, igual que se ha
hecho en `telemetry-parameters.md`.
