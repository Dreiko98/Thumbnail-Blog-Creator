# 🎨 Generador Avanzado de Thumbnails para Blog

Un generador profesional de thumbnails con sistema robusto de iconos, configuración flexible y soporte para archivos PSD con capas separadas.

## ✨ Características Principales

### 🔧 **Nueva: Verificación Automática de Extensiones**
- **Corrección automática** de extensiones incorrectas
- **Añadido automático** de extensiones faltantes
- **Preservación** de extensiones correctas
- **Soporte** para nombres con múltiples puntos
- **Insensibilidad** a mayúsculas/minúsculas

### 🎯 Sistema Avanzado de Iconos
- **Google Images**: Búsqueda web inteligente con scraping
- **SimpleIcons**: Biblioteca de iconos vectoriales
- **Icons8**: Iconos de alta calidad
- **Fallback genérico**: Icono automático cuando no se encuentra ninguno

### 📐 Configuración Flexible
- **Archivo YAML**: Configuración externa completa
- **Valores por defecto**: Funciona sin configuración
- **Personalización total**: Colores, sombras, tamaños, posicionamiento

### 🎨 Salida Profesional
- **PNG**: Imágenes estándar de alta calidad
- **PSD**: Archivos de Photoshop con capas separadas
- **Calidad configurable**: Control total sobre la compresión

## 🚀 Instalación Rápida

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd Thumbnail-Blog-Creator
```

### 2. Configurar entorno virtual (recomendado)
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# o
.venv\Scripts\activate     # Windows
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

## 💻 Uso

### Modo Interactivo (Recomendado)
```bash
python thumbnail_maker.py
```

El script te guiará paso a paso:
1. **Título** del thumbnail
2. **Imagen de fondo** (ruta del archivo)
3. **Iconos** (términos de búsqueda separados por comas)
4. **Formato de salida** (PNG o PSD)
5. **Nombre del archivo** (con verificación automática de extensión)

### Ejemplos de Uso

#### Ejemplo 1: Thumbnail básico
```
📝 Título del thumbnail: Cómo Crear APIs con Python
📷 Ruta de la imagen de fondo: ./backgrounds/code_bg.jpg
🔍 Términos de iconos: python, api, flask
🎨 Formato: PNG
💾 Archivo de salida: python_api_tutorial
```
**Resultado**: `python_api_tutorial.png` (extensión añadida automáticamente)

#### Ejemplo 2: Thumbnail profesional en PSD
```
📝 Título del thumbnail: Machine Learning con TensorFlow
📷 Ruta de la imagen de fondo: ./images/ai_background.png
🔍 Términos de iconos: tensorflow, python, artificial intelligence
🎨 Formato: PSD
💾 Archivo de salida: ml_tensorflow_guide.jpg
```
**Resultado**: `ml_tensorflow_guide.psd` (extensión corregida automáticamente)

## 🔧 Demostración de Validación de Extensiones

Prueba la nueva funcionalidad de verificación automática:

```bash
python demo_extension_validation.py
```

Esta demostración muestra:
- ✅ Corrección de extensiones incorrectas
- ✅ Añadido de extensiones faltantes  
- ✅ Preservación de extensiones correctas
- ✅ Modo interactivo para probar tus propios casos

## ⚙️ Configuración Avanzada

### Archivo `config.yaml`

```yaml
# Dimensiones del canvas
canvas:
  width: 1920
  height: 1080

# Configuración del fondo
background:
  blur_radius: 25

# Configuración del texto
text:
  max_width: 0.8
  line_spacing: 1.1
  color: [255, 255, 255, 255]
  start_size: 160
  
  outer_shadow:
    offset: [4, 4]
    blur: 8
    color: [0, 0, 0, 180]

# Configuración de iconos
icons:
  max_width: 200
  gap: 30
  
  outer_shadow:
    offset: [4, 4]
    blur: 8
    color: [0, 0, 0, 180]

# Posicionamiento
layout:
  text_offset_y: -80
  icons_offset_y: 40
