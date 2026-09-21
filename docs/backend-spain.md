# Deepal Spain Backend Notes

## Estado

Información obtenida mediante análisis del tráfico de la aplicación oficial Deepal para España.

---

## Autenticación SMS

Endpoint:

/intl-app-gw/intl-app-auth/api/login/send-auth-code

---

## Autenticación Email

Endpoint:

/intl-app-gw/intl-app-auth/api/login/email-send-auth-code

---

## Login SMS

Endpoint:

/intl-app-gw/intl-app-auth/api/login/login-by-mobile-code

Devuelve:

- token
- refreshToken
- cacToken
- userId
- caUserId
- cacUserId

---

## Login Email

Endpoint:

/intl-app-gw/intl-app-auth/api/login/email-code-in

Devuelve:

- token
- refreshToken
- cacToken
- userId
- caUserId
- cacUserId

---

## Refresh Token

Endpoint:

/intl-app-gw/intl-app-auth/api/auth/refresh-token

---

## Vehicle Discovery

Endpoint:

/intl-app-gw/intl-app-user/api/car/vehicles

---

## MQTT Connection Configuration

Endpoint:

/user-apigw/vot-connect-conf-center/api/device/getConnConf

Requiere:

X-Tsp-User-Token = access_token

Importante:

NO utilizar cacToken

---

## MQTT Auth Token

Endpoint:

/user-apigw/vot-connect-auth-center/api/auth/getAuthTokenByUserId

Requiere:

userId

---

## Remote Control (sin PIN) — desde v1.2.1b2

Ver [`remote-control.md`](remote-control.md) para el protocolo completo
(firma RSA-SHA256, número de serie cifrado, etc.). Resumen de endpoints:

/intl-app-gw/intl-app-car-control/api/serial-no/get
/intl-app-gw/intl-app-car-control/api/control/air-conditioner
/intl-app-gw/intl-app-car-control/api/control/condition-inquiry
/intl-app-gw/intl-app-car-control/api/control/flashing-honking

Confirmado contra el vehículo real: parpadeo de luces y claxon. Pendiente:
climatización (ver `remote-control.md`, sección 4). Puertas, ventanas y
maletero necesitan además el PIN de control — no implementado todavía.

---

## Confirmaciones realizadas

✅ Login SMS España (+34)

✅ Login Email

✅ Vehicle Discovery

✅ MQTT Config

✅ MQTT Auth

✅ X-Tsp-User-Token = access_token

❌ X-Tsp-User-Token = cacToken

✅ Control remoto sin PIN (parpadeo de luces, claxon)

⚠️ Control remoto sin PIN (climatización) — pendiente de confirmar

---

# Telemetry Inventory

## Battery

- soc

## Range

- remainedPowerMile

## Vehicle

- totalOdometer
- totalMeterYesterday (🆕 v1.2.1, ver nota)
- igniteCumulativeMileage (🆕 v1.2.1, ver nota)
- latestDate

## Climate

- vehicleTemperature
- innerHumidity

## Charging

- ChrgSts
- chargDeltMins

## Doors

- driverDoor
- passengerDoor
- leftRearDoor
- rightRearDoor

## Windows

- diverWindow
- passengerWindow
- leftRearWindow
- rightRearWindow

## Locks

- driverDoorLock
- passengerDoorLock

## TPMS

- lfTyrePressure
- rfTyrePressure
- lrTyrePressure
- rrTyrePressure
- leftFrontTireTemperature (🆕 v1.2.1, no funcional en el vehículo real — ver nota)
- rightFrontTireTemperature (🆕 v1.2.1, no funcional en el vehículo real — ver nota)
- leftRearTireTemperature (🆕 v1.2.1, no funcional en el vehículo real — ver nota)
- rightRearTireTemperature (🆕 v1.2.1, no funcional en el vehículo real — ver nota)

## Lights

- highBeam
- lowBeam
- positionLamp
- turnLndicatorLeft
- turnLndicatorRight

---

## Nota v1.2.1: campos importados por comparación con otro proyecto

Los 6 campos marcados 🆕 no se descubrieron por captura propia, sino
comparando con el proyecto open-source `ha-deepal-alternative` (que
reverse-engineerea el mismo backend). Los dos de kilometraje siguen
pendientes de confirmar; los 4 de temperatura por neumático ya se han
probado contra el vehículo real y **no funcionan** (muestran "Desconocido")
— ver `docs/telemetry-parameters.md` para el detalle y el siguiente paso
pendiente (un volcado de diagnósticos).

Ese mismo proyecto tenía además el control remoto del vehículo documentado
(puertas, ventanas, maletero, clima, luces...), incluyendo el mecanismo de
firma de comandos (RSA-SHA256 con la misma clave privada del login) y el
PIN de control para acciones físicas. La parte sin PIN (clima, luces,
claxon) ya está implementada — ver la sección "Remote Control" más arriba y
`docs/remote-control.md`. Puertas/ventanas/maletero (con PIN) siguen siendo
el siguiente gran bloque de trabajo pendiente de diseño.
