# DEC Deepal S05 - Comunidad Deepal España

<p align="center">
  <img src="custom_components/deepal_spain_dec/brand/icon.png" alt="Deepal logo" width="160">
</p>

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)

Integración no oficial para Home Assistant destinada a vehículos Deepal S05 comercializados en España.

Telegram: https://t.me/deepalespana_general

**Requiere Home Assistant 2026.3.0 o superior** (usa el mecanismo de iconos de marca locales introducido en esa versión; en versiones anteriores la integración funciona pero sin icono).

## ⚠️ Avisos Importantes

- El uso de esta integración se realiza bajo tu propia responsabilidad.
- DEC Deepal S05 es una integración no oficial para Home Assistant y no está afiliada, respaldada ni soportada por Deepal, Changan ni ningún fabricante relacionado.
- Esta integración ha sido desarrollada específicamente para vehículos Deepal S05 comercializados en España y puede no funcionar correctamente con vehículos registrados en otros países o regiones.
- Además de telemetría y monitorización, incluye control remoto en beta (encender/apagar climatización y fijar temperatura, parpadear luces, tocar el claxon) — ver la sección de funcionalidades más abajo y [`docs/remote-control.md`](docs/remote-control.md) para el estado exacto de cada comando. Puertas, ventanas y maletero (requieren PIN de control) no están implementados todavía.
- El inicio de sesión desde Home Assistant puede invalidar la sesión activa en la aplicación oficial Deepal. Del mismo modo, volver a iniciar sesión en la aplicación oficial puede requerir reautenticación en Home Assistant.

## 🚗 Vehículo Compatible

**Deepal S05 España**
- Telemetría en tiempo real.
- Datos de estado del vehículo.
- Control remoto en beta: climatización, luces, claxon (ver más abajo). Puertas, ventanas y maletero pendientes de una fase posterior.

## ✅ Funcionalidades Actuales

- Inicio de sesión mediante número de teléfono español (+34) y código SMS.
- Reconexión automática cuando la sesión cloud expira.
- Sensores de telemetría del vehículo.
- Sensores binarios de estado.
- Imagen dinámica del vehículo.
- Actualización manual de datos desde Home Assistant.
- **Control remoto (beta):** parpadear luces y tocar el claxon, confirmados
  funcionando contra el vehículo real. Encender/apagar la climatización y
  fijar temperatura está implementado pero todavía pendiente de confirmar.
  Ver [`docs/remote-control.md`](docs/remote-control.md) — puertas,
  ventanas y maletero (requieren PIN de control) quedan para una fase
  posterior.
- Integración basada en la plataforma cloud oficial utilizada por Deepal España.

## 📥 Instalación

**HACS**

- Abre HACS en Home Assistant.
- Accede a Integrations.
- Selecciona Custom repositories desde el menú de opciones.
- Añade el repositorio: https://github.com/manuelem1984/ha-deepal-spain-dec
- Selecciona el tipo Integration.
- Instala DEC Deepal S05.
- Reinicia Home Assistant.

**Instalación Manual**

- Descarga la última versión desde: https://github.com/manuelem1984/ha-deepal-spain-dec

DEC Deepal S05 GitHub Repository

- Copia la carpeta: `custom_components/deepal_spain_dec`
- al directorio: `config/custom_components/`
- Reinicia Home Assistant.

## ⚙️ Configuración

- Abre Home Assistant.
- Ve a: `Ajustes → Dispositivos y Servicios → Añadir Integración`
- Busca: `DEC Deepal S05`
- Introduce tu número de teléfono asociado a la aplicación Deepal España.
- Introduce el código SMS recibido.
- Selecciona tu vehículo.

Una vez completado el proceso, Home Assistant comenzará a mostrar la información disponible del vehículo.

## 🗑️ Desinstalación

**Desde Home Assistant (siempre, tanto si instalaste por HACS como a mano):**

- Ve a `Ajustes → Dispositivos y Servicios`.
- Busca la tarjeta `DEC Deepal S05` y ábrela.
- Pulsa el menú ⋮ de la entrada de configuración → `Eliminar`.

Esto borra el dispositivo y todas sus entidades de Home Assistant, junto con las credenciales guardadas (tokens, clave privada de login). **No** cierra la sesión en la aplicación oficial de Deepal ni afecta a tu cuenta — puedes seguir usando la app con normalidad.

**Si instalaste con HACS**, además:

- Ve a `HACS → Integrations`.
- Busca `DEC Deepal S05` en tus repositorios instalados y pulsa `Eliminar`/`Desinstalar`.
- Reinicia Home Assistant.

**Si instalaste manualmente**, además:

- Borra la carpeta `config/custom_components/deepal_spain_dec`.
- Reinicia Home Assistant.

## 📝 Notas

- La integración consulta periódicamente los datos almacenados en la nube de Deepal.
- Algunas entidades pueden tardar varios minutos en reflejar cambios producidos en el vehículo.
- Si utilizas simultáneamente la aplicación oficial y Home Assistant, puede ser necesario volver a iniciar sesión ocasionalmente.
- El conjunto de sensores disponibles puede ampliarse en futuras versiones a medida que se descubran nuevos puntos de integración.
- Consulta [docs/telemetry-parameters.md](docs/telemetry-parameters.md) para ver el inventario completo de parámetros que expone el vehículo y cuáles están ya implementados.
- Consulta [docs/remote-control.md](docs/remote-control.md) para ver el estado exacto de cada comando de control remoto.

## 🚧 Estado del Proyecto

**DEC Deepal S05** es un proyecto en desarrollo basado en ingeniería inversa del ecosistema Deepal.
Se esperan mejoras continuas, nuevas entidades y posibles cambios incompatibles entre versiones mientras evoluciona el conocimiento de las APIs utilizadas por la plataforma.

Agradecimientos a la comunidad de Home Assistant por su colaboración y apoyo durante el desarrollo del proyecto.

## Comunidad

<p align="center">
  <img src="deepalespana.jpeg" alt="Deepal logo" width="210">
</p>

Si quieres saber más y estar al tanto de todo únete a nosotros en...
Telegram: https://t.me/deepalespana_general
