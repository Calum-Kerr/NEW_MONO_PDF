#!/bin/bash

# Enhanced deployment script for PDF tools platform on Heroku
# Supports both snackpdf.com and revisepdf.com custom domains

set -e  # Exit on any error

echo "🚀 Starting Heroku deployment for PDF Tools Platform..."

# Configuration
SNACKPDF_APP="${HEROKU_SNACKPDF_APP:-snackpdf-prod}"
REVISEPDF_APP="${HEROKU_REVISEPDF_APP:-revisepdf-prod}"
GIT_BRANCH="${DEPLOY_BRANCH:-main}"

# Color codes for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v heroku &> /dev/null; then
        log_error "Heroku CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! heroku auth:whoami &> /dev/null; then
        log_error "Please login to Heroku first: heroku auth:login"
        exit 1
    fi
    
    if ! command -v git &> /dev/null; then
        log_error "Git is not installed."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Create Heroku apps if they don't exist
create_heroku_apps() {
    log_info "Creating Heroku applications..."
    
    # Create SnackPDF app
    if heroku apps:info $SNACKPDF_APP &> /dev/null; then
        log_info "SnackPDF app '$SNACKPDF_APP' already exists"
    else
        log_info "Creating SnackPDF app '$SNACKPDF_APP'..."
        heroku apps:create $SNACKPDF_APP --region us
        log_success "Created SnackPDF app"
    fi
    
    # Create RevisePDF app
    if heroku apps:info $REVISEPDF_APP &> /dev/null; then
        log_info "RevisePDF app '$REVISEPDF_APP' already exists"
    else
        log_info "Creating RevisePDF app '$REVISEPDF_APP'..."
        heroku apps:create $REVISEPDF_APP --region us
        log_success "Created RevisePDF app"
    fi
}

# Configure environment variables
configure_environment() {
    log_info "Configuring environment variables..."
    
    # Common environment variables for both apps
    ENV_VARS=(
        "FLASK_ENV=production"
        "SECRET_KEY=${SECRET_KEY:-$(openssl rand -hex 32)}"
        "SUPABASE_URL=${SUPABASE_URL}"
        "SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}"
        "SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}"
        "SUPABASE_STORAGE_BUCKET=${SUPABASE_STORAGE_BUCKET:-pdf-files}"
        "STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}"
        "STRIPE_WEBHOOK_SECRET=${STRIPE_WEBHOOK_SECRET}"
        "STRIPE_PRO_MONTHLY_PRICE_ID=${STRIPE_PRO_MONTHLY_PRICE_ID}"
        "STRIPE_PRO_YEARLY_PRICE_ID=${STRIPE_PRO_YEARLY_PRICE_ID}"
        "STRIPE_ENTERPRISE_PRICE_ID=${STRIPE_ENTERPRISE_PRICE_ID}"
        "STIRLING_PDF_URL=${STIRLING_PDF_URL:-https://stirling-pdf.herokuapp.com}"
        "STIRLING_PDF_API_KEY=${STIRLING_PDF_API_KEY}"
        "MAX_FILE_SIZE=52428800"
        "WEB_CONCURRENCY=4"
        "GUNICORN_TIMEOUT=120"
    )
    
    # Set environment variables for SnackPDF
    log_info "Setting environment variables for SnackPDF app..."
    for env_var in "${ENV_VARS[@]}"; do
        heroku config:set "$env_var" --app $SNACKPDF_APP
    done
    
    # Set platform-specific variables
    heroku config:set "PLATFORM=snackpdf" --app $SNACKPDF_APP
    heroku config:set "PRIMARY_DOMAIN=snackpdf.com" --app $SNACKPDF_APP
    
    # Set environment variables for RevisePDF
    log_info "Setting environment variables for RevisePDF app..."
    for env_var in "${ENV_VARS[@]}"; do
        heroku config:set "$env_var" --app $REVISEPDF_APP
    done
    
    # Set platform-specific variables
    heroku config:set "PLATFORM=revisepdf" --app $REVISEPDF_APP
    heroku config:set "PRIMARY_DOMAIN=revisepdf.com" --app $REVISEPDF_APP
    
    log_success "Environment variables configured"
}

