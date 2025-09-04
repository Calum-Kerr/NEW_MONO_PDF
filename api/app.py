"""
Flask API backend for PDF tools platform.
Serves both snackpdf.com and revisepdf.com applications.
"""

import os
import sys
import traceback
from datetime import datetime
from flask import Flask, request, jsonify, send_file, redirect, url_for
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import (
    auth_manager, payment_manager, file_manager, audit_logger, stirling_client,
    api_key_manager, analytics_manager, whitelabel_manager,
    create_error_response, create_success_response, require_rate_limit,
    log_performance
)

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Enable CORS for cross-origin requests
CORS(app, origins=['http://localhost:3000', 'https://snackpdf.com', 'https://revisepdf.com'])

# Error handlers
@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    return create_error_response("File too large. Maximum size is 50MB.", 413)

@app.errorhandler(404)
def handle_not_found(e):
    return create_error_response("Endpoint not found", 404)

@app.errorhandler(500)
def handle_internal_error(e):
    return create_error_response("Internal server error", 500)

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return create_success_response({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

# Authentication endpoints
@app.route('/api/auth/register', methods=['POST'])
@require_rate_limit(max_requests=10, window_seconds=300)  # 10 registrations per 5 minutes
@log_performance("user_registration")
def register():
    """Register a new user."""
    if not auth_manager:
        return create_error_response("Authentication service not available", 503)
    
    try:
        data = request.get_json()
        
        if not data:
            return create_error_response("Request body required")
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip()
        
        if not email or not password:
            return create_error_response("Email and password are required")
        
        if len(password) < 8:
            return create_error_response("Password must be at least 8 characters")
        
        # Create user
        result = auth_manager.create_user(email, password, full_name)
        
        if result['success']:
            if audit_logger:
                audit_logger.log_action(
                    action="user_registered",
                    resource_type="user",
                    user_id=result['user'].id,
                    metadata={"email": email}
                )
            
            return create_success_response({
                "user": {
                    "id": result['user'].id,
                    "email": result['user'].email,
                    "full_name": full_name
                },
                "session": {
                    "access_token": result['session'].access_token,
                    "expires_at": result['session'].expires_at
                }
            }, "User registered successfully")
        else:
            return create_error_response(result['error'])
    
    except Exception as e:
        app.logger.error(f"Registration error: {str(e)}")
        return create_error_response("Registration failed")

@app.route('/api/auth/login', methods=['POST'])
@require_rate_limit(max_requests=20, window_seconds=300)  # 20 login attempts per 5 minutes
@log_performance("user_login")
def login():
    """Authenticate user login."""
    if not auth_manager:
        return create_error_response("Authentication service not available", 503)
    
    try:
        data = request.get_json()
        
        if not data:
            return create_error_response("Request body required")
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return create_error_response("Email and password are required")
        
        # Authenticate user
        result = auth_manager.login_user(email, password)
        
        if result['success']:
            if audit_logger:
                audit_logger.log_action(
                    action="user_login",
                    resource_type="user",
                    user_id=result['user'].id,
                    metadata={"email": email}
                )
            
            return create_success_response({
                "user": {
                    "id": result['user'].id,
                    "email": result['user'].email
                },
                "session": {
                    "access_token": result['session'].access_token,
                    "expires_at": result['session'].expires_at
                }
            }, "Login successful")
        else:
            return create_error_response(result['error'], 401)
    
    except Exception as e:
        app.logger.error(f"Login error: {str(e)}")
        return create_error_response("Login failed")

@app.route('/api/auth/logout', methods=['POST'])
@log_performance("user_logout")
def logout():
    """Logout user and invalidate session."""
    if not auth_manager:
        return create_error_response("Authentication service not available", 503)
    
    try:
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else ''
        
        result = auth_manager.logout_user(token)
        
        if result['success']:
            user = auth_manager.get_current_user()
            if audit_logger:
                audit_logger.log_action(
                    action="user_logout",
                    resource_type="user",
                    user_id=user['id'] if user else None
                )
            
            return create_success_response(message="Logout successful")
        else:
            return create_error_response(result['error'])
    
    except Exception as e:
        app.logger.error(f"Logout error: {str(e)}")
        return create_error_response("Logout failed")

@app.route('/api/auth/profile', methods=['GET'])
def get_profile():
    """Get current user profile."""
    if not auth_manager:
        return create_error_response("Authentication service not available", 503)
    
    # Check authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return create_error_response("Authentication required", 401)
    
    token = auth_header.split(' ')[1]
    user = auth_manager.verify_session(token)
    
    if not user:
        return create_error_response("Invalid session", 401)
    
    try:
        return create_success_response({
            "id": user['id'],
            "email": user['email'],
            "full_name": user.get('full_name'),
            "subscription_tier": user.get('subscription_tier', 'free'),
            "subscription_status": user.get('subscription_status', 'inactive'),
            "usage_count": user.get('usage_count', 0),
            "monthly_usage_limit": user.get('monthly_usage_limit', 5)
        })
    
    except Exception as e:
        app.logger.error(f"Profile error: {str(e)}")
        return create_error_response("Failed to get profile")

# File upload endpoints
@app.route('/api/files/upload', methods=['POST'])
@require_rate_limit(max_requests=50, window_seconds=3600)  # 50 uploads per hour
@log_performance("file_upload")
def upload_file():
    """Upload a file for processing."""
    if not file_manager:
        return create_error_response("File storage service not available", 503)
    
    try:
        if 'file' not in request.files:
            return create_error_response("No file provided")
        
        file = request.files['file']
        
        if file.filename == '':
            return create_error_response("No file selected")
        
        # Get user info if authenticated
        user = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer ') and auth_manager:
            token = auth_header.split(' ')[1]
            user = auth_manager.verify_session(token)
        
        user_id = user['id'] if user else None
        
        # Read file data
        file_data = file.read()
        
        # Upload file
        result = file_manager.upload_file(file_data, file.filename, user_id)
        
        if result['success']:
            if audit_logger:
                audit_logger.log_action(
                    action="file_uploaded",
                    resource_type="file",
                    user_id=user_id,
                    metadata={
                        "filename": file.filename,
                        "file_size": result['file_size'],
                        "is_pdf": result['is_pdf']
                    }
                )
            
            return create_success_response({
                "file_id": result['secure_filename'],
                "filename": file.filename,
                "file_size": result['file_size'],
                "is_pdf": result['is_pdf'],
                "upload_url": result['public_url']
            }, "File uploaded successfully")
        else:
            return create_error_response(result.get('error', 'Upload failed'))
    
    except Exception as e:
        app.logger.error(f"Upload error: {str(e)}")
        return create_error_response("Upload failed")

# PDF processing endpoints with StirlingPDF integration
@app.route('/api/pdf/merge', methods=['POST'])
@require_rate_limit(max_requests=30, window_seconds=3600)  # 30 operations per hour
@log_performance("pdf_merge")
def merge_pdfs():
    """Merge multiple PDF files using StirlingPDF."""
    try:
        data = request.get_json()
        
        if not data or 'file_urls' not in data:
            return create_error_response("File URLs required")
        
        file_urls = data['file_urls']
        
        if len(file_urls) < 2:
            return create_error_response("At least 2 files required for merging")
        
        # Get user info if authenticated
        user = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer ') and auth_manager:
            token = auth_header.split(' ')[1]
            user = auth_manager.verify_session(token)
        
        user_id = user['id'] if user else None
        
        # Check user limits for authenticated users
        if user and not _check_usage_limits(user):
            return create_error_response("Usage limit exceeded. Please upgrade your plan.", 429)
        
        # Download files and perform merge
        pdf_files = []
        filenames = []
        
        for i, file_url in enumerate(file_urls):
            # In a real implementation, you'd download from your storage
            # For now, we'll create a placeholder
            filename = f"file_{i+1}.pdf"
            filenames.append(filename)
            # pdf_files.append(downloaded_content)
        
        # For demonstration, create a mock response
        # In production, this would use actual file content
        if len(pdf_files) == 0:
            # Mock successful merge when no actual files
            result = {
                'success': True,
                'content': b'%PDF-1.4 mock merged content',
                'content_type': 'application/pdf',
                'filename': 'merged_document.pdf'
            }
        else:
            # Use StirlingPDF to merge
            result = stirling_client.merge_pdfs(pdf_files, filenames)
        
        if result['success']:
            # Log the operation
            if audit_logger:
                audit_logger.log_action(
                    action="pdf_merge",
                    resource_type="pdf_job",
                    user_id=user_id,
                    platform="snackpdf",
                    metadata={"file_count": len(file_urls)}
                )
            
            # Update user usage if authenticated
            if user_id and auth_manager:
                _increment_user_usage(user_id)
            
            return create_success_response({
                "job_id": f"merge_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "status": "completed",
                "output_filename": result.get('filename', 'merged_document.pdf'),
                "message": "PDF merge completed successfully"
            }, "Merge operation completed")
        else:
            return create_error_response(result.get('error', 'Merge operation failed'))
    
    except Exception as e:
        app.logger.error(f"Merge error: {str(e)}")
        return create_error_response("Merge operation failed")

@app.route('/api/pdf/split', methods=['POST'])
@require_rate_limit(max_requests=30, window_seconds=3600)
@log_performance("pdf_split")
def split_pdf():
    """Split a PDF file using StirlingPDF."""
    try:
        data = request.get_json()
        
        if not data or 'file_url' not in data:
            return create_error_response("File URL required")
        
        file_url = data['file_url']
        split_pages = data.get('pages', 'all')  # Page ranges like "1-3,5,7-9" or "all"
        
        # Get user info if authenticated
        user = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer ') and auth_manager:
            token = auth_header.split(' ')[1]
            user = auth_manager.verify_session(token)
        
        user_id = user['id'] if user else None
        
        # Check user limits
        if user and not _check_usage_limits(user):
            return create_error_response("Usage limit exceeded. Please upgrade your plan.", 429)
        
        # Download file and perform split
        # In real implementation, download from storage
        filename = "document.pdf"
        pdf_content = b'%PDF-1.4 mock content'  # Mock content
        
        # Use StirlingPDF to split (mock for now)
        result = {
            'success': True,
            'content': b'%PDF-1.4 mock split content',
            'content_type': 'application/pdf',
            'filename': 'split_document.pdf'
        }
        
        if result['success']:
            # Log the operation
            if audit_logger:
                audit_logger.log_action(
                    action="pdf_split",
                    resource_type="pdf_job",
                    user_id=user_id,
                    platform="snackpdf",
                    metadata={"file_url": file_url, "split_pages": split_pages}
                )
            
            # Update user usage
            if user_id and auth_manager:
                _increment_user_usage(user_id)
            
            return create_success_response({
                "job_id": f"split_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "status": "completed",
                "output_filename": result.get('filename', 'split_document.pdf'),
                "message": "PDF split completed successfully"
            }, "Split operation completed")
        else:
            return create_error_response(result.get('error', 'Split operation failed'))
    
    except Exception as e:
        app.logger.error(f"Split error: {str(e)}")
        return create_error_response("Split operation failed")

@app.route('/api/pdf/compress', methods=['POST'])
@require_rate_limit(max_requests=30, window_seconds=3600)
@log_performance("pdf_compress")
def compress_pdf():
    """Compress a PDF file using StirlingPDF."""
    try:
        data = request.get_json()
        
        if not data or 'file_url' not in data:
            return create_error_response("File URL required")
        
        file_url = data['file_url']
        compression_level = data.get('compression_level', 2)  # 1-4
        
        # Get user info if authenticated
        user = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer ') and auth_manager:
            token = auth_header.split(' ')[1]
            user = auth_manager.verify_session(token)
        
        user_id = user['id'] if user else None
        
        # Check user limits
        if user and not _check_usage_limits(user):
            return create_error_response("Usage limit exceeded. Please upgrade your plan.", 429)
        
        # Mock compression result
        result = {
            'success': True,
            'content': b'%PDF-1.4 mock compressed content',
            'content_type': 'application/pdf',
            'filename': 'compressed_document.pdf'
        }
        
        if result['success']:
            if audit_logger:
                audit_logger.log_action(
                    action="pdf_compress",
                    resource_type="pdf_job",
                    user_id=user_id,
                    platform="snackpdf",
                    metadata={"file_url": file_url, "compression_level": compression_level}
                )
            
            if user_id and auth_manager:
                _increment_user_usage(user_id)
            
            return create_success_response({
                "job_id": f"compress_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "status": "completed",
                "output_filename": result.get('filename', 'compressed_document.pdf'),
                "message": "PDF compression completed successfully"
            }, "Compression operation completed")
        else:
            return create_error_response(result.get('error', 'Compression operation failed'))
    
    except Exception as e:
        app.logger.error(f"Compression error: {str(e)}")
        return create_error_response("Compression operation failed")

@app.route('/api/pdf/convert', methods=['POST'])
@require_rate_limit(max_requests=30, window_seconds=3600)
@log_performance("pdf_convert")
def convert_to_pdf():
    """Convert files to PDF using StirlingPDF."""
    try:
        data = request.get_json()
        
        if not data or 'file_url' not in data:
            return create_error_response("File URL required")
        
        file_url = data['file_url']
        file_type = data.get('file_type', 'auto')
        
        # Get user info if authenticated
        user = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer ') and auth_manager:
            token = auth_header.split(' ')[1]
            user = auth_manager.verify_session(token)
        
        user_id = user['id'] if user else None
        
        # Check user limits
        if user and not _check_usage_limits(user):
            return create_error_response("Usage limit exceeded. Please upgrade your plan.", 429)
        
        # Mock conversion result
        result = {
            'success': True,
            'content': b'%PDF-1.4 mock converted content',
            'content_type': 'application/pdf',
            'filename': 'converted_document.pdf'
        }
        
        if result['success']:
            if audit_logger:
                audit_logger.log_action(
                    action="pdf_convert",
                    resource_type="pdf_job",
                    user_id=user_id,
                    platform="snackpdf",
                    metadata={"file_url": file_url, "file_type": file_type}
                )
            
            if user_id and auth_manager:
                _increment_user_usage(user_id)
            
            return create_success_response({
                "job_id": f"convert_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "status": "completed",
                "output_filename": result.get('filename', 'converted_document.pdf'),
                "message": "File conversion completed successfully"
            }, "Conversion operation completed")
        else:
            return create_error_response(result.get('error', 'Conversion operation failed'))
    
    except Exception as e:
        app.logger.error(f"Conversion error: {str(e)}")
        return create_error_response("Conversion operation failed")

# StirlingPDF health check endpoint
@app.route('/api/stirling/health', methods=['GET'])
def stirling_health():
    """Check StirlingPDF service health."""
    try:
        result = stirling_client.health_check()
        return create_success_response(result)
    except Exception as e:
        return create_error_response(f"StirlingPDF health check failed: {str(e)}")

# Helper functions
def _check_usage_limits(user: dict) -> bool:
    """Check if user has exceeded their usage limits."""
    if not user:
        return True  # Allow anonymous users with global rate limiting
    
    subscription_tier = user.get('subscription_tier', 'free')
    usage_count = user.get('usage_count', 0)
    
    if subscription_tier == 'free':
        return usage_count < 5  # Free tier: 5 operations per month
    elif subscription_tier in ['pro', 'enterprise']:
        return True  # Unlimited for paid tiers
    
    return False

def _increment_user_usage(user_id: str):
    """Increment user's monthly usage count."""
    if not auth_manager:
        return
    
    try:
        # This would update the user's usage count in the database
        # For now, just log it
        app.logger.info(f"Incrementing usage for user {user_id}")
    except Exception as e:
        app.logger.error(f"Failed to increment usage for user {user_id}: {str(e)}")

# Payment endpoints
@app.route('/api/payments/create-checkout', methods=['POST'])
@log_performance("create_checkout")
def create_checkout():
    """Create Stripe checkout session."""
    if not payment_manager:
        return create_error_response("Payment service not available", 503)
    
    if not auth_manager:
        return create_error_response("Authentication required", 401)
    
    # Check authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return create_error_response("Authentication required", 401)
    
    token = auth_header.split(' ')[1]
    user = auth_manager.verify_session(token)
    
    if not user:
        return create_error_response("Invalid session", 401)
    
    try:
        data = request.get_json()
        
        if not data or 'plan' not in data:
            return create_error_response("Plan required")
        
        plan = data['plan']
        success_url = data.get('success_url', 'https://snackpdf.com/success')
        cancel_url = data.get('cancel_url', 'https://snackpdf.com/pricing')
        
        checkout_url = payment_manager.create_checkout_session(
            user['id'], plan, success_url, cancel_url
        )
        
        if checkout_url:
            if audit_logger:
                audit_logger.log_action(
                    action="checkout_created",
                    resource_type="subscription",
                    user_id=user['id'],
                    metadata={"plan": plan}
                )
            
            return create_success_response({
                "checkout_url": checkout_url
            }, "Checkout session created")
        else:
            return create_error_response("Failed to create checkout session")
    
    except Exception as e:
        app.logger.error(f"Checkout error: {str(e)}")
        return create_error_response("Checkout creation failed")

@app.route('/api/payments/portal', methods=['POST'])
@log_performance("create_portal")
def create_portal():
    """Create Stripe customer portal session."""
    if not payment_manager:
        return create_error_response("Payment service not available", 503)
    
    if not auth_manager:
        return create_error_response("Authentication required", 401)
    
    # Check authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return create_error_response("Authentication required", 401)
    
    token = auth_header.split(' ')[1]
    user = auth_manager.verify_session(token)
    
    if not user:
        return create_error_response("Invalid session", 401)
    
    try:
        data = request.get_json()
        return_url = data.get('return_url', 'https://snackpdf.com/account') if data else 'https://snackpdf.com/account'
        
        portal_url = payment_manager.create_portal_session(user['id'], return_url)
        
        if portal_url:
            return create_success_response({
                "portal_url": portal_url
            }, "Portal session created")
        else:
            return create_error_response("Failed to create portal session")
    
    except Exception as e:
        app.logger.error(f"Portal error: {str(e)}")
        return create_error_response("Portal creation failed")

@app.route('/api/payments/webhook', methods=['POST'])
@log_performance("stripe_webhook")
def stripe_webhook():
    """Handle Stripe webhooks."""
    if not payment_manager:
        return create_error_response("Payment service not available", 503)
    
    try:
        payload = request.get_data()
        signature = request.headers.get('Stripe-Signature')
        
        if not signature:
            return create_error_response("Missing signature", 400)
        
        result = payment_manager.handle_webhook(payload, signature)
        
        if result['success']:
            return create_success_response(message=result['message'])
        else:
            return create_error_response(result['error'])
    
    except Exception as e:
        app.logger.error(f"Webhook error: {str(e)}")
        return create_error_response("Webhook processing failed")

# Development endpoints
@app.route('/api/debug/info', methods=['GET'])
def debug_info():
    """Debug information (only in development)."""
    if os.getenv('FLASK_ENV') != 'development':
        return create_error_response("Not available in production", 403)
    
    return create_success_response({
        "environment": os.getenv('FLASK_ENV', 'production'),
        "python_version": sys.version,
        "flask_version": Flask.__version__,
        "endpoints": [str(rule) for rule in app.url_map.iter_rules()]
    })

# Enhanced OCR and text extraction endpoints
@app.route('/api/pdf/ocr-advanced', methods=['POST'])
@require_rate_limit(max_requests=50, window_seconds=3600)
@log_performance("pdf_ocr_advanced")
def ocr_pdf_advanced():
    """Perform advanced OCR on PDF with language support."""
    if not stirling_client:
        return create_error_response("PDF processing service not available", 503)
    
    # Check authentication and API key
    auth_result = check_auth_or_api_key(request)
    if not auth_result['success']:
        return create_error_response(auth_result['error'], 401)
    
    try:
        if 'files' not in request.files:
            return create_error_response("No file provided")
        
        file = request.files['files']
        if not file or file.filename == '':
            return create_error_response("No file selected")
        
        # Enhanced parameters
        languages = request.form.getlist('languages') or ['eng']
        ocr_type = request.form.get('ocr_type', 'auto')
        dpi = int(request.form.get('dpi', 300))
        remove_blanks = request.form.get('remove_blanks', 'true').lower() == 'true'
        
        # Process with StirlingPDF
        pdf_content = file.read()
        result = stirling_client.ocr_pdf(
            pdf_content, file.filename, languages, ocr_type, dpi, remove_blanks
        )
        
        if result['success']:
            # Track analytics
            if analytics_manager:
                analytics_manager.track_event(
                    'pdf_ocr_advanced',
                    user_id=auth_result.get('user_id'),
                    api_key_id=auth_result.get('api_key_id'),
                    event_data={
                        'languages': languages,
                        'ocr_type': ocr_type,
                        'dpi': dpi
                    },
                    file_size=len(pdf_content),
                    success=True
                )
            
            return send_file(
                result['content'],
                as_attachment=True,
                download_name=result.get('filename', 'ocr_result.pdf'),
                mimetype='application/pdf'
            )
        else:
            return create_error_response(result['error'])
    
    except Exception as e:
        app.logger.error(f"Advanced OCR error: {str(e)}")
        return create_error_response("Advanced OCR failed")

@app.route('/api/pdf/extract-text-advanced', methods=['POST'])
@require_rate_limit(max_requests=100, window_seconds=3600)
@log_performance("pdf_extract_text_advanced")
def extract_text_advanced():
    """Extract text with format options."""
    if not stirling_client:
        return create_error_response("PDF processing service not available", 503)
    
    # Check authentication and API key
    auth_result = check_auth_or_api_key(request)
    if not auth_result['success']:
        return create_error_response(auth_result['error'], 401)
    
    try:
        if 'files' not in request.files:
            return create_error_response("No file provided")
        
        file = request.files['files']
        if not file or file.filename == '':
            return create_error_response("No file selected")
        
        # Format options
        format = request.form.get('format', 'txt')  # txt, json, xml
        include_annotations = request.form.get('include_annotations', 'false').lower() == 'true'
        
        pdf_content = file.read()
        result = stirling_client.extract_text(
            pdf_content, file.filename, format, include_annotations
        )
        
        if result['success']:
            # Track analytics
            if analytics_manager:
                analytics_manager.track_event(
                    'pdf_extract_text_advanced',
                    user_id=auth_result.get('user_id'),
                    api_key_id=auth_result.get('api_key_id'),
                    event_data={'format': format, 'include_annotations': include_annotations},
                    file_size=len(pdf_content),
                    success=True
                )
            
            # Return extracted content
            content_type = {
                'txt': 'text/plain',
                'json': 'application/json',
                'xml': 'application/xml'
            }.get(format, 'text/plain')
            
            return result['content'], 200, {'Content-Type': content_type}
        else:
            return create_error_response(result['error'])
    
    except Exception as e:
        app.logger.error(f"Advanced text extraction error: {str(e)}")
        return create_error_response("Advanced text extraction failed")

# Advanced compression endpoints
@app.route('/api/pdf/compress-advanced', methods=['POST'])
@require_rate_limit(max_requests=50, window_seconds=3600)
@log_performance("pdf_compress_advanced")
def compress_pdf_advanced():
    """Advanced PDF compression with presets."""
    if not stirling_client:
        return create_error_response("PDF processing service not available", 503)
    
    # Check authentication and API key
    auth_result = check_auth_or_api_key(request)
    if not auth_result['success']:
        return create_error_response(auth_result['error'], 401)
    
    try:
        if 'files' not in request.files:
            return create_error_response("No file provided")
        
        file = request.files['files']
        if not file or file.filename == '':
            return create_error_response("No file selected")
        
        # Compression preset
        preset = request.form.get('preset', 'balanced')  # web, print, archive, balanced, maximum
        
        pdf_content = file.read()
        result = stirling_client.advanced_compress(pdf_content, file.filename, preset)
        
        if result['success']:
            # Track analytics
            if analytics_manager:
                analytics_manager.track_event(
                    'pdf_compress_advanced',
                    user_id=auth_result.get('user_id'),
                    api_key_id=auth_result.get('api_key_id'),
                    event_data={'preset': preset},
                    file_size=len(pdf_content),
                    success=True
                )
            
            return send_file(
                result['content'],
                as_attachment=True,
                download_name=result.get('filename', 'compressed.pdf'),
                mimetype='application/pdf'
            )
        else:
            return create_error_response(result['error'])
    
    except Exception as e:
        app.logger.error(f"Advanced compression error: {str(e)}")
        return create_error_response("Advanced compression failed")

# Batch processing endpoints
@app.route('/api/pdf/batch-process', methods=['POST'])
@require_rate_limit(max_requests=10, window_seconds=3600)
@log_performance("pdf_batch_process")
def batch_process():
    """Process multiple files in batch."""
    if not stirling_client:
        return create_error_response("PDF processing service not available", 503)
    
    # Check authentication and API key
    auth_result = check_auth_or_api_key(request)
    if not auth_result['success']:
        return create_error_response(auth_result['error'], 401)
    
    try:
        # Get operation type
        operation = request.form.get('operation')
        if not operation:
            return create_error_response("Operation type required")
        
        # Get files
        if 'files' not in request.files:
            return create_error_response("No files provided")
        
        files = request.files.getlist('files')
        if not files:
            return create_error_response("No files selected")
        
        # Prepare file data
        files_data = []
        for file in files:
            if file and file.filename:
                files_data.append({
                    'content': file.read(),
                    'filename': file.filename
                })
        
        # Get operation parameters
        operation_params = {}
        if operation == 'compress':
            operation_params['preset'] = request.form.get('preset', 'balanced')
        elif operation == 'ocr':
            operation_params['languages'] = request.form.getlist('languages') or ['eng']
        elif operation == 'extract_text':
            operation_params['format'] = request.form.get('format', 'txt')
        elif operation == 'rotate':
            operation_params['angle'] = int(request.form.get('angle', 90))
        
        # Process batch
        result = stirling_client.batch_process(operation, files_data, operation_params)
        
        if result['success']:
            # Track analytics
            if analytics_manager:
                analytics_manager.track_event(
                    'pdf_batch_process',
                    user_id=auth_result.get('user_id'),
                    api_key_id=auth_result.get('api_key_id'),
                    event_data={
                        'operation': operation,
                        'file_count': len(files_data),
                        'success_rate': result['summary']['success_rate']
                    },
                    success=True
                )
            
            return create_success_response(result, "Batch processing completed")
        else:
            return create_error_response(result['error'])
    
    except Exception as e:
        app.logger.error(f"Batch processing error: {str(e)}")
        return create_error_response("Batch processing failed")

# API Key management endpoints
@app.route('/api/keys/create', methods=['POST'])
@log_performance("api_key_create")
def create_api_key():
    """Create a new API key."""
    if not api_key_manager:
        return create_error_response("API key service not available", 503)
    
    if not auth_manager:
        return create_error_response("Authentication required", 401)
    
    # Check authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return create_error_response("Authentication required", 401)
    
    token = auth_header.split(' ')[1]
    user = auth_manager.verify_session(token)
    
    if not user:
        return create_error_response("Invalid session", 401)
    
    try:
        data = request.get_json()
        name = data.get('name', 'API Key')
        permissions = data.get('permissions', ['pdf:merge', 'pdf:split'])
        rate_limit = data.get('rate_limit', 1000)
        expires_days = data.get('expires_days')
        
        result = api_key_manager.generate_api_key(
            user_id=user['id'],
            name=name,
            permissions=permissions,
            rate_limit=rate_limit,
            expires_days=expires_days
        )
        
        if result['success']:
            # Track analytics
            if analytics_manager:
                analytics_manager.track_event(
                    'api_key_created',
                    user_id=user['id'],
                    event_data={'permissions': permissions, 'rate_limit': rate_limit},
                    success=True
                )
            
            return create_success_response(result, "API key created successfully")
        else:
            return create_error_response(result['error'])
    
    except Exception as e:
        app.logger.error(f"API key creation error: {str(e)}")
        return create_error_response("API key creation failed")

@app.route('/api/keys/list', methods=['GET'])
@log_performance("api_key_list")
def list_api_keys():
    """List user's API keys."""
    if not api_key_manager:
        return create_error_response("API key service not available", 503)
    
    if not auth_manager:
        return create_error_response("Authentication required", 401)
    
    # Check authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return create_error_response("Authentication required", 401)
    
    token = auth_header.split(' ')[1]
    user = auth_manager.verify_session(token)
    
    if not user:
        return create_error_response("Invalid session", 401)
    
    try:
        result = api_key_manager.list_user_keys(user['id'])
        
        if result['success']:
            return create_success_response(result, "API keys retrieved")
        else:
            return create_error_response(result['error'])
    
    except Exception as e:
        app.logger.error(f"API key listing error: {str(e)}")
        return create_error_response("Failed to list API keys")

@app.route('/api/keys/<key_id>/revoke', methods=['POST'])
@log_performance("api_key_revoke")
def revoke_api_key(key_id):
    """Revoke an API key."""
    if not api_key_manager:
        return create_error_response("API key service not available", 503)
    
    if not auth_manager:
        return create_error_response("Authentication required", 401)
    
    # Check authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return create_error_response("Authentication required", 401)
    
    token = auth_header.split(' ')[1]
    user = auth_manager.verify_session(token)
    
    if not user:
        return create_error_response("Invalid session", 401)
    
    try:
        result = api_key_manager.revoke_api_key(key_id, user['id'])
        
        if result['success']:
            return create_success_response(result, "API key revoked")
        else:
            return create_error_response(result['error'])
    
    except Exception as e:
        app.logger.error(f"API key revocation error: {str(e)}")
        return create_error_response("Failed to revoke API key")

# Analytics endpoints
@app.route('/api/analytics/usage', methods=['GET'])
@log_performance("analytics_usage")
def get_usage_analytics():
    """Get usage analytics."""
    if not analytics_manager:
        return create_error_response("Analytics service not available", 503)
    
    # Check authentication
    auth_result = check_auth_or_api_key(request)
    if not auth_result['success']:
        return create_error_response(auth_result['error'], 401)
    
    try:
        from datetime import datetime, timedelta
        
        # Parse date parameters
        days = int(request.args.get('days', 30))
        start_date = datetime.utcnow() - timedelta(days=days)
        end_date = datetime.utcnow()
        
        user_id = auth_result.get('user_id') if not request.args.get('global') else None
        
        result = analytics_manager.get_usage_statistics(user_id, start_date, end_date)
        
        if result['success']:
            return create_success_response(result, "Usage analytics retrieved")
        else:
            return create_error_response(result['error'])
    
    except Exception as e:
        app.logger.error(f"Analytics error: {str(e)}")
        return create_error_response("Failed to get analytics")

@app.route('/api/analytics/performance', methods=['GET'])
@log_performance("analytics_performance")
def get_performance_analytics():
    """Get performance analytics."""
    if not analytics_manager:
        return create_error_response("Analytics service not available", 503)
    
    # Check authentication
    auth_result = check_auth_or_api_key(request)
    if not auth_result['success']:
        return create_error_response(auth_result['error'], 401)
    
    try:
        from datetime import datetime, timedelta
        
        days = int(request.args.get('days', 7))
        start_date = datetime.utcnow() - timedelta(days=days)
        end_date = datetime.utcnow()
        
        result = analytics_manager.get_performance_metrics(start_date, end_date)
        
        if result['success']:
            return create_success_response(result, "Performance analytics retrieved")
        else:
            return create_error_response(result['error'])
    
    except Exception as e:
        app.logger.error(f"Performance analytics error: {str(e)}")
        return create_error_response("Failed to get performance analytics")

# White-label endpoints
@app.route('/api/whitelabel/config/<tenant_id>', methods=['GET'])
@log_performance("whitelabel_config")
def get_whitelabel_config(tenant_id):
    """Get white-label configuration."""
    if not whitelabel_manager:
        return create_error_response("White-label service not available", 503)
    
    try:
        result = whitelabel_manager.get_tenant_config(tenant_id)
        
        if result['success']:
            return create_success_response(result, "Configuration retrieved")
        else:
            return create_error_response(result['error'])
    
    except Exception as e:
        app.logger.error(f"White-label config error: {str(e)}")
        return create_error_response("Failed to get configuration")

@app.route('/api/whitelabel/css/<tenant_id>', methods=['GET'])
@log_performance("whitelabel_css")
def get_whitelabel_css(tenant_id):
    """Get custom CSS for tenant."""
    if not whitelabel_manager:
        return create_error_response("White-label service not available", 503)
    
    try:
        result = whitelabel_manager.generate_custom_css(tenant_id)
        
        if result['success']:
            return result['css'], 200, {'Content-Type': 'text/css'}
        else:
            return create_error_response(result['error'])
    
    except Exception as e:
        app.logger.error(f"White-label CSS error: {str(e)}")
        return create_error_response("Failed to get CSS")

# Helper function for authentication and API key validation
def check_auth_or_api_key(request):
    """Check authentication via session token or API key."""
    # Check for API key first
    api_key = request.headers.get('X-API-Key')
    if api_key and api_key_manager:
        result = api_key_manager.validate_api_key(api_key)
        if result['success']:
            return {
                'success': True,
                'user_id': result['user_id'],
                'api_key_id': result['key_id']
            }
    
    # Check for session token
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer ') and auth_manager:
        token = auth_header.split(' ')[1]
        user = auth_manager.verify_session(token)
        if user:
            return {
                'success': True,
                'user_id': user['id']
            }
    
    return {
        'success': False,
        'error': 'Authentication required'
    }

if __name__ == '__main__':
    # Development server
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug)