# PDF Tools Monorepo

A comprehensive PDF tools platform with two branded sites:
- **snackpdf.com** → All-in-one PDF tools (iLovePDF clone)
- **revisepdf.com** → Live PDF editor (PDFfiller clone)

## 🏗️ Project Structure

```
├── snackpdf/          # Frontend for snackpdf.com (iLovePDF-style)
│   ├── index.html     # Main homepage with tool grid
│   ├── css/           # Custom styles and Bootstrap theme
│   └── js/            # Frontend JavaScript and API integration
├── revisepdf/         # Frontend for revisepdf.com (live PDF editor)
│   ├── index.html     # PDF editor interface
│   ├── css/           # Editor-specific styles
│   └── js/            # PDF viewer and annotation tools
├── api/               # Backend API (Python Flask)
│   ├── app.py         # Main Flask application
│   ├── requirements.txt # Python dependencies
│   └── .env.example   # Environment configuration template
├── supabase/          # Database schema and migrations
│   ├── schema.sql     # Complete database schema
│   └── README.md      # Database documentation
├── scripts/           # Development tools and deployment scripts
│   ├── setup.sh       # Development environment setup
│   ├── dev.sh         # Start development servers
│   └── deploy.sh      # Heroku deployment script
├── core/              # Shared utilities (auth, payments, file handling)
│   ├── auth.py        # Authentication and session management
│   ├── payments.py    # Stripe integration and webhooks
│   ├── files.py       # File upload and storage management
│   └── utils.py       # General utilities and rate limiting
├── Procfile           # Heroku deployment configuration
└── README.md          # This file
```

## 🚀 Tech Stack

- **Frontend**: HTML + Bootstrap 5.3 + Vanilla JavaScript
- **Backend**: Python Flask with RESTful API
- **Database**: Supabase (auth, database, storage)
- **Payments**: Stripe (subscriptions and webhooks)
- **PDF Processing**: StirlingPDF integration for advanced operations
- **Hosting**: Heroku with custom domains and SSL
- **Storage**: Supabase Storage for file handling
- **Monitoring**: New Relic and built-in performance tracking

## ⚡ Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd NEW_MONO_PDF
./scripts/setup.sh
```

### 2. Configure Environment

Copy and edit the environment file:

```bash
cp api/.env.example api/.env
# Edit api/.env with your configuration
```

Required configuration:
- Supabase project URL and keys
- Stripe API keys and webhook secret
- Email SMTP settings (optional)

### 3. Database Setup

1. Create a Supabase project at https://supabase.com
2. Run the SQL schema in Supabase SQL editor:
   ```sql
   -- Copy and paste contents of supabase/schema.sql
   ```
3. Configure RLS policies and storage bucket

### 4. Start Development

```bash
./scripts/dev.sh
```

This starts:
- Flask API server on http://localhost:5000
- SnackPDF frontend on http://localhost:3000
- RevisePDF frontend on http://localhost:3001

## 🌟 Features

### SnackPDF (iLovePDF Clone)
- **Merge PDF**: Combine multiple PDF files
- **Split PDF**: Extract pages or split into separate files
- **Compress PDF**: Reduce file size while maintaining quality
- **Convert to PDF**: Convert Word, Excel, PowerPoint, images to PDF
- **Extract Pages**: Extract specific pages from documents
- **Rotate PDF**: Rotate pages in documents
- **Secure Upload**: Drag-and-drop file upload with validation
- **User Accounts**: Registration, login, usage tracking
- **Responsive Design**: Mobile-friendly interface

### RevisePDF (PDFfiller Clone)
- **Live PDF Editor**: In-browser PDF editing experience
- **Fill Forms**: Add text to PDF forms and fields
- **Digital Signatures**: Create and insert signatures
- **Annotations**: Highlight, draw, add notes
- **Text Tools**: Add custom text with formatting options
- **Image Insertion**: Add logos and images to documents
- **Real-time Preview**: See changes as you make them
- **Save & Download**: Export edited PDFs

### Backend API
- **RESTful API**: Clean, documented endpoints
- **Authentication**: JWT-based session management
- **File Upload**: Secure file handling with validation
- **Rate Limiting**: Built-in protection against abuse
- **Audit Logging**: Comprehensive user activity tracking
- **Stripe Integration**: Subscription management and webhooks
- **Error Handling**: Comprehensive error responses

## 🔐 Security Features

- **Row Level Security**: Database-level access controls
- **File Validation**: Comprehensive upload validation
- **Rate Limiting**: API endpoint protection
- **Session Management**: Secure token-based authentication
- **CORS Configuration**: Proper cross-origin handling
- **Input Sanitization**: Protection against XSS and injection
- **File Expiration**: Automatic cleanup of temporary files

## 💳 Subscription Tiers

### Free Tier
- 5 operations per month
- Basic PDF tools
- File size limit: 10MB
- Files deleted after 24 hours

### Pro Tier ($9.99/month)
- Unlimited operations
- All PDF tools including OCR and advanced compression
- File size limit: 50MB
- Priority processing
- Email support

### Enterprise Tier ($29.99/month)
- Everything in Pro
- API access with keys
- White-label options
- Custom integrations
- Phone support
- Custom usage limits

## 📊 SEO Optimization

Both sites are optimized for search engines with:
- **Meta Tags**: Comprehensive title, description, keywords
- **Open Graph**: Social media sharing optimization
- **Twitter Cards**: Twitter-specific sharing tags
- **Structured Data**: JSON-LD markup for rich snippets
- **Canonical URLs**: Proper URL canonicalization
- **Mobile-First**: Responsive design principles
- **Fast Loading**: Optimized assets and CDN usage
- **Semantic HTML**: Proper heading structure and landmarks

## 🚀 Deployment

### Development
```bash
./scripts/dev.sh
```

### Production (Heroku)

1. **Create Heroku Apps:**
   ```bash
   heroku create snackpdf-app
   heroku create revisepdf-app
   ```

2. **Configure Environment Variables:**
   ```bash
   heroku config:set FLASK_ENV=production --app snackpdf-app
   heroku config:set SECRET_KEY=your_secret_key --app snackpdf-app
   # ... add all required environment variables
   ```

3. **Deploy:**
   ```bash
   git push heroku main
   ```

4. **Configure Custom Domains:**
   ```bash
   heroku domains:add snackpdf.com --app snackpdf-app
   heroku domains:add revisepdf.com --app revisepdf-app
   ```

## 📝 API Documentation

### Authentication Endpoints
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/profile` - Get user profile