# Add Heroku Postgres addon
setup_addons() {
    log_info "Setting up Heroku addons..."
    
    # Add Postgres addon to both apps if not already present
    if ! heroku addons --app $SNACKPDF_APP | grep -q "heroku-postgresql"; then
        heroku addons:create heroku-postgresql:mini --app $SNACKPDF_APP
        log_success "Added PostgreSQL to SnackPDF app"
    fi
    
    if ! heroku addons --app $REVISEPDF_APP | grep -q "heroku-postgresql"; then
        heroku addons:create heroku-postgresql:mini --app $REVISEPDF_APP
        log_success "Added PostgreSQL to RevisePDF app"
    fi
    
    # Add Redis for caching and rate limiting
    if ! heroku addons --app $SNACKPDF_APP | grep -q "heroku-redis"; then
        heroku addons:create heroku-redis:mini --app $SNACKPDF_APP
        log_success "Added Redis to SnackPDF app"
    fi
    
    if ! heroku addons --app $REVISEPDF_APP | grep -q "heroku-redis"; then
        heroku addons:create heroku-redis:mini --app $REVISEPDF_APP
        log_success "Added Redis to RevisePDF app"
    fi
    
    # Add New Relic for monitoring (optional)
    if [[ "${NEW_RELIC_LICENSE_KEY}" != "" ]]; then
        if ! heroku addons --app $SNACKPDF_APP | grep -q "newrelic"; then
            heroku addons:create newrelic:wayne --app $SNACKPDF_APP
            heroku config:set NEW_RELIC_LICENSE_KEY="$NEW_RELIC_LICENSE_KEY" --app $SNACKPDF_APP
        fi
        
        if ! heroku addons --app $REVISEPDF_APP | grep -q "newrelic"; then
            heroku addons:create newrelic:wayne --app $REVISEPDF_APP
            heroku config:set NEW_RELIC_LICENSE_KEY="$NEW_RELIC_LICENSE_KEY" --app $REVISEPDF_APP
        fi
        
        log_success "Added New Relic monitoring"
    fi
}

# Configure custom domains
setup_domains() {
    log_info "Setting up custom domains..."
    
    # Add custom domains
    if ! heroku domains --app $SNACKPDF_APP | grep -q "snackpdf.com"; then
        heroku domains:add snackpdf.com --app $SNACKPDF_APP
        heroku domains:add www.snackpdf.com --app $SNACKPDF_APP
        log_success "Added snackpdf.com domains"
    fi
    
    if ! heroku domains --app $REVISEPDF_APP | grep -q "revisepdf.com"; then
        heroku domains:add revisepdf.com --app $REVISEPDF_APP
        heroku domains:add www.revisepdf.com --app $REVISEPDF_APP
        log_success "Added revisepdf.com domains"
    fi
    
    # Enable automated certificate management
    heroku certs:auto:enable --app $SNACKPDF_APP
    heroku certs:auto:enable --app $REVISEPDF_APP
    
    log_success "SSL certificates enabled"
    
    # Display DNS configuration instructions
    echo ""
    log_warning "DNS Configuration Required:"
    echo "Please configure the following DNS records with your domain provider:"
    echo ""
    echo "SnackPDF.com DNS Records:"
    heroku domains --app $SNACKPDF_APP | grep -E "(snackpdf\.com|DNS Target)"
    echo ""
    echo "RevisePDF.com DNS Records:"
    heroku domains --app $REVISEPDF_APP | grep -E "(revisepdf\.com|DNS Target)"
    echo ""
}

