#!/bin/bash
# Deployment script for NEW_MONO_PDF

set -e

echo "🚀 Starting deployment process..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if we're in the correct directory
if [ ! -f "api/app.py" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Install dependencies
print_status "Installing Python dependencies..."
cd api
pip install -r requirements.txt
cd ..

# Check environment variables
print_status "Checking environment variables..."
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating from template..."
    cp .env.template .env
    print_warning "Please edit .env with your actual configuration values"
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p tmp/uploads
mkdir -p tmp/pdf_processing
mkdir -p logs

# Set up database
print_status "Setting up database..."
if [ -n "$DATABASE_URL" ] || [ -n "$SUPABASE_URL" ]; then
    print_status "Database configuration found"
    # In production, you would run migrations here
    # psql $DATABASE_URL -f supabase/schema.sql
else
    print_warning "No database configuration found in environment"
fi

# Test application
print_status "Testing application..."
cd api
python -c "import app; print('✓ Application imports successfully')"
cd ..

# Static file optimization (if needed)
print_status "Optimizing static files..."
# In production, you might want to minify CSS/JS files here

# Set proper permissions
print_status "Setting file permissions..."
chmod +x scripts/*.sh 2>/dev/null || true

print_status "Deployment preparation complete!"

echo ""
echo "📋 Next steps:"
echo "1. Set up your environment variables in .env"
echo "2. Configure your database (Supabase recommended)"
echo "3. Set up Stripe webhooks"
echo "4. Deploy to Heroku:"
echo "   - heroku create your-app-name"
echo "   - heroku config:set $(cat .env | grep -v '^#' | xargs)"
echo "   - git push heroku main"
echo ""
echo "For local development:"
echo "   cd api && python app.py"
echo ""
print_status "Deployment script completed successfully!"