"""
Advanced security module.
Provides document encryption, DRM (Digital Rights Management), and advanced access controls.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import uuid
import hashlib
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import PyPDF2
from io import BytesIO

class SecurityLevel(Enum):
    """Document security levels."""
    NONE = "none"
    BASIC = "basic"
    STANDARD = "standard"
    HIGH = "high"
    ENTERPRISE = "enterprise"

class AccessAction(Enum):
    """Document access actions."""
    VIEW = "view"
    DOWNLOAD = "download"
    PRINT = "print"
    COPY = "copy"
    EDIT = "edit"
    SHARE = "share"
    DELETE = "delete"

@dataclass
class DRMPolicy:
    """Digital Rights Management policy."""
    policy_id: str
    name: str
    description: str
    allowed_actions: List[AccessAction]
    max_views: Optional[int]
    max_downloads: Optional[int]
    max_prints: Optional[int]
    expires_at: Optional[datetime]
    ip_restrictions: List[str]  # CIDR ranges
    device_restrictions: List[str]  # Device fingerprints
    time_restrictions: Dict[str, Any]  # Time-based access rules
    watermark_enabled: bool
    watermark_text: Optional[str]
    created_at: datetime
    created_by: str

@dataclass
class DocumentSecurity:
    """Document security configuration."""
    document_id: str
    security_level: SecurityLevel
    encryption_enabled: bool
    encryption_key_id: Optional[str]
    password_protected: bool
    password_hash: Optional[str]
    drm_policy_id: Optional[str]
    access_log_enabled: bool
    audit_trail_enabled: bool
    created_at: datetime
    updated_at: datetime

@dataclass
class AccessEvent:
    """Document access event for audit trail."""
    event_id: str
    document_id: str
    user_id: str
    action: AccessAction
    ip_address: str
    user_agent: str
    device_fingerprint: Optional[str]
    success: bool
    failure_reason: Optional[str]
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class EncryptionKey:
    """Encryption key information."""
    key_id: str
    key_type: str  # symmetric, asymmetric
    algorithm: str
    key_data: bytes
    salt: Optional[bytes]
    created_at: datetime
    expires_at: Optional[datetime]
    owner_id: str

class DocumentEncryption:
    """Handles document encryption and decryption."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_symmetric_key(self) -> EncryptionKey:
        """Generate a symmetric encryption key."""
        key_id = str(uuid.uuid4())
        key_data = Fernet.generate_key()
        
        return EncryptionKey(
            key_id=key_id,
            key_type="symmetric",
            algorithm="fernet",
            key_data=key_data,
            salt=None,
            created_at=datetime.utcnow(),
            expires_at=None,
            owner_id=""
        )
    
    def generate_asymmetric_keypair(self) -> tuple[EncryptionKey, EncryptionKey]:
        """Generate asymmetric key pair (public/private)."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()
        
        # Serialize keys
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        private_key_obj = EncryptionKey(
            key_id=str(uuid.uuid4()),
            key_type="asymmetric_private",
            algorithm="rsa_2048",
            key_data=private_pem,
            salt=None,
            created_at=datetime.utcnow(),
            expires_at=None,
            owner_id=""
        )
        
        public_key_obj = EncryptionKey(
            key_id=str(uuid.uuid4()),
            key_type="asymmetric_public",
            algorithm="rsa_2048",
            key_data=public_pem,
            salt=None,
            created_at=datetime.utcnow(),
            expires_at=None,
            owner_id=""
        )
        
        return private_key_obj, public_key_obj
    
    def encrypt_file_symmetric(self, file_path: str, encryption_key: EncryptionKey) -> str:
        """Encrypt file using symmetric encryption."""
        try:
            fernet = Fernet(encryption_key.key_data)
            
            with open(file_path, 'rb') as file:
                file_data = file.read()
            
            encrypted_data = fernet.encrypt(file_data)
            
            # Save encrypted file
            encrypted_path = f"{file_path}.encrypted"
            with open(encrypted_path, 'wb') as file:
                file.write(encrypted_data)
            
            return encrypted_path
            
        except Exception as e:
            self.logger.error(f"Error encrypting file: {str(e)}")
            raise
    
    def decrypt_file_symmetric(self, encrypted_path: str, encryption_key: EncryptionKey, 
                             output_path: str) -> bool:
        """Decrypt file using symmetric encryption."""
        try:
            fernet = Fernet(encryption_key.key_data)
            
            with open(encrypted_path, 'rb') as file:
                encrypted_data = file.read()
            
            decrypted_data = fernet.decrypt(encrypted_data)
            
            with open(output_path, 'wb') as file:
                file.write(decrypted_data)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error decrypting file: {str(e)}")
            return False
    
    def encrypt_pdf_with_password(self, file_path: str, password: str) -> str:
        """Encrypt PDF with password protection."""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                pdf_writer = PyPDF2.PdfWriter()
                
                # Copy all pages
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)
                
                # Add password protection
                pdf_writer.encrypt(password)
                
                # Save encrypted PDF
                encrypted_path = f"{file_path}.protected.pdf"
                with open(encrypted_path, 'wb') as output_file:
                    pdf_writer.write(output_file)
                
                return encrypted_path
                
        except Exception as e:
            self.logger.error(f"Error password protecting PDF: {str(e)}")
            raise

class DRMManager:
    """Manages Digital Rights Management policies and enforcement."""
    
    def __init__(self):
        self.policies: Dict[str, DRMPolicy] = {}
        self.document_security: Dict[str, DocumentSecurity] = {}
        self.access_counters: Dict[str, Dict[str, int]] = {}  # document_id -> action -> count
        self.logger = logging.getLogger(__name__)
    
    def create_drm_policy(self, name: str, description: str, creator_id: str,
                         allowed_actions: List[AccessAction] = None,
                         max_views: int = None, max_downloads: int = None,
                         max_prints: int = None, expires_at: datetime = None,
                         ip_restrictions: List[str] = None,
                         watermark_enabled: bool = False,
                         watermark_text: str = None) -> DRMPolicy:
        """Create a new DRM policy."""
        policy_id = str(uuid.uuid4())
        
        policy = DRMPolicy(
            policy_id=policy_id,
            name=name,
            description=description,
            allowed_actions=allowed_actions or [AccessAction.VIEW],
            max_views=max_views,
            max_downloads=max_downloads,
            max_prints=max_prints,
            expires_at=expires_at,
            ip_restrictions=ip_restrictions or [],
            device_restrictions=[],
            time_restrictions={},
            watermark_enabled=watermark_enabled,
            watermark_text=watermark_text,
            created_at=datetime.utcnow(),
            created_by=creator_id
        )
        
        self.policies[policy_id] = policy
        self.logger.info(f"Created DRM policy {policy_id}: {name}")
        
        return policy
    
    def apply_drm_to_document(self, document_id: str, policy_id: str,
                             security_level: SecurityLevel = SecurityLevel.STANDARD) -> DocumentSecurity:
        """Apply DRM policy to a document."""
        doc_security = DocumentSecurity(
            document_id=document_id,
            security_level=security_level,
            encryption_enabled=security_level in [SecurityLevel.HIGH, SecurityLevel.ENTERPRISE],
            encryption_key_id=None,
            password_protected=False,
            password_hash=None,
            drm_policy_id=policy_id,
            access_log_enabled=True,
            audit_trail_enabled=security_level in [SecurityLevel.HIGH, SecurityLevel.ENTERPRISE],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.document_security[document_id] = doc_security
        self.access_counters[document_id] = {}
        
        self.logger.info(f"Applied DRM policy {policy_id} to document {document_id}")
        return doc_security
    
    def check_access_permission(self, document_id: str, user_id: str, action: AccessAction,
                               ip_address: str = None, user_agent: str = None) -> tuple[bool, str]:
        """Check if user has permission to perform action on document."""
        if document_id not in self.document_security:
            return True, "No security policy applied"
        
        doc_security = self.document_security[document_id]
        
        if not doc_security.drm_policy_id:
            return True, "No DRM policy applied"
        
        if doc_security.drm_policy_id not in self.policies:
            return False, "DRM policy not found"
        
        policy = self.policies[doc_security.drm_policy_id]
        
        # Check if action is allowed
        if action not in policy.allowed_actions:
            return False, f"Action {action.value} not permitted by DRM policy"
        
        # Check expiration
        if policy.expires_at and datetime.utcnow() > policy.expires_at:
            return False, "DRM policy has expired"
        
        # Check usage limits
        doc_counters = self.access_counters.get(document_id, {})
        
        if action == AccessAction.VIEW and policy.max_views:
            current_views = doc_counters.get("view", 0)
            if current_views >= policy.max_views:
                return False, f"Maximum views ({policy.max_views}) exceeded"
        
        if action == AccessAction.DOWNLOAD and policy.max_downloads:
            current_downloads = doc_counters.get("download", 0)
            if current_downloads >= policy.max_downloads:
                return False, f"Maximum downloads ({policy.max_downloads}) exceeded"
        
        if action == AccessAction.PRINT and policy.max_prints:
            current_prints = doc_counters.get("print", 0)
            if current_prints >= policy.max_prints:
                return False, f"Maximum prints ({policy.max_prints}) exceeded"
        
        # Check IP restrictions
        if policy.ip_restrictions and ip_address:
            allowed = False
            for ip_range in policy.ip_restrictions:
                if self._ip_in_range(ip_address, ip_range):
                    allowed = True
                    break
            if not allowed:
                return False, f"IP address {ip_address} not allowed"
        
        return True, "Access granted"
    
    def record_access_event(self, document_id: str, user_id: str, action: AccessAction,
                           ip_address: str, user_agent: str, success: bool,
                           failure_reason: str = None) -> AccessEvent:
        """Record document access event."""
        event_id = str(uuid.uuid4())
        
        event = AccessEvent(
            event_id=event_id,
            document_id=document_id,
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=self._generate_device_fingerprint(user_agent),
            success=success,
            failure_reason=failure_reason,
            timestamp=datetime.utcnow(),
            metadata={}
        )
        
        # Update counters if successful
        if success:
            if document_id not in self.access_counters:
                self.access_counters[document_id] = {}
            
            counter_key = action.value
            self.access_counters[document_id][counter_key] = self.access_counters[document_id].get(counter_key, 0) + 1
        
        self.logger.info(f"Recorded access event {event_id} for document {document_id}")
        return event
    
    def get_document_security(self, document_id: str) -> Optional[DocumentSecurity]:
        """Get document security configuration."""
        return self.document_security.get(document_id)
    
    def get_drm_policy(self, policy_id: str) -> Optional[DRMPolicy]:
        """Get DRM policy by ID."""
        return self.policies.get(policy_id)
    
    def update_drm_policy(self, policy_id: str, **updates) -> bool:
        """Update DRM policy."""
        if policy_id not in self.policies:
            return False
        
        policy = self.policies[policy_id]
        
        for key, value in updates.items():
            if hasattr(policy, key):
                setattr(policy, key, value)
        
        self.logger.info(f"Updated DRM policy {policy_id}")
        return True
    
    def revoke_document_access(self, document_id: str) -> bool:
        """Revoke all access to a document."""
        if document_id in self.document_security:
            # Set expiration to now
            doc_security = self.document_security[document_id]
            if doc_security.drm_policy_id and doc_security.drm_policy_id in self.policies:
                policy = self.policies[doc_security.drm_policy_id]
                policy.expires_at = datetime.utcnow()
                self.logger.info(f"Revoked access to document {document_id}")
                return True
        
        return False
    
    def get_access_statistics(self, document_id: str) -> Dict[str, Any]:
        """Get access statistics for a document."""
        stats = {
            "document_id": document_id,
            "total_views": 0,
            "total_downloads": 0,
            "total_prints": 0,
            "last_accessed": None
        }
        
        if document_id in self.access_counters:
            counters = self.access_counters[document_id]
            stats["total_views"] = counters.get("view", 0)
            stats["total_downloads"] = counters.get("download", 0)
            stats["total_prints"] = counters.get("print", 0)
        
        return stats
    
    def _ip_in_range(self, ip: str, ip_range: str) -> bool:
        """Check if IP address is in CIDR range."""
        try:
            import ipaddress
            return ipaddress.ip_address(ip) in ipaddress.ip_network(ip_range)
        except:
            return False
    
    def _generate_device_fingerprint(self, user_agent: str) -> str:
        """Generate device fingerprint from user agent."""
        if not user_agent:
            return ""
        
        # Simple fingerprint based on user agent hash
        return hashlib.md5(user_agent.encode()).hexdigest()[:16]

class SecurityManager:
    """Main security management class."""
    
    def __init__(self):
        self.encryption = DocumentEncryption()
        self.drm = DRMManager()
        self.encryption_keys: Dict[str, EncryptionKey] = {}
        self.logger = logging.getLogger(__name__)
    
    def secure_document(self, document_id: str, file_path: str, security_level: SecurityLevel,
                       creator_id: str, password: str = None,
                       drm_config: Dict[str, Any] = None) -> DocumentSecurity:
        """Apply comprehensive security to a document."""
        
        # Create DRM policy if specified
        drm_policy_id = None
        if drm_config:
            drm_policy = self.drm.create_drm_policy(
                name=drm_config.get("name", f"Policy for {document_id}"),
                description=drm_config.get("description", "Auto-generated policy"),
                creator_id=creator_id,
                allowed_actions=[AccessAction(a) for a in drm_config.get("allowed_actions", ["view"])],
                max_views=drm_config.get("max_views"),
                max_downloads=drm_config.get("max_downloads"),
                max_prints=drm_config.get("max_prints"),
                expires_at=drm_config.get("expires_at"),
                ip_restrictions=drm_config.get("ip_restrictions", []),
                watermark_enabled=drm_config.get("watermark_enabled", False),
                watermark_text=drm_config.get("watermark_text")
            )
            drm_policy_id = drm_policy.policy_id
        
        # Apply DRM to document
        doc_security = self.drm.apply_drm_to_document(document_id, drm_policy_id, security_level)
        
        # Apply encryption if required
        if security_level in [SecurityLevel.HIGH, SecurityLevel.ENTERPRISE]:
            encryption_key = self.encryption.generate_symmetric_key()
            encryption_key.owner_id = creator_id
            self.encryption_keys[encryption_key.key_id] = encryption_key
            
            # Encrypt the file
            encrypted_path = self.encryption.encrypt_file_symmetric(file_path, encryption_key)
            doc_security.encryption_enabled = True
            doc_security.encryption_key_id = encryption_key.key_id
            
            self.logger.info(f"Encrypted document {document_id} with key {encryption_key.key_id}")
        
        # Apply password protection if specified
        if password and file_path.lower().endswith('.pdf'):
            try:
                protected_path = self.encryption.encrypt_pdf_with_password(file_path, password)
                doc_security.password_protected = True
                doc_security.password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                self.logger.info(f"Password protected document {document_id}")
            except Exception as e:
                self.logger.error(f"Failed to password protect document: {str(e)}")
        
        doc_security.updated_at = datetime.utcnow()
        return doc_security
    
    def access_document(self, document_id: str, user_id: str, action: AccessAction,
                       ip_address: str, user_agent: str) -> tuple[bool, str, Optional[str]]:
        """Secure document access with permission checking and logging."""
        
        # Check permissions
        allowed, reason = self.drm.check_access_permission(
            document_id, user_id, action, ip_address, user_agent
        )
        
        # Record access event
        self.drm.record_access_event(
            document_id, user_id, action, ip_address, user_agent, allowed, reason if not allowed else None
        )
        
        decrypted_path = None
        
        if allowed:
            # Handle decryption if needed
            doc_security = self.drm.get_document_security(document_id)
            if doc_security and doc_security.encryption_enabled and doc_security.encryption_key_id:
                encryption_key = self.encryption_keys.get(doc_security.encryption_key_id)
                if encryption_key:
                    # In a real implementation, you would decrypt to a temporary location
                    decrypted_path = f"/tmp/decrypted_{document_id}_{user_id}.pdf"
                    # self.encryption.decrypt_file_symmetric(encrypted_path, encryption_key, decrypted_path)
        
        return allowed, reason, decrypted_path
    
    def get_document_security_info(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive security information for a document."""
        doc_security = self.drm.get_document_security(document_id)
        if not doc_security:
            return None
        
        info = asdict(doc_security)
        
        # Add DRM policy info
        if doc_security.drm_policy_id:
            drm_policy = self.drm.get_drm_policy(doc_security.drm_policy_id)
            if drm_policy:
                info["drm_policy"] = asdict(drm_policy)
        
        # Add access statistics
        info["access_stats"] = self.drm.get_access_statistics(document_id)
        
        return info
    
    def revoke_document_access(self, document_id: str) -> bool:
        """Revoke all access to a document."""
        return self.drm.revoke_document_access(document_id)

# Global security manager instance
security_manager = SecurityManager()