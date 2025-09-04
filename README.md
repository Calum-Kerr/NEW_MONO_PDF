# NEW_MONO_PDF - Complete PDF Tools Platform

A comprehensive monorepo containing both SnackPDF (all-in-one PDF tools) and RevisePDF (live PDF editor) applications.

## 🚀 Features

### SnackPDF (iLovePDF clone)
- **Merge PDF** - Combine multiple PDF files into one
- **Split PDF** - Extract pages or split into multiple documents  
- **Compress PDF** - Reduce file size while maintaining quality
- **Convert to PDF** - Convert Word, Excel, images to PDF
- **PDF to Image** - Convert PDF pages to JPG/PNG
- **Premium editing** - Advanced PDF editing features

### RevisePDF (PDFfiller clone)
- Live in-browser PDF editing
- Add text, images, signatures
- Form filling capabilities
- Collaborative editing

## 🏗️ Architecture

```
NEW_MONO_PDF/
├── snackpdf/          # SnackPDF frontend (iLovePDF clone)
│   ├── static/        # CSS, JS, images
│   └── templates/     # HTML templates
├── revisepdf/         # RevisePDF frontend (PDFfiller clone)
│   ├── static/        # CSS, JS, images  
│   └── templates/     # HTML templates
├── api/               # Backend API (Flask)
│   ├── routes/        # API route handlers
│   ├── models/        # Data models
│   └── utils/         # Utility functions
├── core/              # Shared utilities
│   ├── auth.py        # Authentication management
│   ├── payments.py    # Stripe integration
│   ├── storage.py     # File storage & management
│   └── pdf_processor.py # PDF processing logic
├── supabase/          # Database schema and migrations
├── scripts/           # Development and deployment scripts
└── README.md
```

## 🛠️ Tech Stack

- **Frontend**: HTML5, Bootstrap 5.3, Vanilla JavaScript
- **Backend**: Python Flask + SQLAlchemy  
- **Database**: PostgreSQL (via Supabase)
- **Authentication**: Supabase Auth + JWT
- **Payments**: Stripe (subscriptions only)
- **File Storage**: Supabase Storage + local temp storage
- **Hosting**: Heroku
- **PDF Processing**: PyPDF2, Pillow, ReportLab

## 📋 Prerequisites

- Python 3.9+
- Node.js 16+ (for frontend tools)
- PostgreSQL database (Supabase recommended)
- Stripe account for payments
- Heroku account for deployment

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/Calum-Kerr/NEW_MONO_PDF.git
cd NEW_MONO_PDF
```

### 2. Set up environment variables
```bash
cp .env.template .env
# Edit .env with your actual configuration values
```

### 3. Set up the database
```bash
# Run the database schema
psql -f supabase/schema.sql your_database_url
```

### 4. Install Python dependencies
```bash
cd api
pip install -r requirements.txt
```

### 5. Run the development server
```bash
# From the api directory
python app.py
```

### 6. Open your browser
- SnackPDF: http://localhost:5000
- API Documentation: http://localhost:5000/api

## 🗄️ Database Setup

The database schema is defined in `supabase/schema.sql`. It includes:

- **users** - User accounts and profiles
- **sessions** - Authentication sessions  
- **subscriptions** - Stripe subscription data
- **pdf_jobs** - PDF processing job tracking
- **job_status** - Async job status tracking
- **audit_log** - User action analytics
- **file_storage** - File metadata and storage
- **usage_limits** - Freemium usage tracking

### Key Features:
- Row Level Security (RLS) policies
- Automatic timestamp updates
- Usage limit enforcement
- Audit logging for analytics

## 💳 Payment Integration

Stripe is integrated for subscription management:

### Supported Plans:
- **Free**: 5 jobs/month, 10MB file limit
- **Premium**: 100 jobs/month, 100MB file limit
- **Enterprise**: 1000 jobs/month, 1GB file limit

### Webhook Events:
- Subscription creation/updates
- Payment success/failure
- Customer portal events

## 🔐 Authentication

Authentication uses Supabase Auth with session management:

### Features:
- Email/password registration
- Session token management
- Password reset functionality
- User profile management

### Protected Routes:
- Dashboard and profile pages
- Premium tool features
- Usage analytics

## 📁 File Processing

PDF processing pipeline:

1. **Upload** - Validate and store files temporarily
2. **Process** - Execute tool-specific operations
3. **Track** - Monitor job progress and status
4. **Download** - Provide secure download links
5. **Cleanup** - Automatic file deletion after 24h

### Supported Operations:
- Merge multiple PDFs
- Split PDF by page ranges
- Compress with quality levels
- Convert images/documents to PDF
- Extract PDF pages as images

## 🌐 Deployment

### Heroku Deployment

1. **Create Heroku app**
```bash
heroku create your-app-name
```

2. **Set environment variables**
```bash
heroku config:set FLASK_ENV=production
heroku config:set SUPABASE_URL=your_url
# Set all other environment variables
```

3. **Deploy**
```bash
git push heroku main
```

### Environment Variables Required:
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_KEY` - Supabase service key
- `STRIPE_SECRET_KEY` - Stripe secret key
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook secret
- `FLASK_SECRET_KEY` - Flask session secret

