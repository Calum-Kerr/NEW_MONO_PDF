# Production Deployment Guide

This guide provides comprehensive instructions for deploying the PDF Tools Platform to production on Heroku with custom domains.

## 🏗️ Architecture Overview

The platform consists of:
- **Two Heroku Apps**: One for snackpdf.com, one for revisepdf.com
- **Shared Backend**: Flask API with StirlingPDF integration
- **Database**: Supabase (PostgreSQL + Authentication + Storage)
- **Payments**: Stripe with webhook support
- **PDF Processing**: StirlingPDF for advanced operations
- **Domains**: Custom SSL-enabled domains

## 📋 Prerequisites

### Required Services
1. **Heroku Account** with CLI installed
2. **Supabase Project** with database and storage configured
3. **Stripe Account** with API keys
4. **Domain Names**: snackpdf.com and revisepdf.com
5. **StirlingPDF Instance** (optional - can use hosted version)

### Local Development Setup
```bash
# Clone repository
git clone <repository-url>
cd NEW_MONO_PDF

# Install dependencies
cd api
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env with your configuration
```

## 🚀 Production Deployment

### Step 1: Environment Configuration

Set the following environment variables locally for the deployment script:

```bash
# Required - Supabase Configuration
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="eyJ..."
export SUPABASE_SERVICE_ROLE_KEY="eyJ..."
export SUPABASE_STORAGE_BUCKET="pdf-files"

# Required - Stripe Configuration
export STRIPE_SECRET_KEY="sk_live_..."
export STRIPE_WEBHOOK_SECRET="whsec_..."
export STRIPE_PRO_MONTHLY_PRICE_ID="price_..."
export STRIPE_PRO_YEARLY_PRICE_ID="price_..."
export STRIPE_ENTERPRISE_PRICE_ID="price_..."

# Optional - StirlingPDF Configuration
export STIRLING_PDF_URL="https://your-stirling-instance.herokuapp.com"
export STIRLING_PDF_API_KEY="your_api_key"

# Optional - Monitoring
export NEW_RELIC_LICENSE_KEY="your_license_key"

# Optional - Custom App Names
export HEROKU_SNACKPDF_APP="snackpdf-prod"
export HEROKU_REVISEPDF_APP="revisepdf-prod"
```

### Step 2: Deploy to Heroku

Run the enhanced deployment script:

```bash
# Full deployment (recommended for first deployment)
./scripts/deploy.sh

# Or deploy in parts
./scripts/deploy.sh config-only    # Configure environment only
./scripts/deploy.sh deploy-only    # Deploy code only
./scripts/deploy.sh verify         # Verify deployment only
```

The script will:
1. ✅ Create Heroku applications
2. ✅ Configure environment variables
3. ✅ Set up add-ons (PostgreSQL, Redis, New Relic)
4. ✅ Configure custom domains with SSL
5. ✅ Deploy applications
6. ✅ Scale dynos for production
7. ✅ Verify deployment health

### Step 3: Domain Configuration

After deployment, configure DNS records with your domain provider:

**For snackpdf.com:**
```
Type: CNAME
Name: @
Value: <DNS_TARGET_FROM_HEROKU>

Type: CNAME  
Name: www
Value: <DNS_TARGET_FROM_HEROKU>
```

**For revisepdf.com:**
```
Type: CNAME
Name: @
Value: <DNS_TARGET_FROM_HEROKU>

Type: CNAME
Name: www
Value: <DNS_TARGET_FROM_HEROKU>
```

*Replace `<DNS_TARGET_FROM_HEROKU>` with the values shown after deployment.*

### Step 4: Supabase Configuration

1. **Import Database Schema:**
   ```sql
   -- Run the contents of supabase/schema.sql in Supabase SQL editor
   ```

2. **Configure Storage Bucket:**
   - Create bucket named `pdf-files`
   - Set appropriate RLS policies
   - Configure CORS for file uploads

3. **Authentication Settings:**
   - Enable email authentication
   - Configure redirect URLs for your domains
   - Set up any social auth providers

### Step 5: Stripe Configuration

1. **Webhook Endpoints:**
   - Add webhook endpoint: `https://snackpdf.com/api/payments/webhook`
   - Add webhook endpoint: `https://revisepdf.com/api/payments/webhook`
   - Select events: `customer.subscription.*`, `invoice.*`, `checkout.session.completed`

2. **Products and Prices:**
   - Create Pro Monthly subscription
   - Create Pro Yearly subscription  
   - Create Enterprise subscription
   - Update environment variables with price IDs

## 📊 Monitoring and Maintenance

### Application Monitoring
```bash
# View logs
heroku logs --tail --app snackpdf-prod
heroku logs --tail --app revisepdf-prod

# Check app status
heroku ps --app snackpdf-prod
heroku ps --app revisepdf-prod

# Monitor performance
heroku addons:open newrelic --app snackpdf-prod
```

