"""
Collaborative editing module.
Provides real-time document collaboration, sharing, and user presence features.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import uuid
from enum import Enum

class PermissionLevel(Enum):
    """Document permission levels."""
    READ = "read"
    COMMENT = "comment"
    EDIT = "edit"
    ADMIN = "admin"

class CollaborationEvent(Enum):
    """Types of collaboration events."""
    JOIN = "join"
    LEAVE = "leave"
    EDIT = "edit"
    COMMENT = "comment"
    SAVE = "save"
    CURSOR_MOVE = "cursor_move"

@dataclass
class UserPresence:
    """Represents a user's presence in a collaborative session."""
    user_id: str
    username: str
    avatar_url: Optional[str]
    cursor_position: Optional[Dict[str, int]]
    last_activity: datetime
    permission_level: PermissionLevel
    color: str  # Unique color for user identification

@dataclass
class DocumentShare:
    """Represents a shared document."""
    share_id: str
    document_id: str
    owner_id: str
    title: str
    description: Optional[str]
    permissions: Dict[str, PermissionLevel]  # user_id -> permission
    public_access: bool
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

@dataclass
class Comment:
    """Document comment or annotation."""
    comment_id: str
    document_id: str
    user_id: str
    username: str
    content: str
    position: Dict[str, Any]  # Page, coordinates, etc.
    thread_id: Optional[str]
    parent_id: Optional[str]
    resolved: bool
    created_at: datetime
    updated_at: datetime

@dataclass
class EditOperation:
    """Represents a collaborative edit operation."""
    operation_id: str
    document_id: str
    user_id: str
    operation_type: str  # insert, delete, format, etc.
    position: Dict[str, Any]
    content: Any
    timestamp: datetime

