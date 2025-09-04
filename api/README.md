# Flask API Backend

This directory contains the Flask API backend that serves both snackpdf.com and revisepdf.com applications.

## Features

- **Authentication**: User registration, login, session management
- **File Upload**: Secure file upload with validation and storage
- **PDF Processing**: Integration endpoints for StirlingPDF operations
- **Payments**: Stripe subscription management and webhook handling
- **Rate Limiting**: Built-in rate limiting for API endpoints
- **Audit Logging**: Comprehensive logging of user actions
- **CORS**: Cross-origin resource sharing for frontend integration

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/profile` - Get user profile

### File Operations
- `POST /api/files/upload` - Upload files for processing

### PDF Processing
- `POST /api/pdf/merge` - Merge multiple PDFs
- `POST /api/pdf/split` - Split PDF into pages
- Additional endpoints for other PDF operations

### Payments
- `POST /api/payments/create-checkout` - Create Stripe checkout session
- `POST /api/payments/portal` - Create customer portal session
- `POST /api/payments/webhook` - Handle Stripe webhooks

### Utilities
- `GET /health` - Health check endpoint
- `GET /api/debug/info` - Debug information (development only)

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run the development server:
```bash
python app.py
```

## Environment Variables

Create a `.env` file with the following variables:

```
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your_secret_key

# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_STORAGE_BUCKET=pdf-files

# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRO_MONTHLY_PRICE_ID=price_...
STRIPE_PRO_YEARLY_PRICE_ID=price_...
STRIPE_ENTERPRISE_PRICE_ID=price_...

# Email Configuration (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=your_email@gmail.com
FROM_NAME=PDF Tools

# File Configuration
MAX_FILE_SIZE=52428800  # 50MB in bytes
```

## Deployment

For production deployment on Heroku:

1. Set up Heroku app
2. Configure environment variables
3. Deploy using Git or GitHub integration

The app includes a `Procfile` for Heroku deployment.