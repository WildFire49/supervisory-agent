"""
Context Template Models
Stores editable business rules and schema context templates per database connection
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class ConnectionContextTemplateModel(Base):
    """Database model for connection-specific context templates"""
    __tablename__ = "connection_context_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Template metadata
    template_name = Column(String(255), nullable=False)
    template_version = Column(String(50), default="1.0")
    is_active = Column(Boolean, default=True)
    
    # Core template content
    business_rules_template = Column(Text, nullable=False)  # Business rules like your rules.txt
    schema_context_template = Column(Text, nullable=False)  # Schema rules like your schema-rules.txt
    domain_specific_prompts = Column(Text, nullable=True)   # Domain-specific prompt engineering
    
    # Query generation context
    table_relationships = Column(JSON, default=dict)       # Key table relationships
    common_patterns = Column(JSON, default=list)          # Common query patterns for this domain
    field_mappings = Column(JSON, default=dict)           # Field name mappings and aliases
    
    # User feedback and corrections
    user_corrections = Column(JSON, default=list)         # User-provided corrections and feedback
    failed_queries_log = Column(JSON, default=list)       # Log of failed/incorrect queries
    success_patterns = Column(JSON, default=list)         # Successful query patterns
    
    # Metadata
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    success_rate = Column(Integer, default=0)  # Percentage of successful queries


class QueryCorrectionLogModel(Base):
    """Database model for logging query corrections and user feedback"""
    __tablename__ = "query_correction_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("connection_context_templates.id"), nullable=False)
    
    # Original query details
    natural_language_question = Column(Text, nullable=False)
    generated_sql_original = Column(Text, nullable=False)
    execution_success_original = Column(Boolean, default=False)
    error_message_original = Column(Text, nullable=True)
    
    # User correction
    user_feedback = Column(Text, nullable=False)           # User's explanation of what was wrong
    corrected_sql = Column(Text, nullable=True)            # User-provided correct SQL (optional)
    correction_type = Column(String(100), nullable=False)  # wrong_table, wrong_column, wrong_logic, etc.
    
    # Corrected query details (after applying user feedback)
    generated_sql_corrected = Column(Text, nullable=True)
    execution_success_corrected = Column(Boolean, default=False)
    improvement_score = Column(Integer, nullable=True)     # 1-10 rating of improvement
    
    # Context enhancement
    additional_context = Column(Text, nullable=True)       # Additional context provided by user
    rule_suggestions = Column(JSON, default=list)         # Suggested rule additions
    
    # Metadata
    corrected_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    applied_to_template = Column(Boolean, default=False)   # Whether correction was applied to template


class TemplateUsageLogModel(Base):
    """Database model for tracking template usage and effectiveness"""
    __tablename__ = "template_usage_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("connection_context_templates.id"), nullable=False)
    
    # Query execution details
    natural_language_question = Column(Text, nullable=False)
    generated_sql = Column(Text, nullable=False)
    execution_success = Column(Boolean, default=False)
    execution_time_ms = Column(Integer, nullable=True)
    
    # Template effectiveness metrics
    context_relevance_score = Column(Integer, nullable=True)  # 1-10 how relevant was the context
    rule_compliance_score = Column(Integer, nullable=True)    # 1-10 how well rules were followed
    user_satisfaction_score = Column(Integer, nullable=True)  # 1-10 user satisfaction with result
    
    # Context used
    rules_applied = Column(JSON, default=list)            # Which specific rules were applied
    tables_referenced = Column(JSON, default=list)        # Which tables were referenced
    patterns_matched = Column(JSON, default=list)         # Which patterns were matched
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    domain_hint = Column(String(100), nullable=True)
