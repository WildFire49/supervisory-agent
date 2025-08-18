"""
Database Migration: Add Business Rules Tables
Creates tables for business rules template system
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid


def upgrade():
    """Create business rules tables"""
    
    # Create business_rules table
    op.create_table(
        'business_rules',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('rule_id', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('connection_id', UUID(as_uuid=True), nullable=False, index=True),
        
        # Rule classification
        sa.Column('category', sa.String(50), nullable=False, index=True),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        
        # Rule patterns (stored as JSON)
        sa.Column('trigger_patterns', JSON, default=list),
        sa.Column('table_patterns', JSON, default=list),
        sa.Column('column_patterns', JSON, default=list),
        
        # Rule actions (stored as JSON)
        sa.Column('allowed_tables', JSON, default=list),
        sa.Column('forbidden_tables', JSON, default=list),
        sa.Column('required_joins', JSON, default=list),
        sa.Column('date_field_mappings', JSON, default=dict),
        sa.Column('sql_transformations', JSON, default=list),
        
        # Metadata
        sa.Column('confidence_score', sa.Float, default=0.8),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        
        # Examples (stored as JSON)
        sa.Column('positive_examples', JSON, default=list),
        sa.Column('negative_examples', JSON, default=list),
    )
    
    # Create business_rule_templates table
    op.create_table(
        'business_rule_templates',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('template_id', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('domain', sa.String(100), nullable=False, index=True),
        
        # Template patterns (stored as JSON)
        sa.Column('extraction_patterns', JSON, default=list),
        
        # Metadata
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create rule_validation_logs table
    op.create_table(
        'rule_validation_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('connection_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('query_id', sa.String(255), nullable=True, index=True),
        
        # Validation details
        sa.Column('original_sql', sa.Text, nullable=False),
        sa.Column('corrected_sql', sa.Text, nullable=True),
        sa.Column('is_valid', sa.Boolean, nullable=False),
        
        # Violated rules (stored as JSON)
        sa.Column('violated_rules', JSON, default=list),
        sa.Column('warnings', JSON, default=list),
        sa.Column('suggestions', JSON, default=list),
        
        # Metadata
        sa.Column('validation_timestamp', sa.DateTime, default=sa.func.now()),
        sa.Column('processing_time_ms', sa.Float, nullable=True),
    )
    
    # Create rule_extraction_logs table
    op.create_table(
        'rule_extraction_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('connection_id', UUID(as_uuid=True), nullable=False, index=True),
        
        # Extraction details
        sa.Column('schema_context_hash', sa.String(64), nullable=False),
        sa.Column('domain_hints', JSON, default=list),
        sa.Column('extracted_rules_count', sa.Integer, default=0),
        sa.Column('confidence_score', sa.Float, default=0.0),
        sa.Column('extraction_notes', sa.Text, nullable=True),
        
        # Processing details
        sa.Column('extraction_timestamp', sa.DateTime, default=sa.func.now()),
        sa.Column('processing_time_ms', sa.Float, nullable=True),
        sa.Column('llm_model_used', sa.String(100), nullable=True),
        
        # Results (stored as JSON)
        sa.Column('extracted_rule_ids', JSON, default=list),
    )
    
    # Create indexes for better performance
    op.create_index('idx_business_rules_connection_category', 'business_rules', ['connection_id', 'category'])
    op.create_index('idx_business_rules_connection_severity', 'business_rules', ['connection_id', 'severity'])
    op.create_index('idx_rule_validation_logs_connection_timestamp', 'rule_validation_logs', ['connection_id', 'validation_timestamp'])
    op.create_index('idx_rule_extraction_logs_connection_timestamp', 'rule_extraction_logs', ['connection_id', 'extraction_timestamp'])


def downgrade():
    """Drop business rules tables"""
    
    # Drop indexes
    op.drop_index('idx_rule_extraction_logs_connection_timestamp')
    op.drop_index('idx_rule_validation_logs_connection_timestamp')
    op.drop_index('idx_business_rules_connection_severity')
    op.drop_index('idx_business_rules_connection_category')
    
    # Drop tables
    op.drop_table('rule_extraction_logs')
    op.drop_table('rule_validation_logs')
    op.drop_table('business_rule_templates')
    op.drop_table('business_rules')
