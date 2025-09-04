-- NEW_MONO_PDF Database Schema
-- This schema supports both SnackPDF and RevisePDF applications
-- Created: $(date)

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users table for authentication and profile management
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    avatar_url TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    subscription_status VARCHAR(20) DEFAULT 'free', -- free, premium, enterprise
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sessions table for managing user sessions
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Subscriptions table for Stripe integration
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    stripe_customer_id VARCHAR(255),
    status VARCHAR(50) NOT NULL, -- active, canceled, past_due, etc.
    plan_name VARCHAR(100) NOT NULL, -- premium, enterprise
    plan_price DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'USD',
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- PDF jobs table for tracking all PDF operations
CREATE TABLE IF NOT EXISTS pdf_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_id VARCHAR(255), -- For anonymous users
    job_type VARCHAR(50) NOT NULL, -- merge, split, compress, convert, edit, etc.
    application VARCHAR(20) NOT NULL, -- snackpdf, revisepdf
    input_file_name VARCHAR(255),
    input_file_size BIGINT,
    input_file_url TEXT,
    output_file_name VARCHAR(255),
    output_file_size BIGINT,
    output_file_url TEXT,
    parameters JSONB, -- Store job-specific parameters
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Job status table for tracking async operations
CREATE TABLE IF NOT EXISTS job_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES pdf_jobs(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed
    progress_percentage INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit log for analytics and tracking
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_id VARCHAR(255),
    action VARCHAR(100) NOT NULL, -- login, logout, upload, download, subscribe, etc.
    entity_type VARCHAR(50), -- user, job, subscription
    entity_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- File storage metadata
CREATE TABLE IF NOT EXISTS file_storage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    job_id UUID REFERENCES pdf_jobs(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    file_type VARCHAR(100),
    storage_path TEXT NOT NULL,
    storage_provider VARCHAR(50) DEFAULT 'supabase', -- supabase, s3, local
    is_temporary BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Usage limits table for freemium model
CREATE TABLE IF NOT EXISTS usage_limits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    jobs_used INTEGER DEFAULT 0,
    jobs_limit INTEGER DEFAULT 5, -- Free tier limit
    file_size_used BIGINT DEFAULT 0,
    file_size_limit BIGINT DEFAULT 10485760, -- 10MB in bytes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_id ON subscriptions(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_pdf_jobs_user_id ON pdf_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_pdf_jobs_session_id ON pdf_jobs(session_id);
CREATE INDEX IF NOT EXISTS idx_pdf_jobs_type ON pdf_jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_pdf_jobs_created_at ON pdf_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_job_status_job_id ON job_status(job_id);
CREATE INDEX IF NOT EXISTS idx_job_status_status ON job_status(status);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_file_storage_user_id ON file_storage(user_id);
CREATE INDEX IF NOT EXISTS idx_file_storage_job_id ON file_storage(job_id);
CREATE INDEX IF NOT EXISTS idx_usage_limits_user_id ON usage_limits(user_id);

-- Functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_job_status_updated_at BEFORE UPDATE ON job_status
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_usage_limits_updated_at BEFORE UPDATE ON usage_limits
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE pdf_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE file_storage ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_limits ENABLE ROW LEVEL SECURITY;

-- Basic RLS policies (users can only access their own data)
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can view own sessions" ON sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view own subscriptions" ON subscriptions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view own pdf jobs" ON pdf_jobs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own pdf jobs" ON pdf_jobs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own job status" ON job_status
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM pdf_jobs 
            WHERE pdf_jobs.id = job_status.job_id 
            AND pdf_jobs.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can view own file storage" ON file_storage
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view own usage limits" ON usage_limits
    FOR SELECT USING (auth.uid() = user_id);

-- Insert default usage limits for new users
CREATE OR REPLACE FUNCTION create_user_usage_limits()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO usage_limits (user_id, period_start, period_end)
    VALUES (
        NEW.id,
        DATE_TRUNC('month', NOW()),
        DATE_TRUNC('month', NOW()) + INTERVAL '1 month' - INTERVAL '1 day'
    );
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER create_usage_limits_for_new_user
    AFTER INSERT ON users
    FOR EACH ROW EXECUTE FUNCTION create_user_usage_limits();

-- Views for common queries
CREATE VIEW user_current_usage AS
SELECT 
    u.id as user_id,
    u.email,
    u.subscription_status,
    ul.jobs_used,
    ul.jobs_limit,
    ul.file_size_used,
    ul.file_size_limit,
    ul.period_start,
    ul.period_end
FROM users u
LEFT JOIN usage_limits ul ON u.id = ul.user_id
WHERE ul.period_start <= NOW() AND ul.period_end >= NOW();

CREATE VIEW job_summary AS
SELECT 
    pj.id,
    pj.user_id,
    pj.job_type,
    pj.application,
    pj.input_file_name,
    pj.output_file_name,
    js.status,
    js.progress_percentage,
    js.error_message,
    pj.created_at,
    js.completed_at
FROM pdf_jobs pj
LEFT JOIN job_status js ON pj.id = js.job_id;