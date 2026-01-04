from flask import Blueprint, request, jsonify
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
INPUT_FILES_METADATA = os.path.join(UPLOAD_FOLDER, 'input_files.json') 
Evaluator.FILE_DIR = UPLOAD_FOLDER


execution_bp = Blueprint('execution', __name__)



def load_input_filenames():
    """Carga la lista de nombres de archivos de entrada desde JSON."""
    if os.path.exists(INPUT_FILES_METADATA):
        with open(INPUT_FILES_METADATA, 'r') as f:
            try:
                
                return set(json.load(f))
            except json.JSONDecodeError:
                return set()
    return set()

def clean_output_files():
    """Borra todos los archivos que NO sean archivos de entrada o el metadata JSON."""
    
    persistent_files = load_input_filenames()
    persistent_files.add(os.path.basename(INPUT_FILES_METADATA))
    
    deleted_count = 0
    
    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            if filename not in persistent_files:
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                try:
                    os.remove(filepath)
                    deleted_count += 1
                except Exception as e:
                    print(f"Error al borrar archivo '{filename}': {e}")
    
    print(f"Archivos de salida antiguos eliminados: {deleted_count}")


def compile_and_run(code_source):
    
    redirected_output = io.StringIO()
    
    try:
        with contextlib.redirect_stdout(redirected_output):
            
            lexer = Lexer(code_source)
            tokens = lexer.tokenize() 
            
            
            parser = Parser(tokens) 
            
            evaluator = Evaluator()
            
            
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