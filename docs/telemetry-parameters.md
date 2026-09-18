# Catálogo de parámetros de telemetría

Inventario de todas las claves que el vehículo envía por MQTT, su estado de
implementación en la integración y las comprobaciones pendientes.

- **Vehículo de referencia:** Deepal S05 (VIN `LS6CME0P6TK106840`)
- **Última captura:** 2026-09-18 (coche en uso, entrando en cochera — no en reposo)
- **Claves recibidas en la captura:** 113
- **Mapeadas a entidades:** 36
- **Sin mapear:** 77

## Cómo capturar valores

Activar el log de depuración:

```yaml
logger:
  default: warning
  logs:
    custom_components.deepal_spain_dec.mqtt: debug
```

Pulsar *Actualizar datos del vehículo* y buscar en los registros:

- `Deepal MQTT: mapped keys received=` → claves presentes en el payload
- `Deepal MQTT: candidate values=` → valores reales de las candidatas
- `Deepal MQTT: unmapped service_code=` → servicios completos sin mapear

### Leyenda de estado

| Símbolo | Significado |
| --- | --- |
| OK | Mapeada y expuesta como entidad |
| ? | Recibida, semántica sin confirmar |
| X | Buscada por el código pero nunca recibida |
| - | Descartada (no aplica al S05) |

---

## 1. Implementadas

Claves ya mapeadas en `telemetry.py`. No requieren acción.

| Clave | Entidad | Notas |
| --- | --- | --- |
| `soc` / `socDsp` / `remainPower` | Batería (%) | Se usa la primera disponible |
| `remainedPowerMile` / `totalResidualMileage` | Autonomía estimada | |
| `totalOdometer` | Odómetro | |
| `engineStatus` | Motor encendido | |
| `latestDate` | Última actualización | ISO 8601 |
| `ChrgSts` | Cargando | |
| `BattACChrgInCurr` / `BattDCChrgInCurr` / `battACChrgInCurr` / `battDCChrgInCurr` | Corriente de carga | El fabricante envía ambas grafías |
| `chargDeltMins` | Minutos restantes de carga | `8191` = valor nulo |
| `vehicleTemperature` | Temperatura interior | |
| `innerHumidity` | Humedad interior | Décimas de % (se divide entre 10) |
| `driverDoor` / `passengerDoor` / `leftRearDoor` / `rightRearDoor` | Puertas | |
| `trunk` | Maletero | |
| `driverDoorLock` / `passengerDoorLock` | Cierre | |
| `diverWindow` / `passengerWindow` / `leftRearWindow` / `rightRearWindow` | Ventanas | `diverWindow` es errata del fabricante |
| `lfTyrePressure` / `rfTyrePressure` / `lrTyrePressure` / `rrTyrePressure` | Presión neumáticos | ✅ Confirmado 2026-09-18: la unidad en bruto **sí es kPa** (293,82 / 288,33 / 291,08 / 296,57 kPa ÷ 100 ≈ 2,9 / 2,9 / 2,9 / 3,0 bar, coincide con la app). Mostrado en `sensor.py` como bar vía `suggested_unit_of_measurement` (sin tocar el valor guardado) |
| `highBeam` / `lowBeam` / `positionLamp` | Luces | |
| `turnLndicatorLeft` / `turnLndicatorRight` | Intermitentes | `Lndicator` es errata del fabricante |

## 2. Buscadas pero nunca recibidas

`telemetry.py` consulta estas claves y el vehículo no las envía, por lo que las
entidades asociadas quedan permanentemente vacías. Hay que localizar el nombre
real o retirar la entidad.

| Clave buscada | Entidad afectada | Acción |
| --- | --- | --- |
| `outsideTemperature`, `externalTemperature` | Temperatura exterior | X Buscar nombre real |
| `vehicleSpeed`, `speed` | Velocidad | X Puede no exponerse en reposo |

> Comprobar si aparecen con el coche en marcha: es posible que solo se envíen
> con el contacto dado.

## 3. Candidatas prioritarias

Recibidas pero sin mapear. Ordenadas por utilidad práctica.

### 3.1 Carga

