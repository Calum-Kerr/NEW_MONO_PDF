# Scripts Directory

This directory contains utility scripts for development, deployment, and maintenance of the PDF tools platform.

## Scripts

### `setup.sh`
Development environment setup script. Run this first to set up your local development environment.

```bash
./scripts/setup.sh
```

What it does:
- Creates Python virtual environment
- Installs backend dependencies
- Creates environment file from template
- Sets up necessary directories

### `dev.sh`
Development server script. Starts all servers for local development.

```bash
./scripts/dev.sh
```

Starts:
- Flask API server on port 5000
- SnackPDF frontend on port 3000  
- RevisePDF frontend on port 3001

### `deploy.sh`
Deployment preparation script for Heroku.

```bash
./scripts/deploy.sh
```

What it does:
- Checks dependencies
- Provides deployment instructions
- Lists required environment variables

## Usage

1. **Initial Setup:**
   ```bash
   ./scripts/setup.sh
   ```

2. **Configure Environment:**
   Edit `api/.env` with your configuration values

3. **Start Development:**
   ```bash
   ./scripts/dev.sh
   ```

4. **Deploy to Production:**
   ```bash
   ./scripts/deploy.sh
   ```

## Environment Variables

Required for development and production:

```bash
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your_secret_key

# Supabase Configuration  
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Stripe Configuration
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=your_webhook_secret

# Email Configuration (optional)
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

## Additional Scripts

You can add more scripts here for:
- Database migrations
- Backup operations
- Testing automation
- Performance monitoring
- Log analysis