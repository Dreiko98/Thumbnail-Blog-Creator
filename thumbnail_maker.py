#!/usr/bin/env python3
import io
import math
import os
import textwrap
from pathlib import Path
from typing import List, Tuple
import platform

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# PSD
from pytoshop.user import nested_layers as nl

# -------------------- CONFIG --------------------
CANVAS_W, CANVAS_H = 1920, 1080          # tamaño final (puedes cambiarlo)
BG_BLUR_RADIUS = 25                      # desenfoque gaussiano
TEXT_MAX_WIDTH = 0.8                     # % del ancho del canvas ocupado por el texto
TEXT_LINE_SPACING = 1.1                  # multiplicador del tamaño de fuente
TEXT_OUTER_SHADOW_OFFSET = (4, 4)
TEXT_OUTER_SHADOW_BLUR = 8
TEXT_INNER_SHADOW_OFFSET = (3, 3)
TEXT_INNER_SHADOW_BLUR = 6
TEXT_COLOR = (255, 255, 255, 255)
ICON_OUTER_SHADOW_OFFSET = (4, 4)
ICON_OUTER_SHADOW_BLUR = 8
ICON_MAX_WIDTH = 200                     # ancho máx por icono (reducido de 380 a 200)
ICON_GAP = 30                            # separación entre iconos (reducido de 40 a 30)

# Detectar fuente según el OS
def get_font_path():
    system = platform.system()
    if system == "Linux":
        # Probar diferentes fuentes comunes en Linux
        fonts = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Arial.ttf"  # fallback
        ]
    elif system == "Windows":
        fonts = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf"
        ]
    elif system == "Darwin":  # macOS
        fonts = [
            "/System/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc"
        ]
    else:
        fonts = []
    
    for font in fonts:
        if os.path.exists(font):
            return font
    
    # Si no encuentra ninguna, usar fuente por defecto de PIL
    return None

FONT_PATH = get_font_path()
# ------------------------------------------------


# ---------- Utilidades de iconos ----------
def download_icon(query: str) -> Image.Image:
    """
    Descarga un icono PNG transparente usando simpleicons + cairosvg.
    query: 'windows', 'ubuntu', 'photoshop', etc.
    """
    slug = query.lower().replace(" ", "")
    url = f"https://cdn.simpleicons.org/{slug}/ffffff"  # blanco para que combine bien
    r = requests.get(url, timeout=15)
    if r.status_code != 200:
        raise RuntimeError(f"No se pudo descargar icono '{query}' ({r.status_code})")
    # El recurso es SVG -> convertir a PNG
    import cairosvg
    png_bytes = cairosvg.svg2png(bytestring=r.content, output_width=512, output_height=512)
    return Image.open(io.BytesIO(png_bytes)).convert("RGBA")


# ---------- Sombra exterior ----------
def drop_shadow(img: Image.Image, offset: Tuple[int, int], blur: int, shadow_color=(0, 0, 0, 180)):
    ox, oy = offset
    base = Image.new("RGBA", (img.width + abs(ox) + blur * 2, img.height + abs(oy) + blur * 2), (0, 0, 0, 0))
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    shadow.paste(shadow_color, (max(ox, 0) + blur, max(oy, 0) + blur),
                 img.split()[-1])  # usar alpha del original
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(shadow)
    base.alpha_composite(img, (blur + max(-ox, 0), blur + max(-oy, 0)))
    return base


# ---------- Sombra interior ----------
def inner_shadow(text_img: Image.Image, offset: Tuple[int, int], blur: int, shadow_color=(0, 0, 0, 120)):
    """
    text_img: imagen RGBA donde solo el texto tiene alpha>0
    Devuelve una nueva imagen RGBA con la sombra interior aplicada.
    """
    ox, oy = offset
    alpha = text_img.split()[-1]
    inv_alpha = Image.eval(alpha, lambda a: 255 - a)
    shadow = Image.new("L", text_img.size, 0)
    shadow.paste(255, (ox, oy), inv_alpha)
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    # recortar a solo donde hay texto
    shadow = Image.composite(shadow, Image.new("L", text_img.size, 0), alpha)
    rgba_shadow = Image.merge("RGBA", [Image.new("L", text_img.size, c) for c in shadow_color[:3]] + [shadow])
    out = text_img.copy()
    out.alpha_composite(rgba_shadow)
    return out


