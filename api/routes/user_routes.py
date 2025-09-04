from flask import Blueprint, request, jsonify, current_app
from core.storage import validate_session
from core.auth import AuthManager

bp = Blueprint('users', __name__)
auth_manager = AuthManager()

@bp.route('/profile', methods=['GET'])
@validate_session
def get_profile():
    """Get user profile information"""
    try:
        user = request.current_user
        
        # Remove sensitive information
        safe_user = {
            'id': user['id'],
            'email': user['email'],
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'avatar_url': user.get('avatar_url'),
            'subscription_status': user['subscription_status'],
            'is_verified': user['is_verified'],
            'created_at': user['created_at']
        }
        
        return jsonify({'user': safe_user}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get profile error: {str(e)}")
        return jsonify({'error': 'Failed to get profile'}), 500

@bp.route('/profile', methods=['PUT'])
@validate_session
def update_profile():
    """Update user profile information"""
    try:
        user = request.current_user
        data = request.get_json()
        
        # Define allowed fields for update
        allowed_fields = ['first_name', 'last_name', 'avatar_url']
        update_data = {}
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        result = auth_manager.update_user_profile(user['id'], update_data)
        
        if result['success']:
            return jsonify({
                'message': 'Profile updated successfully',
                'user': result['user']
            }), 200
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        current_app.logger.error(f"Update profile error: {str(e)}")
        return jsonify({'error': 'Failed to update profile'}), 500

@bp.route('/change-password', methods=['POST'])
@validate_session
def change_password():
    """Change user password"""
    try:
        user = request.current_user
        data = request.get_json()
        
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        result = auth_manager.change_password(
            user_id=user['id'],
            current_password=data['current_password'],
            new_password=data['new_password']
        )
        
        if result['success']:
            return jsonify({'message': 'Password changed successfully'}), 200
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        current_app.logger.error(f"Change password error: {str(e)}")
        return jsonify({'error': 'Failed to change password'}), 500

@bp.route('/jobs', methods=['GET'])
@validate_session
def get_user_jobs():
    """Get user's PDF processing job history"""
    try:
        user = request.current_user
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        # Limit the maximum number of results per page
        limit = min(limit, 100)
        
        result = auth_manager.get_user_jobs(
            user_id=user['id'],
            page=page,
            limit=limit
        )
        
        if result['success']:
            return jsonify({
                'jobs': result['jobs'],
                'pagination': result['pagination']
            }), 200
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        current_app.logger.error(f"Get user jobs error: {str(e)}")
        return jsonify({'error': 'Failed to get job history'}), 500

@bp.route('/delete-account', methods=['DELETE'])
@validate_session
def delete_account():
    """Delete user account and all associated data"""
    try:
        user = request.current_user
        data = request.get_json()
        
        if not data.get('password'):
            return jsonify({'error': 'Password confirmation is required'}), 400
        
        result = auth_manager.delete_user_account(
            user_id=user['id'],
            password=data['password']
        )
        
        if result['success']:
            return jsonify({'message': 'Account deleted successfully'}), 200
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        current_app.logger.error(f"Delete account error: {str(e)}")
        return jsonify({'error': 'Failed to delete account'}), 500