#!/usr/bin/env python3
# wsgi.py - Punto de entrada WSGI para Gunicorn

import sys
import os

# Agregar el directorio del proyecto al path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Activar entorno virtual
venv_path = os.path.join(project_dir, '.venv')
if os.path.exists(venv_path):
    activate_script = os.path.join(venv_path, 'bin', 'activate_this.py')
    if os.path.exists(activate_script):
        with open(activate_script) as f:
            exec(f.read(), {'__file__': activate_script})

# Importar la aplicación Flask
from web_app import app

if __name__ == "__main__":
    app.run()