| Clave | Hipótesis | Valor en reposo | Valor cargando | Estado |
| --- | --- | --- | --- | --- |
| `acChargeGunConnectionState` | Conector AC enchufado | | | ? |
| `dcChargeGunConnectionState` | Conector DC enchufado | | | ? |
| `chargeCoverStatus` | Tapa de carga abierta | | | ? |
| `chargeSystemStatus` | Estado del sistema de carga | | | ? |
| `powerBatteryStatus` | Estado batería tracción | | | ? |
| `powerBatteryBreakStatus` | Desconexión de batería | | | ? |

### 3.2 Climatización

| Clave | Hipótesis | Apagado | Encendido | Estado |
| --- | --- | --- | --- | --- |
| `airStatus` | A/C encendido | | | ? |
| `airConditioningSetTemperature` | Consigna de temperatura | | | ✅ Confirmado 2026-09-18: `22.5` = 22,5 °C directos (grados, sin escalar) |
| `airConditioningHairRatings` | Velocidad del ventilador | | | ? Visto `2` el 2026-09-18 (climatización encendida). Rango total aún sin confirmar |
| `airRecycleStatus` | Recirculación de aire | | | ? |
| `frontDefrostStatus` | Desempañado delantero | | | ? |
| `airPurifierStatus` | Purificador de aire | | | ? |

### 3.3 Asientos y volante

| Clave | Hipótesis | Apagado | Encendido | Estado |
| --- | --- | --- | --- | --- |
| `driverSeatHeatStatus` | Calefacción asiento conductor | | | ? Confirmar si es 0-3 |
| `passengerSeatHeatStatus` | Calefacción asiento pasajero | | | ? |
| `driverSeatAirStatus` | Ventilación asiento conductor | | | ? |
| `passengerSeatAirStatus` | Ventilación asiento pasajero | | | ? |
| `steeringWheelHeating` | Volante calefactado | | | ? |

### 3.4 Apertura y carrocería

| Clave | Hipótesis | Cerrado | Abierto | Estado |
| --- | --- | --- | --- | --- |
| `hoodStatus` | Capó | | | ? |
| `skyWindowDegree` | Apertura techo solar | | | ? Confirmar escala 0-100 |
| `leftAnteriorWindowDegree` | Apertura ventana del. izq. | | | ? |
| `rightAnteriorWindowDegree` | Apertura ventana del. dcha. | | | ? |
| `leftRearWindowDegree` | Apertura ventana tras. izq. | | | ? |
| `rightRearWindowDegree` | Apertura ventana tras. dcha. | | | ? |
| `spoilerPosition` | Posición del alerón | | | ? |
| `spoilerMovement` | Alerón en movimiento | | | ? |

> Los `*Degree` permitirían sustituir los sensores binarios de ventana por
> sensores de porcentaje de apertura.

### 3.5 Neumáticos

| Clave | Hipótesis | Normal | Aviso | Estado |
| --- | --- | --- | --- | --- |
| `lfPressureWarning` | Aviso presión del. izq. | | | ? |
| `rfPressureWarning` | Aviso presión del. dcha. | | | ? |
| `lrPressureWarning` | Aviso presión tras. izq. | | | ? |
| `rrPressureWarning` | Aviso presión tras. dcha. | | | ? |
| `tireTemperatureStatus` | Temperatura de neumáticos | | | ? Comprobar si es global o por rueda |
| `tpmsLightStatus` | Testigo TPMS | | | ? |

### 3.6 Llave y accesos

| Clave | Hipótesis | Estado |
| --- | --- | --- |
| `keyLowPower` | Pila del mando baja | ? |
| `keylessEntryStartSystemStatus` | Estado sistema keyless | ? |
| `unlockKeyDrivingStatus` | Circulando con puertas abiertas | ? |
| `unlockKeyDrivingStartTime` | Marca temporal del aviso anterior | ? |
| `reverseRadarStatus` | Sensores de aparcamiento | ? |

### 3.7 Luces adicionales

| Clave | Hipótesis | Estado |
| --- | --- | --- |
| `frontFoglamp` | Antiniebla delantero | ? |
| `rearFoglamp` | Antiniebla trasero | ? |
| `brakeLightStatus` | Luz de freno | ? |

## 4. Testigos del cuadro