### File Operations
- `POST /api/files/upload` - Upload files for processing

### PDF Processing
- `POST /api/pdf/merge` - Merge multiple PDFs
- `POST /api/pdf/split` - Split PDF into pages
- `POST /api/pdf/compress` - Compress PDF file size
- `POST /api/pdf/convert` - Convert files to PDF

### Payment Operations
- `POST /api/payments/create-checkout` - Create Stripe checkout
- `POST /api/payments/portal` - Create customer portal
- `POST /api/payments/webhook` - Handle Stripe webhooks

### Utility Endpoints
- `GET /health` - Health check
- `GET /api/debug/info` - Debug information (dev only)

## 🧪 Testing

Run the test suite:
```bash
cd api
python -m pytest tests/
```

Test the API endpoints:
```bash
curl http://localhost:5000/health
```

## 📚 Documentation

Detailed documentation is available in each component:
- [API Documentation](api/README.md)
- [Database Schema](supabase/README.md)
- [Core Utilities](core/README.md)
- [Deployment Scripts](scripts/README.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation in each component
- Review the example environment configuration

## 🔄 Roadmap

### Phase 1 (Current)
- ✅ Core infrastructure and database schema
- ✅ Authentication and user management
- ✅ Basic PDF operations (merge, split)
- ✅ Payment integration with Stripe
- ✅ Frontend interfaces for both sites

### Phase 2 (Completed)
- ✅ StirlingPDF integration for advanced operations
- ✅ Enhanced Heroku deployment with custom domains
- ✅ Production-ready scaling configuration
- ✅ Comprehensive documentation and guides
- ✅ Advanced error handling and graceful degradation

### Phase 3 (Current)
- ✅ OCR and text extraction capabilities
- ✅ Advanced compression algorithms  
- ✅ Batch processing for multiple files
- ✅ Mobile applications (React Native)
- ✅ API for third-party integrations
- ✅ White-label solutions for enterprises
- ✅ Advanced analytics and reporting

### Phase 4
- [ ] AI-powered document analysis
- [ ] Collaborative editing features
- [ ] Integration with cloud storage providers
- [ ] Advanced security features (encryption, DRM)

## 📚 Enhanced Documentation

- **[Deployment Guide](DEPLOYMENT.md)** - Comprehensive production deployment instructions
- **[StirlingPDF Integration](STIRLING_INTEGRATION.md)** - Advanced PDF processing integration guide
- [API Documentation](api/README.md) - RESTful API endpoints and usage
- [Database Schema](supabase/README.md) - Database structure and relationships
- [Core Utilities](core/README.md) - Shared functionality and utilities
- [Deployment Scripts](scripts/README.md) - Automated deployment tools