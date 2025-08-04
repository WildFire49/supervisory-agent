-- Database initialization script for Supervisory Agent
-- This script creates all necessary tables and initial data

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create customers table
CREATE TABLE IF NOT EXISTS customers (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    bank VARCHAR(100) NOT NULL,
    product VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create workflow_sessions table
CREATE TABLE IF NOT EXISTS workflow_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(id),
    workflow_name VARCHAR(255) NOT NULL,
    current_action VARCHAR(255),
    session_data JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create workflows table for workflow definitions
CREATE TABLE IF NOT EXISTS workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bank VARCHAR(100) NOT NULL,
    product VARCHAR(100) NOT NULL,
    workflow_data JSONB NOT NULL,
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    deleted_at TIMESTAMP WITH TIME ZONE,
    modified_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create pending_workflow_modifications table
CREATE TABLE IF NOT EXISTS pending_workflow_modifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bank VARCHAR(100) NOT NULL,
    product VARCHAR(100) NOT NULL,
    user_id VARCHAR(255),
    modification_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_customers_bank_product ON customers(bank, product);
CREATE INDEX IF NOT EXISTS idx_workflow_sessions_customer_id ON workflow_sessions(customer_id);
CREATE INDEX IF NOT EXISTS idx_workflow_sessions_status ON workflow_sessions(status);
CREATE INDEX IF NOT EXISTS idx_workflows_bank_product ON workflows(bank, product);
CREATE INDEX IF NOT EXISTS idx_workflows_active ON workflows(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_pending_modifications_bank_product ON pending_workflow_modifications(bank, product);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
DROP TRIGGER IF EXISTS update_customers_updated_at ON customers;
CREATE TRIGGER update_customers_updated_at 
    BEFORE UPDATE ON customers 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_workflow_sessions_updated_at ON workflow_sessions;
CREATE TRIGGER update_workflow_sessions_updated_at 
    BEFORE UPDATE ON workflow_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_workflows_updated_at ON workflows;
CREATE TRIGGER update_workflows_updated_at 
    BEFORE UPDATE ON workflows 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample workflow data for SBI KCC
INSERT INTO workflows (bank, product, workflow_data, version, is_active) 
VALUES (
    'SBI',
    'KCC',
    '{
        "name": "KCC Application Process",
        "description": "Kisan Credit Card application workflow for SBI",
        "actions": [
            {
                "id": "welcome",
                "name": "Welcome Screen",
                "description": "Welcome the customer and explain the KCC process",
                "stage": "initiation",
                "order": 1
            },
            {
                "id": "mobile-verification",
                "name": "Mobile Verification",
                "description": "Verify customer mobile number with OTP",
                "stage": "verification",
                "order": 2
            },
            {
                "id": "aadhar-verification",
                "name": "Aadhar Verification",
                "description": "Verify customer Aadhar details",
                "stage": "verification",
                "order": 3
            },
            {
                "id": "verify-otp",
                "name": "OTP Verification",
                "description": "Verify OTP sent to registered mobile",
                "stage": "verification",
                "order": 4
            },
            {
                "id": "personal-details",
                "name": "Personal Details",
                "description": "Collect customer personal information",
                "stage": "data-collection",
                "order": 5
            },
            {
                "id": "address-details",
                "name": "Address Details",
                "description": "Collect customer address information",
                "stage": "data-collection",
                "order": 6
            },
            {
                "id": "land-details",
                "name": "Land Details",
                "description": "Collect agricultural land information",
                "stage": "data-collection",
                "order": 7
            },
            {
                "id": "crop-details",
                "name": "Crop Details",
                "description": "Collect crop cultivation details",
                "stage": "data-collection",
                "order": 8
            },
            {
                "id": "income-details",
                "name": "Income Details",
                "description": "Collect income and financial information",
                "stage": "data-collection",
                "order": 9
            },
            {
                "id": "document-upload",
                "name": "Document Upload",
                "description": "Upload required documents",
                "stage": "documentation",
                "order": 10
            },
            {
                "id": "review-application",
                "name": "Review Application",
                "description": "Review all entered information",
                "stage": "review",
                "order": 11
            },
            {
                "id": "submit-application",
                "name": "Submit Application",
                "description": "Final submission of KCC application",
                "stage": "submission",
                "order": 12
            }
        ]
    }',
    1,
    true
) ON CONFLICT DO NOTHING;

-- Insert sample workflow data for Federal Bank KCC
INSERT INTO workflows (bank, product, workflow_data, version, is_active) 
VALUES (
    'Federal',
    'KCC',
    '{
        "name": "Federal Bank KCC Application",
        "description": "Kisan Credit Card application workflow for Federal Bank",
        "actions": [
            {
                "id": "welcome",
                "name": "Welcome Screen",
                "description": "Welcome to Federal Bank KCC application",
                "stage": "initiation",
                "order": 1
            },
            {
                "id": "mobile-verification",
                "name": "Mobile Verification",
                "description": "Verify mobile number",
                "stage": "verification",
                "order": 2
            },
            {
                "id": "customer-details",
                "name": "Customer Details",
                "description": "Basic customer information",
                "stage": "data-collection",
                "order": 3
            },
            {
                "id": "farming-details",
                "name": "Farming Details",
                "description": "Agricultural information",
                "stage": "data-collection",
                "order": 4
            },
            {
                "id": "document-verification",
                "name": "Document Verification",
                "description": "Upload and verify documents",
                "stage": "documentation",
                "order": 5
            },
            {
                "id": "application-review",
                "name": "Application Review",
                "description": "Final review and submission",
                "stage": "submission",
                "order": 6
            }
        ]
    }',
    1,
    true
) ON CONFLICT DO NOTHING;

