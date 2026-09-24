# Parámetros de telemetría

Qué datos envía el Deepal S05 por MQTT, cuáles usa la integración, cómo se
interpretan y cuáles quedan por investigar. Para los comandos (escribir en el
coche en lugar de leerlo) ver [`remote-control.md`](remote-control.md).

- **Vehículo de referencia:** Deepal S05 España.
- **Última revisión:** v1.3.1b13.
- **Claves vistas en las capturas:** 113 · **leídas por la integración:** 54
  (lista exacta en `telemetry.MAPPED_KEYS`).

## Leyenda

| Símbolo | Significado |
| --- | --- |
| ✅ | Comprobado con el coche real |
| ⚠️ | Implementado; interpretación tomada de material de referencia, pendiente de comprobar con el coche real |
| ? | Llega del coche, pero aún no se sabe qué significa |
| ❌ | Descartado (no llega, no sirve o no aplica al S05) |

## Cómo se procesan los datos

1. `mqtt.py` recibe el mensaje del coche (un diccionario plano `clave: valor`).
2. `telemetry.parameters_to_telemetry()` lo convierte en un `DeepalTelemetry`
   (`models.py`) con valores ya limpios: enteros, decimales, booleanos o `None`
   si el dato no llega.
3. Tras cada lectura MQTT, `coordinator._async_overlay_condition()` pide un
   segundo endpoint REST y **sustituye** solo los datos de asientos, volante y
   desempañado (el MQTT no es fiable para ellos, ver
   [`remote-control.md`](remote-control.md#4-lectura-fiable-de-asientos-y-volante)).
4. Cada entidad (`sensor.py`, `binary_sensor.py`...) lee un campo de
   `DeepalTelemetry`.

Reglas de conversión que se repiten:

- **Booleano** (`as_bool`): `0` → falso, cualquier otro número → verdadero.
- **Conector de carga** (`as_charge_connector_connected`): `0` y `1` → no
  conectado; `2` o más → conectado.
- **Nivel de asiento** (`as_seat_level`): valor en bruto 0-6 ÷ 2 → nivel 0-3.
- Si un dato no llega, la entidad muestra *Desconocido* en lugar de inventar un
  valor.

---

## 1. Datos en uso

### Batería y carga

| Clave | Entidad | Estado | Notas |
| --- | --- | --- | --- |
| `soc` / `socDsp` / `remainPower` | Batería | ✅ | Se usa la primera que llegue |
| `remainedPowerMile` / `totalResidualMileage` | Autonomía estimada | ✅ | |
| `ChrgSts` | Carga | ✅ | |
| `acChargeGunConnectionState` | Conector AC | ✅ | `0`/`1` = no conectado; `2`+ = conectado (se ha visto `3` cargando). Un booleano simple fallaba: el coche manda `1` desenchufado |
| `dcChargeGunConnectionState` | Conector DC | ✅ | Mismo umbral que el AC |
| (calculado) | Carga - Estado | ✅ | Combina Carga + Conector AC + Conector DC → Desconectado / Conectado AC / Conectado DC / Cargando AC / Cargando DC |
| `BattACChrgInCurr` / `BattDCChrgInCurr` / `battACChrgInCurr` / `battDCChrgInCurr` | Corriente de carga | ✅ | Primer valor disponible (AC o DC). El coche usa las dos grafías |
| `BattACChrgInCurr` / `battACChrgInCurr` | Corriente de carga AC | ⚠️ | Nuevo en 1.3.1b13. Solo la parte AC |
| `BattDCChrgInCurr` / `battDCChrgInCurr` | Corriente de carga DC | ⚠️ | Nuevo en 1.3.1b13. Solo la parte DC |
| `chargDeltMins` | Tiempo de carga restante | ✅ | `8191` significa "sin estimación" → *Desconocido* |

### Estado del vehículo

| Clave | Entidad | Estado | Notas |
| --- | --- | --- | --- |
| `totalOdometer` | Kilometraje total | ✅ | |
| `latestDate` / `lastUpdatedAt` | Última actualización | ✅ | ISO 8601, se guarda en UTC |
| `engineStatus` | Motor - Estado | ✅ | Muestra "Encendido"/"Apagado" |
| `powerStatusFeedBack` | Estado de alimentación | ⚠️ | Nuevo en 1.3.1b13. Código numérico en bruto (sensor de diagnóstico). Pendiente de anotar qué valor corresponde a apagado / accesorios / encendido / listo para circular |
| (fijo) | Vehículo conectado | ✅ | Siempre "conectado" si la lectura tuvo éxito: indica que el coche responde en la nube, **no** que esté enchufado |

### Puertas, cierres y ventanillas

| Clave | Entidad | Estado | Notas |
| --- | --- | --- | --- |
| `driverDoor` / `passengerDoor` / `leftRearDoor` / `rightRearDoor` | Puerta Delantera/Trasera Izquierda/Derecha | ✅ | Son las puertas físicas |
| `trunk` | Maletero | ✅ | |
| `hoodStatus` | Capó | ✅ | `0` cerrado, `1` abierto |
| (calculado) | Alguna puerta abierta | ⚠️ | Nuevo en 1.3.1b13. Encendido si cualquiera de las 4 puertas **o el maletero** está abierto. El capó no cuenta. *Desconocido* solo si no se sabe nada de ninguna |
| `driverDoorLock` / `passengerDoorLock` | Puerta Delantera Izquierda/Derecha Bloqueo | ⚠️ | Tipo "cerradura" de HA: *encendido = desbloqueado*. El material de referencia indica `0` = bloqueado; **falta comprobarlo** con el coche (cerrarlo con el mando y mirar la entidad) |
| (calculado) | Cierre centralizado | ⚠️ | Nuevo en 1.3.1b13. "Desbloqueado" si cualquiera de las dos puertas delanteras lo está. Sigue exactamente la misma convención que las dos entidades anteriores, así que si esa convención se corrige, se corrige para las tres a la vez |
| `diverWindow` / `passengerWindow` / `leftRearWindow` / `rightRearWindow` | Ventanilla Delantera/Trasera Izquierda/Derecha | ⚠️ | Nuevo en 1.3.1b13. `0` cerrada, otro valor abierta. `diverWindow` es una errata del propio coche. **Ojo:** el S05 no tiene marco en las ventanillas y las baja unos milímetros al abrir la puerta; puede verse "abierta" un momento al abrir o cerrar una puerta |

### Neumáticos

| Clave | Entidad | Estado | Notas |
| --- | --- | --- | --- |
| `lfTyrePressure` / `rfTyrePressure` / `lrTyrePressure` / `rrTyrePressure` | Presión neumático | ✅ | Llega en kPa y se muestra en bar (293,8 kPa ≈ 2,9 bar, igual que la app) |
| `lfPressureWarning` / `rfPressureWarning` / `lrPressureWarning` / `rrPressureWarning` | Alarma neumático | ⚠️ | Nuevo en 1.3.1b13. Tipo "problema": `0` = OK, otro valor = aviso. Muy difícil de comprobar a propósito; con presiones normales debe verse OK |

### Clima interior

| Clave | Entidad | Estado | Notas |
| --- | --- | --- | --- |
| `vehicleTemperature` | Temperatura interior | ✅ | Grados directos |
| `innerHumidity` | Humedad interior | ✅ | Llega en décimas de % (se divide entre 10) |
| `airStatus` | Climatizador - Estado | ✅ | `1` encendido, `0` apagado |
| `airConditioningHairRatings` | Climatizador - Ventilador | ✅ | Nivel entero; máximo sin confirmar |
| `airConditioningSetTemperature` | Climatizador - Temperatura | ✅ | Grados directos (`22.5`). El comando de escritura usa décimas (`225`) |

### Asientos, volante y desempañado

El MQTT **no es fiable** para estos datos (guarda el último nivel configurado, no
el estado actual). Se usan solo como reserva si falla el endpoint REST que los
sustituye.

| Clave MQTT (reserva) | Clave REST (la que se usa) | Entidad |
| --- | --- | --- |
| `driverSeatHeatStatus` / `passengerSeatHeatStatus` | `seat.leftFront.heatStatus` / `seat.rightFront.heatStatus` | Calefacción asiento conductor / acompañante |
| `driverSeatAirStatus` / `passengerSeatAirStatus` | `seat.leftFront.ventStatus` / `seat.rightFront.ventStatus` | Ventilación asiento conductor / acompañante |
| `steeringWheelHeating` | `vehicleStatus.steeringWheelHeater` | Volante calefactado |
| `frontDefrostStatus` | `hvac.defrostStatus` | Desempañado delantero |

### Luces

| Clave | Entidad | Estado |
| --- | --- | --- |
| `highBeam` / `lowBeam` / `positionLamp` | Luz de carretera / de cruce / de posición | ✅ |
| `turnLndicatorLeft` / `turnLndicatorRight` | Luz Intermitente Izquierdo / Derecho | ✅ (`Lndicator` es errata del coche) |

---

## 2. Descartados

### No llegan nunca en el S05

Se buscaron en todas las capturas (coche parado y en marcha) y no aparecen. Las
entidades se retiraron para no mostrar *Desconocido* para siempre.

| Clave | Entidad retirada | Versión |
| --- | --- | --- |
| `outsideTemperature`, `externalTemperature` | Temperatura exterior | 1.2.0 |
| `vehicleSpeed`, `speed` | Velocidad | 1.2.0 |
| `totalMeterYesterday` | Kilometraje de ayer | 1.2.1b10 |
| `igniteCumulativeMileage` | Kilometraje del trayecto | 1.2.1b10 |
| `leftFrontTireTemperature` y resto de ruedas | Temperatura de cada neumático | 1.2.1b10 |

### Llegan, pero no sirven

| Clave | Motivo |
| --- | --- |
| `leftAnteriorWindowDegree` / `rightAnteriorWindowDegree` / `leftRearWindowDegree` / `rightRearWindowDegree` | No es la apertura de la ventanilla: es su **movimiento**. Solo cambia mientras el cristal se mueve y vuelve a `0` al pararse |

### No aplican al S05

| Clave | Motivo |
| --- | --- |
| `fuelLeftover`, `remainingFuel`, `remainedOilMile` | El S05 de España es eléctrico puro (sin depósito) |
| `leftBackSeatHeatStatus`, `rightBackSeatHeatStatus`, `leftBackSeatVentilateStatus`, `rightBackSeatVentilateStatus` | El S05 de España no tiene calefacción ni ventilación en las plazas traseras |
| `airPurifierStatus` (como "calidad del aire") | El material de referencia lo interpreta como nivel de calidad del aire, pero excluye ese dato para el S05. Sigue en la lista de candidatas como "purificador" |
| `electronichandbrakeStatus` (como sensor de freno de mano) | Igual: el material de referencia no lo considera fiable en el S05. Sigue como candidata |

---

## 3. Candidatas (llegan, pero aún no se sabe qué significan)

### Carga

| Clave | Hipótesis |
| --- | --- |
| `chargeCoverStatus` | Tapa de carga abierta |
| `chargeSystemStatus` | Estado del sistema de carga |
| `powerBatteryStatus` | Estado de la batería de tracción |
| `powerBatteryBreakStatus` | Desconexión de la batería |

### Climatización

| Clave | Hipótesis |
| --- | --- |
| `airRecycleStatus` | Recirculación de aire |
| `airPurifierStatus` | Purificador de aire |

### Carrocería

| Clave | Hipótesis |
| --- | --- |
| `skyWindowDegree` | Apertura del techo. No cambió al mover la cortinilla; falta probar moviendo el cristal |
| `spoilerPosition` / `spoilerMovement` | Posición / movimiento del alerón |

### Llave y accesos

| Clave | Hipótesis |
| --- | --- |
| `keyLowPower` | Pila del mando baja |
| `keylessEntryStartSystemStatus` | Sistema de acceso sin llave |
| `unlockKeyDrivingStatus` / `unlockKeyDrivingStartTime` | Circulando con puertas abiertas (y cuándo empezó) |
| `reverseRadarStatus` | Sensores de aparcamiento |

### Luces adicionales

| Clave | Hipótesis |
| --- | --- |
| `frontFoglamp` / `rearFoglamp` | Antinieblas delantero / trasero |
| `brakeLightStatus` | Luz de freno |

### Testigos del cuadro

Probablemente avisos de avería (candidatos a binary_sensor de tipo "problema").
Con el coche sano deberían valer `0`.

> **Ojo:** con el coche recién circulando aparecieron en `1` `aebLightStatus`,
> `accLightStatus`, `accStatus`, `ldwStatus`, `lwdLightStatus` y
> `machineOilStatus`. Los de asistencia a la conducción (frenada de emergencia,
> crucero, carril) probablemente indican "sistema activo", no avería. Falta una
> captura con el coche apagado para confirmarlo.

| Clave | Testigo probable |
| --- | --- |
| `absLightStatus` / `absStatus` | ABS |
| `airBagLightStatus` | Airbag |
| `batt12VLightStatus` | Batería de 12 V |
| `bcuBattSocLightStatus` | Nivel de batería de tracción |
| `brakeFluidLightStatus` | Líquido de frenos |
| `coolanTemperatureLightStatus` | Temperatura del refrigerante |
| `emsLightStatus` | Gestión del motor |
| `epbLightStatus` | Freno de mano eléctrico |
| `epsLightStatus` | Dirección asistida |
| `espLightStatus` | Control de estabilidad |
| `oilPressureLightStatus` | Presión de aceite |
| `oilFuelLightStatus` | Reserva de combustible |
| `powerLimitLightStatus` | Potencia limitada |
| `powerSystemLightStatus` | Sistema eléctrico |
| `aebLightStatus` | Frenada de emergencia |
| `iaccLightStatus` / `accLightStatus` / `accStatus` | Control de crucero |
| `lwdLightStatus` / `ldwStatus` | Aviso de cambio de carril |
| `pepsLightStatus` | Acceso sin llave |
| `tpmsLightStatus` | Testigo de presión de neumáticos |
| `batteryVoltageError` | Error de tensión de batería |

### Estado de subsistemas

| Clave | Subsistema |
| --- | --- |
| `airbagSystemStatus` | Airbags |
| `brakeFluidStatus` | Líquido de frenos |
| `electronichandbrakeStatus` | Freno de mano |
| `engineSystemStatus` | Motor |
| `engineCoolantStatus` | Refrigerante |
| `evpowercontrolSystemStatus` | Control de potencia EV |
| `machineOilStatus` | Aceite |
| `motorSystemStatus` | Motor eléctrico |
| `transmissionSystemStatus` | Transmisión |
| `vehicleStabilityControlSystemStatus` | Control de estabilidad |
| `assistantSteeringStatus` | Dirección asistida |

---

## 4. Cómo capturar datos del coche

**Opción A — diagnósticos (recomendada).** En la página del dispositivo, menú ⋮ →
*Descargar diagnósticos*. El JSON incluye:

- `entidades_mapeadas`: el valor actual de cada entidad.
- `parametros_en_bruto`: todo lo que mandó el coche en la última lectura.
- `sin_mapear`: lo que llega pero ninguna entidad usa todavía.

Datos personales (VIN, tokens, teléfono...) salen ocultos automáticamente.

**Opción B — registro de depuración.**

```yaml
logger:
  default: warning
  logs:
    custom_components.deepal_spain_dec.mqtt: debug
```

Pulsa *Actualizar datos del vehículo* y busca en los registros:

- `Deepal MQTT: mapped keys received=` → claves que llegaron.
- `Deepal MQTT: candidate values=` → valores reales de las candidatas.
- `Deepal MQTT: unmapped service_code=` → bloques completos sin mapear.

### Plan de prueba en dos capturas

1. **Captura A (reposo):** coche cerrado con el mando, sin contacto, clima
   apagado, sin cargar.
2. **Captura B (con cambios):** anota cada acción que hagas, por ejemplo:
   abrir el capó, bajar una ventanilla concreta, abrir el techo (el cristal),
   encender el clima a 21 °C, cambiar la velocidad del ventilador, activar un
   asiento, enchufar el cable, encender antinieblas, **abrir el coche con el
   mando** (para confirmar los bloqueos) y **dar el contacto** (para el Estado de
   alimentación).

Comparando A y B, cada clave que cambia queda identificada junto con su escala.
Anota el resultado en las tablas de arriba.

## 5. Pendiente de investigar

- **Bloqueos:** confirmar qué valor de `driverDoorLock` / `passengerDoorLock`
  significa "bloqueado" (afecta a las dos entidades de bloqueo y a Cierre
  centralizado).
- **Estado de alimentación:** anotar los valores de `powerStatusFeedBack` en cada
  situación (apagado, accesorios, contacto, listo) para darle nombres legibles.
- **Temperatura exterior y de neumáticos:** el endpoint REST que ya se usa para los
  asientos parece incluirlas. Se podrían recuperar desde ahí.
- **Frescura de los datos REST:** comparar su `lastUpdatedAt` con el del MQTT antes
  de sustituir, para no pisar un dato nuevo con uno viejo.
- **GPS:** no hay ninguna prueba de que esta API exponga la posición. Los
  diagnósticos ocultan `lat`/`lon`/`lng`/`latitude`/`longitude` por precaución, por
  si algún día aparecen.
