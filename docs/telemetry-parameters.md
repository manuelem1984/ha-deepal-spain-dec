# Catálogo de parámetros de telemetría

Inventario de todas las claves que el vehículo envía por MQTT, su estado de
implementación en la integración y las comprobaciones pendientes.

- **Vehículo de referencia:** Deepal S05 (VIN `LS6CME0P6TK106840`)
- **Última actualización:** 2026-09-18 (limpieza v1.2.0: 4 campos confirmados como no útiles y retirados)
- **Claves recibidas en la primera captura:** 113
- **Mapeadas a entidades:** 37
- **Sin mapear / descartadas deliberadamente:** 76

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
| `diverWindow` / `passengerWindow` / `leftRearWindow` / `rightRearWindow` | ~~Ventanas~~ | ❌ Retirada en v1.2.0: duplicaba `driverDoor`/`passengerDoor`/`leftRearDoor`/`rightRearDoor` (renombradas a "Ventanilla..." al descubrir que ese era el par correcto). Se mantiene solo un conjunto de entidades. `diverWindow` es errata del fabricante |
| `lfTyrePressure` / `rfTyrePressure` / `lrTyrePressure` / `rrTyrePressure` | Presión neumáticos | ✅ Confirmado 2026-09-18: la unidad en bruto **sí es kPa** (293,82 / 288,33 / 291,08 / 296,57 kPa ÷ 100 ≈ 2,9 / 2,9 / 2,9 / 3,0 bar, coincide con la app). Mostrado en `sensor.py` como bar vía `suggested_unit_of_measurement` (sin tocar el valor guardado) |
| `highBeam` / `lowBeam` / `positionLamp` | Luces | |
| `turnLndicatorLeft` / `turnLndicatorRight` | Intermitentes | `Lndicator` es errata del fabricante |
| `hoodStatus` | Capó | ✅ Confirmado 2026-09-18: `"0"` = cerrado, `"1"` = abierto |
| `airStatus` | Aire acondicionado encendido | ✅ Confirmado 2026-09-18: `1` = encendido, `0` = apagado |
| `airConditioningHairRatings` | Velocidad del ventilador | ✅ Confirmado 2026-09-18: nivel entero (visto `2`). Rango completo (máximo) aún sin confirmar |
| `airConditioningSetTemperature` | Consigna de temperatura del clima | ✅ Confirmado 2026-09-18: grados directos (`22.5` = 22,5 °C), sin escalar |
| `leftAnteriorWindowDegree` / `rightAnteriorWindowDegree` / `leftRearWindowDegree` / `rightRearWindowDegree` | ~~% de apertura de cada ventana~~ | ❌ Retirada en v1.2.0: confirmado el 2026-09-18 que **no** es la posición de la ventana, sino su **aceleración de movimiento** — el valor solo cambia mientras el cristal se está moviendo y vuelve a `0` en cuanto se detiene (aunque quede abierto). No sirve para saber si una ventana está abierta o cerrada, así que no se expone como entidad. Explica además un valor `12` visto repetidamente junto a la puerta abierta: el S05 no tiene marco en las ventanillas y las baja solo unos milímetros al abrir la puerta (para no rozar la junta), lo que activa brevemente este campo de aceleración sin que nadie tocara la ventana |

## 2. Buscadas pero nunca recibidas (retiradas en v1.2.0)

`telemetry.py` consultaba estas claves, pero el vehículo nunca las envía — se
ha confirmado en todas las capturas hechas hasta ahora, con el coche tanto
parado como en marcha. Las entidades correspondientes ("Temperatura exterior"
y "Velocidad") se han retirado en v1.2.0 en vez de dejarlas mostrando
"Desconocido" para siempre.

| Clave buscada | Entidad retirada | Notas |
| --- | --- | --- |
| `outsideTemperature`, `externalTemperature` | Temperatura exterior | Si en el futuro aparece un nombre de campo distinto para esto, se puede volver a añadir |
| `vehicleSpeed`, `speed` | Velocidad | Probado también con el coche circulando (entrando en cochera) sin que apareciera ninguno de los dos campos |

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
| `skyWindowDegree` | Apertura techo solar | | | ? Sin cambios en la prueba del 2026-09-18 pese a mover "el parasol" — puede que el parasol (cortinilla textil) y el techo corredizo (cristal) sean mecanismos distintos. Falta probar moviendo el cristal, no la cortinilla |
| `spoilerPosition` | Posición del alerón | | | ? |
| `spoilerMovement` | Alerón en movimiento | | | ? |

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
