Aquí tienes un **README.md** listo para tu repo:

# Thumbnail Maker (Python)

Script para generar **thumbnails estilo blog/YouTube** de forma automática:

- Fondo con **desenfoque gaussiano**
- Texto centrado en **Arial blanco**, con **sombra exterior** + **sombra interior**
- **Uno o varios iconos PNG** descargados automáticamente (SimpleIcons)
- Exporta **PNG/JPG de alta calidad** y **PSD con capas editables** (para seguir trabajando en Photoshop)

---

## 🚀 Requisitos

- Python 3.8+
- Dependencias:

```bash
pip install pillow pytoshop requests cairosvg
````

> **Tip (Linux):** instala Arial con `sudo apt install ttf-mscorefonts-installer` o cambia la ruta a otra fuente en la config.

---

## 📦 Instalación

1. Clona o descarga este repo.
2. Asegúrate de tener las dependencias instaladas.
3. Ajusta la ruta de la fuente (`FONT_PATH`) en el script si no usas Windows.

---

## 🧰 Uso rápido (CLI)

```bash
python thumbnail_maker.py fondo.jpg \
  -t "Mi Dual boot Windows 11\ny Ubuntu" \
  -i windows -i ubuntu \
  --out-png dualboot.png --out-psd dualboot.psd
```

* `fondo.jpg`: imagen base
* `-t/--text`: texto principal (usa `\n` para saltos de línea manuales)
* `-i/--icon`: puedes repetirlo para varios iconos (usa nombres válidos de [SimpleIcons](https://simpleicons.org))
* `--out-png`: nombre del PNG/JPG final
* `--out-psd`: nombre del PSD con capas

Otro ejemplo:

```bash
python thumbnail_maker.py mi_cuarto.jpg \
  -t "Convirtiendo mi cuarto en un wallpaper con" \
  -i photoshop -i openai \
  --out-png cuarto.png --out-psd cuarto.psd
```

---

## 🔧 Configuración rápida

En la parte superior del script (`CONFIG`) puedes ajustar:

* `CANVAS_W`, `CANVAS_H`: tamaño final (1920×1080 por defecto)
* `BG_BLUR_RADIUS`: intensidad del desenfoque
* `TEXT_MAX_WIDTH`: ancho máximo usado por el bloque de texto (porcentaje del lienzo)
* Offsets y blur de sombras (texto e iconos)
* `ICON_MAX_WIDTH`, `ICON_GAP`: tamaño y separación de iconos
* `FONT_PATH`: ruta a tu tipografía

---

## 🧩 Uso como módulo (desde otro script)

```python
from thumbnail_maker import build_thumbnail

build_thumbnail(
    background_path="fondo.jpg",
    text="Mi título increíble",
    icon_queries=["windows", "ubuntu"],
    out_png="salida.png",
    out_psd="salida.psd"
)
```

---

## 🖼️ Sobre los iconos

El script usa **SimpleIcons** (`https://cdn.simpleicons.org/<slug>/ffffff`) y convierte el SVG a PNG con `cairosvg`.
Para usar otro proveedor:

* Cambia la función `download_icon()` para apuntar a la API/URL que prefieras.
* O pasa rutas locales directamente (puedes modificar la firma para aceptarlas).

---

## 📁 Estructura de capas en el PSD

* `Background_Blur`
* `Text` (texto con sombras integradas)
* `Icon_1`, `Icon_2`, ...

> Puedes separar aún más las sombras en capas individuales si lo necesitas (edita la lista `layers_for_psd`).

---

## ❗ Problemas comunes

* **“No pude ajustar el texto, es demasiado largo.”**
  Reduce el texto o aumenta `TEXT_MAX_WIDTH`/disminuye `start_size`.

* **La fuente no se encuentra**
  Cambia `FONT_PATH` a una ruta válida o instala la fuente.

* **Icono no encontrado (404)**
  Verifica el nombre en SimpleIcons. Ej: `adobephotoshop` vs `photoshop`.

---

## 🛣️ Roadmap / Ideas

* GUI sencilla (Tkinter/Gradio) para arrastrar y soltar
* Soporte para múltiples estilos de tipografía y color
* Efectos adicionales (stroke, glow, gradientes)
* Plantillas JSON para diferentes layouts

---

## 🤝 Contribuye

1. Haz un fork
2. Crea una rama: `git checkout -b feature/lo-que-sea`
3. Haz commit: `git commit -m "Añade X"`
4. Push: `git push origin feature/lo-que-sea`
5. Abre un PR

---

## 📄 Licencia

MIT. Usa este código libremente, ¡pero sin garantías! Consulta `LICENSE`.

---

## ✨ Créditos

* [Pillow](https://python-pillow.org/)
* [pytoshop](https://github.com/kyamagu/pytoshop)
* [SimpleIcons](https://simpleicons.org/)
* [CairoSVG](https://cairosvg.org/)
