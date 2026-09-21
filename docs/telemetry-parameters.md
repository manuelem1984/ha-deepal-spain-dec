# Catálogo de parámetros de telemetría

Inventario de todas las claves que el vehículo envía por MQTT, su estado de
implementación en la integración y las comprobaciones pendientes. Para el
control remoto (escribir en el coche, no leerlo), ver
[`remote-control.md`](remote-control.md).

- **Vehículo de referencia:** Deepal S05 (VIN `LS6CME0P6TK106840`)
- **Última actualización:** 2026-09-2x (v1.2.1b7/b8: renombrado de entidades
  tras pruebas reales — confirmado que `driverDoor`/etc. son puertas, no
  ventanas; temperatura por neumático confirmada como no funcional, pendiente
  de diagnósticos)
- **Claves recibidas en la primera captura:** 113
- **Mapeadas a entidades:** 43
- **Sin mapear / descartadas deliberadamente:** 70

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
| `totalMeterYesterday` | Kilometraje de ayer | 🆕 v1.2.1: campo importado por comparación con otro proyecto (`ha-deepal-alternative`), pendiente de confirmar con este vehículo |
| `igniteCumulativeMileage` | Kilometraje desde el encendido actual | 🆕 v1.2.1: ídem, pendiente de confirmar |
| `engineStatus` | Motor - Estado | Muestra "Encendido"/"Apagado" (traducción propia, ver `strings.json`), no el texto genérico de `device_class: running` |
| `latestDate` | Última actualización | ISO 8601 |
| `ChrgSts` | Cargando | |
| `BattACChrgInCurr` / `BattDCChrgInCurr` / `battACChrgInCurr` / `battDCChrgInCurr` | Corriente de carga | El fabricante envía ambas grafías |
| `chargDeltMins` | Minutos restantes de carga | `8191` = valor nulo |
| `vehicleTemperature` | Temperatura interior | |
| `innerHumidity` | Humedad interior | Décimas de % (se divide entre 10) |
| `driverDoor` / `passengerDoor` / `leftRearDoor` / `rightRearDoor` | Puerta Delantera/Trasera Izquierda/Derecha | ✅ Confirmado contra el vehículo real: son las puertas físicas (abrir una puerta cambia esta entidad). Renombradas de "Ventanilla..." a "Puerta..." en v1.2.1b7 — la hipótesis anterior de que estos campos eran ventanas era incorrecta |
| `trunk` | Maletero | |
| `driverDoorLock` / `passengerDoorLock` | Puerta Delantera Izquierda/Derecha Bloqueo | Renombradas en v1.2.1b7 (antes "Puerta del Conductor/Acompañante Bloqueo") |
| `diverWindow` / `passengerWindow` / `leftRearWindow` / `rightRearWindow` | ~~Ventanas~~ | ❌ Retirada en v1.2.0 por duplicar el conjunto anterior. `diverWindow` es errata del fabricante. **Ojo:** dado que `driverDoor`/etc. han resultado ser las puertas de verdad, estos campos (`diverWindow`/etc.) podrían ser en realidad las ventanas — pendiente de confirmar si interesa recuperarlos como entidad de ventana en el futuro |
| `lfTyrePressure` / `rfTyrePressure` / `lrTyrePressure` / `rrTyrePressure` | Presión neumáticos | ✅ Confirmado 2026-09-18: la unidad en bruto **sí es kPa** (293,82 / 288,33 / 291,08 / 296,57 kPa ÷ 100 ≈ 2,9 / 2,9 / 2,9 / 3,0 bar, coincide con la app). Mostrado en `sensor.py` como bar vía `suggested_unit_of_measurement` (sin tocar el valor guardado) |
| `leftFrontTireTemperature` / `rightFrontTireTemperature` / `leftRearTireTemperature` / `rightRearTireTemperature` | Temperatura por neumático | ❌ Probado contra el vehículo real: las 4 entidades muestran "Desconocido" permanentemente. Los nombres de campo venían de `ha-deepal-alternative`, nunca confirmados con este coche — puede que el S05 no los envíe con estos nombres, o no los envíe en absoluto. **Pendiente de un volcado de diagnósticos** para decidir si se buscan con otro nombre o se retiran, como se hizo con temperatura exterior/velocidad |
| `highBeam` / `lowBeam` / `positionLamp` | Luces | |
| `turnLndicatorLeft` / `turnLndicatorRight` | Luz Intermitente Izquierdo/Derecho | `Lndicator` es errata del fabricante. Entidades renombradas en v1.2.1b7 (antes "Intermitente izquierdo/derecho") |
| `hoodStatus` | Capó | ✅ Confirmado 2026-09-18: `"0"` = cerrado, `"1"` = abierto |
| `airStatus` | Climatizador - Estado | ✅ Confirmado 2026-09-18: `1` = encendido, `0` = apagado. Renombrada en v1.2.1b7 (antes "Aire acondicionado encendido") |
| `airConditioningHairRatings` | Climatizador - Ventilador | ✅ Confirmado 2026-09-18: nivel entero (visto `2`). Rango completo (máximo) aún sin confirmar. Renombrada en v1.2.1b7 (antes "Velocidad del ventilador") |
| `airConditioningSetTemperature` | Climatizador - Temperatura | ✅ Confirmado 2026-09-18: grados directos (`22.5` = 22,5 °C), sin escalar. Renombrada en v1.2.1b7 (antes "Consigna de temperatura"). **Ojo:** el comando de escritura (`control_air_conditioner`, ver `remote-control.md`) espera el valor en décimas de grado — formato distinto al de lectura, sin confirmar todavía |
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
| `tireTemperatureStatus` | ~~Temperatura de neumáticos~~ | | | ❌ Hipótesis descartada en v1.2.1: no es un campo agregado. Ver `leftFrontTireTemperature`/etc. en la sección 1 — que a su vez tampoco han funcionado en la prueba real, ver nota ahí |
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
| `leftBackSeatHeatStatus` / `rightBackSeatHeatStatus` / `leftBackSeatVentilateStatus` / `rightBackSeatVentilateStatus` | - Detectados en `ha-deepal-alternative`, pero el Deepal S05 comercializado en España **no lleva** calefacción/ventilación en las plazas traseras — de propósito, no se implementan |

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
3. Abrir el techo solar por completo (el cristal, no solo la cortinilla)
4. Encender la climatización a una temperatura exacta (por ejemplo 21 °C)
5. Poner el ventilador en una velocidad concreta
6. Activar la calefacción del asiento del conductor
7. Enchufar el cable de carga
8. Encender los antiniebla

Comparando A y B, cada clave que cambie queda identificada sin ambigüedad,
incluida su escala. Anotar los resultados en las columnas vacías de las tablas
anteriores.

## Pendiente de investigar

- **Temperatura por neumático**: confirmado que no funciona con este
  vehículo (sección 1) — necesita un volcado de diagnósticos para decidir
  el siguiente paso.
- **Control remoto**: puertas, ventanas y maletero (requieren PIN) — ver
  [`remote-control.md`](remote-control.md) para el estado completo. La
  climatización, luces y claxon ya están implementados (sin PIN); luces y
  claxon confirmados funcionando, climatización pendiente de una segunda
  prueba tras el arreglo de renovación de sesión en v1.2.1b8.
- Posición GPS: no aparece en la telemetría MQTT. Comprobar si se expone por un
  endpoint REST distinto.
