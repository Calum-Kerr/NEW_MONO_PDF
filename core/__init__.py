# Core module initialization
import os

# Import utilities first (no dependencies)
from .utils import (
    rate_limiter,
    audit_logger, 
    email_manager,
    format_file_size,
    validate_email,
    generate_unique_id,
    sanitize_filename,
    create_error_response,
    create_success_response,
    require_rate_limit,
    log_performance
)

# Import StirlingPDF client
from .stirling_pdf import stirling_client

# Import new Phase 3 modules
try:
    from .api_keys import api_key_manager
except ImportError as e:
    print(f"Warning: API key manager not available: {e}")
    api_key_manager = None

try:
    from .analytics import analytics_manager
except ImportError as e:
    print(f"Warning: Analytics manager not available: {e}")
    analytics_manager = None

try:
    from .whitelabel import whitelabel_manager
except ImportError as e:
    print(f"Warning: White-label manager not available: {e}")
    whitelabel_manager = None

# Conditional imports to handle missing environment variables gracefully
try:
    from .auth import auth_manager
except ValueError as e:
    if "Missing Supabase configuration" in str(e):
        print("Warning: Supabase not configured, authentication will be disabled")
        auth_manager = None
    else:
        raise

try:
    from .payments import payment_manager
except ValueError as e:
    if "Missing Stripe configuration" in str(e):
        print("Warning: Stripe not configured, payments will be disabled")
        payment_manager = None
    else:
        raise

try:
    from .files import file_manager
except ValueError as e:
    if "Missing" in str(e):
        print("Warning: File storage not configured, file operations will be limited")
        file_manager = None
    else:
        raise

__all__ = [
    'auth_manager',
    'payment_manager', 
    'file_manager',
    'stirling_client',
    'api_key_manager',
    'analytics_manager',
    'whitelabel_manager',
    'rate_limiter',
    'audit_logger',
    'email_manager',
    'format_file_size',
    'validate_email',
    'generate_unique_id',
    'sanitize_filename',
    'create_error_response',
    'create_success_response',
    'require_rate_limit',
    'log_performance'
]