### Health Checks
```bash
# Test health endpoints
curl https://snackpdf.com/health
curl https://revisepdf.com/health

# Test StirlingPDF integration
curl https://snackpdf.com/api/stirling/health
```

### Scaling

```bash
# Scale web dynos
heroku ps:scale web=4:standard-2x --app snackpdf-prod

# Scale for high traffic
heroku ps:scale web=8:performance-m --app snackpdf-prod

# Add worker dynos for background processing
heroku ps:scale worker=2:standard-1x --app snackpdf-prod
```

## 🔧 Configuration Management

### Environment Variables

**Core Configuration:**
- `FLASK_ENV=production`
- `SECRET_KEY` - Generated automatically or provide your own
- `WEB_CONCURRENCY=4` - Number of Gunicorn workers
- `GUNICORN_TIMEOUT=120` - Request timeout

**Platform Specific:**
- `PLATFORM=snackpdf` or `PLATFORM=revisepdf`
- `PRIMARY_DOMAIN=snackpdf.com` or `PRIMARY_DOMAIN=revisepdf.com`

**Scaling Configuration:**
```bash
# Update worker count
heroku config:set WEB_CONCURRENCY=8 --app snackpdf-prod

# Update timeout for large file processing
heroku config:set GUNICORN_TIMEOUT=300 --app snackpdf-prod
```

## 🛡️ Security Considerations

### SSL Certificates
- Automated SSL certificates are enabled via Heroku
- Certificates auto-renew before expiration
- Force HTTPS redirects are configured

### Environment Security
- All sensitive data stored in environment variables
- No secrets committed to repository
- Stripe webhook signature verification enabled
- Rate limiting configured for all endpoints

### Database Security
- Row Level Security (RLS) enabled in Supabase
- Service role key used only for server-side operations
- User data isolated by authentication

## 📈 Performance Optimization

### Recommended Add-ons for Scale

**For Production Traffic (1000+ users):**
```bash
# Upgrade database
heroku addons:create heroku-postgresql:standard-0 --app snackpdf-prod

# Add Redis for caching
heroku addons:create heroku-redis:premium-0 --app snackpdf-prod

# Add monitoring
heroku addons:create newrelic:pro --app snackpdf-prod
```

**For Enterprise Scale (10,000+ users):**
```bash
# Dedicated database
heroku addons:create heroku-postgresql:standard-2 --app snackpdf-prod

# High-performance Redis
heroku addons:create heroku-redis:premium-5 --app snackpdf-prod

# Scale to performance dynos
heroku ps:scale web=6:performance-m --app snackpdf-prod
```

### File Processing Optimization
- Large files processed asynchronously
- Background job queue for heavy operations
- CDN integration for static assets
- File cleanup scheduled tasks

## 🚨 Troubleshooting

### Common Issues

**1. Application Won't Start:**
```bash
# Check logs
heroku logs --tail --app snackpdf-prod

# Verify environment variables
heroku config --app snackpdf-prod

# Check dyno status
heroku ps --app snackpdf-prod
```

**2. Database Connection Issues:**
```bash
# Verify Supabase configuration
heroku config:get SUPABASE_URL --app snackpdf-prod

# Test database connectivity
heroku run python -c "from core import auth_manager; print('DB OK')" --app snackpdf-prod
```

**3. StirlingPDF Integration Issues:**
```bash
# Test StirlingPDF connectivity
curl https://snackpdf.com/api/stirling/health

# Check StirlingPDF configuration
heroku config:get STIRLING_PDF_URL --app snackpdf-prod
```

**4. Domain/SSL Issues:**
```bash
# Check domain status
heroku domains --app snackpdf-prod

# Verify SSL certificates
heroku certs --app snackpdf-prod

# Force SSL certificate refresh
heroku certs:auto:refresh --app snackpdf-prod
```

### Performance Troubleshooting

**High Response Times:**
1. Check dyno metrics in Heroku dashboard
2. Review New Relic performance data
3. Scale dynos if needed
4. Optimize database queries

**Memory Issues:**
1. Monitor dyno memory usage
2. Scale to larger dyno types
3. Optimize file processing
4. Implement file cleanup

## 📞 Support and Maintenance

### Regular Maintenance Tasks

**Weekly:**
- Review application logs for errors
- Check dyno utilization metrics
- Monitor database performance
- Verify SSL certificate status

**Monthly:**
- Update dependencies if needed
- Review security vulnerabilities
- Analyze usage patterns
- Optimize resource allocation

**Quarterly:**
- Performance review and optimization
- Security audit
- Backup and disaster recovery testing
- Cost optimization review

### Backup Strategy

**Database:**
- Heroku Postgres automated daily backups
- Supabase built-in backup system
- Manual backup before major updates

**Configuration:**
- Environment variables documented
- Deployment scripts in version control
- Infrastructure as code

For additional support, refer to:
- Heroku documentation: https://devcenter.heroku.com/
- Supabase documentation: https://supabase.com/docs
- Stripe documentation: https://stripe.com/docs