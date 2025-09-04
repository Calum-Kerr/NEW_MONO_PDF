from flask import Blueprint, request, jsonify, current_app, send_file
from core.storage import validate_session, FileManager
from core.pdf_processor import PDFProcessor
import uuid
import os

bp = Blueprint('pdf', __name__)
file_manager = FileManager()
pdf_processor = PDFProcessor()

@bp.route('/upload', methods=['POST'])
def upload_file():
    """Upload PDF file for processing"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type and size
        if not file_manager.validate_pdf_file(file):
            return jsonify({'error': 'Invalid PDF file'}), 400
        
        # Get user info from session or create anonymous session
        user_id = None
        session_id = None
        
        auth_header = request.headers.get('Authorization')
        if auth_header:
            # Authenticated user
            # This would be validated by the @validate_session decorator
            user_id = request.current_user.get('id') if hasattr(request, 'current_user') else None
        else:
            # Anonymous user - create session
            session_id = str(uuid.uuid4())
        
        # Upload file and create job record
        result = file_manager.upload_file(
            file=file,
            user_id=user_id,
            session_id=session_id
        )
        
        if result['success']:
            return jsonify({
                'message': 'File uploaded successfully',
                'file_id': result['file_id'],
                'job_id': result['job_id']
            }), 200
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        current_app.logger.error(f"File upload error: {str(e)}")
        return jsonify({'error': 'File upload failed'}), 500

@bp.route('/merge', methods=['POST'])
def merge_pdfs():
    """Merge multiple PDF files"""
    try:
        data = request.get_json()
        
        if not data.get('file_ids') or len(data['file_ids']) < 2:
            return jsonify({'error': 'At least 2 files required for merging'}), 400
        
        result = pdf_processor.merge_pdfs(
            file_ids=data['file_ids'],
            user_id=getattr(request, 'current_user', {}).get('id'),
            session_id=data.get('session_id')
        )
        
        if result['success']:
            return jsonify({
                'message': 'PDFs merged successfully',
                'job_id': result['job_id'],
                'download_url': result['download_url']
            }), 200
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        current_app.logger.error(f"PDF merge error: {str(e)}")
        return jsonify({'error': 'PDF merge failed'}), 500

@bp.route('/split', methods=['POST'])
def split_pdf():
    """Split PDF into multiple files"""
    try:
        data = request.get_json()
        
        if not data.get('file_id'):
            return jsonify({'error': 'File ID is required'}), 400
        
        if not data.get('pages'):
            return jsonify({'error': 'Page ranges are required'}), 400
        
        result = pdf_processor.split_pdf(
            file_id=data['file_id'],
            pages=data['pages'],
            user_id=getattr(request, 'current_user', {}).get('id'),
            session_id=data.get('session_id')
        )
        
        if result['success']:
            return jsonify({
                'message': 'PDF split successfully',
                'job_id': result['job_id'],
                'download_urls': result['download_urls']
            }), 200
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        current_app.logger.error(f"PDF split error: {str(e)}")
        return jsonify({'error': 'PDF split failed'}), 500

@bp.route('/compress', methods=['POST'])
def compress_pdf():
    """Compress PDF file"""
    try:
        data = request.get_json()
        
        if not data.get('file_id'):
            return jsonify({'error': 'File ID is required'}), 400
        
        compression_level = data.get('compression_level', 'medium')
        
        result = pdf_processor.compress_pdf(
            file_id=data['file_id'],
            compression_level=compression_level,
            user_id=getattr(request, 'current_user', {}).get('id'),
            session_id=data.get('session_id')
        )
        
        if result['success']:
            return jsonify({
                'message': 'PDF compressed successfully',
                'job_id': result['job_id'],
                'download_url': result['download_url'],
                'original_size': result['original_size'],
                'compressed_size': result['compressed_size']
            }), 200
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        current_app.logger.error(f"PDF compression error: {str(e)}")
        return jsonify({'error': 'PDF compression failed'}), 500

@bp.route('/convert', methods=['POST'])
def convert_pdf():
    """Convert PDF to other formats or convert to PDF"""
    try:
        data = request.get_json()
        
        if not data.get('file_id'):
            return jsonify({'error': 'File ID is required'}), 400
        
        if not data.get('target_format'):
            return jsonify({'error': 'Target format is required'}), 400
        
        result = pdf_processor.convert_file(
            file_id=data['file_id'],
            target_format=data['target_format'],
            user_id=getattr(request, 'current_user', {}).get('id'),
            session_id=data.get('session_id')
        )
        
        if result['success']:
            return jsonify({
                'message': 'File converted successfully',
                'job_id': result['job_id'],
                'download_url': result['download_url']
            }), 200
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        current_app.logger.error(f"File conversion error: {str(e)}")
        return jsonify({'error': 'File conversion failed'}), 500

@bp.route('/job/<job_id>/status', methods=['GET'])
def get_job_status(job_id):
    """Get status of a PDF processing job"""
    try:
        result = pdf_processor.get_job_status(job_id)
        
        if result['success']:
            return jsonify({
                'job_id': job_id,
                'status': result['status'],
                'progress': result['progress'],
                'error_message': result.get('error_message'),
                'download_url': result.get('download_url')
            }), 200
        else:
            return jsonify({'error': result['error']}), 404
            
    except Exception as e:
        current_app.logger.error(f"Job status error: {str(e)}")
        return jsonify({'error': 'Failed to get job status'}), 500

@bp.route('/download/<file_id>')
def download_file(file_id):
    """Download processed file"""
    try:
        result = file_manager.get_download_file(file_id)
        
        if result['success']:
            return send_file(
                result['file_path'],
                as_attachment=True,
                download_name=result['filename']
            )
        else:
            return jsonify({'error': result['error']}), 404
            
    except Exception as e:
        current_app.logger.error(f"File download error: {str(e)}")
        return jsonify({'error': 'File download failed'}), 500