Probablemente booleanos de avería, candidatos a `binary_sensor` con
`device_class: problem`. Todos deberían valer `0` con el coche sano, lo que
facilita confirmar la polaridad.

> ⚠️ **Hallazgo 2026-09-18 — dos familias distintas, no confundir:**
> en una captura real con el coche recién circulando (sin ninguna avería
> conocida), estos campos aparecieron en `1` en vez de `0`:
> `aebLightStatus`, `accLightStatus`, `accStatus`, `ldwStatus`,
> `lwdLightStatus`, `machineOilStatus`. La hipótesis más probable es que los
> relacionados con ADAS (frenada de emergencia, control de crucero, aviso de
> cambio de carril) indican **"sistema activo/disponible"**, no una avería —
> tendría sentido que estén a `1` con el coche en marcha. Quedan pendientes
> de confirmar con una captura del coche parado/apagado (deberían bajar a
> `0`, o no — hay que comprobarlo). El resto de la tabla de abajo sí se
> comportó como se esperaba (`0` en todos, sin avisos).

| Clave | Testigo probable |
| --- | --- |
| `absLightStatus` | ABS |
| `airBagLightStatus` | Airbag |
| `batt12VLightStatus` | Batería 12 V |
| `bcuBattSocLightStatus` | Nivel de batería de tracción |
| `brakeFluidLightStatus` | Líquido de frenos |
| `coolanTemperatureLightStatus` | Temperatura refrigerante |
| `emsLightStatus` | Gestión del motor |
| `epbLightStatus` | Freno de mano eléctrico |
| `epsLightStatus` | Dirección asistida |
| `espLightStatus` | Control de estabilidad |
| `oilPressureLightStatus` | Presión de aceite |
| `oilFuelLightStatus` | Reserva de combustible |
| `powerLimitLightStatus` | Potencia limitada |
| `powerSystemLightStatus` | Sistema eléctrico |
| `aebLightStatus` | Frenada de emergencia |
| `iaccLightStatus` | Control de crucero adaptativo |
| `lwdLightStatus` | Aviso de cambio de carril |
| `accLightStatus` | Control de crucero |
| `pepsLightStatus` | Acceso sin llave |
| `ldwStatus` | Aviso de cambio de carril |
| `accStatus` | Estado del control de crucero |
| `absStatus` | Estado del ABS |
| `batteryVoltageError` | Error de tensión de batería |

### Estados de subsistema

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
| `powerStatusFeedBack` | Estado de alimentación |

## 5. No aplicables al S05

Heredadas de plataformas de combustión. El S05 es eléctrico puro, por lo que se
espera que devuelvan cero o valores sin sentido.

| Clave | Motivo |
| --- | --- |
| `fuelLeftover` | - Sin depósito |
| `remainingFuel` | - Sin depósito |
| `remainedOilMile` | - Sin depósito |

> Confirmar que efectivamente valen `0`. Si devolvieran algo coherente habría
> que revisar la hipótesis.

---

## Plan de comprobación en el vehículo

Dos capturas comparadas bastan para deducir la mayoría de escalas.

**Captura A — reposo**

Coche cerrado, sin contacto, climatización apagada, sin cargar.

**Captura B — con cambios provocados**

Aplicar y anotar cada acción:

1. Abrir el capó
2. Bajar una ventanilla concreta hasta la mitad
3. Abrir el techo solar por completo
4. Encender la climatización a una temperatura exacta (por ejemplo 21 °C)
5. Poner el ventilador en una velocidad concreta
6. Activar la calefacción del asiento del conductor
7. Enchufar el cable de carga
8. Encender los antiniebla

Comparando A y B, cada clave que cambie queda identificada sin ambigüedad,
incluida su escala. Anotar los resultados en las columnas vacías de las tablas
anteriores.

## Pendiente de investigar

- Canal de comandos: `parse_connection_config` excluye los topics con
  `/commands/` y `/set/`. Es la vía para bloqueo remoto, climatización y otras
  acciones. Requiere capturar el tráfico de la app oficial para conocer el
  formato del payload.
- Posición GPS: no aparece en la telemetría MQTT. Comprobar si se expone por un
  endpoint REST distinto.
- Confirmar la unidad de presión de neumáticos.