```

## 🏗️ Arquitectura del Sistema

### Clases Principales

#### `FileExtensionValidator`
- **Propósito**: Validación y corrección automática de extensiones
- **Métodos**: `validate_and_fix_extension()`
- **Casos manejados**: 
  - Extensiones faltantes → Añade automáticamente
  - Extensiones incorrectas → Corrige automáticamente
  - Extensiones correctas → Preserva sin cambios

#### `ThumbnailConfig`
- **Propósito**: Manejo de configuración YAML
- **Características**: Valores por defecto, fusión inteligente
- **Uso**: `config.get('text.color', default_value)`

#### `IconSearcher`
- **Propósito**: Búsqueda multi-fuente de iconos
- **Estrategias**: Google Images → SimpleIcons → Icons8 → Genérico
- **Formato**: Conversión automática SVG→PNG

#### `ThumbnailGenerator`
- **Propósito**: Generación de thumbnails finales
- **Formatos**: PNG (estándar) y PSD (con capas)
- **Características**: Texto multi-línea, sombras, iconos posicionados

## 📁 Estructura del Proyecto

```
Thumbnail-Blog-Creator/
├── thumbnail_maker.py              # Script principal
├── demo_extension_validation.py    # Demostración de validación
├── config.yaml                     # Configuración principal
├── requirements.txt                # Dependencias Python
├── README.md                       # Este archivo
├── .gitignore                      # Archivos ignorados por Git
└── examples/                       # (Generado) Archivos de ejemplo
    ├── thumbnails/                 # Thumbnails generados
    └── backgrounds/                # Imágenes de fondo de ejemplo
```

## 📋 Dependencias

### Principales
- **Pillow**: Manipulación de imágenes
- **requests**: Descargas HTTP
- **PyYAML**: Configuración YAML
- **beautifulsoup4**: Scraping web
- **lxml**: Parser HTML/XML

### Opcionales
- **cairosvg**: Conversión SVG→PNG
- **psd-tools**: Generación de archivos PSD

## 🔍 Ejemplos de Validación de Extensiones

| Entrada | Formato | Salida | Acción |
|---------|---------|--------|--------|
| `mi_thumbnail` | PNG | `mi_thumbnail.png` | ➕ Extensión añadida |
| `archivo.jpg` | PNG | `archivo.png` | 🔧 Extensión corregida |
| `correcto.png` | PNG | `correcto.png` | ✅ Sin cambios |
| `proyecto.final.psd` | PSD | `proyecto.final.psd` | ✅ Sin cambios |
| `` (vacío) | PNG | `thumbnail.png` | 🆕 Nombre por defecto |

## 🐛 Solución de Problemas

### Error: "Dependencia faltante"
```bash
pip install -r requirements.txt
```

### Error: "Imagen de fondo no encontrada"
- Verifica la ruta del archivo
- Usa rutas absolutas si hay problemas
- Formatos soportados: JPG, PNG, GIF, BMP

### Error: "No se puede crear PSD"
```bash
pip install psd-tools
```

### Iconos no encontrados
- El sistema usa fallback automático
- Se genera un icono genérico con la primera letra
- Verifica conexión a internet para búsquedas web

## 🤝 Contribuir

1. Fork del repositorio
2. Crear branch de feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit de cambios (`git commit -am 'Añade nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

## 🙏 Créditos

- **Sistema de iconos**: Google Images, SimpleIcons, Icons8
- **Generación PSD**: psd-tools
- **Procesamiento de imágenes**: Pillow
- **Desarrollo**: GitHub Copilot Assistant

---

## 🆕 Changelog v3.0

### ✨ Nuevas Características
- **Verificación automática de extensiones de archivo**
- **Corrección automática de extensiones incorrectas**
- **Añadido automático de extensiones faltantes**
- **Demostración interactiva de validación**

### 🔧 Mejoras
- **Manejo robusto de nombres de archivo**
- **Preservación de extensiones correctas**
- **Soporte para múltiples puntos en nombres**
- **Documentación expandida**

### 🐛 Correcciones
- **Manejo de nombres de archivo vacíos**
- **Validación insensible a mayúsculas/minúsculas**
- **Mejor experiencia de usuario en entrada interactiva**
