## Qué cambia y por qué

<!-- Describe el cambio. Si corrige un issue, enlázalo: "Fixes #123" -->

## Tipo de cambio

- [ ] Corrección de fallo
- [ ] Nuevo campo de telemetría / entidad
- [ ] Nuevo comando de control remoto
- [ ] Documentación
- [ ] Infraestructura (CI, tests, housekeeping)

## Checklist

- [ ] `python -m compileall custom_components/deepal_spain_dec` pasa sin errores
- [ ] `pytest tests/` pasa en local (o he revisado por qué falla)
- [ ] Si añado un campo de telemetría o comando nuevo, he actualizado `docs/telemetry-parameters.md` o `docs/remote-control.md`
- [ ] Si toco `manifest.json`, la versión coincide con el tag/release que se va a publicar
- [ ] No he incluido ningún dato personal (VIN, tokens, número de teléfono) en el PR ni en los logs de ejemplo

## Cómo se ha probado

<!-- ¿Contra el vehículo real, con datos simulados, o solo compilación/tests? Sé honesto sobre lo que falta por confirmar. -->