# Deploy applications
deploy_apps() {
    log_info "Deploying applications..."
    
    # Ensure we're on the correct branch
    current_branch=$(git branch --show-current)
    if [[ "$current_branch" != "$GIT_BRANCH" ]]; then
        log_warning "Currently on branch '$current_branch', switching to '$GIT_BRANCH'"
        git checkout $GIT_BRANCH
    fi
    
    # Add Heroku remotes if they don't exist
    if ! git remote | grep -q "heroku-snackpdf"; then
        heroku git:remote -a $SNACKPDF_APP -r heroku-snackpdf
    fi
    
    if ! git remote | grep -q "heroku-revisepdf"; then
        heroku git:remote -a $REVISEPDF_APP -r heroku-revisepdf
    fi
    
    # Deploy to both apps
    log_info "Deploying to SnackPDF app..."
    git push heroku-snackpdf $GIT_BRANCH:main --force
    
    log_info "Deploying to RevisePDF app..."
    git push heroku-revisepdf $GIT_BRANCH:main --force
    
    log_success "Deployment completed"
}

# Scale dynos for production
scale_dynos() {
    log_info "Scaling dynos for production..."
    
    # Scale web dynos for both apps
    heroku ps:scale web=2:standard-1x --app $SNACKPDF_APP
    heroku ps:scale web=2:standard-1x --app $REVISEPDF_APP
    
    # Scale worker dynos if background processing is needed
    # heroku ps:scale worker=1:standard-1x --app $SNACKPDF_APP
    # heroku ps:scale worker=1:standard-1x --app $REVISEPDF_APP
    
    log_success "Dynos scaled for production load"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Note: Since we're using Supabase, migrations are handled there
    # This is a placeholder for any Heroku-specific database setup
    
    log_success "Database setup completed"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check app status
    heroku ps --app $SNACKPDF_APP
    heroku ps --app $REVISEPDF_APP
    
    # Test health endpoints
    SNACKPDF_URL="https://${SNACKPDF_APP}.herokuapp.com"
    REVISEPDF_URL="https://${REVISEPDF_APP}.herokuapp.com"
    
    if curl -f "$SNACKPDF_URL/health" > /dev/null 2>&1; then
        log_success "SnackPDF app is responding"
    else
        log_error "SnackPDF app health check failed"
    fi
    
    if curl -f "$REVISEPDF_URL/health" > /dev/null 2>&1; then
        log_success "RevisePDF app is responding"
    else
        log_error "RevisePDF app health check failed"
    fi
    
    echo ""
    log_success "Deployment verification completed!"
    echo ""
    echo "📱 Application URLs:"
    echo "   SnackPDF: $SNACKPDF_URL"
    echo "   RevisePDF: $REVISEPDF_URL"
    echo ""
    echo "🌐 Custom Domain URLs (after DNS configuration):"
    echo "   SnackPDF: https://snackpdf.com"
    echo "   RevisePDF: https://revisepdf.com"
}

# Main deployment flow
main() {
    log_info "PDF Tools Platform - Heroku Deployment"
    echo "========================================"
    
    check_prerequisites
    create_heroku_apps
    setup_addons
    configure_environment
    setup_domains
    deploy_apps
    scale_dynos
    run_migrations
    verify_deployment
    
    log_success "🎉 Deployment completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Configure DNS records as shown above"
    echo "2. Set up your Supabase project and import the schema"
    echo "3. Configure Stripe webhooks to point to your apps"
    echo "4. Test both applications thoroughly"
    echo ""
    echo "For monitoring and logs:"
    echo "  heroku logs --tail --app $SNACKPDF_APP"
    echo "  heroku logs --tail --app $REVISEPDF_APP"
}

# Handle script arguments
case "${1:-}" in
    "config-only")
        configure_environment
        ;;
    "deploy-only")
        deploy_apps
        ;;
    "verify")
        verify_deployment
        ;;
    *)
        main
        ;;
esac