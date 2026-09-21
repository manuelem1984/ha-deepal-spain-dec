# Contribuir a DEC Deepal S05

Gracias por el interés en colaborar. Este es un proyecto pequeño, mantenido por la
Comunidad Deepal España, y se basa en ingeniería inversa del backend de Deepal — así
que la honestidad sobre qué está confirmado y qué no es más importante aquí que en un
proyecto típico.

## Antes de empezar

- Si es un fallo o una idea, abre primero un [Issue](https://github.com/manuelem1984/ha-deepal-spain-dec/issues) — evita trabajo duplicado.
- Si es un campo de telemetría o comando de control nuevo, revisa
  [`docs/telemetry-parameters.md`](docs/telemetry-parameters.md) y
  [`docs/remote-control.md`](docs/remote-control.md) primero: puede que ya esté
  documentado como "candidata sin confirmar".

## Entorno de desarrollo

No hace falta un Home Assistant real para la mayoría de cambios en la lógica pura
(`telemetry.py`, `crypto.py`, `api_errors.py`):

```bash
pip install pytest cryptography
pytest tests/ -v
```

Para probar la integración de verdad hace falta una instancia de Home Assistant
(≥ 2026.3.0) y una cuenta de Deepal España — idealmente una cuenta secundaria con el
vehículo compartido, no la cuenta propietaria (ver el README, sección "Avisos
Importantes").

## Antes de abrir el Pull Request

- `python -m compileall custom_components/deepal_spain_dec` sin errores.
- `pytest tests/` en verde.
- Si añades un campo de telemetría o comando nuevo, documéntalo en
  `docs/telemetry-parameters.md` o `docs/remote-control.md`, aunque no lo hayas
  podido confirmar todavía contra el vehículo real — marca claramente qué está
  confirmado y qué es solo una hipótesis.
- Si tocas `manifest.json`, la versión debe coincidir con el tag que se vaya a
  publicar (ver más abajo).

## Publicar una versión (solo mantenedores)

1. Sube la versión en `manifest.json` — es la única fuente de verdad, `const.py` la
   lee sola.
2. Commit y push.
3. Crea el tag/release en GitHub (marca **pre-release** si es una beta) usando la
   plantilla de [`.github/release_template.md`](.github/release_template.md).
4. El workflow de CI valida automáticamente que el tag coincide con la versión de
   `manifest.json` — si no coincide, el release falla y hay que corregirlo antes de
   volver a intentarlo.

## Sobre los datos sensibles

Nunca compartas (ni en Issues, ni en PRs, ni en capturas) tu VIN completo, tokens de
sesión, ni tu número de teléfono. El menú de "Descargar diagnósticos" de la propia
integración ya oculta estos campos automáticamente — úsalo en vez de pegar logs en
crudo cuando sea posible.
