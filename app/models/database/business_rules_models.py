"""
SQLAlchemy Database Models for Business Rules Template System
"""

from sqlalchemy import Column, String, Text, Float, DateTime, Boolean, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class BusinessRuleModel(Base):
    """Database model for business rules"""
    __tablename__ = "business_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(String(255), unique=True, nullable=False, index=True)
    connection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Rule classification
    category = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Rule patterns (stored as JSON)
    trigger_patterns = Column(JSON, default=list)
    table_patterns = Column(JSON, default=list)
    column_patterns = Column(JSON, default=list)
    
    # Rule actions (stored as JSON)
    allowed_tables = Column(JSON, default=list)
    forbidden_tables = Column(JSON, default=list)
    required_joins = Column(JSON, default=list)
    date_field_mappings = Column(JSON, default=dict)
    sql_transformations = Column(JSON, default=list)
    
    # Metadata
    confidence_score = Column(Float, default=0.8)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Examples (stored as JSON)
    positive_examples = Column(JSON, default=list)
    negative_examples = Column(JSON, default=list)
    
    # Relationship to database connections
    # connection = relationship("DatabaseConnectionModel", back_populates="business_rules")


class BusinessRuleTemplateModel(Base):
    """Database model for business rule templates"""
    __tablename__ = "business_rule_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    domain = Column(String(100), nullable=False, index=True)
    
    # Template patterns (stored as JSON)
    extraction_patterns = Column(JSON, default=list)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to rules
    rules = relationship("BusinessRuleModel", 
                        primaryjoin="BusinessRuleTemplateModel.template_id == foreign(BusinessRuleModel.rule_id)",
                        viewonly=True)


class RuleValidationLogModel(Base):
    """Database model for rule validation logs"""
    __tablename__ = "rule_validation_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    query_id = Column(String(255), nullable=True, index=True)
    
    # Validation details
    original_sql = Column(Text, nullable=False)
    corrected_sql = Column(Text, nullable=True)
    is_valid = Column(Boolean, nullable=False)
    
    # Violated rules (stored as JSON)
    violated_rules = Column(JSON, default=list)
    warnings = Column(JSON, default=list)
    suggestions = Column(JSON, default=list)
    
    # Metadata
    validation_timestamp = Column(DateTime, default=datetime.utcnow)
    processing_time_ms = Column(Float, nullable=True)


class RuleExtractionLogModel(Base):
    """Database model for rule extraction logs"""
    __tablename__ = "rule_extraction_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Extraction details
    schema_context_hash = Column(String(64), nullable=False)  # Hash of schema context
    domain_hints = Column(JSON, default=list)
    extracted_rules_count = Column(Integer, default=0)
    confidence_score = Column(Float, default=0.0)
    extraction_notes = Column(Text, nullable=True)
    
    # Processing details
    extraction_timestamp = Column(DateTime, default=datetime.utcnow)
    processing_time_ms = Column(Float, nullable=True)
    llm_model_used = Column(String(100), nullable=True)
    
    # Results (stored as JSON)
    extracted_rule_ids = Column(JSON, default=list)
