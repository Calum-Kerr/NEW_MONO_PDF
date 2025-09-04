# Supabase Configuration

This directory contains the Supabase database schema and configuration files for the PDF tools platform.

## Files

- `schema.sql` - Complete database schema with tables, indexes, and RLS policies
- `seed.sql` - Sample data for development and testing
- `migrations/` - Database migration files (future)

## Database Tables

### Core Tables
- **users** - User profiles extending Supabase auth
- **sessions** - User session tracking
- **subscriptions** - Stripe subscription management
- **pdf_jobs** - All PDF processing operations
- **job_status** - Async job status tracking
- **audit_log** - Analytics and user activity tracking
- **api_keys** - API access management

### Key Features
- Row Level Security (RLS) enabled on all tables
- UUID primary keys throughout
- Comprehensive indexing for performance
- Automatic timestamp management
- Cleanup functions for expired data

## Setup

1. Create a new Supabase project
2. Run the schema.sql file in the SQL editor
3. Configure RLS policies as needed
4. Set up environment variables in your application

## Environment Variables

```
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```