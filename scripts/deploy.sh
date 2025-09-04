#!/bin/bash

# Deployment script for PDF tools platform on Heroku

echo "🚀 Starting deployment process..."

# Check if we're in the right directory
if [ ! -f "Procfile" ]; then
    echo "❌ Error: Procfile not found. Make sure you're in the project root directory."
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
cd api
pip install -r requirements.txt
cd ..

# Run database migrations if needed
echo "🗄️ Setting up database..."
# Note: Supabase migrations would be run here

# Build frontend assets if needed
echo "🎨 Building frontend assets..."
# Note: Any build steps for frontend would go here

# Set environment variables
echo "⚙️ Setting environment variables..."
echo "Make sure to set the following environment variables in Heroku:"
echo "- FLASK_ENV=production"
echo "- SECRET_KEY=your_secret_key"
echo "- SUPABASE_URL=your_supabase_url"
echo "- SUPABASE_ANON_KEY=your_anon_key"
echo "- SUPABASE_SERVICE_ROLE_KEY=your_service_role_key"
echo "- STRIPE_SECRET_KEY=your_stripe_secret_key"
echo "- STRIPE_WEBHOOK_SECRET=your_webhook_secret"

echo "✅ Deployment preparation complete!"
echo ""
echo "To deploy to Heroku:"
echo "1. heroku create your-app-name"
echo "2. heroku config:set [environment variables]"
echo "3. git push heroku main"
echo ""
echo "For multiple apps (snackpdf.com and revisepdf.com):"
echo "1. heroku create snackpdf-app"
echo "2. heroku create revisepdf-app"
echo "3. Configure custom domains in Heroku dashboard"