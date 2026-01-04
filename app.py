from flask import Flask, render_template, session, jsonify # Se agregó jsonify
import os
import shutil 
import time 
import uuid 

from routes_execution import execution_bp, UPLOAD_FOLDER
from routes_download import download_bp
from routes_upload import upload_bp

app = Flask(__name__)

app.secret_key = 'tu_clave_secreta_aqui' 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- NUEVAS CONFIGURACIONES PARA PLANTILLAS ---
# Ruta absoluta a la carpeta de plantillas .txt
REFFS_DIR = os.path.join(app.root_path, 'templates', 'reffs')
# Aseguramos que la carpeta exista para evitar errores
if not os.path.exists(REFFS_DIR):
    os.makedirs(REFFS_DIR)

app.register_blueprint(execution_bp)
app.register_blueprint(download_bp)
app.register_blueprint(upload_bp)

# --- NUEVAS RUTAS PARA EL SISTEMA DE PLANTILLAS ---
@app.route('/get_templates')
def get_templates():
    """Lista los nombres de archivos .txt en la carpeta reffs."""
    try:
        files = [f for f in os.listdir(REFFS_DIR) if f.endswith('.txt')]
        return jsonify(files)
    except Exception as e:
        return jsonify([])

@app.route('/get_template_content/<filename>')
def get_template_content(filename):
    """Devuelve el contenido de un archivo de plantilla específico."""
    # Validación básica de seguridad para evitar saltos de directorio
    if ".." in filename or "/" in filename:
        return "Nombre de archivo no válido", 400
        
    path = os.path.join(REFFS_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Plantilla no encontrada", 404
# --- FIN DE NUEVAS RUTAS ---

@app.before_request
def ensure_user_context():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    
    user_folder = os.path.join(UPLOAD_FOLDER, session['user_id'])
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

INPUT_FILES_METADATA = os.path.join(UPLOAD_FOLDER, 'input_files.json')

def clean_all_temporary_files():
    """Elimina todos los archivos en el directorio temporal (temp_files) al inicio del servidor."""
    print(">>> Limpiando todos los archivos de entrada/salida temporales...")
    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            try:
                if os.path.isfile(filepath) or os.path.islink(filepath):
                    os.unlink(filepath)
                elif os.path.isdir(filepath):
                    shutil.rmtree(filepath)
            except Exception as e:
                print(f'Error al eliminar {filepath}: {e}')
    
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    print(">>> Limpieza completada.")

# --- NUEVA FUNCIÓN DE LIMPIEZA DE SESIÓN ---
def clean_user_session_folder():
    """Borra los archivos específicos del usuario actual."""
    if 'user_id' in session:
        user_folder = os.path.join(UPLOAD_FOLDER, session['user_id'])
        if os.path.exists(user_folder):
            for filename in os.listdir(user_folder):
                filepath = os.path.join(user_folder, filename)
                try:
                    if os.path.isfile(filepath) or os.path.islink(filepath):
                        os.unlink(filepath)
                    elif os.path.isdir(filepath):
                        shutil.rmtree(filepath)
                except Exception as e:
                    print(f"Error limpiando sesión: {e}")
# --------------------------------------------

@app.route('/')
def index():
    # Limpiamos la carpeta del usuario al cargar la página principal
    clean_user_session_folder() 
    
    css_path = os.path.join(app.root_path, 'static', 'style.css')
    if os.path.exists(css_path):
        cache_buster = int(os.stat(css_path).st_mtime)
    else:
        cache_buster = int(time.time())
    
    return render_template('index.html', cache_buster=cache_buster)

if __name__ == '__main__':
    clean_all_temporary_files() 
    
    print("\n--- INICIANDO SERVIDOR FLASK ---")
    print(f"Abriendo http://127.0.0.1:5000/ - Directorio de archivos: {UPLOAD_FOLDER}")
    app.run(debug=True, port=5000)
