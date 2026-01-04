from flask import Blueprint, send_from_directory, session # Se agregó session
import os

UPLOAD_FOLDER = 'temp_files'

download_bp = Blueprint('download', __name__)

# --- MODIFICACIÓN: Función para obtener la ruta dinámica del usuario ---
def get_user_folder():
    user_id = session.get('user_id', 'default')
    return os.path.join(UPLOAD_FOLDER, user_id)

@download_bp.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """Ruta para servir el archivo generado para su descarga desde la carpeta del usuario."""
    try:
        # --- MODIFICACIÓN: Usar la carpeta específica del usuario ---
        user_folder = get_user_folder()
        return send_from_directory(user_folder, filename, as_attachment=True)
    except FileNotFoundError:
        return "Archivo no encontrado para descarga.", 404
