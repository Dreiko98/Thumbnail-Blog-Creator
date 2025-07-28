#!/usr/bin/env python3
import io
import math
import os
import textwrap
from pathlib import Path
from typing import List, Tuple, Dict, Any
import platform
import yaml
from datetime import datetime

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# PSD (opcional)
try:
    from pytoshop.user import nested_layers as nl
    PSD_AVAILABLE = True
except ImportError:
    PSD_AVAILABLE = False


# -------------------- CONFIGURACIÓN --------------------
def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Carga la configuración desde el archivo YAML"""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Archivo de configuración no encontrado: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_output_directory() -> Path:
    """Crea y retorna el directorio de salida basado en la fecha actual"""
    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = Path("assets") / today
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

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

# ------------------------------------------------


# ---------- Utilidades de iconos ----------
def download_icon(query: str) -> Image.Image:
    """
    Descarga un icono PNG transparente usando simpleicons + cairosvg.
    Sistema robusto con múltiples intentos y fallbacks.
    query: 'windows', 'ubuntu', 'photoshop', etc.
    """
    import cairosvg
    
    # Lista de variaciones para intentar
    variations = [
        query.lower().replace(" ", ""),
        query.lower().replace(" ", "").replace("-", ""),
        query.lower().replace(" ", "").replace(".", ""),
        f"{query.lower()}dotcom",
        f"{query.lower()}js" if not query.lower().endswith("js") else query.lower()[:-2],
    ]
    
    # Iconos de fallback populares
    fallback_icons = [
        "code", "terminal", "gear", "star", "circle", "square", 
        "triangle", "heart", "home", "user", "settings", "tool"
    ]
    
    print(f"🔍 Buscando icono para: '{query}'")
    
    # Intentar con las variaciones del query original
    for i, variation in enumerate(variations):
        try:
            url = f"https://cdn.simpleicons.org/{variation}/ffffff"
            print(f"  Intento {i+1}: {variation}")
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                png_bytes = cairosvg.svg2png(bytestring=r.content, output_width=512, output_height=512)
                print(f"  ✅ Encontrado: {variation}")
                return Image.open(io.BytesIO(png_bytes)).convert("RGBA")
        except Exception as e:
            print(f"  ❌ Error con {variation}: {str(e)[:50]}...")
            continue
    
    # Si no funciona ninguna variación, intentar con iconos de fallback
    print(f"⚠️  No se encontró '{query}', probando iconos de fallback...")
    for fallback in fallback_icons:
        try:
            url = f"https://cdn.simpleicons.org/{fallback}/ffffff"
            print(f"  Fallback: {fallback}")
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                png_bytes = cairosvg.svg2png(bytestring=r.content, output_width=512, output_height=512)
                print(f"  ✅ Usando fallback: {fallback}")
                return Image.open(io.BytesIO(png_bytes)).convert("RGBA")
        except Exception:
            continue
    
    # Último recurso: crear un icono genérico
    print(f"🔧 Creando icono genérico para '{query}'")
    return create_generic_icon(query)

def create_generic_icon(text: str) -> Image.Image:
    """
    Crea un icono genérico con las iniciales del texto
    """
    # Crear imagen base
    size = 512
    img = Image.new("RGBA", (size, size), (100, 100, 100, 255))
    draw = ImageDraw.Draw(img)
    
    # Crear círculo de fondo
    margin = 50
    draw.ellipse([margin, margin, size-margin, size-margin], fill=(150, 150, 150, 255))
    
    # Obtener iniciales (máximo 2 caracteres)
    initials = "".join([word[0].upper() for word in text.split() if word])[:2]
    if not initials:
        initials = "?"
    
    # Intentar cargar fuente o usar la por defecto
    try:
        font_path = get_font_path()
        if font_path:
            font = ImageFont.truetype(font_path, size=200)
        else:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    # Calcular posición centrada para el texto
    try:
        bbox = draw.textbbox((0, 0), initials, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except:
        text_width = len(initials) * 100
        text_height = 120
    
    text_x = (size - text_width) // 2
    text_y = (size - text_height) // 2
    
    # Dibujar texto
    draw.text((text_x, text_y), initials, fill=(255, 255, 255, 255), font=font)
    
    return img


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
def render_text_block(text: str, max_width_px: int, font_path: str, config: Dict[str, Any]) -> Tuple[Image.Image, int]:
    """
    Crea una imagen RGBA con el texto centrado línea por línea y retorna (img, font_size).
    Disminuye el tamaño hasta que el bloque quepa dentro de max_width_px.
    """
    text_config = config['text']
    start_size = text_config['start_size']
    line_spacing = text_config['line_spacing']
    text_color = tuple(text_config['color'])
    
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
            
        height = int(size * line_spacing * len(lines))
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
                draw.text(((max_width_px - w) / 2, y), l, font=font, fill=text_color)
                y += int(size * line_spacing)
            return img.crop(img.getbbox()), size
        size -= 4
    raise RuntimeError("No pude ajustar el texto, es demasiado largo.")



# ---------- Sistema de entrada interactiva ----------
def interactive_input() -> dict:
    """
    Sistema interactivo para recopilar información del usuario
    """
    print("\n" + "="*60)
    print("🎨 GENERADOR DE THUMBNAILS INTERACTIVO")
    print("="*60)
    
    # 1. Imagen de fondo
    print("\n📸 IMAGEN DE FONDO")
    print("-" * 20)
    while True:
        background_path = input("Introduce la ruta de la imagen de fondo: ").strip()
        if background_path and os.path.exists(background_path):
            break
        elif background_path and not os.path.exists(background_path):
            print(f"❌ No se encontró el archivo: {background_path}")
            print("   Asegúrate de que la ruta sea correcta.")
        else:
            print("❌ Por favor, introduce una ruta válida.")
    
    # 2. Texto principal
    print("\n✏️  TEXTO PRINCIPAL")
    print("-" * 20)
    print("💡 Tip: Puedes usar \\n para crear saltos de línea")
    while True:
        text = input("Introduce el texto principal: ").strip()
        if text:
            # Reemplazar \n literales por saltos de línea reales
            text = text.replace("\\n", "\n")
            break
        else:
            print("❌ El texto no puede estar vacío.")
    
    # 3. Iconos
    print("\n🎯 ICONOS")
    print("-" * 20)
    print("💡 Puedes usar nombres de SimpleIcons como: python, javascript, react, etc.")
    print("💡 Presiona Enter sin escribir nada para finalizar la lista")
    
    icons = []
    icon_count = 1
    while True:
        icon_name = input(f"Icono #{icon_count} (Enter para terminar): ").strip()
        if not icon_name:
            break
        icons.append(icon_name)
        print(f"   ✅ Agregado: {icon_name}")
        icon_count += 1
    
    if not icons:
        print("ℹ️  No se agregaron iconos. Se generará solo con texto.")
    
    # 4. Tamaño de iconos
    print("\n📐 CONFIGURACIÓN DE ICONOS")
    print("-" * 20)
    try:
        config = load_config("config.yaml")
        default_size = config['icons']['max_width']
    except:
        default_size = 200
    
    while True:
        size_input = input(f"Tamaño máximo de iconos en píxeles (default: {default_size}): ").strip()
        if not size_input:
            icon_size = default_size
            break
        try:
            icon_size = int(size_input)
            if icon_size < 50:
                print("❌ El tamaño mínimo es 50px")
                continue
            elif icon_size > 800:
                print("❌ El tamaño máximo es 800px")
                continue
            break
        except ValueError:
            print("❌ Por favor, introduce un número válido.")
    
    # 5. Nombres de archivos de salida
    print("\n💾 ARCHIVOS DE SALIDA")
    print("-" * 20)
    
    # Generar nombres por defecto basados en el texto
    safe_text = "".join(c for c in text.replace("\n", "_").replace(" ", "_") if c.isalnum() or c in "_-")[:20]
    default_png = f"{safe_text}_thumbnail.png"
    default_psd = f"{safe_text}_thumbnail.psd"
    
    png_name = input(f"Nombre del archivo PNG (default: {default_png}): ").strip()
    if not png_name:
        png_name = default_png
    
    psd_name = input(f"Nombre del archivo PSD (default: {default_psd}): ").strip()
    if not psd_name:
        psd_name = default_psd
    
    # 6. Resumen
    print("\n📋 RESUMEN DE LA CONFIGURACIÓN")
    print("=" * 40)
    print(f"📸 Imagen de fondo: {background_path}")
    print(f"✏️  Texto: {repr(text)}")
    print(f"🎯 Iconos: {', '.join(icons) if icons else 'Ninguno'}")
    print(f"📐 Tamaño de iconos: {icon_size}px")
    print(f"💾 Archivo PNG: {png_name}")
    print(f"💾 Archivo PSD: {psd_name}")
    
    # Confirmación
    print("\n🤔 ¿Proceder con la generación?")
    while True:
        confirm = input("Confirmar (s/n): ").strip().lower()
        if confirm in ['s', 'si', 'sí', 'y', 'yes']:
            break
        elif confirm in ['n', 'no']:
            print("❌ Operación cancelada.")
            exit(0)
        else:
            print("❌ Por favor, responde 's' para sí o 'n' para no.")
    
    return {
        'background_path': background_path,
        'text': text,
        'icons': icons,
        'icon_size': icon_size,
        'png_name': png_name,
        'psd_name': psd_name
    }
def build_thumbnail(
    background_path: str,
    text: str,
    icon_queries: List[str],
    out_png: str = "thumbnail.png",
    out_psd: str = "thumbnail.psd",
    icon_size: int = None,  # Nuevo parámetro para tamaño de iconos
    config_path: str = "config.yaml"
):
    # Cargar configuración
    config = load_config(config_path)
    font_path = get_font_path()
    
    # Extraer configuraciones
    canvas_w = config['canvas']['width']
    canvas_h = config['canvas']['height']
    bg_blur = config['background']['blur_radius']
    text_max_width = config['text']['max_width']
    text_offset_y = config['layout']['text_offset_y']
    icons_offset_y = config['layout']['icons_offset_y']
    
    icon_max_width = icon_size if icon_size else config['icons']['max_width']
    icon_gap = config['icons']['gap']
    
    # Configurar directorios de salida
    output_dir = get_output_directory()
    out_png_path = output_dir / out_png
    out_psd_path = output_dir / out_psd
    
    # 1) Fondo
    bg = Image.open(background_path).convert("RGBA")
    bg = bg.resize((canvas_w, canvas_h), Image.LANCZOS)
    bg_blur = bg.filter(ImageFilter.GaussianBlur(bg_blur))

    # 2) Texto
    text_img, font_size = render_text_block(text, int(canvas_w * text_max_width), font_path, config)
    
    # Aplicar sombras al texto
    text_inner_offset = tuple(config['text']['inner_shadow']['offset'])
    text_inner_blur = config['text']['inner_shadow']['blur']
    text_inner_color = tuple(config['text']['inner_shadow']['color'])
    text_img = inner_shadow(text_img, text_inner_offset, text_inner_blur, text_inner_color)
    
    text_outer_offset = tuple(config['text']['outer_shadow']['offset'])
    text_outer_blur = config['text']['outer_shadow']['blur']
    text_outer_color = tuple(config['text']['outer_shadow']['color'])
    text_with_shadow = drop_shadow(text_img, text_outer_offset, text_outer_blur, text_outer_color)

    # 3) Iconos
    icons = []
    icon_shadow_offset = tuple(config['icons']['outer_shadow']['offset'])
    icon_shadow_blur = config['icons']['outer_shadow']['blur']
    icon_shadow_color = tuple(config['icons']['outer_shadow']['color'])
    
    for q in icon_queries:
        icon = download_icon(q).convert("RGBA")
        # redimensionar manteniendo proporción
        scale = icon_max_width / icon.width
        icon = icon.resize((int(icon.width * scale), int(icon.height * scale)), Image.LANCZOS)
        icon = drop_shadow(icon, icon_shadow_offset, icon_shadow_blur, icon_shadow_color)
        icons.append(icon)

    # 4) Composición final
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    canvas.alpha_composite(bg_blur)

    # posicionar texto centrado con offset configurado
    text_x = (canvas_w - text_with_shadow.width) // 2
    text_y = (canvas_h - text_with_shadow.height) // 2 + text_offset_y
    canvas.alpha_composite(text_with_shadow, (text_x, text_y))

    # iconos debajo del texto
    total_icons_w = sum(i.width for i in icons) + icon_gap * (len(icons) - 1 if icons else 0)
    cur_x = (canvas_w - total_icons_w) // 2
    icons_y = text_y + text_with_shadow.height + icons_offset_y
    for icon in icons:
        canvas.alpha_composite(icon, (cur_x, icons_y))
        cur_x += icon.width + icon_gap

    # 5) Guardar PNG/JPG
    png_quality = config['output']['png_quality']
    canvas.convert("RGB").save(out_png_path, quality=png_quality)

    # 6) Intentar guardar PSD (opcional)
    if config['output']['create_psd'] and out_psd and out_psd.endswith('.psd') and PSD_AVAILABLE:
        try:
            # PSD simplificado - solo la imagen final como una capa
            nl_layer = nl.Image(name="Thumbnail_Complete", image=canvas)
            root = nl.Group("root", [nl_layer])
            with open(out_psd_path, "wb") as f:
                nl.export(root, f)
            print(f"📄 PSD creado: {out_psd_path}")
        except Exception as e:
            print(f"⚠️  Error creando PSD: {e}")
    elif config['output']['create_psd'] and not PSD_AVAILABLE:
        print("⚠️  PSD solicitado pero pytoshop no está disponible.")

    print(f"✅ Thumbnail generado: {out_png_path}")
    print(f"📐 Tamaño de iconos usado: {icon_max_width}px")
    print(f"📁 Directorio de salida: {output_dir}")
    if icons:
        print(f"🎨 Iconos incluidos: {', '.join(icon_queries)}")


# ----------- CLI -----------
if __name__ == "__main__":
    import argparse
    
    # Cargar configuración para obtener valores por defecto
    try:
        config = load_config("config.yaml")
        default_icon_size = config['icons']['max_width']
    except:
        default_icon_size = 200
    
    parser = argparse.ArgumentParser(
        description="Generador de thumbnails estilo blog.",
        epilog="💡 Tip: Ejecuta sin argumentos para el modo interactivo"
    )
    parser.add_argument("background", nargs='?', help="Ruta a la imagen de fondo")
    parser.add_argument("-t", "--text", help="Texto principal")
    parser.add_argument("-i", "--icon", action="append", default=[], help="Nombre(s) de iconos (simpleicons)")
    parser.add_argument("--out-png", default="thumbnail.png", help="Nombre del archivo PNG de salida")
    parser.add_argument("--out-psd", default="thumbnail.psd", help="Nombre del archivo PSD de salida")
    parser.add_argument("--icon-size", type=int, help=f"Tamaño máximo de iconos en píxeles (default: {default_icon_size})")
    parser.add_argument("--config", default="config.yaml", help="Ruta al archivo de configuración YAML")
    parser.add_argument("--interactive", "-I", action="store_true", help="Forzar modo interactivo")
    args = parser.parse_args()

    # Determinar si usar modo interactivo
    use_interactive = args.interactive or (not args.background or not args.text)
    
    if use_interactive:
        print("🔄 Iniciando modo interactivo...")
        params = interactive_input()
        build_thumbnail(
            background_path=params['background_path'],
            text=params['text'],
            icon_queries=params['icons'],
            out_png=params['png_name'],
            out_psd=params['psd_name'],
            icon_size=params['icon_size'],
            config_path=args.config
        )
    else:
        # Modo tradicional (CLI con argumentos)
        build_thumbnail(
            background_path=args.background,
            text=args.text,
            icon_queries=args.icon,
            out_png=args.out_png,
            out_psd=args.out_psd,
            icon_size=args.icon_size,
            config_path=args.config
        )