class CollaborativeSessionManager:
    """Manages real-time collaborative editing sessions."""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, UserPresence]] = {}  # document_id -> user_id -> presence
        self.document_shares: Dict[str, DocumentShare] = {}  # share_id -> document share
        self.comments: Dict[str, List[Comment]] = {}  # document_id -> comments
        self.edit_history: Dict[str, List[EditOperation]] = {}  # document_id -> operations
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Color palette for user identification
        self.user_colors = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
            "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9"
        ]
        self.color_index = 0
    
    def create_document_share(self, document_id: str, owner_id: str, title: str, 
                            description: str = None, public_access: bool = False,
                            expires_at: datetime = None) -> DocumentShare:
        """Create a new document share."""
        share_id = str(uuid.uuid4())
        
        share = DocumentShare(
            share_id=share_id,
            document_id=document_id,
            owner_id=owner_id,
            title=title,
            description=description,
            permissions={owner_id: PermissionLevel.ADMIN},
            public_access=public_access,
            expires_at=expires_at,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.document_shares[share_id] = share
        self.logger.info(f"Created document share {share_id} for document {document_id}")
        
        return share
    
    def add_collaborator(self, share_id: str, user_id: str, permission: PermissionLevel) -> bool:
        """Add a collaborator to a document share."""
        if share_id not in self.document_shares:
            return False
        
        share = self.document_shares[share_id]
        share.permissions[user_id] = permission
        share.updated_at = datetime.utcnow()
        
        self.logger.info(f"Added collaborator {user_id} to share {share_id} with {permission.value} permission")
        return True
    
    def remove_collaborator(self, share_id: str, user_id: str) -> bool:
        """Remove a collaborator from a document share."""
        if share_id not in self.document_shares:
            return False
        
        share = self.document_shares[share_id]
        if user_id in share.permissions and user_id != share.owner_id:
            del share.permissions[user_id]
            share.updated_at = datetime.utcnow()
            
            # Remove from active session if present
            if share.document_id in self.active_sessions and user_id in self.active_sessions[share.document_id]:
                del self.active_sessions[share.document_id][user_id]
            
            self.logger.info(f"Removed collaborator {user_id} from share {share_id}")
            return True
        
        return False
    
    def join_session(self, document_id: str, user_id: str, username: str, 
                    avatar_url: str = None) -> UserPresence:
        """User joins a collaborative editing session."""
        if document_id not in self.active_sessions:
            self.active_sessions[document_id] = {}
        
        # Get user color
        color = self._get_user_color(user_id)
        
        # Get user permission
        permission = self._get_user_permission(document_id, user_id)
        
        presence = UserPresence(
            user_id=user_id,
            username=username,
            avatar_url=avatar_url,
            cursor_position=None,
            last_activity=datetime.utcnow(),
            permission_level=permission,
            color=color
        )
        
        self.active_sessions[document_id][user_id] = presence
        self.logger.info(f"User {user_id} joined session for document {document_id}")
        
        return presence
    
    def leave_session(self, document_id: str, user_id: str) -> bool:
        """User leaves a collaborative editing session."""
        if document_id in self.active_sessions and user_id in self.active_sessions[document_id]:
            del self.active_sessions[document_id][user_id]
            
            # Clean up empty sessions
            if not self.active_sessions[document_id]:
                del self.active_sessions[document_id]
            
            self.logger.info(f"User {user_id} left session for document {document_id}")
            return True
        
        return False
    
    def update_cursor_position(self, document_id: str, user_id: str, 
                             position: Dict[str, int]) -> bool:
        """Update user's cursor position."""
        if (document_id in self.active_sessions and 
            user_id in self.active_sessions[document_id]):
            
            presence = self.active_sessions[document_id][user_id]
            presence.cursor_position = position
            presence.last_activity = datetime.utcnow()
            
            return True
        
        return False
    
    def get_active_users(self, document_id: str) -> List[UserPresence]:
        """Get list of active users in a document session."""
        if document_id not in self.active_sessions:
            return []
        
        # Clean up inactive users (inactive for more than 5 minutes)
        cutoff_time = datetime.utcnow() - timedelta(minutes=5)
        active_users = []
        
        for user_id, presence in list(self.active_sessions[document_id].items()):
            if presence.last_activity >= cutoff_time:
                active_users.append(presence)
            else:
                del self.active_sessions[document_id][user_id]
        
        return active_users
    
    def add_comment(self, document_id: str, user_id: str, username: str, 
                   content: str, position: Dict[str, Any], 
                   thread_id: str = None, parent_id: str = None) -> Comment:
        """Add a comment to a document."""
        comment_id = str(uuid.uuid4())
        
        comment = Comment(
            comment_id=comment_id,
            document_id=document_id,
            user_id=user_id,
            username=username,
            content=content,
            position=position,
            thread_id=thread_id or comment_id,
            parent_id=parent_id,
            resolved=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        if document_id not in self.comments:
            self.comments[document_id] = []
        
        self.comments[document_id].append(comment)
        self.logger.info(f"Added comment {comment_id} to document {document_id}")
        
        return comment
    
    def resolve_comment(self, document_id: str, comment_id: str) -> bool:
        """Resolve a comment."""
        if document_id in self.comments:
            for comment in self.comments[document_id]:
                if comment.comment_id == comment_id:
                    comment.resolved = True
                    comment.updated_at = datetime.utcnow()
                    return True
        
        return False
    
    def get_document_comments(self, document_id: str, include_resolved: bool = False) -> List[Comment]:
        """Get comments for a document."""
        if document_id not in self.comments:
            return []
        
        comments = self.comments[document_id]
        
        if not include_resolved:
            comments = [c for c in comments if not c.resolved]
        
        return sorted(comments, key=lambda c: c.created_at)
    
    def record_edit_operation(self, document_id: str, user_id: str, 
                            operation_type: str, position: Dict[str, Any], 
                            content: Any) -> EditOperation:
        """Record an edit operation for collaborative editing."""
        operation_id = str(uuid.uuid4())
        
        operation = EditOperation(
            operation_id=operation_id,
            document_id=document_id,
            user_id=user_id,
            operation_type=operation_type,
            position=position,
            content=content,
            timestamp=datetime.utcnow()
        )
        
        if document_id not in self.edit_history:
            self.edit_history[document_id] = []
        
        self.edit_history[document_id].append(operation)
        
        # Keep only last 1000 operations to prevent memory issues
        if len(self.edit_history[document_id]) > 1000:
            self.edit_history[document_id] = self.edit_history[document_id][-1000:]
        
        return operation
    
    def get_edit_history(self, document_id: str, since: datetime = None) -> List[EditOperation]:
        """Get edit history for a document."""
        if document_id not in self.edit_history:
            return []
        
        operations = self.edit_history[document_id]
        
        if since:
            operations = [op for op in operations if op.timestamp >= since]
        
        return sorted(operations, key=lambda op: op.timestamp)
    
    def _get_user_color(self, user_id: str) -> str:
        """Get a consistent color for a user."""
        # Use hash of user_id to get consistent color
        user_hash = hash(user_id) % len(self.user_colors)
        return self.user_colors[user_hash]
    
    def _get_user_permission(self, document_id: str, user_id: str) -> PermissionLevel:
        """Get user permission for a document."""
        # Find the document share that contains this document
        for share in self.document_shares.values():
            if share.document_id == document_id:
                if user_id in share.permissions:
                    return share.permissions[user_id]
                elif share.public_access:
                    return PermissionLevel.READ
        
        return PermissionLevel.READ  # Default permission
    
    def get_document_share(self, share_id: str) -> Optional[DocumentShare]:
        """Get document share by ID."""
        return self.document_shares.get(share_id)
    
    def get_shares_for_document(self, document_id: str) -> List[DocumentShare]:
        """Get all shares for a document."""
        return [share for share in self.document_shares.values() 
                if share.document_id == document_id]
    
    def get_user_shared_documents(self, user_id: str) -> List[DocumentShare]:
        """Get documents shared with a user."""
        shares = []
        for share in self.document_shares.values():
            if (user_id in share.permissions or 
                share.public_access or 
                share.owner_id == user_id):
                shares.append(share)
        
        return sorted(shares, key=lambda s: s.updated_at, reverse=True)
    
    def check_permission(self, document_id: str, user_id: str, 
                        required_permission: PermissionLevel) -> bool:
        """Check if user has required permission for document."""
        user_permission = self._get_user_permission(document_id, user_id)
        
        # Define permission hierarchy
        permission_levels = {
            PermissionLevel.READ: 1,
            PermissionLevel.COMMENT: 2,
            PermissionLevel.EDIT: 3,
            PermissionLevel.ADMIN: 4
        }
        
        return permission_levels.get(user_permission, 0) >= permission_levels.get(required_permission, 0)

# Global collaborative session manager instance
collaboration_manager = CollaborativeSessionManager()