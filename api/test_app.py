"""
Simple Flask API for testing without external dependencies.
"""

import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Enable CORS for cross-origin requests
CORS(app, origins=['http://localhost:3000', 'http://localhost:3001'])

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "success": True,
        "data": {
            "status": "healthy", 
            "timestamp": datetime.utcnow().isoformat()
        },
        "timestamp": datetime.utcnow().isoformat()
    })

# Debug endpoint
@app.route('/api/debug/info', methods=['GET'])
def debug_info():
    return jsonify({
        "success": True,
        "data": {
            "environment": os.getenv('FLASK_ENV', 'production'),
            "version": "1.0.0",
            "endpoints": [str(rule) for rule in app.url_map.iter_rules()]
        },
        "timestamp": datetime.utcnow().isoformat()
    })

# Mock authentication endpoints
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400
    
    return jsonify({
        "success": True,
        "data": {
            "user": {
                "id": "mock_user_id",
                "email": data.get('email')
            },
            "session": {
                "access_token": "mock_token",
                "expires_at": "2024-12-31T23:59:59Z"
            }
        },
        "message": "User registered successfully (mock)"
    })

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400
    
    return jsonify({
        "success": True,
        "data": {
            "user": {
                "id": "mock_user_id",
                "email": data.get('email')
            },
            "session": {
                "access_token": "mock_token",
                "expires_at": "2024-12-31T23:59:59Z"
            }
        },
        "message": "Login successful (mock)"
    })

# Mock file upload endpoint
@app.route('/api/files/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    return jsonify({
        "success": True,
        "data": {
            "file_id": "mock_file_id",
            "filename": file.filename,
            "file_size": len(file.read()),
            "is_pdf": file.filename.lower().endswith('.pdf'),
            "upload_url": f"https://storage.example.com/mock/{file.filename}"
        },
        "message": "File uploaded successfully (mock)"
    })

# Mock PDF processing endpoints
@app.route('/api/pdf/merge', methods=['POST'])
def merge_pdfs():
    data = request.get_json()
    if not data or 'file_urls' not in data:
        return jsonify({"error": "File URLs required"}), 400
    
    return jsonify({
        "success": True,
        "data": {
            "job_id": "mock_job_id",
            "status": "completed",
            "output_url": "https://storage.example.com/mock/merged.pdf"
        },
        "message": "PDF merge completed (mock)"
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f"🚀 Starting Flask API server on port {port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"🌐 Health check: http://localhost:{port}/health")
    print(f"📚 Debug info: http://localhost:{port}/api/debug/info")
    
    app.run(host='0.0.0.0', port=port, debug=debug)