from flask import Blueprint, request, jsonify, current_app
from core.auth import AuthManager
from core.storage import validate_session
import uuid

bp = Blueprint('auth', __name__)
auth_manager = AuthManager()

@bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create user
        result = auth_manager.create_user(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name']
        )
        
        if result['success']:
            return jsonify({
                'message': 'User created successfully',
                'user': result['user']
            }), 201
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        current_app.logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500

@bp.route('/login', methods=['POST'])
def login():
    """Login user and create session"""
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        result = auth_manager.authenticate_user(
            email=data['email'],
            password=data['password'],
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        if result['success']:
            return jsonify({
                'message': 'Login successful',
                'user': result['user'],
                'session_token': result['session_token']
            }), 200
        else:
            return jsonify({'error': result['error']}), 401
            
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@bp.route('/logout', methods=['POST'])
@validate_session
def logout():
    """Logout user and invalidate session"""
    try:
        session_token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        result = auth_manager.logout_user(session_token)
        
        if result['success']:
            return jsonify({'message': 'Logout successful'}), 200
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        return jsonify({'error': 'Logout failed'}), 500

@bp.route('/verify-session', methods=['GET'])
@validate_session
def verify_session():
    """Verify if session is valid"""
    return jsonify({
        'valid': True,
        'user': request.current_user
    }), 200

@bp.route('/refresh-token', methods=['POST'])
@validate_session
def refresh_token():
    """Refresh session token"""
    try:
        session_token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        result = auth_manager.refresh_session(session_token)
        
        if result['success']:
            return jsonify({
                'message': 'Token refreshed',
                'session_token': result['session_token']
            }), 200
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {str(e)}")
        return jsonify({'error': 'Token refresh failed'}), 500