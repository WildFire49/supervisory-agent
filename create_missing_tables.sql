-- Create missing business_rules table and related tables
-- Run this in your PostgreSQL database

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Business Rules Table
CREATE TABLE IF NOT EXISTS business_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id VARCHAR(255) UNIQUE NOT NULL,
    connection_id UUID NOT NULL,
    category VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    trigger_patterns JSONB DEFAULT '[]'::jsonb,
    table_patterns JSONB DEFAULT '[]'::jsonb,
    column_patterns JSONB DEFAULT '[]'::jsonb,
    allowed_tables JSONB DEFAULT '[]'::jsonb,
    forbidden_tables JSONB DEFAULT '[]'::jsonb,
    required_joins JSONB DEFAULT '[]'::jsonb,
    date_field_mappings JSONB DEFAULT '{}'::jsonb,
    sql_transformations JSONB DEFAULT '[]'::jsonb,
    confidence_score FLOAT DEFAULT 0.8,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    positive_examples JSONB DEFAULT '[]'::jsonb,
    negative_examples JSONB DEFAULT '[]'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_business_rules_rule_id ON business_rules(rule_id);
CREATE INDEX IF NOT EXISTS idx_business_rules_connection_id ON business_rules(connection_id);
CREATE INDEX IF NOT EXISTS idx_business_rules_category ON business_rules(category);

-- Business Rule Templates Table
CREATE TABLE IF NOT EXISTS business_rule_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    domain VARCHAR(100) NOT NULL,
    extraction_patterns JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_business_rule_templates_template_id ON business_rule_templates(template_id);
CREATE INDEX IF NOT EXISTS idx_business_rule_templates_domain ON business_rule_templates(domain);

-- Rule Validation Logs Table
CREATE TABLE IF NOT EXISTS rule_validation_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    connection_id UUID NOT NULL,
    query_id VARCHAR(255),
    original_sql TEXT NOT NULL,
    corrected_sql TEXT,
    is_valid BOOLEAN NOT NULL,
    violated_rules JSONB DEFAULT '[]'::jsonb,
    warnings JSONB DEFAULT '[]'::jsonb,
    suggestions JSONB DEFAULT '[]'::jsonb,
    validation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_time_ms FLOAT
);

CREATE INDEX IF NOT EXISTS idx_rule_validation_logs_connection_id ON rule_validation_logs(connection_id);
CREATE INDEX IF NOT EXISTS idx_rule_validation_logs_query_id ON rule_validation_logs(query_id);

-- Rule Extraction Logs Table
CREATE TABLE IF NOT EXISTS rule_extraction_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    connection_id UUID NOT NULL,
    schema_context_hash VARCHAR(64) NOT NULL,
    domain_hints JSONB DEFAULT '[]'::jsonb,
    extracted_rules_count INTEGER DEFAULT 0,
    confidence_score FLOAT DEFAULT 0.0,
    extraction_notes TEXT,
    extraction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_time_ms FLOAT,
    llm_model_used VARCHAR(100),
    extracted_rule_ids JSONB DEFAULT '[]'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_rule_extraction_logs_connection_id ON rule_extraction_logs(connection_id);

-- Insert some basic business rules for your existing connection
INSERT INTO business_rules (
    rule_id, connection_id, category, severity, title, description,
    allowed_tables, forbidden_tables, trigger_patterns
) VALUES (
    'collection_query_rule_1',
    'cf07263-83e2-449f-8e26-08f7d3a584b6'::uuid,
    'data_access',
    'high',
    'Collection Query Enforcement',
    'Enforce proper table usage for collection-related queries',
    '["staging_dashboard.loan_emi_mapping", "staging_dashboard.collection_details", "staging_dashboard.collection_user", "staging_dashboard.employee"]'::jsonb,
    '["staging_dashboard.disbursement_fed", "staging_dashboard.loan_fed"]'::jsonb,
    '["collection", "emi", "field officer", "payment"]'::jsonb
) ON CONFLICT (rule_id) DO NOTHING;

-- Verify tables were created
SELECT 
    table_name,
    table_type
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('business_rules', 'business_rule_templates', 'rule_validation_logs', 'rule_extraction_logs')
ORDER BY table_name;
