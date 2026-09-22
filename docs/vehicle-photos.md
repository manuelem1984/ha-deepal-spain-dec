# Fotos del vehículo por versión y color

Desde la v1.3.1, la integración puede mostrar una foto que coincida
exactamente con la versión y el color del coche del usuario, en vez de una
foto genérica. Se elige en Ajustes → Dispositivos y Servicios → esta
integración → **Configurar**.

## Dónde van los archivos

```
custom_components/deepal_spain_dec/assets/vehicle_photos/
```

## Convención de nombres

```
<grupo_visual>_<color>.png
```

- **`<grupo_visual>`**: `pro` o `max`. El Max AWD es mecánicamente distinto
  (tracción total) pero **exteriormente idéntico** al Max, así que comparte
  las mismas fotos — no hace falta subir una copia aparte para "Max AWD".
- **`<color>`**: uno de los 5 colores oficiales del S05, en minúsculas y con
  guion bajo:

| Color oficial | Nombre de archivo |
| --- | --- |
| Andromeda Blue | `andromeda_blue` |
| Deep Space Black | `deep_space_black` |
| Ganymede Grey | `ganymede_grey` |
| Mercury Silver | `mercury_silver` |
| Moonlight White | `moonlight_white` |

## Los 10 archivos completos

```
pro_andromeda_blue.png
pro_deep_space_black.png
pro_ganymede_grey.png
pro_mercury_silver.png
pro_moonlight_white.png
max_andromeda_blue.png
max_deep_space_black.png
max_ganymede_grey.png
max_mercury_silver.png
max_moonlight_white.png
```

## Prioridad al mostrar la imagen (`image.py`)

1. Si el usuario ha elegido versión **y** color en Configurar, y existe el
   archivo correspondiente → esa foto exacta.
2. Si no, y Deepal devuelve una URL de imagen para el vehículo → esa.
3. Si no, la foto genérica de siempre (`assets/deepal_s05.png`).

Si falta algún archivo de la lista de arriba, no pasa nada — simplemente se
usa el escalón 2 o 3 para esa combinación hasta que se añada.
