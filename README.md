# DEC Deepal S05 - Comunidad Deepal España

<p align="center">
  <img src="custom_components/deepal_spain_dec/brand/icon.png" alt="Logo DEC" width="160">
</p>

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)

Integración **no oficial** de Home Assistant para el **Deepal S05 comercializado
en España**. Lee la telemetría del coche desde la nube oficial de Deepal y permite
algunos comandos remotos (climatización, luces, claxon, asientos...).

- **Requiere Home Assistant 2026.3.0 o superior** (en versiones anteriores funciona,
  pero sin el icono de la marca).
- Comunidad y soporte: [Telegram Deepal España](https://t.me/deepalespana_general)

---

## ⚠️ Antes de instalar

- La usas **bajo tu propia responsabilidad**. No está afiliada ni respaldada por
  Deepal, Changan ni ningún fabricante.
- Pensada y probada solo con el **Deepal S05 de España**. Con coches de otros países
  o modelos puede no funcionar.
- **Iniciar sesión desde Home Assistant puede cerrar la sesión de la app oficial**
  (y al revés). Lo recomendable es usar una **cuenta secundaria** con el coche
  compartido desde la cuenta principal.
- Los comandos remotos actúan sobre el coche de verdad. Úsalos solo cuando sea
  seguro.

---

## 📥 Instalación

### Con HACS (recomendado)

1. HACS → menú ⋮ → **Repositorios personalizados**.
2. Añade `https://github.com/manuelem1984/ha-deepal-spain-dec` con tipo
   **Integración**.
3. Instala **DEC Deepal S05** y reinicia Home Assistant.

### Manual

1. Descarga la última versión desde
   [Releases](https://github.com/manuelem1984/ha-deepal-spain-dec/releases).
2. Copia la carpeta `custom_components/deepal_spain_dec` dentro de
   `config/custom_components/`.
3. Reinicia Home Assistant.

## ⚙️ Configuración

1. `Ajustes → Dispositivos y servicios → Añadir integración` → busca
   **DEC Deepal S05**.
2. Elige cómo iniciar sesión: **SMS** (teléfono español +34) o **correo
   electrónico**.
3. Introduce el código que recibas y selecciona tu vehículo.

Opcional: en **Configurar** puedes elegir la versión (Pro / Max / Max AWD) y el
color de tu coche para que la imagen del vehículo coincida con el tuyo
(ver [`docs/vehicle-photos.md`](docs/vehicle-photos.md)).

---

## 🚗 Entidades

Todas las entidades cuelgan de un único dispositivo (el coche). Los datos se
actualizan cada **5 minutos** y tras cada comando; el botón *Actualizar datos del
vehículo* fuerza una lectura inmediata.

Leyenda: ✅ comprobado con el coche real · ⚠️ implementado, pendiente de comprobar
con el coche real.

### Batería y carga

| Entidad | Tipo | Estado |
| --- | --- | --- |
| Batería | sensor (%) | ✅ |
| Autonomía estimada | sensor (km) | ✅ |
| Carga | binary_sensor | ✅ |
| Carga - Estado | sensor (Desconectado / Conectado AC / Conectado DC / Cargando AC / Cargando DC) | ✅ |
| Conector AC · Conector DC | binary_sensor | ✅ |
| Corriente de carga | sensor (A) | ✅ |
| Corriente de carga AC · Corriente de carga DC | sensor (A) | ⚠️ nuevo en 1.3.1b13 |
| Tiempo de carga restante | sensor (min) | ✅ |

### Estado del vehículo

| Entidad | Tipo | Estado |
| --- | --- | --- |
| Kilometraje total | sensor (km) | ✅ |
| Última actualización | sensor (fecha) | ✅ |
| Vehículo conectado | binary_sensor | ✅ |
| Motor - Estado | binary_sensor | ✅ |
| Estado de alimentación | sensor de diagnóstico (código en bruto) | ⚠️ nuevo en 1.3.1b13 |

### Puertas, cierres y ventanillas

| Entidad | Tipo | Estado |
| --- | --- | --- |
| Puerta Delantera/Trasera Izquierda/Derecha (4) | binary_sensor | ✅ |
| Maletero · Capó | binary_sensor | ✅ |
| Alguna puerta abierta (4 puertas + maletero) | binary_sensor | ⚠️ nuevo en 1.3.1b13 |
| Puerta Delantera Izquierda/Derecha Bloqueo (2) | binary_sensor | ⚠️ |
| Cierre centralizado | binary_sensor | ⚠️ nuevo en 1.3.1b13 |
| Ventanilla Delantera/Trasera Izquierda/Derecha (4) | binary_sensor | ⚠️ nuevo en 1.3.1b13 |

### Neumáticos

| Entidad | Tipo | Estado |
| --- | --- | --- |
| Presión neumático (4) | sensor (bar) | ✅ |
| Alarma neumático (4) | binary_sensor (problema) | ⚠️ nuevo en 1.3.1b13 |

### Clima interior y luces

| Entidad | Tipo | Estado |
| --- | --- | --- |
| Temperatura interior · Humedad interior | sensor | ✅ |
| Climatizador - Estado / Temperatura / Ventilador | binary_sensor / sensor | ✅ |
| Luz de carretera, de cruce, de posición, intermitentes | binary_sensor | ✅ |

### Control remoto

| Entidad | Tipo | ¿PIN? | Estado |
| --- | --- | --- | --- |
| Climatización (encender/apagar y temperatura) | climate | No | ✅ |
| Parpadear luces · Tocar el claxon | button | No | ✅ |
| Luces y claxon a la vez | button | No | ⚠️ |
| Calefacción / ventilación asiento conductor y acompañante (0-3) | number | No | ⚠️ |
| Volante calefactado · Desempañado delantero | switch | No | ⚠️ |
| Actualizar datos del vehículo | button | No | ✅ |
| Imagen del vehículo | image | — | ✅ |

**Aún no disponible:** abrir/cerrar puertas, ventanillas y maletero. Necesitan el
PIN de control remoto y llegarán en una fase posterior
(ver [`docs/remote-control.md`](docs/remote-control.md)).

---

## 🗑️ Desinstalación

1. `Ajustes → Dispositivos y servicios → DEC Deepal S05` → menú ⋮ → **Eliminar**.
   Borra el dispositivo, sus entidades y las credenciales guardadas. No afecta a tu
   cuenta ni a la app oficial.
2. Si la instalaste con **HACS**: HACS → DEC Deepal S05 → **Eliminar**.
   Si la instalaste **a mano**: borra `config/custom_components/deepal_spain_dec`.
3. Reinicia Home Assistant.

## 🛟 Problemas frecuentes

- **Una entidad tarda en cambiar**: el coche no envía datos al instante; espera al
  siguiente ciclo o pulsa *Actualizar datos del vehículo*.
- **Me pide volver a iniciar sesión**: normal si has entrado en la app oficial con la
  misma cuenta. Usa una cuenta secundaria para evitarlo.
- **Un comando falla con el coche dormido**: el coche a veces rechaza comandos si
  lleva mucho tiempo parado; vuelve a intentarlo tras usarlo.
- **Para reportar un fallo** usa *Descargar diagnósticos* en la página del
  dispositivo (oculta automáticamente VIN, tokens y teléfono) y abre un
  [Issue](https://github.com/manuelem1984/ha-deepal-spain-dec/issues).

---

## 📚 Documentación

| Documento | Contenido |
| --- | --- |
| [`CHANGELOG.md`](CHANGELOG.md) | Cambios de cada versión |
| [`docs/telemetry-parameters.md`](docs/telemetry-parameters.md) | Qué datos manda el coche, cuáles se usan y cómo se interpretan |
| [`docs/remote-control.md`](docs/remote-control.md) | Comandos remotos: protocolo, estado y pendientes |
| [`docs/backend-spain.md`](docs/backend-spain.md) | Endpoints de la nube de Deepal España |
| [`docs/vehicle-photos.md`](docs/vehicle-photos.md) | Fotos por versión y color |
| [`docs/roadmap.md`](docs/roadmap.md) | Próximos pasos |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Cómo colaborar y publicar versiones |

## 🚧 Estado del proyecto

Proyecto en desarrollo basado en ingeniería inversa. Puede haber cambios entre
versiones beta mientras se descubre más sobre la plataforma. Gracias a la comunidad
de Home Assistant y a Comunidad Deepal España por las pruebas.

<p align="center">
  <img src="deepalespana.jpeg" alt="Comunidad Deepal España" width="210">
</p>

¿Quieres estar al día? Únete en [Telegram](https://t.me/deepalespana_general).
