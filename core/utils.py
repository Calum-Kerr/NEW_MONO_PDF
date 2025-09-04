"""
General utility functions for PDF tools platform.
Includes logging, rate limiting, email notifications, and error handling.
"""

import os
import time
import smtplib
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps
from flask import request, jsonify, g
from supabase import create_client, Client
from collections import defaultdict

class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def is_allowed(self, key: str, max_requests: int = 100, window_seconds: int = 3600) -> bool:
        """Check if request is allowed under rate limit."""
        now = time.time()
        
        # Cleanup old entries periodically
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup_expired_entries(now)
            self.last_cleanup = now
        
        # Get requests for this key
        key_requests = self.requests[key]
        
        # Remove expired requests
        cutoff_time = now - window_seconds
        key_requests[:] = [req_time for req_time in key_requests if req_time > cutoff_time]
        
        # Check if under limit
        if len(key_requests) >= max_requests:
            return False
        
        # Add current request
        key_requests.append(now)
        return True
    
    def _cleanup_expired_entries(self, current_time: float):
        """Remove expired entries from all keys."""
        cutoff_time = current_time - 3600  # 1 hour ago
        
        for key in list(self.requests.keys()):
            self.requests[key][:] = [
                req_time for req_time in self.requests[key] 
                if req_time > cutoff_time
            ]
            
            # Remove empty entries
            if not self.requests[key]:
                del self.requests[key]

class AuditLogger:
    """Audit logging for user actions and system events."""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if self.supabase_url and self.service_key:
            self.supabase: Client = create_client(self.supabase_url, self.service_key)
        else:
            self.supabase = None
    
    def log_action(self, action: str, resource_type: str = None, resource_id: str = None,
                  user_id: str = None, platform: str = None, metadata: Dict = None):
        """Log an action to the audit trail."""
        try:
            if not self.supabase:
                return
            
            log_entry = {
                'action': action,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'user_id': user_id,
                'platform': platform,
                'ip_address': request.remote_addr if request else None,
                'user_agent': request.headers.get('User-Agent') if request else None,
                'metadata': metadata or {},
                'created_at': datetime.utcnow().isoformat()
            }
            
            self.supabase.table('audit_log').insert(log_entry).execute()
            
        except Exception as e:
            logging.error(f"Failed to log audit entry: {e}")

class EmailManager:
    """Email notification manager."""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_username)
        self.from_name = os.getenv('FROM_NAME', 'PDF Tools')
    
    def send_email(self, to_email: str, subject: str, html_content: str, 
                   text_content: str = None) -> bool:
        """Send an email notification."""
        try:
            if not all([self.smtp_username, self.smtp_password, to_email]):
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Add text content
            if text_content:
                part1 = MIMEText(text_content, 'plain')
                msg.attach(part1)
            
            # Add HTML content
            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to send email: {e}")
            return False
    
    def send_welcome_email(self, user_email: str, user_name: str = None) -> bool:
        """Send welcome email to new users."""
        subject = "Welcome to PDF Tools!"
        
        html_content = f"""
        <html>
        <body>
            <h2>Welcome to PDF Tools{f', {user_name}' if user_name else ''}!</h2>
            <p>Thank you for joining our platform. You now have access to powerful PDF tools:</p>
            <ul>
                <li><strong>SnackPDF</strong> - All-in-one PDF tools for merging, splitting, compressing and more</li>
                <li><strong>RevisePDF</strong> - Live PDF editor for forms, annotations, and signatures</li>
            </ul>
            <p>Get started today with your free account!</p>
            <p>Best regards,<br>The PDF Tools Team</p>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to PDF Tools{f', {user_name}' if user_name else ''}!
        
        Thank you for joining our platform. You now have access to powerful PDF tools:
        
        - SnackPDF: All-in-one PDF tools for merging, splitting, compressing and more
        - RevisePDF: Live PDF editor for forms, annotations, and signatures
        
        Get started today with your free account!
        
        Best regards,
        The PDF Tools Team
        """
        
        return self.send_email(user_email, subject, html_content, text_content)
    
    def send_subscription_confirmation(self, user_email: str, plan_name: str) -> bool:
        """Send subscription confirmation email."""
        subject = f"Subscription Confirmed - {plan_name}"
        
        html_content = f"""
        <html>
        <body>
            <h2>Subscription Confirmed</h2>
            <p>Your {plan_name} subscription has been activated successfully!</p>
            <p>You now have access to all premium features including:</p>
            <ul>
                <li>Unlimited PDF operations</li>
                <li>Advanced tools (OCR, compression)</li>
                <li>Priority processing</li>
                <li>Premium support</li>
            </ul>
            <p>Thank you for your subscription!</p>
            <p>Best regards,<br>The PDF Tools Team</p>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, html_content)

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def validate_email(email: str) -> bool:
    """Validate email address format."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def generate_unique_id() -> str:
    """Generate a unique ID."""
    import uuid
    return str(uuid.uuid4())

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    import re
    # Remove or replace unsafe characters
    filename = re.sub(r'[^\w\s.-]', '', filename)
    # Replace spaces with underscores
    filename = re.sub(r'\s+', '_', filename)
    # Limit length
    if len(filename) > 100:
        name, ext = os.path.splitext(filename)
        filename = name[:90] + ext
    
    return filename

def create_error_response(message: str, code: int = 400, details: Dict = None) -> tuple:
    """Create standardized error response."""
    response = {
        "error": True,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if details:
        response["details"] = details
    
    return jsonify(response), code

def create_success_response(data: Any = None, message: str = None) -> Dict:
    """Create standardized success response."""
    response = {
        "success": True,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if message:
        response["message"] = message
    
    if data is not None:
        response["data"] = data
    
    return jsonify(response)

def require_rate_limit(max_requests: int = 100, window_seconds: int = 3600):
    """Decorator to add rate limiting to routes."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Use IP address as rate limit key
            key = request.remote_addr or 'unknown'
            
            # Check rate limit
            if not rate_limiter.is_allowed(key, max_requests, window_seconds):
                return create_error_response(
                    "Rate limit exceeded",
                    429,
                    {"max_requests": max_requests, "window_seconds": window_seconds}
                )
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def log_performance(action: str):
    """Decorator to log performance metrics."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = f(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                
                audit_logger.log_action(
                    action=f"performance_{action}",
                    resource_type="function",
                    metadata={
                        "execution_time_ms": execution_time,
                        "function_name": f.__name__
                    }
                )
                
                return result
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                
                audit_logger.log_action(
                    action=f"error_{action}",
                    resource_type="function",
                    metadata={
                        "execution_time_ms": execution_time,
                        "function_name": f.__name__,
                        "error": str(e)
                    }
                )
                
                raise
        
        return decorated_function
    return decorator

# Global instances
rate_limiter = RateLimiter()
audit_logger = AuditLogger()
email_manager = EmailManager()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)