## 📊 Analytics & Monitoring

### Built-in Analytics:
- User registration and login tracking
- Tool usage statistics
- File processing metrics
- Error logging and monitoring

### Usage Limits:
- Automatic usage tracking per user
- Monthly limit resets
- Upgrade prompts for limit exceeds

## 🔧 Development

### API Routes:

#### Authentication (`/api/auth`)
- `POST /register` - User registration
- `POST /login` - User login
- `POST /logout` - User logout
- `GET /verify-session` - Session validation

#### PDF Tools (`/api/pdf`)
- `POST /upload` - File upload
- `POST /merge` - Merge PDFs
- `POST /split` - Split PDF
- `POST /compress` - Compress PDF
- `POST /convert` - Convert files
- `GET /job/{id}/status` - Job status
- `GET /download/{id}` - Download file

#### Payments (`/api/payments`)
- `POST /create-checkout-session` - Stripe checkout
- `POST /webhook` - Stripe webhooks
- `GET /subscription/status` - Subscription info
- `POST /subscription/cancel` - Cancel subscription

#### Users (`/api/users`)
- `GET /profile` - Get user profile
- `PUT /profile` - Update profile
- `GET /jobs` - Job history
- `DELETE /delete-account` - Delete account

### Frontend Structure:

#### SnackPDF (`/snackpdf`)
- Bootstrap 5.3 responsive design
- Tool grid with iLovePDF-inspired layout
- Drag & drop file upload
- Real-time processing status
- Usage tracking widgets

#### Core JavaScript (`/snackpdf/static/js`)
- `main.js` - Primary application logic
- `auth.js` - Authentication management
- Modular, class-based architecture
- Error handling and user feedback

## 🚦 Testing

### Manual Testing:
1. Test all PDF tools with various file types
2. Verify authentication flow
3. Test payment integration (Stripe test mode)
4. Check usage limit enforcement
5. Validate file cleanup processes

### Load Testing:
- Test concurrent file uploads
- Monitor memory usage during processing
- Verify database performance under load

## 🔒 Security

### File Security:
- File type validation
- Size limit enforcement  
- Temporary file cleanup
- Secure download URLs

### Data Security:
- RLS policies on all tables
- Session token validation
- Password hashing (bcrypt)
- CORS configuration

### API Security:
- Rate limiting (recommended)
- Input validation
- Error message sanitization
- Secure headers

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

Copyright © 2024 NEW_MONO_PDF. All rights reserved.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Email: support@snackpdf.com
- Documentation: [Link to docs]

---

**Built with ❤️ for PDF lovers everywhere**