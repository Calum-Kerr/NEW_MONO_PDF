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
    auth_manager, payment_manager, file_manager, audit_logger,
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
@auth_manager.require_auth
@log_performance("user_logout")
def logout():
    """Logout user and invalidate session."""
    try:
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else ''
        
        result = auth_manager.logout_user(token)
        
        if result['success']:
            user = auth_manager.get_current_user()
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
@auth_manager.require_auth
def get_profile():
    """Get current user profile."""
    try:
        user = auth_manager.get_current_user()
        
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
    try:
        if 'file' not in request.files:
            return create_error_response("No file provided")
        
        file = request.files['file']
        
        if file.filename == '':
            return create_error_response("No file selected")
        
        # Get user info if authenticated
        user = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            user = auth_manager.verify_session(token)
        
        user_id = user['id'] if user else None
        
        # Read file data
        file_data = file.read()
        
        # Upload file
        result = file_manager.upload_file(file_data, file.filename, user_id)
        
        if result['success']:
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

# PDF processing endpoints (placeholder for StirlingPDF integration)
@app.route('/api/pdf/merge', methods=['POST'])
@auth_manager.require_auth
@require_rate_limit(max_requests=30, window_seconds=3600)  # 30 operations per hour
@log_performance("pdf_merge")
def merge_pdfs():
    """Merge multiple PDF files."""
    try:
        data = request.get_json()
        
        if not data or 'file_urls' not in data:
            return create_error_response("File URLs required")
        
        file_urls = data['file_urls']
        
        if len(file_urls) < 2:
            return create_error_response("At least 2 files required for merging")
        
        user = auth_manager.get_current_user()
        
        # TODO: Integrate with StirlingPDF API
        # For now, return a placeholder response
        
        audit_logger.log_action(
            action="pdf_merge",
            resource_type="pdf_job",
            user_id=user['id'],
            platform="snackpdf",
            metadata={"file_count": len(file_urls)}
        )
        
        return create_success_response({
            "job_id": "placeholder_job_id",
            "status": "processing",
            "message": "PDF merge started"
        }, "Merge operation initiated")
    
    except Exception as e:
        app.logger.error(f"Merge error: {str(e)}")
        return create_error_response("Merge operation failed")

@app.route('/api/pdf/split', methods=['POST'])
@auth_manager.require_auth
@require_rate_limit(max_requests=30, window_seconds=3600)
@log_performance("pdf_split")
def split_pdf():
    """Split a PDF file."""
    try:
        data = request.get_json()
        
        if not data or 'file_url' not in data:
            return create_error_response("File URL required")
        
        file_url = data['file_url']
        split_pages = data.get('pages', [])  # Array of page ranges
        
        user = auth_manager.get_current_user()
        
        # TODO: Integrate with StirlingPDF API
        
        audit_logger.log_action(
            action="pdf_split",
            resource_type="pdf_job",
            user_id=user['id'],
            platform="snackpdf",
            metadata={"file_url": file_url, "split_pages": split_pages}
        )
        
        return create_success_response({
            "job_id": "placeholder_job_id",
            "status": "processing",
            "message": "PDF split started"
        }, "Split operation initiated")
    
    except Exception as e:
        app.logger.error(f"Split error: {str(e)}")
        return create_error_response("Split operation failed")

# Payment endpoints
@app.route('/api/payments/create-checkout', methods=['POST'])
@auth_manager.require_auth
@log_performance("create_checkout")
def create_checkout():
    """Create Stripe checkout session."""
    try:
        data = request.get_json()
        
        if not data or 'plan' not in data:
            return create_error_response("Plan required")
        
        plan = data['plan']
        success_url = data.get('success_url', 'https://snackpdf.com/success')
        cancel_url = data.get('cancel_url', 'https://snackpdf.com/pricing')
        
        user = auth_manager.get_current_user()
        
        checkout_url = payment_manager.create_checkout_session(
            user['id'], plan, success_url, cancel_url
        )
        
        if checkout_url:
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
@auth_manager.require_auth
@log_performance("create_portal")
def create_portal():
    """Create Stripe customer portal session."""
    try:
        data = request.get_json()
        return_url = data.get('return_url', 'https://snackpdf.com/account') if data else 'https://snackpdf.com/account'
        
        user = auth_manager.get_current_user()
        
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

if __name__ == '__main__':
    # Development server
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug)