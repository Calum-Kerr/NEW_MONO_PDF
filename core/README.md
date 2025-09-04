# Core Shared Utilities

This directory contains shared utilities used across both snackpdf and revisepdf platforms.

## Modules

### `auth.py`
Authentication and session management using Supabase:
- User registration and login
- Session validation and management
- Authentication decorators for Flask routes
- API key generation and validation
- Subscription tier requirements

### `payments.py`
Stripe payment integration:
- Subscription management (Pro, Enterprise tiers)
- Webhook handling for payment events
- Customer portal integration
- Payment status tracking

### `files.py`
File handling and storage management:
- File upload validation and processing
- Supabase storage integration
- Secure filename generation
- File cleanup and expiration
- Temporary file management

### `utils.py`
General utility functions:
- Logging and audit trail
- Rate limiting
- Email notifications
- Error handling

## Usage

```python
from core.auth import auth_manager
from core.payments import payment_manager
from core.files import file_manager

# Authentication
@auth_manager.require_auth
def protected_route():
    user = auth_manager.get_current_user()
    return {"user": user}

# File upload
result = file_manager.upload_file(file_data, filename, user_id)

# Payment processing
checkout_url = payment_manager.create_checkout_session(
    user_id, 'pro_monthly', success_url, cancel_url
)
```

## Environment Variables

Required environment variables for core functionality:

```
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRO_MONTHLY_PRICE_ID=price_...
STRIPE_PRO_YEARLY_PRICE_ID=price_...
STRIPE_ENTERPRISE_PRICE_ID=price_...

# File Storage
SUPABASE_STORAGE_BUCKET=pdf-files
MAX_FILE_SIZE=52428800  # 50MB in bytes
```