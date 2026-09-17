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

## Lights

- highBeam
- lowBeam
- positionLamp
- turnLndicatorLeft
- turnLndicatorRight
