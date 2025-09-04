"""
Core authentication utilities for PDF tools platform.
Handles Supabase authentication and session management.
"""

import os
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from supabase import create_client, Client
from functools import wraps
from flask import request, jsonify, g

class AuthManager:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        self.service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not all([self.supabase_url, self.supabase_key, self.service_key]):
            raise ValueError("Missing Supabase configuration")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.admin_client: Client = create_client(self.supabase_url, self.service_key)
    
    def create_user(self, email: str, password: str, full_name: str = None) -> Dict[str, Any]:
        """Create a new user account."""
        try:
            # Create user in Supabase Auth
            auth_response = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if auth_response.user:
                # Create user profile
                profile_data = {
                    "id": auth_response.user.id,
                    "email": email,
                    "full_name": full_name,
                    "created_at": datetime.utcnow().isoformat()
                }
                
                profile_response = self.admin_client.table('users').insert(profile_data).execute()
                
                return {
                    "success": True,
                    "user": auth_response.user,
                    "session": auth_response.session
                }
            
            return {"success": False, "error": "Failed to create user"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user and create session."""
        try:
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response.session:
                # Update last login
                self.admin_client.table('users').update({
                    "last_login_at": datetime.utcnow().isoformat()
                }).eq('id', auth_response.user.id).execute()
                
                # Create session record
                session_data = {
                    "user_id": auth_response.user.id,
                    "session_token": auth_response.session.access_token,
                    "ip_address": request.remote_addr if request else None,
                    "user_agent": request.headers.get('User-Agent') if request else None,
                    "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
                }
                
                self.admin_client.table('sessions').insert(session_data).execute()
                
                return {
                    "success": True,
                    "user": auth_response.user,
                    "session": auth_response.session
                }
            
            return {"success": False, "error": "Invalid credentials"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def logout_user(self, session_token: str) -> Dict[str, Any]:
        """Logout user and invalidate session."""
        try:
            # Invalidate session in database
            self.admin_client.table('sessions').update({
                "is_active": False
            }).eq('session_token', session_token).execute()
            
            # Sign out from Supabase
            self.supabase.auth.sign_out()
            
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def verify_session(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify session token and return user data."""
        try:
            # Check session in database
            session_response = self.admin_client.table('sessions').select(
                "*, users(*)"
            ).eq('session_token', token).eq('is_active', True).single().execute()
            
            if session_response.data:
                session = session_response.data
                
                # Check if session is expired
                expires_at = datetime.fromisoformat(session['expires_at'].replace('Z', '+00:00'))
                if datetime.utcnow().replace(tzinfo=expires_at.tzinfo) > expires_at:
                    return None
                
                return session['users']
            
            return None
            
        except Exception:
            return None
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user from request context."""
        return getattr(g, 'current_user', None)
    
    def require_auth(self, f):
        """Decorator to require authentication for routes."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"error": "Missing or invalid authorization header"}), 401
            
            token = auth_header.split(' ')[1]
            user = self.verify_session(token)
            
            if not user:
                return jsonify({"error": "Invalid or expired session"}), 401
            
            g.current_user = user
            return f(*args, **kwargs)
        
        return decorated_function
    
    def require_subscription(self, tiers: list = None):
        """Decorator to require specific subscription tiers."""
        if tiers is None:
            tiers = ['pro', 'enterprise']
        
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                user = self.get_current_user()
                
                if not user:
                    return jsonify({"error": "Authentication required"}), 401
                
                if user.get('subscription_tier', 'free') not in tiers:
                    return jsonify({
                        "error": "Subscription required",
                        "required_tiers": tiers,
                        "current_tier": user.get('subscription_tier', 'free')
                    }), 403
                
                return f(*args, **kwargs)
            
            return decorated_function
        return decorator
    
    def generate_api_key(self, user_id: str, key_name: str, permissions: list = None) -> str:
        """Generate a new API key for a user."""
        if permissions is None:
            permissions = []
        
        # Generate secure random API key
        api_key = f"pdf_{secrets.token_urlsafe(32)}"
        
        # Hash the key for storage
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Store in database
        key_data = {
            "user_id": user_id,
            "key_name": key_name,
            "api_key_hash": key_hash,
            "permissions": permissions,
            "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat()
        }
        
        self.admin_client.table('api_keys').insert(key_data).execute()
        
        return api_key
    
    def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Verify API key and return associated user."""
        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            key_response = self.admin_client.table('api_keys').select(
                "*, users(*)"
            ).eq('api_key_hash', key_hash).eq('is_active', True).single().execute()
            
            if key_response.data:
                key_data = key_response.data
                
                # Check if key is expired
                if key_data['expires_at']:
                    expires_at = datetime.fromisoformat(key_data['expires_at'].replace('Z', '+00:00'))
                    if datetime.utcnow().replace(tzinfo=expires_at.tzinfo) > expires_at:
                        return None
                
                # Update last used timestamp
                self.admin_client.table('api_keys').update({
                    "last_used_at": datetime.utcnow().isoformat()
                }).eq('id', key_data['id']).execute()
                
                return key_data['users']
            
            return None
            
        except Exception:
            return None

# Global auth manager instance
try:
    auth_manager = AuthManager()
except ValueError as e:
    if "Missing Supabase configuration" in str(e):
        print("Warning: Supabase not configured, authentication will be disabled")
        auth_manager = None
    else:
        raise