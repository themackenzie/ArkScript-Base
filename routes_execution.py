from flask import Blueprint, request, jsonify, session # Se agregó session
from io import StringIO
import sys
import os
import json 
import contextlib 
import io 


from core_interpreter.lexer import Lexer
from core_interpreter.parser import Parser
from core_interpreter.evaluator import Evaluator


UPLOAD_FOLDER = 'temp_files'

# --- MODIFICACIÓN: Funciones para rutas dinámicas por usuario ---
def get_user_folder():
    user_id = session.get('user_id', 'default')
    folder = os.path.join(UPLOAD_FOLDER, user_id)
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder

def get_metadata_path():
    return os.path.join(get_user_folder(), 'input_files.json')

execution_bp = Blueprint('execution', __name__)

def load_input_filenames():
    """Carga la lista de nombres de archivos de entrada desde el JSON del usuario."""
    metadata_path = get_metadata_path() # Uso de ruta dinámica
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            try:
                return set(json.load(f))
            except json.JSONDecodeError:
                return set()
    return set()

def clean_output_files():
    """Borra archivos de salida antiguos solo en la carpeta del usuario actual."""
    user_folder = get_user_folder()
    metadata_path = get_metadata_path()
    
    persistent_files = load_input_filenames()
    persistent_files.add(os.path.basename(metadata_path))
    
    deleted_count = 0
    
    if os.path.exists(user_folder):
        for filename in os.listdir(user_folder):
            if filename not in persistent_files:
                filepath = os.path.join(user_folder, filename)
                try:
                    os.remove(filepath)
                    deleted_count += 1
                except Exception as e:
                    print(f"Error al borrar archivo '{filename}': {e}")
    
    print(f"Archivos de salida antiguos del usuario eliminados: {deleted_count}")


def compile_and_run(code_source):
    redirected_output = io.StringIO()
    
    try:
        with contextlib.redirect_stdout(redirected_output):
            lexer = Lexer(code_source)
            tokens = lexer.tokenize() 
            
            parser = Parser(tokens) 
            
            # --- MODIFICACIÓN: Informar al Evaluator su carpeta de trabajo ---
            evaluator = Evaluator()
            evaluator.FILE_DIR = get_user_folder() # Se asigna la ruta del usuario
            
            evaluator.evaluate(parser.parse())
        
        output_files = evaluator.get_all_output_files()

        return {
            "output": redirected_output.getvalue(),
            "error": False,
            "output_files": output_files
        }
        
    except Exception as e:
        return {
            "output": f"Error de Compilación/Ejecución: {e}\n\n{redirected_output.getvalue()}",
            "error": True,
            "output_files": []
        }



@execution_bp.route('/execute', methods=['POST'])
def execute_code():
    code = request.form.get('code', '')
    if not code:
        return jsonify({"output": "Error: No se proporcionó código fuente.", "error": True, "output_files": []})

    clean_output_files()

    result = compile_and_run(code)

    return jsonify(result)
