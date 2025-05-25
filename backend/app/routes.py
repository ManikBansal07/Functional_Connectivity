from flask import Blueprint, request, jsonify, make_response, send_file, current_app
import os
import nibabel as nib
import numpy as np
from werkzeug.utils import secure_filename
import json
from datetime import datetime
from .model_processor import FunctionalConnectivityProcessor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)

# Configuration
ALLOWED_EXTENSIONS = {'nii', 'nii.gz'}
MODEL_FOLDER = 'models'
MAX_CONTENT_LENGTH = 200 * 1024 * 1024  # 200MB limit

# Create model directory if it doesn't exist
if not os.path.exists(MODEL_FOLDER):
    os.makedirs(MODEL_FOLDER)

# Initialize processor with model path
MODEL_PATH = os.path.join(MODEL_FOLDER, 'FC_Other_Models.ipynb')
processor = FunctionalConnectivityProcessor(MODEL_PATH)

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    # Handle .nii.gz files
    if filename.endswith('.nii.gz'):
        return True
    # Handle .nii files
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'nii'

def create_response(data, status_code=200):
    response = jsonify(data)
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response, status_code

@bp.route('/api/health', methods=['GET', 'OPTIONS'])
def health_check():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    return create_response({'status': 'healthy', 'message': 'Server is running'})

@bp.route('/api/upload', methods=['POST', 'OPTIONS'])
def upload_file():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    logger.info("Received file upload request")
    
    if 'file' not in request.files:
        logger.error("No file part in request")
        return create_response({'error': 'No file part'}, 400)
    
    file = request.files['file']
    if file.filename == '':
        logger.error("No selected file")
        return create_response({'error': 'No selected file'}, 400)
    
    if not allowed_file(file.filename):
        logger.error(f"Invalid file type: {file.filename}")
        return create_response({'error': 'Invalid file type. Only NIfTI files (.nii, .nii.gz) are allowed'}, 400)

    try:
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_CONTENT_LENGTH:
            logger.error(f"File too large: {file_size} bytes")
            return create_response({'error': 'File too large. Maximum size is 200MB'}, 400)

        # Create a unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = secure_filename(f"{timestamp}_{file.filename}")
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        logger.info(f"Saving file to: {filepath}")
        # Save the file
        file.save(filepath)
        
        logger.info("Processing NIfTI file")
        # Process the NIfTI file
        connectivity_matrix, region_names, metrics = processor.process_nifti(filepath)
        
        # Convert numpy array to list for JSON serialization
        matrix_list = connectivity_matrix.tolist()
        
        logger.info("File processed successfully")
        return create_response({
            'message': 'File processed successfully',
            'filename': filename,
            'connectivity_matrix': matrix_list,
            'region_names': region_names,
            'metrics': metrics,
            'files': {
                'connectome': 'connectome.png',
                'matrix': 'connectivity_matrix.png',
                'connections': 'connection_strengths.csv'
            }
        })
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)
        # Clean up the file if it exists
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return create_response({'error': f'Error processing file: {str(e)}'}, 500)

@bp.route('/api/connectome/<filename>', methods=['GET'])
def get_connectome(filename):
    try:
        return send_file(
            os.path.join(current_app.config['UPLOAD_FOLDER'], filename),
            mimetype='image/png'
        )
    except Exception as e:
        logger.error(f"Error retrieving connectome: {str(e)}", exc_info=True)
        return create_response({'error': f'Error retrieving connectome: {str(e)}'}, 404)

@bp.route('/api/matrix/<filename>', methods=['GET'])
def get_matrix(filename):
    try:
        return send_file(
            os.path.join(current_app.config['UPLOAD_FOLDER'], filename),
            mimetype='image/png'
        )
    except Exception as e:
        logger.error(f"Error retrieving matrix: {str(e)}", exc_info=True)
        return create_response({'error': f'Error retrieving matrix: {str(e)}'}, 404)

@bp.route('/api/connections/<filename>', methods=['GET'])
def get_connections(filename):
    try:
        return send_file(
            os.path.join(current_app.config['UPLOAD_FOLDER'], filename),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Error retrieving connections: {str(e)}", exc_info=True)
        return create_response({'error': f'Error retrieving connections: {str(e)}'}, 404) 