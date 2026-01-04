from flask import Flask, render_template, session 
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

app.register_blueprint(execution_bp)
app.register_blueprint(download_bp)
app.register_blueprint(upload_bp)


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

@app.route('/')
def index():
    
    
    
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
