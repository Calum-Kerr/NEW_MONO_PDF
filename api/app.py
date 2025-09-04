from flask import Flask, request, jsonify, session
from flask_cors import CORS
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Enable CORS for frontend applications
CORS(app, origins=[
    'http://localhost:3000',  # Development
    'https://snackpdf.com',   # Production
    'https://revisepdf.com'   # Production
])

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_ANON_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

# Import route modules
from routes import auth_routes, pdf_routes, payment_routes, user_routes

# Register blueprints
app.register_blueprint(auth_routes.bp, url_prefix='/api/auth')
app.register_blueprint(pdf_routes.bp, url_prefix='/api/pdf')
app.register_blueprint(payment_routes.bp, url_prefix='/api/payments')
app.register_blueprint(user_routes.bp, url_prefix='/api/users')

@app.route('/api/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'message': 'NEW_MONO_PDF API is running'
    })

@app.route('/api')
def api_info():
    """API information endpoint"""
    return jsonify({
        'name': 'NEW_MONO_PDF API',
        'version': '1.0.0',
        'description': 'Backend API for SnackPDF and RevisePDF applications',
        'endpoints': {
            'auth': '/api/auth',
            'pdf': '/api/pdf',
            'payments': '/api/payments',
            'users': '/api/users'
        }
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)