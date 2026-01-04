from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
import json 
import time



UPLOAD_FOLDER = 'temp_files'
INPUT_FILES_METADATA = os.path.join(UPLOAD_FOLDER, 'input_files.json')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

upload_bp = Blueprint('upload', __name__)


ALLOWED_EXTENSIONS = ('.txt', '.pdf')

def is_allowed_file(filename):
    """Verifica si la extensión del archivo está permitida."""
    return filename.lower().endswith(ALLOWED_EXTENSIONS)

def load_input_filenames():
    """Carga la lista de nombres de archivos de entrada (ahora incluyendo .pdf) desde JSON."""
    if os.path.exists(INPUT_FILES_METADATA):
        with open(INPUT_FILES_METADATA, 'r') as f:
            try:
                all_files = json.load(f)
                
                return set(f for f in all_files if isinstance(f, str) and is_allowed_file(f))
            except json.JSONDecodeError:
                return set()
    return set()

def save_input_filenames(filenames_set):
    """Guarda la lista de nombres de archivos de entrada en JSON."""
    
    clean_list = [f for f in filenames_set if is_allowed_file(f)]
    with open(INPUT_FILES_METADATA, 'w') as f:
        json.dump(clean_list, f)

@upload_bp.route('/upload', methods=['POST'])
def upload_files():
    files = request.files.getlist('files')
    uploaded_filenames = []
    
    current_input_files = load_input_filenames()
    
    if not files or files[0].filename == '':
        return jsonify({"output": "Error: No se seleccionó ningún archivo para subir.", "error": True})

    try:
        for file in files:
            if file and is_allowed_file(file.filename):  
                filename = secure_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                
                file.save(filepath)
                uploaded_filenames.append(filename)
                
                
                current_input_files.add(filename)
                
            elif file and file.filename:
                
                return jsonify({"output": f"Error de Archivo: El archivo '{file.filename}' debe ser .txt o .pdf.", "error": True})
        
        save_input_filenames(current_input_files)

        return jsonify({
            "output": f"{len(uploaded_filenames)} archivo(s) subido(s) o actualizado(s) con éxito.", 
            "error": False, 
            "current_files": list(current_input_files) 
        })

    except Exception as e:
        return jsonify({"output": f"Error al guardar archivos en el servidor: {e}", "error": True})

@upload_bp.route('/get_input_files', methods=['GET'])
def get_input_files():
    """Devuelve la lista actual de archivos de entrada al frontend."""
    return jsonify({"current_files": list(load_input_filenames())})