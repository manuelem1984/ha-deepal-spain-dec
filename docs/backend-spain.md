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

## Confirmaciones realizadas

✅ Login SMS España (+34)

✅ Login Email

✅ Vehicle Discovery

✅ MQTT Config

✅ MQTT Auth

✅ X-Tsp-User-Token = access_token

❌ X-Tsp-User-Token = cacToken

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
- leftFrontTireTemperature (🆕 v1.2.1, ver nota)
- rightFrontTireTemperature (🆕 v1.2.1, ver nota)
- leftRearTireTemperature (🆕 v1.2.1, ver nota)
- rightRearTireTemperature (🆕 v1.2.1, ver nota)

## Lights

- highBeam
- lowBeam
- positionLamp
- turnLndicatorLeft
- turnLndicatorRight

---

## Nota v1.2.1: campos importados por comparación con otro proyecto

Los 6 campos marcados 🆕 no se han descubierto por captura propia, sino comparando
con el proyecto open-source `ha-deepal-alternative` (que reverse-engineerea el
mismo backend). Los nombres de campo son fiables (su código los usa en
producción), pero los **valores concretos y las unidades siguen sin confirmar
contra este vehículo** — ver `docs/telemetry-parameters.md` para el detalle y
el plan de verificación pendiente.

Ese mismo proyecto tiene además implementado el **control remoto** del
vehículo (puertas, ventanas, maletero, clima, luces...), incluyendo el
mecanismo de firma de comandos (RSA-SHA256 con la misma clave privada del
login) y el PIN de control para acciones físicas. Queda como siguiente gran
bloque de trabajo, pendiente de diseño.