# ---------- Renderizar texto multilínea con ajuste automático ----------
def render_text_block(text: str, max_width_px: int, font_path: str, start_size=160) -> Tuple[Image.Image, int]:
    """
    Crea una imagen RGBA con el texto centrado línea por línea y retorna (img, font_size).
    Disminuye el tamaño hasta que el bloque quepa dentro de max_width_px.
    """
    size = start_size
    while size > 10:
        try:
            if font_path and os.path.exists(font_path):
                font = ImageFont.truetype(font_path, size)
            else:
                # Usar fuente por defecto si no se encuentra la especificada
                font = ImageFont.load_default()
        except (OSError, IOError):
            # Si falla, usar fuente por defecto
            font = ImageFont.load_default()
            
        # partimos el texto por palabras para que cada línea no supere max_width_px
        words = text.split()
        lines = []
        cur = []
        for w in words:
            test = " ".join(cur + [w])
            try:
                w_px = font.getlength(test)
            except AttributeError:
                # Para versiones antiguas de PIL
                w_px = font.getsize(test)[0]
            if w_px <= max_width_px:
                cur.append(w)
            else:
                lines.append(" ".join(cur))
                cur = [w]
        if cur:
            lines.append(" ".join(cur))

        try:
            widths = [font.getlength(l) for l in lines]
        except AttributeError:
            widths = [font.getsize(l)[0] for l in lines]
            
        height = int(size * TEXT_LINE_SPACING * len(lines))
        if max(widths) <= max_width_px:
            # render
            img = Image.new("RGBA", (max_width_px, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            y = 0
            for l in lines:
                try:
                    w = font.getlength(l)
                except AttributeError:
                    w = font.getsize(l)[0]
                draw.text(((max_width_px - w) / 2, y), l, font=font, fill=TEXT_COLOR)
                y += int(size * TEXT_LINE_SPACING)
            return img.crop(img.getbbox()), size
        size -= 4
    raise RuntimeError("No pude ajustar el texto, es demasiado largo.")



# ---------- Pipeline principal ----------
def build_thumbnail(
    background_path: str,
    text: str,
    icon_queries: List[str],
    out_png: str = "thumbnail.png",
    out_psd: str = "thumbnail.psd",
    icon_size: int = None,  # Nuevo parámetro para tamaño de iconos
):
    # Usar el tamaño de icono personalizado o el por defecto
    icon_max_width = icon_size if icon_size else ICON_MAX_WIDTH
    
    # 1) Fondo
    bg = Image.open(background_path).convert("RGBA")
    bg = bg.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
    bg_blur = bg.filter(ImageFilter.GaussianBlur(BG_BLUR_RADIUS))

    # 2) Texto
    text_img, font_size = render_text_block(text, int(CANVAS_W * TEXT_MAX_WIDTH), FONT_PATH)
    text_img = inner_shadow(text_img, TEXT_INNER_SHADOW_OFFSET, TEXT_INNER_SHADOW_BLUR)
    text_with_shadow = drop_shadow(text_img, TEXT_OUTER_SHADOW_OFFSET, TEXT_OUTER_SHADOW_BLUR)

    # 3) Iconos
    icons = []
    for q in icon_queries:
        icon = download_icon(q).convert("RGBA")
        # redimensionar manteniendo proporción
        scale = icon_max_width / icon.width
        icon = icon.resize((int(icon.width * scale), int(icon.height * scale)), Image.LANCZOS)
        icon = drop_shadow(icon, ICON_OUTER_SHADOW_OFFSET, ICON_OUTER_SHADOW_BLUR)
        icons.append(icon)

    # 4) Composición final
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    canvas.alpha_composite(bg_blur)

    # posicionar texto centrado arriba (ligera altura)
    text_x = (CANVAS_W - text_with_shadow.width) // 2
    text_y = (CANVAS_H - text_with_shadow.height) // 2 - 80
    canvas.alpha_composite(text_with_shadow, (text_x, text_y))

    # iconos debajo del texto
    total_icons_w = sum(i.width for i in icons) + ICON_GAP * (len(icons) - 1 if icons else 0)
    cur_x = (CANVAS_W - total_icons_w) // 2
    icons_y = text_y + text_with_shadow.height + 40
    for icon in icons:
        canvas.alpha_composite(icon, (cur_x, icons_y))
        cur_x += icon.width + ICON_GAP

    # 5) Guardar PNG/JPG
    canvas.convert("RGB").save(out_png, quality=95)

    # 6) Intentar guardar PSD (opcional)
    if out_psd and out_psd.endswith('.psd'):
        print("Nota: Generación de PSD deshabilitada temporalmente debido a problemas de compatibilidad.")
        print("Solo se genera el archivo PNG.")

    print(f"✅ Thumbnail generado: {out_png}")
    print(f"📐 Tamaño de iconos usado: {icon_max_width}px")
    if icons:
        print(f"🎨 Iconos incluidos: {', '.join(icon_queries)}")


# ----------- CLI -----------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generador de thumbnails estilo blog.")
    parser.add_argument("background", help="Ruta a la imagen de fondo")
    parser.add_argument("-t", "--text", required=True, help="Texto principal")
    parser.add_argument("-i", "--icon", action="append", default=[], help="Nombre(s) de iconos (simpleicons)")
    parser.add_argument("--out-png", default="thumbnail.png")
    parser.add_argument("--out-psd", default="thumbnail.psd")
    parser.add_argument("--icon-size", type=int, help=f"Tamaño máximo de iconos en píxeles (default: {ICON_MAX_WIDTH})")
    args = parser.parse_args()

    build_thumbnail(args.background, args.text, args.icon, args.out_png, args.out_psd, args.icon_size)
