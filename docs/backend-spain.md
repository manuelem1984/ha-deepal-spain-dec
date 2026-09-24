# Backend de Deepal España

Endpoints de la nube oficial que usa la integración. Obtenidos analizando el
tráfico de la app oficial Deepal para España.

## Servidores

| Nombre en el código | URL | Uso |
| --- | --- | --- |
| `BASE_URL` | `https://m.iov.changanauto.com.de` | Inicio de sesión, vehículos y comandos |
| `CA_BASE_URL` | `https://ca-m.iov.changanauto.com.de` | Configuración y autenticación MQTT |

## Inicio de sesión

| Paso | Endpoint |
| --- | --- |
| Pedir código por SMS | `/intl-app-gw/intl-app-auth/api/login/send-auth-code` |
| Pedir código por correo | `/intl-app-gw/intl-app-auth/api/login/email-send-auth-code` |
| Entrar con código SMS | `/intl-app-gw/intl-app-auth/api/login/login-by-mobile-code` |
| Entrar con código de correo | `/intl-app-gw/intl-app-auth/api/login/email-code-in` |
| Renovar la sesión | `/intl-app-gw/intl-app-auth/api/auth/refresh-token` |

Ambos inicios de sesión devuelven `token`, `refreshToken`, `cacToken`, `userId`,
`caUserId` y `cacUserId`.

## Vehículos

| Paso | Endpoint |
| --- | --- |
| Listar vehículos de la cuenta | `/intl-app-gw/intl-app-user/api/car/vehicles` |
| Estado del vehículo bajo demanda (asientos, clima, estado general) | `/intl-app-gw/intl-app-car-condition/api/vehicle/condition` |

## MQTT (telemetría)

| Paso | Endpoint | Notas |
| --- | --- | --- |
| Configuración de conexión | `/user-apigw/vot-connect-conf-center/api/device/getConnConf` | Cabecera `X-Tsp-User-Token` = `access_token` (**no** el `cacToken`) |
| Token de autenticación MQTT | `/user-apigw/vot-connect-auth-center/api/auth/getAuthTokenByUserId` | Requiere `userId` |

El listado de datos que llegan por MQTT y cómo se interpretan está en
[`telemetry-parameters.md`](telemetry-parameters.md).

## Control remoto

Todos bajo `/intl-app-gw/intl-app-car-control/api/`. El protocolo completo (número
de serie cifrado, firma RSA-SHA256, confirmación del resultado) está en
[`remote-control.md`](remote-control.md).

| Endpoint | Uso | ¿Firmado? |
| --- | --- | --- |
| `serial-no/get` | Número de serie cifrado para firmar | — |
| `control/air-conditioner` | Climatización | Sí |
| `control/flashing-honking` | Luces / claxon | Sí |
| `control/condition-inquiry` | Pedir datos frescos al coche | Sí |
| `control/seats/heat` · `control/seats/wind` | Asientos | Sí |
| `control/steering-wheel/heat` | Volante calefactado | Sí |
| `control/defrost` | Desempañado | Sí |
| `control/control-result` | ¿El coche aceptó el comando? | No |

Puertas, ventanillas y maletero necesitan además el PIN de control; no están
implementados.

## Comprobado

| Qué | Resultado |
| --- | --- |
| Inicio de sesión por SMS (+34) y por correo | ✅ |
| Listado de vehículos | ✅ |
| Configuración y autenticación MQTT | ✅ |
| `X-Tsp-User-Token` = `access_token` | ✅ |
| `X-Tsp-User-Token` = `cacToken` | ❌ no funciona |
| Comandos sin PIN: luces, claxon, climatización | ✅ |
