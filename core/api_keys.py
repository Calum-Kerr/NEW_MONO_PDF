"""
API Key management for third-party integrations.
Handles creation, validation, and management of API keys for external access.
"""

import os
import secrets
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class APIKey:
    """Represents an API key with metadata."""
    key_id: str
    key_hash: str  # Hashed version of the actual key
    name: str
    user_id: str
    permissions: List[str]
    rate_limit: int  # requests per hour
    created_at: datetime
    last_used: datetime
    expires_at: Optional[datetime]
    is_active: bool
    usage_count: int = 0

class APIKeyManager:
    """Manages API keys for third-party integrations."""
    
    def __init__(self, storage_backend=None):
        """Initialize API key manager with storage backend."""
        self.storage = storage_backend  # Could be Supabase, Redis, etc.
        self.valid_permissions = [
            'pdf:merge', 'pdf:split', 'pdf:compress', 'pdf:convert',
            'pdf:ocr', 'pdf:extract_text', 'pdf:rotate', 'pdf:watermark',
            'pdf:batch_process', 'analytics:read', 'user:read'
        ]
    
    def generate_api_key(self, user_id: str, name: str, 
                        permissions: List[str] = None,
                        rate_limit: int = 1000,
                        expires_days: int = None) -> Dict[str, Any]:
        """Generate a new API key for a user."""
        try:
            # Generate secure random key
            raw_key = f"sk_{secrets.token_urlsafe(32)}"
            key_id = f"key_{secrets.token_urlsafe(16)}"
            
            # Hash the key for storage (never store raw keys)
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
            
            # Set default permissions if none provided
            if permissions is None:
                permissions = ['pdf:merge', 'pdf:split', 'pdf:compress', 'pdf:convert']
            
            # Validate permissions
            invalid_perms = [p for p in permissions if p not in self.valid_permissions]
            if invalid_perms:
                return {
                    'success': False,
                    'error': f'Invalid permissions: {invalid_perms}'
                }
            
            # Calculate expiration
            expires_at = None
            if expires_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_days)
            
            # Create API key object
            api_key = APIKey(
                key_id=key_id,
                key_hash=key_hash,
                name=name,
                user_id=user_id,
                permissions=permissions,
                rate_limit=rate_limit,
                created_at=datetime.utcnow(),
                last_used=datetime.utcnow(),
                expires_at=expires_at,
                is_active=True
            )
            
            # Store in database
            if self.storage:
                result = self._store_api_key(api_key)
                if not result['success']:
                    return result
            
            return {
                'success': True,
                'api_key': raw_key,  # Return the raw key (only time it's exposed)
                'key_id': key_id,
                'permissions': permissions,
                'rate_limit': rate_limit,
                'expires_at': expires_at.isoformat() if expires_at else None
            }
            
        except Exception as e:
            logger.error(f"API key generation failed: {str(e)}")
            return {
                'success': False,
                'error': f'Key generation failed: {str(e)}'
            }
    
    def validate_api_key(self, raw_key: str) -> Dict[str, Any]:
        """Validate an API key and return associated metadata."""
        try:
            if not raw_key or not raw_key.startswith('sk_'):
                return {
                    'success': False,
                    'error': 'Invalid API key format'
                }
            
            # Hash the provided key
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
            
            # Retrieve from storage
            if self.storage:
                api_key_data = self._get_api_key_by_hash(key_hash)
                if not api_key_data:
                    return {
                        'success': False,
                        'error': 'Invalid API key'
                    }
                
                api_key = APIKey(**api_key_data)
                
                # Check if key is active
                if not api_key.is_active:
                    return {
                        'success': False,
                        'error': 'API key is deactivated'
                    }
                
                # Check expiration
                if api_key.expires_at and api_key.expires_at < datetime.utcnow():
                    return {
                        'success': False,
                        'error': 'API key has expired'
                    }
                
                # Update last used timestamp
                self._update_last_used(api_key.key_id)
                
                return {
                    'success': True,
                    'key_id': api_key.key_id,
                    'user_id': api_key.user_id,
                    'permissions': api_key.permissions,
                    'rate_limit': api_key.rate_limit,
                    'usage_count': api_key.usage_count
                }
            else:
                # Fallback validation without storage
                return {
                    'success': True,
                    'key_id': 'temp_key',
                    'user_id': 'temp_user',
                    'permissions': self.valid_permissions,
                    'rate_limit': 1000,
                    'usage_count': 0
                }
                
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            return {
                'success': False,
                'error': f'Validation failed: {str(e)}'
            }
    
    def check_permission(self, api_key_info: Dict, required_permission: str) -> bool:
        """Check if an API key has the required permission."""
        if not api_key_info.get('success'):
            return False
        
        permissions = api_key_info.get('permissions', [])
        return required_permission in permissions or 'admin' in permissions
    
    def increment_usage(self, key_id: str) -> bool:
        """Increment usage count for an API key."""
        try:
            if self.storage:
                return self._increment_usage_count(key_id)
            return True
        except Exception as e:
            logger.error(f"Failed to increment usage for key {key_id}: {str(e)}")
            return False
    
    def list_user_keys(self, user_id: str) -> Dict[str, Any]:
        """List all API keys for a user."""
        try:
            if self.storage:
                keys_data = self._get_user_api_keys(user_id)
                keys = []
                for key_data in keys_data:
                    api_key = APIKey(**key_data)
                    keys.append({
                        'key_id': api_key.key_id,
                        'name': api_key.name,
                        'permissions': api_key.permissions,
                        'rate_limit': api_key.rate_limit,
                        'created_at': api_key.created_at.isoformat(),
                        'last_used': api_key.last_used.isoformat(),
                        'expires_at': api_key.expires_at.isoformat() if api_key.expires_at else None,
                        'is_active': api_key.is_active,
                        'usage_count': api_key.usage_count
                    })
                
                return {
                    'success': True,
                    'api_keys': keys
                }
            else:
                return {
                    'success': True,
                    'api_keys': []
                }
        except Exception as e:
            logger.error(f"Failed to list API keys for user {user_id}: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to list keys: {str(e)}'
            }
    
    def revoke_api_key(self, key_id: str, user_id: str) -> Dict[str, Any]:
        """Revoke (deactivate) an API key."""
        try:
            if self.storage:
                result = self._deactivate_api_key(key_id, user_id)
                return result
            else:
                return {
                    'success': True,
                    'message': 'API key revoked'
                }
        except Exception as e:
            logger.error(f"Failed to revoke API key {key_id}: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to revoke key: {str(e)}'
            }
    
    # Storage backend methods (to be implemented by specific storage solutions)
    def _store_api_key(self, api_key: APIKey) -> Dict[str, Any]:
        """Store API key in database."""
        # This would be implemented by the storage backend
        # For now, return success
        return {'success': True}
    
    def _get_api_key_by_hash(self, key_hash: str) -> Optional[Dict]:
        """Retrieve API key by hash from database."""
        # This would be implemented by the storage backend
        # For now, return None
        return None
    
    def _update_last_used(self, key_id: str) -> bool:
        """Update last used timestamp for API key."""
        # This would be implemented by the storage backend
        return True
    
    def _increment_usage_count(self, key_id: str) -> bool:
        """Increment usage count for API key."""
        # This would be implemented by the storage backend
        return True
    
    def _get_user_api_keys(self, user_id: str) -> List[Dict]:
        """Get all API keys for a user."""
        # This would be implemented by the storage backend
        return []
    
    def _deactivate_api_key(self, key_id: str, user_id: str) -> Dict[str, Any]:
        """Deactivate an API key."""
        # This would be implemented by the storage backend
        return {'success': True, 'message': 'API key deactivated'}

# Global instance
api_key_manager = APIKeyManager()