-- Insert sample workflow data for Dhanlaxmi Bank KCC
INSERT INTO workflows (bank, product, workflow_data, version, is_active) 
VALUES (
    'Dhanlaxmi',
    'KCC',
    '{
        "name": "Dhanlaxmi Bank KCC Application",
        "description": "Kisan Credit Card application workflow for Dhanlaxmi Bank",
        "actions": [
            {
                "id": "welcome",
                "name": "Welcome Screen",
                "description": "Welcome to Dhanlaxmi Bank KCC",
                "stage": "initiation",
                "order": 1
            },
            {
                "id": "eligibility-check",
                "name": "Eligibility Check",
                "description": "Check customer eligibility",
                "stage": "verification",
                "order": 2
            },
            {
                "id": "basic-details",
                "name": "Basic Details",
                "description": "Customer basic information",
                "stage": "data-collection",
                "order": 3
            },
            {
                "id": "agricultural-details",
                "name": "Agricultural Details",
                "description": "Farm and crop details",
                "stage": "data-collection",
                "order": 4
            },
            {
                "id": "financial-details",
                "name": "Financial Details",
                "description": "Income and financial information",
                "stage": "data-collection",
                "order": 5
            },
            {
                "id": "document-submission",
                "name": "Document Submission",
                "description": "Submit required documents",
                "stage": "documentation",
                "order": 6
            },
            {
                "id": "final-submission",
                "name": "Final Submission",
                "description": "Complete application submission",
                "stage": "submission",
                "order": 7
            }
        ]
    }',
    1,
    true
) ON CONFLICT DO NOTHING;

-- Create a view for active workflows
CREATE OR REPLACE VIEW active_workflows AS
SELECT 
    id,
    bank,
    product,
    workflow_data,
    version,
    created_at,
    updated_at
FROM workflows 
WHERE is_active = true AND deleted_at IS NULL;

-- Grant necessary permissions (if needed for application user)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- Display success message
DO $$
BEGIN
    RAISE NOTICE 'Database initialization completed successfully!';
    RAISE NOTICE 'Created tables: customers, workflow_sessions, workflows, pending_workflow_modifications';
    RAISE NOTICE 'Inserted sample workflow data for SBI, Federal, and Dhanlaxmi banks';
END $$;
