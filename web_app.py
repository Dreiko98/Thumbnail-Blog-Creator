#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interfaz Web para Generador de Thumbnails
==========================================

Aplicación Flask que proporciona una interfaz web moderna para generar thumbnails.
Compatible con empaquetado como aplicación de escritorio.

Autor: Desarrollador Senior Python
Fecha: Agosto 2025
"""

import os
import base64
import tempfile
import uuid
from io import BytesIO
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from generate_thumbnail import generar_thumbnail
import webbrowser
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'thumbnail_generator_2025'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB máximo

# Directorio temporal para archivos subidos - usar carpetas del proyecto, no /tmp
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(SCRIPT_DIR, '.uploads')
RESULTS_FOLDER = os.path.join(SCRIPT_DIR, '.results')

# Crear carpetas si no existen
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER

print(f"📁 Carpeta de uploads: {UPLOAD_FOLDER}")
print(f"📁 Carpeta de resultados: {RESULTS_FOLDER}")

# Extensiones permitidas
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg'}

def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def cleanup_old_files():
    """Limpia archivos temporales antiguos (más de 24 horas) - NO se ejecuta en cada carga."""
    try:
        current_time = time.time()
        for folder in [UPLOAD_FOLDER, RESULTS_FOLDER]:
            if os.path.exists(folder):
                for filename in os.listdir(folder):
                    file_path = os.path.join(folder, filename)
                    if os.path.isfile(file_path):
                        file_age = current_time - os.path.getctime(file_path)
                        if file_age > 86400:  # 24 horas - más conservador
                            try:
                                os.remove(file_path)
                                print(f"🗑️  Archivo antiguo eliminado: {filename}")
                            except OSError as e:
                                print(f"⚠️  No se pudo eliminar {filename}: {e}")
    except Exception as e:
        print(f"Error limpiando archivos temporales: {e}")

@app.route('/')
def index():
    """Página principal de la aplicación."""
    # No limpiar archivos en cada carga - hacerlo solo en shutdown
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Maneja la subida de archivos (imagen de fondo e iconos)."""
    try:
        response = {'success': False, 'message': '', 'files': {'icons': []}}
        
        # Procesar imagen de fondo
        if 'background_image' in request.files:
            file = request.files['background_image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                response['files']['background'] = unique_filename
                print(f"✅ Imagen de fondo guardada: {unique_filename}")
        
        # Procesar iconos
        icons = []
        for key in request.files:
            if key.startswith('icon_'):
                file = request.files[key]
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(file_path)
                    icons.append(unique_filename)
                    print(f"✅ Icono guardado: {unique_filename}")
        
        # Siempre incluir icons en la respuesta (vacío si no hay)
        response['files']['icons'] = icons
        
        response['success'] = True
        response['message'] = f"Archivos subidos correctamente. Fondo: {'✅' if 'background' in response['files'] else '❌'}, Iconos: {len(icons)}"
        
        print(f"📤 Respuesta /upload: success={response['success']}, background={'✅' if 'background' in response['files'] else '❌'}, icons={len(icons)}")
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/generate', methods=['POST'])
def generate_thumbnail():
    """Genera el thumbnail con los parámetros especificados."""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        if not data.get('title'):
            return jsonify({'success': False, 'message': 'El título es obligatorio'})
        
        if not data.get('background_file'):
            return jsonify({'success': False, 'message': 'La imagen de fondo es obligatoria'})
        
        # Preparar rutas de archivos
        background_file = data.get('background_file')
        print(f"📥 background_file recibido: {background_file}")
        background_path = os.path.join(app.config['UPLOAD_FOLDER'], background_file)
        print(f"   📂 Ruta construida: {background_path}")
        print(f"   ✓ Existe: {os.path.exists(background_path)}")
        
        if not os.path.exists(background_path):
            print(f"   ❌ ARCHIVO NO ENCONTRADO!")
            print(f"   📂 Contenido de {app.config['UPLOAD_FOLDER']}:")
            try:
                for f in os.listdir(app.config['UPLOAD_FOLDER']):
                    print(f"      - {f}")
            except Exception as e:
                print(f"      Error listando: {e}")
            return jsonify({'success': False, 'message': 'Imagen de fondo no encontrada'})
        
        # Preparar iconos
        icon_paths = []
        icon_files = data.get('icon_files', [])
        print(f"📥 icon_files recibido: {icon_files} (type: {type(icon_files)})")
        
        if icon_files and isinstance(icon_files, list) and len(icon_files) > 0:
            for icon_file in icon_files:
                icon_path = os.path.join(app.config['UPLOAD_FOLDER'], icon_file)
                print(f"   🔍 Verificando icono: {icon_path}")
                if os.path.exists(icon_path):
                    icon_paths.append(icon_path)
                    print(f"   ✅ Icono encontrado: {icon_file}")
                else:
                    print(f"   ❌ Icono NO encontrado: {icon_file}")
        
        print(f"📤 Iconos a procesar: {len(icon_paths)}")
        
        # Generar nombre único para el resultado
        result_id = uuid.uuid4().hex
        result_name = f"thumbnail_{result_id}"
        result_path = os.path.join(app.config['RESULTS_FOLDER'], result_name)
        
        # Generar thumbnail usando la función existente
        print(f"🎨 Generando thumbnail:")
        print(f"   📸 Fondo: {background_path}")
        print(f"   📝 Título: {data['title']}")
        print(f"   🎯 Iconos: {len(icon_paths)}")
        
        generar_thumbnail(
            imagen_base=background_path,
            titulo=data['title'],
            iconos=icon_paths,
            ruta_salida=result_path
        )
        
        # Verificar que se generó correctamente
        png_path = f"{result_path}.png"
        if os.path.exists(png_path):
            # Convertir imagen a base64 para preview
            with open(png_path, 'rb') as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
            
            return jsonify({
                'success': True,
                'message': '🎉 Thumbnail generado exitosamente',
                'result_id': result_id,
                'preview': f"data:image/png;base64,{img_base64}",
                'download_url': f"/download/{result_id}"
            })
        else:
            return jsonify({'success': False, 'message': 'Error al generar el thumbnail'})
            
    except Exception as e:
        print(f"❌ Error generando thumbnail: {e}")
        return jsonify({'success': False, 'message': f'Error interno: {str(e)}'})

@app.route('/download/<result_id>')
def download_thumbnail(result_id):
    """Descarga el thumbnail generado."""
    try:
        png_path = os.path.join(app.config['RESULTS_FOLDER'], f"thumbnail_{result_id}.png")
        if os.path.exists(png_path):
            return send_file(
                png_path,
                as_attachment=True,
                download_name=f"thumbnail_{result_id}.png",
                mimetype='image/png'
            )
        else:
            return "Archivo no encontrado", 404
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/health')
def health_check():
    """Endpoint para verificar el estado de la aplicación."""
    return jsonify({'status': 'ok', 'message': 'Thumbnail Generator Web App funcionando correctamente'})

def open_browser():
    """Abre el navegador automáticamente tras iniciar el servidor."""
    time.sleep(1.5)  # Esperar a que el servidor esté listo
    webbrowser.open('http://localhost:5000')

def run_app(debug=False, port=5000):
    """Ejecuta la aplicación Flask."""
    print("\n🚀 INICIANDO THUMBNAIL GENERATOR WEB APP")
    print("═" * 60)
    print(f"📱 Interfaz web disponible en: http://localhost:{port}")
    print("🔧 Presiona Ctrl+C para detener el servidor")
    print("═" * 60)
    
    # Abrir navegador automáticamente en modo producción
    if not debug:
        threading.Thread(target=open_browser, daemon=True).start()
    
    try:
        app.run(
            host='0.0.0.0',
            port=port,
            debug=debug,
            use_reloader=False  # Evitar doble inicio en modo debug
        )
    except KeyboardInterrupt:
        print("\n👋 Cerrando aplicación...")
    finally:
        cleanup_old_files()

if __name__ == '__main__':
    import sys
    
    # Argumentos de línea de comandos
    debug_mode = '--debug' in sys.argv
    port = 5000
    
    if '--port' in sys.argv:
        try:
            port_index = sys.argv.index('--port') + 1
            port = int(sys.argv[port_index])
        except (IndexError, ValueError):
            print("⚠️  Puerto inválido, usando 5000 por defecto")
    
    run_app(debug=debug_mode, port=port)
