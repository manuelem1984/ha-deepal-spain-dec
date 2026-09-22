# Roadmap hacia la siguiente versión estable

Lista de trabajo para ir implementando en sucesivas betas a partir de la
v1.3.0. Se van tachando conforme se completan; cuando esté todo, se publica
la siguiente versión estable.

- [ ] Arreglar el error al enviar varias acciones de control seguidas
      (sustituir la bandera manual de "comando en curso" por un
      `asyncio.Lock()`, para que la segunda acción espere en cola en vez de
      fallar con un error visible; limitar la cola solo a los comandos que
      de verdad comparten estado — por ahora, climatización — dejando
      luces/claxon libres de solapamiento real)
- [ ] Confirmar `windMode` y `runTime` del comando de climatización (siguen
      fijos a valores por defecto, sin investigar qué otros valores acepta
      cada uno)
- [ ] Añadir un botón "luces + claxon a la vez" (`FLASH_HONK_FLASH_BEE`,
      `type=3`, ya definido en `const.py` pero sin usar en ninguna entidad)
- [ ] Investigar en otros proyectos similares si hay comandos adicionales sin
      PIN de control que podamos sumar (asientos, volante calefactado,
      desempañado)
- [ ] Multiidioma y multipaís (desplegable de país en el config flow,
      método de login según país, traducciones de la propia integración)
- [ ] Comandos de control con PIN (puertas, ventanas, maletero — el bloque
      grande que llevamos aplazando)
- [ ] Menú de configuración para elegir versión y color del Deepal S05
      (fotos ya disponibles, pendiente de decidir dónde subirlas al
      repositorio)
- [ ] **Última tarea de esta lista**: diseñar una Card para el coche, con
      la foto, los comandos sin PIN y los comandos con PIN todos juntos
