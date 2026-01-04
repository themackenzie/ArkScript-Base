from flask import Blueprint, send_from_directory
import os


UPLOAD_FOLDER = 'temp_files'


download_bp = Blueprint('download', __name__)


@download_bp.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """Ruta para servir el archivo generado para su descarga."""
    try:
        
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
    except FileNotFoundError:
        return "Archivo no encontrado para descarga.", 404