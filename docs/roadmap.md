# Hoja de ruta

Trabajo previsto hasta la próxima versión estable. El historial de lo ya hecho
está en [`CHANGELOG.md`](../CHANGELOG.md).

## Pruebas con el coche real (prioridad alta)

- [ ] **Entidades nuevas de 1.3.1b13:** ventanillas, alarmas de neumáticos,
      corriente AC/DC, estado de alimentación, "Alguna puerta abierta" y
      "Cierre centralizado".
- [ ] **Bloqueos:** confirmar qué valor en bruto significa "bloqueado"
      (cerrar y abrir el coche con el mando y comparar dos diagnósticos).
- [ ] **Estado de alimentación:** anotar el valor en cada situación (apagado,
      contacto, listo para circular) y darle nombres legibles.
- [ ] Luces y claxon a la vez.
- [ ] Calefacción y ventilación de asientos, volante calefactado y desempañado.
- [ ] Temperatura del climatizador grado a grado frente a la app oficial.

## Mejoras técnicas

- [ ] Comparar la marca de tiempo del endpoint REST de asientos/volante con la
      del MQTT antes de sustituir, para no pisar un dato nuevo con uno viejo.
- [ ] Recuperar temperatura exterior y de neumáticos desde ese mismo endpoint
      REST (el MQTT del S05 no las manda).
- [ ] Investigar `windMode` y `runTime` del comando de climatización.
- [ ] Dar significado a las candidatas de `telemetry-parameters.md` (tapa de
      carga, recirculación, testigos del cuadro...).

## Funcionalidades nuevas

- [ ] **Comandos con PIN:** puertas, ventanillas y maletero (el bloque grande
      pendiente). Ver `remote-control.md`, sección 5.
- [ ] Multiidioma y multipaís (selección de país en la configuración,
      traducciones completas de los nombres de entidad).
- [ ] Tarjeta/panel para el coche con foto, datos y comandos juntos. Un primer
      intento como panel lateral propio se retiró en 1.3.1b9 porque no
      funcionaba bien; antes de reintentarlo, averiguar qué falló.
