# Historial de cambios

Resumen de cada versión. El detalle técnico de cada dato o comando está en
[`docs/telemetry-parameters.md`](docs/telemetry-parameters.md) y
[`docs/remote-control.md`](docs/remote-control.md).

Las versiones `bN` son betas (pre-release en GitHub).

---

## 1.3.1b14

**Comandos con PIN: puertas, ventanillas y maletero.** Bloque completo,
desactivado por defecto — ver [`docs/remote-control.md`](docs/remote-control.md),
sección 5, para el diseño detallado.

| Entidad | Tipo | Estado |
| --- | --- | --- |
| Bloqueo de puertas | lock | ⚠️ sin confirmar con el coche real |
| Maletero | cover | ⚠️ sin confirmar con el coche real |
| Ventanilla Delantera/Trasera Izquierda/Derecha (4) | cover | ⚠️ sin confirmar; forma exacta del payload por ventanilla también sin confirmar |
| Desbloqueo Acciones PIN | lock | Solo con la Opción B — candado de armado, nunca envía comandos al coche |

**Cómo activarlo:** en *Configurar*, activa "PIN de control remoto habilitado"
e introduce el PIN creado desde la app oficial con la misma cuenta — se
verifica en el momento contra el servidor, y no se activa si es incorrecto.
Elige después entre Opción A (comandos directos) y Opción B (hace falta
desbloquear "Desbloqueo Acciones PIN" primero, con rebloqueo automático
pasado el tiempo configurado).

**Otros cambios**

- Las entidades `lock`/`cover` conviven con los `binary_sensor` de solo
  lectura que ya existían para puertas/ventanillas/maletero desde v1.3.1b13.
- Nuevos tests: `tests/test_api.py` (intercambio y renovación del `rcToken`),
  `tests/test_coordinator.py` (decisión de bloqueo por armado),
  `tests/test_config_flow.py` (verificación del PIN al activarlo).

## 1.3.1b13

**Nuevas entidades (solo lectura).** Todos los datos llegan ya en el MQTT
del S05, así que no hace falta ningún permiso ni configuración extra.

| Entidad | Tipo | Dato en bruto | Icono |
| --- | --- | --- | --- |
| Corriente de carga AC | sensor (A) | `BattACChrgInCurr` / `battACChrgInCurr` | `mdi:current-ac` |
| Corriente de carga DC | sensor (A) | `BattDCChrgInCurr` / `battDCChrgInCurr` | `mdi:current-dc` |
| Estado de alimentación | sensor de diagnóstico | `powerStatusFeedBack` | `mdi:car-cog` |
| Ventanilla Delantera Izquierda | binary_sensor (ventana) | `diverWindow` | `mdi:window-open-variant` / `mdi:window-closed-variant` |
| Ventanilla Delantera Derecha | binary_sensor (ventana) | `passengerWindow` | ídem |
| Ventanilla Trasera Izquierda | binary_sensor (ventana) | `leftRearWindow` | ídem |
| Ventanilla Trasera Derecha | binary_sensor (ventana) | `rightRearWindow` | ídem |
| Alarma neumático delantero izquierdo | binary_sensor (problema) | `lfPressureWarning` | `mdi:car-tire-alert` / `mdi:tire` |
| Alarma neumático delantero derecho | binary_sensor (problema) | `rfPressureWarning` | ídem |
| Alarma neumático trasero izquierdo | binary_sensor (problema) | `lrPressureWarning` | ídem |
| Alarma neumático trasero derecho | binary_sensor (problema) | `rrPressureWarning` | ídem |
| Alguna puerta abierta | binary_sensor (puerta) | calculado: 4 puertas + maletero | `mdi:car-door` / `mdi:car` |
| Cierre centralizado | binary_sensor (cerradura) | calculado: bloqueo de las 2 puertas delanteras | `mdi:lock-open-variant` / `mdi:lock` |

**Otros cambios**

- Documentación reorganizada: README con la tabla completa de entidades, nuevo
  `CHANGELOG.md`, y los documentos de `docs/` limpios de notas históricas.
- Nuevas pruebas: cada clave que lee `telemetry.py` tiene que estar declarada
  para los diagnósticos, y las claves de las entidades no pueden repetirse.
- Eliminada la plantilla de release duplicada (`.github/RELEASE_TEMPLATE.md`).

**Pendiente de comprobar con el coche real:** todas las entidades nuevas. Ver
"Cómo probar esta versión" en las notas de la release.

## 1.3.1b10 – 1.3.1b12

- Sensores **Conector AC** y **Conector DC** (manguera enchufada). Corregido el
  umbral: los valores `0` y `1` significan *no conectado*; `2` o más, conectado.
- Nuevo sensor **Carga - Estado** que combina los tres anteriores:
  Desconectado / Conectado AC / Conectado DC / Cargando AC / Cargando DC, con un
  icono distinto para cada estado.
- "Cargando" pasa a llamarse **Carga**.

## 1.3.1b7 – 1.3.1b9

- Se probó un panel propio "DEC - Vehículos" en la barra lateral. No funcionó
  bien y se **retiró por completo** en b9.

## 1.3.1b6

- La lectura de **asientos, volante calefactado y desempañado** por MQTT no era
  fiable (no seguía al estado real). Ahora se lee de un segundo endpoint más
  fiable tras cada actualización; el MQTT queda solo como reserva.

## 1.3.1b4 – 1.3.1b5

- Nuevos controles sin PIN: **calefacción y ventilación de asientos
  delanteros** (niveles 0-3), **volante calefactado** y **desempañado
  delantero**.
- Los comandos que comparten estado se ponen en cola (hasta 30 s) en lugar de
  fallar si se pulsan seguidos.

## 1.3.1b2 – 1.3.1b3

- Elección de **versión y color** del coche en *Configurar* (10 fotos).
- Botón **Luces y claxon a la vez**.
- Arreglada la traducción de las etiquetas del formulario de opciones.

## 1.3.0

- Primera versión estable con **control remoto sin PIN**: climatización
  (confirmada con el coche real), parpadear luces y claxon.
- Instrucciones de desinstalación.

## 1.2.x

- Control remoto sin PIN (firma RSA de comandos, número de serie cifrado).
- Actualización optimista: la entidad cambia al momento y se confirma después.
- Renovación silenciosa de la sesión también en los comandos.
- Confirmación real de cada comando con el coche (`control-result`).
- Redacción adicional en diagnósticos (por subcadena: token, pin, vin...).
- Nombres de entidades revisados: las antiguas "Ventanilla..." eran en realidad
  las **puertas**, y se renombraron a "Puerta...".
- Retiradas entidades que el S05 nunca envía: temperatura exterior, velocidad,
  kilometraje de ayer / del trayecto y temperatura de cada neumático.

## 1.1.x

- Diagnósticos descargables desde la página del dispositivo.
- Reautenticación cuando la sesión caduca.
- Imagen de respaldo del vehículo.
- Presión de neumáticos mostrada en bar.
- Pruebas unitarias y CI (hassfest, HACS, compilación).

## 1.0.x

- Primera versión: inicio de sesión por SMS/correo, telemetría por MQTT,
  sensores, sensores binarios, imagen del vehículo y botón de actualizar.
