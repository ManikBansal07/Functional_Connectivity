from flask import Blueprint, request, jsonify, make_response, send_file
import os
import nibabel as nib
import numpy as np
from werkzeug.utils import secure_filename
import json
from datetime import datetime
from .model_processor import FunctionalConnectivityProcessor

bp = Blueprint('main', __name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
MODEL_FOLDER = 'models'
ALLOWED_EXTENSIONS = {'nii', 'nii.gz'}
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size

# Create necessary directories
for folder in [UPLOAD_FOLDER, MODEL_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Initialize processor with model path
MODEL_PATH = os.path.join(MODEL_FOLDER, 'FC_Other_Models.ipynb')
processor = FunctionalConnectivityProcessor(MODEL_PATH)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_response(data, status_code=200):
    response = jsonify(data)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, status_code

@bp.route('/api/health', methods=['GET', 'OPTIONS'])
def health_check():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', '*')
        response.headers.add('Access-Control-Allow-Methods', '*')
        return response
    
    return create_response({'status': 'healthy', 'message': 'Server is running'})

@bp.route('/api/upload', methods=['POST', 'OPTIONS'])
def upload_file():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', '*')
        response.headers.add('Access-Control-Allow-Methods', '*')
        return response

    if 'file' not in request.files:
        return create_response({'error': 'No file part'}, 400)
    
    file = request.files['file']
    if file.filename == '':
        return create_response({'error': 'No selected file'}, 400)
    
    if not allowed_file(file.filename):
        return create_response({'error': 'Invalid file type. Only NIfTI files (.nii, .nii.gz) are allowed'}, 400)

    try:
        # Create a unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = secure_filename(f"{timestamp}_{file.filename}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save the file
        file.save(filepath)
        
        # Process the NIfTI file
        connectivity_matrix, region_names, metrics = processor.process_nifti(filepath)
        
        # Convert numpy array to list for JSON serialization
        matrix_list = connectivity_matrix.tolist()
        
        return create_response({
            'message': 'File processed successfully',
            'filename': filename,
            'connectivity_matrix': matrix_list,
            'region_names': region_names,
            'metrics': metrics
        })
        
    except Exception as e:
        return create_response({'error': f'Error processing file: {str(e)}'}, 500)

@bp.route('/api/connectome/<filename>', methods=['GET'])
def get_connectome(filename):
    try:
        return send_file(
            os.path.join(UPLOAD_FOLDER, filename),
            mimetype='image/png'
        )
    except Exception as e:
        return create_response({'error': f'Error retrieving connectome: {str(e)}'}, 404) 