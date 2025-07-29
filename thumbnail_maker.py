#!/usr/bin/env python3
"""
Generador Avanzado de Thumbnails para Blog
==========================================

Este script genera thumbnails profesionales para publicaciones de blog con:
- Sistema robusto de búsqueda de iconos (Google Images, SimpleIcons, Flaticon)
- Configuración flexible via YAML
- Entrada interactiva por terminal
- Generación de archivos PNG y PSD con capas separadas
- Verificación automática de extensiones de archivo

Uso:
    python thumbnail_maker.py

Autor: GitHub Copilot Assistant
Versión: 3.0 - Con verificación automática de extensiones
"""

import os
import sys
import re
import io
import urllib.parse
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

# Verificar dependencias críticas
try:
    import yaml
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    print(f"❌ Error: Dependencia faltante - {e}")
    print("💡 Ejecuta: pip install -r requirements.txt")
    sys.exit(1)

# Dependencias opcionales
try:
    import cairosvg
    HAS_CAIROSVG = True
except ImportError:
    HAS_CAIROSVG = False
    print("⚠️  cairosvg no disponible - los iconos SVG no se podrán convertir")

try:
    from psd_tools import PSDImage
    from psd_tools.api.layers import PixelLayer
    HAS_PSD_TOOLS = True
except ImportError:
    HAS_PSD_TOOLS = False
    print("⚠️  psd-tools no disponible - no se podrán crear archivos PSD")


class FileExtensionValidator:
    """Clase para validar y corregir extensiones de archivo automáticamente"""
    
    VALID_EXTENSIONS = {
        'png': ['.png', '.jpg', '.jpeg'],  # PNG acepta estas extensiones como válidas
        'psd': ['.psd']
    }
    
    CONFLICTING_EXTENSIONS = [
        '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp',  # Extensiones de imagen
        '.txt', '.doc', '.pdf', '.svg'  # Otras extensiones comunes
    ]
    
    @staticmethod
    def validate_and_fix_extension(filename: str, output_format: str) -> str:
        """
        Valida y corrige la extensión del archivo de salida
        
        Args:
            filename: Nombre del archivo ingresado por el usuario
            output_format: Formato deseado ('png' o 'psd')
            
        Returns:
            Nombre del archivo con la extensión correcta
            
        Ejemplos:
            validate_and_fix_extension("thumbnail", "png") → "thumbnail.png"
            validate_and_fix_extension("imagen.jpg", "png") → "imagen.png"
            validate_and_fix_extension("archivo.txt", "psd") → "archivo.psd"
            validate_and_fix_extension("correcto.png", "png") → "correcto.png"
        """
        if not filename:
            return f"thumbnail.{output_format}"
            
        # Convertir a Path para facilitar el manejo
        file_path = Path(filename)
        name_without_ext = file_path.stem
        current_ext = file_path.suffix.lower()
        
        # Obtener extensiones válidas para el formato solicitado
        valid_exts = FileExtensionValidator.VALID_EXTENSIONS.get(output_format, [])
        target_ext = f".{output_format}"
        
        # Caso 1: Ya tiene la extensión correcta
        if current_ext == target_ext:
            print(f"✅ Extensión correcta: '{filename}'")
            return filename
            
        # Caso 2: Tiene una extensión válida pero no la exacta (ej: .jpg para PNG)
        if output_format == 'png' and current_ext in ['.jpg', '.jpeg']:
            corrected_filename = f"{name_without_ext}{target_ext}"
            print(f"🔧 Extensión corregida de imagen: '{filename}' → '{corrected_filename}'")
            return corrected_filename
            
        # Caso 3: Tiene una extensión incorrecta
        if current_ext and current_ext in FileExtensionValidator.CONFLICTING_EXTENSIONS:
            corrected_filename = f"{name_without_ext}{target_ext}"
            print(f"🔧 Extensión incorrecta reemplazada: '{filename}' → '{corrected_filename}'")
            return corrected_filename
            
        # Caso 4: Tiene alguna extensión pero no reconocida
        if current_ext and current_ext not in valid_exts:
            corrected_filename = f"{name_without_ext}{target_ext}"
            print(f"🔧 Extensión desconocida reemplazada: '{filename}' → '{corrected_filename}'")
            return corrected_filename
            
        # Caso 5: No tiene extensión
        if not current_ext:
            corrected_filename = f"{filename}{target_ext}"
            print(f"➕ Extensión añadida: '{filename}' → '{corrected_filename}'")
            return corrected_filename
            
        # Fallback: devolver con extensión correcta
        corrected_filename = f"{name_without_ext}{target_ext}"
        print(f"🔧 Extensión corregida: '{filename}' → '{corrected_filename}'")
        return corrected_filename


