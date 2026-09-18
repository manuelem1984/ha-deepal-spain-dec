# Integración Deepal S05 España (by Comunidad Deepal España)

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
- Actualmente, esta versión proporciona únicamente acceso a información de telemetría y monitorización del vehículo. No se incluyen funciones de control remoto.
- El inicio de sesión desde Home Assistant puede invalidar la sesión activa en la aplicación oficial Deepal. Del mismo modo, volver a iniciar sesión en la aplicación oficial puede requerir reautenticación en Home Assistant.

## 🚗 Vehículo Compatible

**Deepal S05 España**
- Telemetría en tiempo real.
- Datos de estado del vehículo.
- Sin funciones de control remoto.

## ✅ Funcionalidades Actuales

- Inicio de sesión mediante número de teléfono español (+34) y código SMS.
- Reconexión automática cuando la sesión cloud expira.
- Sensores de telemetría del vehículo.
- Sensores binarios de estado.
- Imagen dinámica del vehículo.
- Actualización manual de datos desde Home Assistant.
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

## 📝 Notas

- La integración consulta periódicamente los datos almacenados en la nube de Deepal.
- Algunas entidades pueden tardar varios minutos en reflejar cambios producidos en el vehículo.
- Si utilizas simultáneamente la aplicación oficial y Home Assistant, puede ser necesario volver a iniciar sesión ocasionalmente.
- El conjunto de sensores disponibles puede ampliarse en futuras versiones a medida que se descubran nuevos puntos de integración.
- Consulta [docs/telemetry-parameters.md](docs/telemetry-parameters.md) para ver el inventario completo de parámetros que expone el vehículo y cuáles están ya implementados.

## 🚧 Estado del Proyecto

**DEC Deepal S05** es un proyecto en desarrollo basado en ingeniería inversa del ecosistema Deepal.
Se esperan mejoras continuas, nuevas entidades y posibles cambios incompatibles entre versiones mientras evoluciona el conocimiento de las APIs utilizadas por la plataforma.

Agradecimientos a la comunidad de Home Assistant por su colaboración y apoyo durante el desarrollo del proyecto.

Proporcione sus comentarios sobre BizChat

## Comunidad

<p align="center">
  <img src="deepalespana.jpeg" alt="Deepal logo" width="210">
</p>

Si quieres saber más y estar al tanto de todo únete a nosotros en...
Telegram: https://t.me/deepalespana_general
