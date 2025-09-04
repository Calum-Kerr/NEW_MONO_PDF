import bcrypt
import uuid
import jwt
from datetime import datetime, timedelta
from supabase import create_client, Client
import os
from functools import wraps
from flask import request, jsonify

class AuthManager:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.jwt_secret = os.getenv('JWT_SECRET', 'your-jwt-secret-key')

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def create_user(self, email: str, password: str, first_name: str, last_name: str):
        """Create a new user account"""
        try:
            # Check if user already exists
            existing_user = self.supabase.table('users').select('id').eq('email', email).execute()
            if existing_user.data:
                return {'success': False, 'error': 'User with this email already exists'}

            # Hash password
            password_hash = self.hash_password(password)

            # Create user
            user_data = {
                'email': email,
                'password_hash': password_hash,
                'first_name': first_name,
                'last_name': last_name,
                'subscription_status': 'free',
                'is_verified': False
            }

            result = self.supabase.table('users').insert(user_data).execute()
            
            if result.data:
                user = result.data[0]
                # Remove password hash from response
                user.pop('password_hash', None)
                return {'success': True, 'user': user}
            else:
                return {'success': False, 'error': 'Failed to create user'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def authenticate_user(self, email: str, password: str, ip_address: str = None, user_agent: str = None):
        """Authenticate user and create session"""
        try:
            # Get user by email
            user_result = self.supabase.table('users').select('*').eq('email', email).execute()
            
            if not user_result.data:
                return {'success': False, 'error': 'Invalid email or password'}

            user = user_result.data[0]

            # Verify password
            if not self.verify_password(password, user['password_hash']):
                return {'success': False, 'error': 'Invalid email or password'}

            # Create session token
            session_token = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(days=30)

            session_data = {
                'user_id': user['id'],
                'session_token': session_token,
                'expires_at': expires_at.isoformat(),
                'ip_address': ip_address,
                'user_agent': user_agent
            }

            session_result = self.supabase.table('sessions').insert(session_data).execute()

            if session_result.data:
                # Remove password hash from user data
                user.pop('password_hash', None)
                
                # Log authentication event
                self.log_audit_event(
                    user_id=user['id'],
                    action='login',
                    ip_address=ip_address,
                    user_agent=user_agent
                )

                return {
                    'success': True, 
                    'user': user, 
                    'session_token': session_token
                }
            else:
                return {'success': False, 'error': 'Failed to create session'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def validate_session(self, session_token: str):
        """Validate session token and return user data"""
        try:
            # Get session with user data
            session_result = self.supabase.table('sessions').select(
                '*, users(*)'
            ).eq('session_token', session_token).gt(
                'expires_at', datetime.utcnow().isoformat()
            ).execute()

            if session_result.data:
                session = session_result.data[0]
                user = session['users']
                user.pop('password_hash', None)
                return {'success': True, 'user': user}
            else:
                return {'success': False, 'error': 'Invalid or expired session'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def logout_user(self, session_token: str):
        """Logout user by invalidating session"""
        try:
            # Delete session
            result = self.supabase.table('sessions').delete().eq(
                'session_token', session_token
            ).execute()

            return {'success': True}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def refresh_session(self, session_token: str):
        """Refresh session token"""
        try:
            # Get current session
            session_result = self.supabase.table('sessions').select('*').eq(
                'session_token', session_token
            ).execute()

            if not session_result.data:
                return {'success': False, 'error': 'Session not found'}

            session = session_result.data[0]

            # Create new session token
            new_token = str(uuid.uuid4())
            new_expires_at = datetime.utcnow() + timedelta(days=30)

            # Update session
            update_result = self.supabase.table('sessions').update({
                'session_token': new_token,
                'expires_at': new_expires_at.isoformat()
            }).eq('session_token', session_token).execute()

            if update_result.data:
                return {'success': True, 'session_token': new_token}
            else:
                return {'success': False, 'error': 'Failed to refresh session'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_user_profile(self, user_id: str, update_data: dict):
        """Update user profile information"""
        try:
            result = self.supabase.table('users').update(update_data).eq(
                'id', user_id
            ).execute()

            if result.data:
                user = result.data[0]
                user.pop('password_hash', None)
                return {'success': True, 'user': user}
            else:
                return {'success': False, 'error': 'Failed to update profile'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def change_password(self, user_id: str, current_password: str, new_password: str):
        """Change user password"""
        try:
            # Get current user
            user_result = self.supabase.table('users').select('password_hash').eq(
                'id', user_id
            ).execute()

            if not user_result.data:
                return {'success': False, 'error': 'User not found'}

            user = user_result.data[0]

            # Verify current password
            if not self.verify_password(current_password, user['password_hash']):
                return {'success': False, 'error': 'Current password is incorrect'}

            # Hash new password
            new_password_hash = self.hash_password(new_password)

            # Update password
            result = self.supabase.table('users').update({
                'password_hash': new_password_hash
            }).eq('id', user_id).execute()

            if result.data:
                # Log password change event
                self.log_audit_event(
                    user_id=user_id,
                    action='password_change'
                )
                return {'success': True}
            else:
                return {'success': False, 'error': 'Failed to change password'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_user_jobs(self, user_id: str, page: int = 1, limit: int = 20):
        """Get user's job history with pagination"""
        try:
            offset = (page - 1) * limit

            # Get jobs with status
            jobs_result = self.supabase.table('job_summary').select('*').eq(
                'user_id', user_id
            ).order('created_at', desc=True).range(offset, offset + limit - 1).execute()

            # Get total count
            count_result = self.supabase.table('pdf_jobs').select(
                'id', count='exact'
            ).eq('user_id', user_id).execute()

            total_count = count_result.count if count_result.count else 0
            total_pages = (total_count + limit - 1) // limit

            return {
                'success': True,
                'jobs': jobs_result.data,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total_count': total_count,
                    'total_pages': total_pages
                }
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def delete_user_account(self, user_id: str, password: str):
        """Delete user account and all associated data"""
        try:
            # Verify password
            user_result = self.supabase.table('users').select('password_hash').eq(
                'id', user_id
            ).execute()

            if not user_result.data:
                return {'success': False, 'error': 'User not found'}

            user = user_result.data[0]

            if not self.verify_password(password, user['password_hash']):
                return {'success': False, 'error': 'Password is incorrect'}

            # Delete user (cascade will handle related data)
            result = self.supabase.table('users').delete().eq('id', user_id).execute()

            return {'success': True}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def log_audit_event(self, user_id: str = None, session_id: str = None, action: str = '', 
                       entity_type: str = None, entity_id: str = None, details: dict = None,
                       ip_address: str = None, user_agent: str = None):
        """Log audit event"""
        try:
            audit_data = {
                'user_id': user_id,
                'session_id': session_id,
                'action': action,
                'entity_type': entity_type,
                'entity_id': entity_id,
                'details': details,
                'ip_address': ip_address,
                'user_agent': user_agent
            }

            self.supabase.table('audit_log').insert(audit_data).execute()

        except Exception as e:
            # Don't fail the main operation if audit logging fails
            print(f"Audit logging error: {str(e)}")

def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'Authentication required'}), 401

        try:
            token = auth_header.replace('Bearer ', '')
            auth_manager = AuthManager()
            result = auth_manager.validate_session(token)
            
            if result['success']:
                request.current_user = result['user']
                return f(*args, **kwargs)
            else:
                return jsonify({'error': 'Invalid session'}), 401
                
        except Exception as e:
            return jsonify({'error': 'Authentication failed'}), 401

    return decorated_function