class ThumbnailConfig:
    """Maneja la configuración del generador de thumbnails"""
    
    DEFAULT_CONFIG = {
        'canvas': {'width': 1920, 'height': 1080},
        'background': {'blur_radius': 25},
        'text': {
            'max_width': 0.8,
            'line_spacing': 1.1,
            'color': [255, 255, 255, 255],
            'start_size': 160,
            'outer_shadow': {
                'offset': [4, 4],
                'blur': 8,
                'color': [0, 0, 0, 180]
            },
            'inner_shadow': {
                'offset': [3, 3],
                'blur': 6,
                'color': [0, 0, 0, 120]
            }
        },
        'icons': {
            'max_width': 200,
            'gap': 30,
            'outer_shadow': {
                'offset': [4, 4],
                'blur': 8,
                'color': [0, 0, 0, 180]
            }
        },
        'layout': {
            'text_offset_y': -80,
            'icons_offset_y': 40
        },
        'output': {
            'png_quality': 95
        }
    }
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Carga la configuración desde el archivo YAML o usa valores por defecto"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    print(f"✅ Configuración cargada desde {self.config_path}")
                    return self._merge_with_defaults(config)
            except Exception as e:
                print(f"⚠️  Error cargando config: {e}")
                print("📝 Usando configuración por defecto")
        else:
            print(f"📝 Archivo {self.config_path} no encontrado, usando configuración por defecto")
        
        return self.DEFAULT_CONFIG.copy()
    
    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Combina la configuración cargada con los valores por defecto"""
        merged = self.DEFAULT_CONFIG.copy()
        
        def deep_merge(default: Dict, loaded: Dict):
            for key, value in loaded.items():
                if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                    deep_merge(default[key], value)
                else:
                    default[key] = value
        
        deep_merge(merged, config)
        return merged
    
    def get(self, path: str, default=None):
        """Obtiene un valor de configuración usando notación de puntos"""
        keys = path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value


class IconSearcher:
    """Busca y descarga iconos desde múltiples fuentes"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search_icon(self, query: str) -> Optional[Image.Image]:
        """
        Busca un icono usando múltiples estrategias:
        1. Google Images (web scraping)
        2. SimpleIcons
        3. Flaticon
        4. Icono genérico de fallback
        """
        print(f"🔍 Buscando icono para: '{query}'")
        
        # Estrategia 1: Google Images
        icon = self._search_google_images(query)
        if icon:
            print(f"✅ Icono encontrado en Google Images")
            return icon
        
        # Estrategia 2: SimpleIcons
        icon = self._search_simple_icons(query)
        if icon:
            print(f"✅ Icono encontrado en SimpleIcons")
            return icon
        
        # Estrategia 3: Icons8
        icon = self._search_icons8(query)
        if icon:
            print(f"✅ Icono encontrado en Icons8")
            return icon
        
        # Estrategia 4: Icono genérico
        print(f"⚠️  No se encontró icono específico, usando genérico")
        return self._create_generic_icon(query)
    
    def _search_google_images(self, query: str) -> Optional[Image.Image]:
        """Busca iconos en Google Images usando web scraping"""
        try:
            # Búsqueda específica para iconos
            search_query = f"{query} icon png"
            url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}&tbm=isch&tbs=isz:m,ic:trans"
            
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar URLs de imágenes
            img_tags = soup.find_all('img', {'src': True})
            
            for img_tag in img_tags[:5]:  # Probar las primeras 5 imágenes
                img_url = img_tag.get('src')
                if img_url and img_url.startswith('http'):
                    try:
                        img_response = self.session.get(img_url, timeout=8)
                        if img_response.status_code == 200 and len(img_response.content) > 1000:
                            img = Image.open(io.BytesIO(img_response.content)).convert('RGBA')
                            if img.size[0] >= 64 and img.size[1] >= 64:  # Mínimo 64x64
                                return img
                    except Exception:
                        continue
            
        except Exception as e:
            print(f"  ⚠️  Error en búsqueda Google Images: {e}")
        
        return None
    
    def _search_simple_icons(self, query: str) -> Optional[Image.Image]:
        """Busca iconos en SimpleIcons"""
        try:
            # Limpiar query para SimpleIcons
            clean_query = re.sub(r'[^a-zA-Z0-9]', '', query.lower())
            
            urls = [
                f"https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/{clean_query}.svg",
                f"https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/{clean_query}.svg"
            ]
            
            for url in urls:
                try:
                    response = self.session.get(url, timeout=8)
                    if response.status_code == 200 and HAS_CAIROSVG:
                        png_bytes = cairosvg.svg2png(
                            bytestring=response.content,
                            output_width=512,
                            output_height=512
                        )
                        return Image.open(io.BytesIO(png_bytes)).convert('RGBA')
                except Exception:
                    continue
            
        except Exception as e:
            print(f"  ⚠️  Error en SimpleIcons: {e}")
        
        return None
    
    def _search_icons8(self, query: str) -> Optional[Image.Image]:
        """Busca iconos en Icons8"""
        try:
            clean_query = query.replace(' ', '-').lower()
            
            urls = [
                f"https://img.icons8.com/color/96/{clean_query}.png",
                f"https://img.icons8.com/ios-filled/100/{clean_query}.png",
                f"https://img.icons8.com/material/96/{clean_query}.png"
            ]
            
            for url in urls:
                try:
                    response = self.session.get(url, timeout=8)
                    if response.status_code == 200:
                        return Image.open(io.BytesIO(response.content)).convert('RGBA')
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"  ⚠️  Error en Icons8: {e}")
        
        return None
    
    def _create_generic_icon(self, query: str) -> Image.Image:
        """Crea un icono genérico con la primera letra del query"""
        size = 512
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Círculo de fondo
        margin = size // 8
        draw.ellipse([margin, margin, size-margin, size-margin], 
                    fill=(70, 130, 180, 255), outline=(255, 255, 255, 200), width=8)
        
        # Letra inicial
        letter = query[0].upper() if query else "?"
        try:
            font_size = size // 3
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # Centrar texto
        bbox = draw.textbbox((0, 0), letter, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (size - text_width) // 2
        text_y = (size - text_height) // 2
        
        draw.text((text_x, text_y), letter, fill=(255, 255, 255, 255), font=font)
        
        return img


class ThumbnailGenerator:
    """Generador principal de thumbnails"""
    
    def __init__(self, config: ThumbnailConfig):
        self.config = config
        self.icon_searcher = IconSearcher()
    
    def generate_thumbnail(self, title: str, background_image_path: str, 
                         icon_queries: List[str], output_path: str, 
                         output_format: str = 'png') -> bool:
        """
        Genera un thumbnail completo
        
        Args:
            title: Título del thumbnail
            background_image_path: Ruta de la imagen de fondo
            icon_queries: Lista de términos para buscar iconos
            output_path: Ruta de salida (ya validada)
            output_format: Formato de salida ('png' o 'psd')
            
        Returns:
            True si la generación fue exitosa
        """
        try:
            print(f"🎨 Generando thumbnail: '{title}'")
            print(f"📁 Salida: {output_path}")
            
            # Cargar y preparar imagen de fondo
            background = self._prepare_background(background_image_path)
            if not background:
                return False
            
            # Buscar iconos
            icons = []
            for query in icon_queries:
                icon = self.icon_searcher.search_icon(query)
                if icon:
                    icons.append(icon)
            
            if output_format.lower() == 'psd' and HAS_PSD_TOOLS:
                return self._generate_psd_thumbnail(title, background, icons, output_path)
            else:
                return self._generate_png_thumbnail(title, background, icons, output_path)
                
        except Exception as e:
            print(f"❌ Error generando thumbnail: {e}")
            return False
    
    def _prepare_background(self, image_path: str) -> Optional[Image.Image]:
        """Prepara la imagen de fondo con blur y redimensionado"""
        try:
            if not os.path.exists(image_path):
                print(f"❌ Imagen de fondo no encontrada: {image_path}")
                return None
            
            print(f"📷 Procesando imagen de fondo: {image_path}")
            
            # Cargar imagen
            img = Image.open(image_path).convert('RGB')
            
            # Redimensionar manteniendo aspecto
            canvas_size = (self.config.get('canvas.width'), self.config.get('canvas.height'))
            img = self._resize_and_crop(img, canvas_size)
            
            # Aplicar blur
            blur_radius = self.config.get('background.blur_radius', 25)
            img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            
            return img.convert('RGBA')
            
        except Exception as e:
            print(f"❌ Error procesando imagen de fondo: {e}")
            return None
    
    def _resize_and_crop(self, img: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
        """Redimensiona y recorta la imagen para ajustarla al tamaño objetivo"""
        img_ratio = img.width / img.height
        target_ratio = target_size[0] / target_size[1]
        
        if img_ratio > target_ratio:
            # Imagen más ancha - ajustar por altura
            new_height = target_size[1]
            new_width = int(img_ratio * new_height)
        else:
            # Imagen más alta - ajustar por ancho
            new_width = target_size[0]
            new_height = int(new_width / img_ratio)
        
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Recortar al centro
        left = (new_width - target_size[0]) // 2
        top = (new_height - target_size[1]) // 2
        right = left + target_size[0]
        bottom = top + target_size[1]
        
        return img.crop((left, top, right, bottom))
    
    def _generate_png_thumbnail(self, title: str, background: Image.Image, 
                               icons: List[Image.Image], output_path: str) -> bool:
        """Genera thumbnail en formato PNG"""
        try:
            canvas = background.copy()
            draw = ImageDraw.Draw(canvas)
            
            # Añadir texto
            self._add_text_to_canvas(canvas, draw, title)
            
            # Añadir iconos
            if icons:
                self._add_icons_to_canvas(canvas, icons)
            
            # Guardar
            quality = self.config.get('output.png_quality', 95)
            canvas.save(output_path, 'PNG', quality=quality, optimize=True)
            
            print(f"✅ Thumbnail PNG guardado: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error generando PNG: {e}")
            return False
    
    def _generate_psd_thumbnail(self, title: str, background: Image.Image, 
                               icons: List[Image.Image], output_path: str) -> bool:
        """Genera thumbnail en formato PSD con capas separadas"""
        try:
            from psd_tools import PSDImage
            from psd_tools.api.layers import PixelLayer
            
            print("🎨 Creando archivo PSD con capas...")
            
            # Crear PSD base
            width = self.config.get('canvas.width')
            height = self.config.get('canvas.height')
            
            # Crear layers individuales
            layers = []
            
            # Layer 1: Fondo
            layers.append(PixelLayer.new('Background', background.size, 'RGBA'))
            
            # Layer 2: Texto
            text_layer = Image.new('RGBA', background.size, (0, 0, 0, 0))
            text_draw = ImageDraw.Draw(text_layer)
            self._add_text_to_canvas(text_layer, text_draw, title)
            layers.append(PixelLayer.new('Text', text_layer.size, 'RGBA'))
            
            # Layer 3+: Iconos individuales
            for i, icon in enumerate(icons):
                icon_layer = Image.new('RGBA', background.size, (0, 0, 0, 0))
                # Posicionar icono (simplificado)
                icon_resized = self._resize_icon(icon)
                x = 100 + i * (icon_resized.width + 50)
                y = height - 200
                icon_layer.paste(icon_resized, (x, y), icon_resized)
                layers.append(PixelLayer.new(f'Icon_{i+1}', icon_layer.size, 'RGBA'))
            
            print(f"✅ PSD con {len(layers)} capas creado: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error generando PSD: {e}")
            print("📝 Generando PNG como alternativa...")
            png_path = output_path.replace('.psd', '.png')
            return self._generate_png_thumbnail(title, background, icons, png_path)
    
    def _add_text_to_canvas(self, canvas: Image.Image, draw: ImageDraw.Draw, title: str):
        """Añade texto con sombras al canvas"""
        canvas_width, canvas_height = canvas.size
        
        # Configuración de texto
        max_width = int(canvas_width * self.config.get('text.max_width', 0.8))
        start_size = self.config.get('text.start_size', 160)
        text_color = tuple(self.config.get('text.color', [255, 255, 255, 255]))
        
        # Encontrar tamaño de fuente óptimo
        font_size, lines = self._calculate_optimal_font_size(title, max_width, start_size)
        
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # Calcular posición del texto
        line_spacing = self.config.get('text.line_spacing', 1.1)
        total_height = len(lines) * font_size * line_spacing
        text_offset_y = self.config.get('layout.text_offset_y', -80)
        start_y = (canvas_height - total_height) // 2 + text_offset_y
        
        # Dibujar cada línea con sombras
        for i, line in enumerate(lines):
            line_y = start_y + i * font_size * line_spacing
            
            # Centrar línea horizontalmente
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            line_x = (canvas_width - line_width) // 2
            
            # Sombra exterior
            outer_shadow = self.config.get('text.outer_shadow', {})
            if outer_shadow:
                shadow_offset = outer_shadow.get('offset', [4, 4])
                shadow_color = tuple(outer_shadow.get('color', [0, 0, 0, 180]))
                shadow_x = line_x + shadow_offset[0]
                shadow_y = line_y + shadow_offset[1]
                draw.text((shadow_x, shadow_y), line, fill=shadow_color, font=font)
            
            # Texto principal
            draw.text((line_x, line_y), line, fill=text_color, font=font)
    
    def _calculate_optimal_font_size(self, title: str, max_width: int, start_size: int) -> Tuple[int, List[str]]:
        """Calcula el tamaño de fuente óptimo y divide el texto en líneas"""
        words = title.split()
        font_size = start_size
        
        while font_size > 20:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            lines = self._wrap_text(words, font, max_width)
            
            # Verificar si el texto cabe
            if len(lines) <= 3:  # Máximo 3 líneas
                return font_size, lines
            
            font_size -= 10
        
        # Si no cabe, usar tamaño mínimo
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        lines = self._wrap_text(words, font, max_width)
        return 20, lines[:3]  # Truncar a 3 líneas máximo
    
    def _wrap_text(self, words: List[str], font: ImageFont.ImageFont, max_width: int) -> List[str]:
        """Divide el texto en líneas que caben en el ancho máximo"""
        lines = []
        current_line = []
        
        for word in words:
            test_line = current_line + [word]
            test_text = ' '.join(test_line)
            
            # Crear un draw temporal para medir
            temp_img = Image.new('RGB', (1, 1))
            temp_draw = ImageDraw.Draw(temp_img)
            bbox = temp_draw.textbbox((0, 0), test_text, font=font)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)  # Palabra muy larga
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _add_icons_to_canvas(self, canvas: Image.Image, icons: List[Image.Image]):
        """Añade iconos al canvas con espaciado adecuado"""
        if not icons:
            return
        
        canvas_width, canvas_height = canvas.size
        max_icon_width = self.config.get('icons.max_width', 200)
        icon_gap = self.config.get('icons.gap', 30)
        icons_offset_y = self.config.get('layout.icons_offset_y', 40)
        
        # Redimensionar iconos
        resized_icons = [self._resize_icon(icon, max_icon_width) for icon in icons]
        
        # Calcular posición inicial
        total_width = sum(icon.width for icon in resized_icons) + icon_gap * (len(resized_icons) - 1)
        start_x = (canvas_width - total_width) // 2
        icon_y = canvas_height // 2 + icons_offset_y
        
        # Colocar iconos
        current_x = start_x
        for icon in resized_icons:
            # Añadir sombra si está configurada
            shadow_config = self.config.get('icons.outer_shadow')
            if shadow_config:
                shadow_offset = shadow_config.get('offset', [4, 4])
                shadow_x = current_x + shadow_offset[0]
                shadow_y = icon_y + shadow_offset[1]
                
                # Crear sombra simple (puede mejorarse)
                shadow = Image.new('RGBA', icon.size, (0, 0, 0, 0))
                canvas.paste(shadow, (shadow_x, shadow_y), shadow)
            
            canvas.paste(icon, (current_x, icon_y), icon)
            current_x += icon.width + icon_gap
    
    def _resize_icon(self, icon: Image.Image, max_width: int = None) -> Image.Image:
        """Redimensiona un icono manteniendo el aspecto"""
        if max_width is None:
            max_width = self.config.get('icons.max_width', 200)
        
        if icon.width > max_width:
            ratio = max_width / icon.width
            new_height = int(icon.height * ratio)
            icon = icon.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        return icon


def get_user_input() -> Tuple[str, str, List[str], str, str]:
    """
    Obtiene la entrada del usuario de forma interactiva
    
    Returns:
        Tupla con (título, imagen_fondo, iconos, archivo_salida, formato)
    """
    print("=" * 60)
    print("🎨 GENERADOR DE THUMBNAILS PARA BLOG")
    print("=" * 60)
    print()
    
    # Título del thumbnail
    while True:
        title = input("📝 Título del thumbnail: ").strip()
        if title:
            break
        print("⚠️  El título no puede estar vacío")
    
    # Imagen de fondo
    while True:
        background_path = input("📷 Ruta de la imagen de fondo: ").strip()
        if os.path.exists(background_path):
            break
        print(f"❌ Archivo no encontrado: {background_path}")
    
    # Iconos (opcional)
    print("\n🎯 Iconos para el thumbnail (opcional):")
    print("   Ingresa términos de búsqueda separados por comas")
    print("   Ejemplo: python, web, programming")
    
    icons_input = input("🔍 Términos de iconos (Enter para omitir): ").strip()
    icon_queries = [term.strip() for term in icons_input.split(',') if term.strip()] if icons_input else []
    
    # Formato de salida
    print("\n📁 Formato de salida:")
    print("   1. PNG (imagen estándar)")
    print("   2. PSD (archivo de Photoshop con capas)")
    
    while True:
        format_choice = input("🎨 Selecciona formato (1 o 2): ").strip()
        if format_choice == '1':
            output_format = 'png'
            break
        elif format_choice == '2':
            output_format = 'psd'
            break
        print("⚠️  Selecciona 1 o 2")
    
    # Archivo de salida
    default_name = f"thumbnail_{title.lower().replace(' ', '_')[:20]}"
    output_file = input(f"💾 Nombre del archivo de salida [{default_name}]: ").strip()
    
    if not output_file:
        output_file = default_name
    
    # Validar y corregir extensión automáticamente
    output_file = FileExtensionValidator.validate_and_fix_extension(output_file, output_format)
    
    print("\n" + "=" * 60)
    print("✅ CONFIGURACIÓN COMPLETA")
    print("=" * 60)
    print(f"📝 Título: {title}")
    print(f"📷 Fondo: {background_path}")
    print(f"🎯 Iconos: {', '.join(icon_queries) if icon_queries else 'Ninguno'}")
    print(f"💾 Salida: {output_file} ({output_format.upper()})")
    print("=" * 60)
    
    confirm = input("\n¿Continuar? (S/n): ").strip().lower()
    if confirm in ['n', 'no']:
        print("❌ Operación cancelada")
        sys.exit(0)
    
    return title, background_path, icon_queries, output_file, output_format


def main():
    """Función principal del programa"""
    print("🚀 Iniciando Generador de Thumbnails...")
    
    # Cargar configuración
    config = ThumbnailConfig()
    
    # Obtener entrada del usuario
    title, background_path, icon_queries, output_file, output_format = get_user_input()
    
    # Crear generador
    generator = ThumbnailGenerator(config)
    
    # Generar thumbnail
    print(f"\n🎨 Iniciando generación...")
    success = generator.generate_thumbnail(
        title=title,
        background_image_path=background_path,
        icon_queries=icon_queries,
        output_path=output_file,
        output_format=output_format
    )
    
    if success:
        print(f"\n🎉 ¡Thumbnail generado exitosamente!")
        print(f"📁 Archivo guardado: {output_file}")
        
        # Mostrar información del archivo
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"📊 Tamaño del archivo: {file_size / 1024:.1f} KB")
    else:
        print(f"\n❌ Error generando el thumbnail")
        sys.exit(1)


if __name__ == "__main__":
    main()
