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

# PSD con psd-tools (para creación de archivos con capas)
try:
    from psd_tools import PSDImage
    from psd_tools.api.layers import PixelLayer
    PSD_TOOLS_AVAILABLE = True
except ImportError:
    PSD_TOOLS_AVAILABLE = False

# PSD con pytoshop (fallback legacy)
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
def download_flaticon_icon(query: str) -> Image.Image:
    """
    Intenta descargar un icono desde Flaticon usando búsqueda libre
    Mejorado con más iconos y mejor lógica de búsqueda
    """
    print(f"🌐 Intentando buscar '{query}' en Flaticon...")
    
    try:
        # URLs de búsqueda en Flaticon (usando términos populares)
        search_terms = [
            query.lower().strip(),
            query.lower().replace(" ", ""),
            query.lower().replace("-", " "),
            query.lower().replace("_", " "),
            query.lower().replace(".", ""),
        ]
        
        # Iconos populares de tecnología como fallback
        tech_fallbacks = [
            "computer", "laptop", "code", "programming", "software", 
            "technology", "web", "internet", "digital", "app"
        ]
        
        # Base de datos ampliada de iconos gratuitos de Flaticon
        flaticon_free_icons = {
            # Tecnología general
            "code": "https://cdn-icons-png.flaticon.com/512/270/270798.png",
            "programming": "https://cdn-icons-png.flaticon.com/512/1005/1005141.png",
            "computer": "https://cdn-icons-png.flaticon.com/512/3474/3474360.png",
            "laptop": "https://cdn-icons-png.flaticon.com/512/3474/3474374.png",
            "web": "https://cdn-icons-png.flaticon.com/512/1828/1828833.png",
            "software": "https://cdn-icons-png.flaticon.com/512/2166/2166823.png",
            "app": "https://cdn-icons-png.flaticon.com/512/3474/3474359.png",
            "technology": "https://cdn-icons-png.flaticon.com/512/2166/2166823.png",
            "internet": "https://cdn-icons-png.flaticon.com/512/1828/1828833.png",
            "digital": "https://cdn-icons-png.flaticon.com/512/2166/2166823.png",
            "website": "https://cdn-icons-png.flaticon.com/512/1006/1006771.png",
            "monitor": "https://cdn-icons-png.flaticon.com/512/109/109612.png",
            "desktop": "https://cdn-icons-png.flaticon.com/512/109/109612.png",
            
            # Lenguajes de programación
            "javascript": "https://cdn-icons-png.flaticon.com/512/5968/5968292.png",
            "js": "https://cdn-icons-png.flaticon.com/512/5968/5968292.png",
            "python": "https://cdn-icons-png.flaticon.com/512/5968/5968350.png",
            "java": "https://cdn-icons-png.flaticon.com/512/226/226777.png",
            "html": "https://cdn-icons-png.flaticon.com/512/732/732212.png",
            "css": "https://cdn-icons-png.flaticon.com/512/732/732190.png",
            "php": "https://cdn-icons-png.flaticon.com/512/919/919830.png",
            "cpp": "https://cdn-icons-png.flaticon.com/512/6132/6132222.png",
            "csharp": "https://cdn-icons-png.flaticon.com/512/6132/6132221.png",
            "ruby": "https://cdn-icons-png.flaticon.com/512/919/919842.png",
            "golang": "https://cdn-icons-png.flaticon.com/512/919/919831.png",
            "go": "https://cdn-icons-png.flaticon.com/512/919/919831.png",
            "rust": "https://cdn-icons-png.flaticon.com/512/5968/5968380.png",
            
            # Frameworks y librerías
            "react": "https://cdn-icons-png.flaticon.com/512/1126/1126012.png",
            "reactjs": "https://cdn-icons-png.flaticon.com/512/1126/1126012.png",
            "vue": "https://cdn-icons-png.flaticon.com/512/1005/1005141.png",
            "vuejs": "https://cdn-icons-png.flaticon.com/512/1005/1005141.png",
            "angular": "https://cdn-icons-png.flaticon.com/512/5968/5968267.png",
            "node": "https://cdn-icons-png.flaticon.com/512/919/919825.png",
            "nodejs": "https://cdn-icons-png.flaticon.com/512/919/919825.png",
            "express": "https://cdn-icons-png.flaticon.com/512/919/919825.png",
            "django": "https://cdn-icons-png.flaticon.com/512/5968/5968350.png",
            "flask": "https://cdn-icons-png.flaticon.com/512/5968/5968350.png",
            "nextjs": "https://cdn-icons-png.flaticon.com/512/1126/1126012.png",
            "next": "https://cdn-icons-png.flaticon.com/512/1126/1126012.png",
            "svelte": "https://cdn-icons-png.flaticon.com/512/1005/1005141.png",
            
            # Base de datos
            "database": "https://cdn-icons-png.flaticon.com/512/1231/1231179.png",
            "db": "https://cdn-icons-png.flaticon.com/512/1231/1231179.png",
            "mysql": "https://cdn-icons-png.flaticon.com/512/1231/1231179.png",
            "postgresql": "https://cdn-icons-png.flaticon.com/512/1231/1231179.png",
            "postgres": "https://cdn-icons-png.flaticon.com/512/1231/1231179.png",
            "mongodb": "https://cdn-icons-png.flaticon.com/512/919/919836.png",
            "mongo": "https://cdn-icons-png.flaticon.com/512/919/919836.png",
            "redis": "https://cdn-icons-png.flaticon.com/512/1231/1231179.png",
            "sqlite": "https://cdn-icons-png.flaticon.com/512/1231/1231179.png",
            
            # DevOps y herramientas
            "server": "https://cdn-icons-png.flaticon.com/512/2906/2906274.png",
            "cloud": "https://cdn-icons-png.flaticon.com/512/1570/1570121.png",
            "api": "https://cdn-icons-png.flaticon.com/512/2164/2164832.png",
            "docker": "https://cdn-icons-png.flaticon.com/512/919/919853.png",
            "kubernetes": "https://cdn-icons-png.flaticon.com/512/2164/2164832.png",
            "aws": "https://cdn-icons-png.flaticon.com/512/1570/1570121.png",
            "azure": "https://cdn-icons-png.flaticon.com/512/1570/1570121.png",
            "gcp": "https://cdn-icons-png.flaticon.com/512/1570/1570121.png",
            "firebase": "https://cdn-icons-png.flaticon.com/512/919/919852.png",
            "git": "https://cdn-icons-png.flaticon.com/512/270/270798.png",
            "github": "https://cdn-icons-png.flaticon.com/512/733/733553.png",
            "gitlab": "https://cdn-icons-png.flaticon.com/512/270/270798.png",
            "bitbucket": "https://cdn-icons-png.flaticon.com/512/270/270798.png",
            "jenkins": "https://cdn-icons-png.flaticon.com/512/2164/2164832.png",
            "ci": "https://cdn-icons-png.flaticon.com/512/2164/2164832.png",
            "cd": "https://cdn-icons-png.flaticon.com/512/2164/2164832.png",
            
            # Móvil y SO
            "mobile": "https://cdn-icons-png.flaticon.com/512/619/619153.png",
            "android": "https://cdn-icons-png.flaticon.com/512/270/270780.png",
            "ios": "https://cdn-icons-png.flaticon.com/512/731/731985.png",
            "windows": "https://cdn-icons-png.flaticon.com/512/732/732221.png",
            "linux": "https://cdn-icons-png.flaticon.com/512/226/226772.png",
            "macos": "https://cdn-icons-png.flaticon.com/512/731/731985.png",
            "ubuntu": "https://cdn-icons-png.flaticon.com/512/226/226772.png",
            
            # Herramientas y editores
            "vscode": "https://cdn-icons-png.flaticon.com/512/906/906324.png",
            "vim": "https://cdn-icons-png.flaticon.com/512/906/906324.png",
            "emacs": "https://cdn-icons-png.flaticon.com/512/906/906324.png",
            "editor": "https://cdn-icons-png.flaticon.com/512/906/906324.png",
            "ide": "https://cdn-icons-png.flaticon.com/512/906/906324.png",
            "terminal": "https://cdn-icons-png.flaticon.com/512/2541/2541988.png",
            "console": "https://cdn-icons-png.flaticon.com/512/2541/2541988.png",
            "bash": "https://cdn-icons-png.flaticon.com/512/2541/2541988.png",
            "shell": "https://cdn-icons-png.flaticon.com/512/2541/2541988.png",
            
            # Desarrollo web
            "frontend": "https://cdn-icons-png.flaticon.com/512/1006/1006771.png",
            "backend": "https://cdn-icons-png.flaticon.com/512/2906/2906274.png",
            "fullstack": "https://cdn-icons-png.flaticon.com/512/1006/1006771.png",
            "ui": "https://cdn-icons-png.flaticon.com/512/1006/1006771.png",
            "ux": "https://cdn-icons-png.flaticon.com/512/1006/1006771.png",
            "design": "https://cdn-icons-png.flaticon.com/512/1006/1006771.png",
            "responsive": "https://cdn-icons-png.flaticon.com/512/619/619153.png",
            
            # AI y Machine Learning
            "ai": "https://cdn-icons-png.flaticon.com/512/8637/8637099.png",
            "ml": "https://cdn-icons-png.flaticon.com/512/8637/8637099.png",
            "machinelearning": "https://cdn-icons-png.flaticon.com/512/8637/8637099.png",
            "deeplearning": "https://cdn-icons-png.flaticon.com/512/8637/8637099.png",
            "tensorflow": "https://cdn-icons-png.flaticon.com/512/8637/8637099.png",
            "pytorch": "https://cdn-icons-png.flaticon.com/512/8637/8637099.png",
            "neural": "https://cdn-icons-png.flaticon.com/512/8637/8637099.png",
            "robot": "https://cdn-icons-png.flaticon.com/512/8637/8637099.png",
            
            # Otros conceptos
            "security": "https://cdn-icons-png.flaticon.com/512/2913/2913145.png",
            "encryption": "https://cdn-icons-png.flaticon.com/512/2913/2913145.png",
            "blockchain": "https://cdn-icons-png.flaticon.com/512/2913/2913145.png",
            "crypto": "https://cdn-icons-png.flaticon.com/512/2913/2913145.png",
            "network": "https://cdn-icons-png.flaticon.com/512/1570/1570121.png",
            "testing": "https://cdn-icons-png.flaticon.com/512/2164/2164832.png",
            "bug": "https://cdn-icons-png.flaticon.com/512/1006/1006555.png",
            "optimization": "https://cdn-icons-png.flaticon.com/512/2906/2906274.png",
            "performance": "https://cdn-icons-png.flaticon.com/512/2906/2906274.png",
        }
        
        # Intentar con los términos de búsqueda
        for term in search_terms + tech_fallbacks:
            try:
                # Buscar coincidencia exacta primero
                if term in flaticon_free_icons:
                    icon_url = flaticon_free_icons[term]
                    print(f"  🎯 Coincidencia exacta encontrada: {term}")
                else:
                    # Buscar coincidencia parcial
                    icon_url = None
                    for key, url in flaticon_free_icons.items():
                        if key in term.lower() or term.lower() in key:
                            icon_url = url
                            print(f"  🎯 Coincidencia parcial encontrada: {key} para {term}")
                            break
                
                if icon_url:
                    print(f"  � Descargando desde Flaticon: {icon_url}")
                    response = requests.get(icon_url, timeout=10, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    if response.status_code == 200:
                        img = Image.open(io.BytesIO(response.content))
                        # Convertir a RGBA y redimensionar
                        img = img.convert("RGBA")
                        img = img.resize((512, 512), Image.Resampling.LANCZOS)
                        print(f"  ✅ Icono descargado exitosamente desde Flaticon")
                        return img
                    else:
                        print(f"  ❌ Error HTTP {response.status_code} al descargar de Flaticon")
                        
            except Exception as e:
                print(f"  ❌ Error buscando '{term}' en Flaticon: {str(e)[:50]}...")
                continue
        
        # Si no se encontró nada específico, usar un icono por defecto
        if flaticon_free_icons:
            default_url = flaticon_free_icons["code"]  # Icono de código como fallback
            print(f"  🔄 Usando icono por defecto de Flaticon...")
            try:
                response = requests.get(default_url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                if response.status_code == 200:
                    img = Image.open(io.BytesIO(response.content))
                    img = img.convert("RGBA")
                    img = img.resize((512, 512), Image.Resampling.LANCZOS)
                    print(f"  ✅ Icono por defecto descargado desde Flaticon")
                    return img
            except Exception as e:
                print(f"  ❌ Error descargando icono por defecto: {str(e)[:50]}...")
                
    except Exception as e:
        print(f"  ❌ Error general en Flaticon: {str(e)[:50]}...")
    
    return None


def download_icon(query: str) -> Image.Image:
    """
    Descarga un icono usando múltiples fuentes con sistema robusto de fallbacks:
    1. SimpleIcons (con variaciones)
    2. Flaticon (si SimpleIcons falla)
    3. Icono genérico (último recurso)
    """
    import cairosvg
    
    print(f"\n🔍 === BÚSQUEDA DE ICONO PARA: '{query}' ===")
    
    # Lista de variaciones para intentar
    variations = [
        query.lower().replace(" ", ""),
        query.lower().replace(" ", "").replace("-", ""),
        query.lower().replace(" ", "").replace(".", ""),
        query.lower().replace("_", ""),
        f"{query.lower()}dotcom",
        f"{query.lower()}js" if not query.lower().endswith("js") else query.lower()[:-2],
        # Agregar más variaciones comunes
        query.lower().replace("js", "javascript"),
        query.lower().replace("py", "python"),
        query.lower().replace("cpp", "cplusplus"),
        query.lower().replace("cs", "csharp"),
    ]
    
    # Iconos de fallback populares en SimpleIcons
    fallback_icons = [
        "code", "terminal", "gear", "star", "circle", "square", 
        "triangle", "heart", "home", "user", "settings", "tool",
        "javascript", "python", "react", "nodejs"
    ]
    
    # 1. FASE 1: SIMPLEICONS - Variaciones del query original
    print(f"📍 FASE 1: Probando SimpleIcons con variaciones...")
    for i, variation in enumerate(variations):
        try:
            url = f"https://cdn.simpleicons.org/{variation}/ffffff"
            print(f"  🔍 SimpleIcons intento {i+1}/{len(variations)}: '{variation}'")
            r = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            if r.status_code == 200:
                try:
                    png_bytes = cairosvg.svg2png(bytestring=r.content, output_width=512, output_height=512)
                    img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
                    print(f"  ✅ ¡ÉXITO! Encontrado en SimpleIcons: '{variation}'")
                    return img
                except Exception as convert_error:
                    print(f"  ⚠️  SVG encontrado pero error al convertir: {str(convert_error)[:50]}...")
                    continue
            else:
                print(f"  ❌ No encontrado (HTTP {r.status_code})")
        except Exception as e:
            print(f"  ❌ Error de conexión: {str(e)[:50]}...")
            continue
    
    # 2. FASE 2: SIMPLEICONS - Iconos de fallback
    print(f"\n📍 FASE 2: Probando SimpleIcons con iconos de fallback...")
    for i, fallback in enumerate(fallback_icons):
        try:
            url = f"https://cdn.simpleicons.org/{fallback}/ffffff"
            print(f"  🔍 SimpleIcons fallback {i+1}/{len(fallback_icons)}: '{fallback}'")
            r = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            if r.status_code == 200:
                try:
                    png_bytes = cairosvg.svg2png(bytestring=r.content, output_width=512, output_height=512)
                    img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
                    print(f"  ✅ Usando fallback de SimpleIcons: '{fallback}'")
                    return img
                except Exception as convert_error:
                    print(f"  ⚠️  SVG encontrado pero error al convertir: {str(convert_error)[:50]}...")
                    continue
            else:
                print(f"  ❌ Fallback no disponible (HTTP {r.status_code})")
        except Exception as e:
            print(f"  ❌ Error de conexión: {str(e)[:50]}...")
            continue
    
    # 3. FASE 3: FLATICON
    print(f"\n📍 FASE 3: Intentando con Flaticon...")
    flaticon_result = download_flaticon_icon(query)
    if flaticon_result:
        print(f"  ✅ ¡ÉXITO! Icono obtenido desde Flaticon")
        return flaticon_result
    else:
        print(f"  ❌ Flaticon también falló")
    
    # 4. FASE 4: ÚLTIMO RECURSO - Crear un icono genérico
    print(f"\n� FASE 4: Creando icono genérico...")
    print(f"⚠️  Todas las fuentes online fallaron para '{query}'")
    print(f"🔧 Generando icono genérico con las iniciales...")
    generic_icon = create_generic_icon(query)
    print(f"  ✅ Icono genérico creado exitosamente")
    return generic_icon

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
    bg_blur_radius = config['background']['blur_radius']
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
    bg_blur = bg.filter(ImageFilter.GaussianBlur(bg_blur_radius))

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

    # 6) Intentar guardar PSD con capas separadas (opcional)
    if config['output']['create_psd'] and out_psd and out_psd.endswith('.psd'):
        print(f"🎨 Creando PSD con capas separadas...")
        
        # Intentar primero con psd-tools (más fácil)
        if PSD_TOOLS_AVAILABLE:
            try:
                print(f"   📦 Usando psd-tools...")
                
                # Crear PSD nuevo
                psd = PSDImage.new("RGB", (canvas_w, canvas_h), color=(0, 0, 0))
                
                # Función auxiliar para crear capa con psd-tools
                def create_psd_layer(pil_image, layer_name):
                    layer = PixelLayer.frompil(pil_image, psd)
                    layer.name = layer_name
                    return layer
                
                # Lista para almacenar capas
                layers_to_add = []
                
                # CAPA 1: Fondo con desenfoque
                print(f"   • Creando capa de fondo...")
                bg_layer = create_psd_layer(bg_blur, "Background_Blur")
                layers_to_add.append(bg_layer)
                
                # CAPA 2: Texto principal con sombras
                print(f"   • Creando capa de texto...")
                text_canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
                text_canvas.alpha_composite(text_with_shadow, (text_x, text_y))
                text_layer = create_psd_layer(text_canvas, "Text_Main")
                layers_to_add.append(text_layer)
                
                # CAPAS 3+: Iconos individuales
                for i, icon in enumerate(icons, 1):
                    print(f"   • Creando capa de icono {i}...")
                    # Calcular posición individual de cada icono
                    individual_x = (canvas_w - total_icons_w) // 2
                    for j in range(i - 1):
                        individual_x += icons[j].width + icon_gap
                    
                    # Crear canvas individual para este icono
                    icon_canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
                    icon_canvas.alpha_composite(icon, (individual_x, icons_y))
                    
                    # Nombre descriptivo basado en la query del icono
                    icon_name = f"Icon_{i}_{icon_queries[i-1] if i-1 < len(icon_queries) else 'unknown'}"
                    icon_layer = create_psd_layer(icon_canvas, icon_name)
                    layers_to_add.append(icon_layer)
                
                # Agregar todas las capas al PSD
                print(f"   • Agregando {len(layers_to_add)} capas al PSD...")
                for layer in layers_to_add:
                    psd.append(layer)
                
                # Guardar PSD
                print(f"   • Guardando archivo PSD...")
                psd.save(out_psd_path)
                
                print(f"✅ PSD creado con {len(layers_to_add)} capas usando psd-tools: {out_psd_path}")
                print(f"📋 Capas incluidas:")
                print(f"   • Background_Blur (fondo con desenfoque)")
                print(f"   • Text_Main (texto principal con sombras)")
                for i, query in enumerate(icon_queries, 1):
                    print(f"   • Icon_{i}_{query} (icono individual)")
                    
            except Exception as e:
                print(f"❌ Error creando PSD con psd-tools: {e}")
                import traceback
                traceback.print_exc()
                
                # Fallback a pytoshop si psd-tools falla
                if PSD_AVAILABLE:
                    print(f"💡 Intentando con pytoshop como fallback...")
                    print(f"⚠️  pytoshop tiene limitaciones, se recomienda instalar psd-tools")
                else:
                    print(f"⚠️  Pytoshop no disponible como fallback")
                    
        # Si psd-tools no está disponible, mostrar advertencia
        elif PSD_AVAILABLE:
            print(f"⚠️  Solo pytoshop disponible - funcionalidad limitada")
            print(f"💡 Para mejor compatibilidad, instala: pip install psd-tools")
        else:
            print("⚠️  Ni psd-tools ni pytoshop están disponibles para crear PSD.")
            print("💡 Para habilitar creación de PSD, instala:")
            print("   pip install psd-tools  # Recomendado")
            print("   pip install pytoshop   # Alternativa")
            print("   pip install pytoshop")

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
