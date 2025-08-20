"""
Streamlined Analysis Storage Models for Template Playground
Production-grade database models for storing analysis results
"""

from sqlalchemy import Column, String, Text, Float, DateTime, Boolean, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class PlaygroundAnalysisSession(Base):
    """Main analysis session for playground workflow"""
    __tablename__ = "playground_analysis_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    connection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, default="playground_user")
    
    # Session metadata
    database_type = Column(String(50), nullable=False)
    database_name = Column(String(255), nullable=True)
    
    # Analysis progress tracking
    status = Column(String(50), default="started")  # started, analyzing, completed, failed
    total_tables_discovered = Column(Integer, default=0)
    tables_analyzed = Column(Integer, default=0)
    columns_analyzed = Column(Integer, default=0)
    
    # Selected items for template creation
    selected_tables = Column(JSON, default=list)
    selected_columns = Column(JSON, default=dict)  # {table_name: [column_names]}
    
    # Timing information
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Analysis summary
    analysis_summary = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)


class PlaygroundTableAnalysis(Base):
    """Streamlined table analysis results"""
    __tablename__ = "playground_table_analysis"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), ForeignKey("playground_analysis_sessions.session_id"), nullable=False, index=True)
    
    # Table identification
    table_name = Column(String(255), nullable=False)
    schema_name = Column(String(255), nullable=True)
    
    # Basic metadata
    row_count = Column(Integer, nullable=True)
    column_count = Column(Integer, default=0)
    
    # AI-generated analysis (no enum mapping)
    business_description = Column(Text, nullable=True)
    primary_purpose = Column(String(500), nullable=True)
    data_category = Column(String(100), nullable=True)
    
    # Relationships
    parent_tables = Column(JSON, default=list)
    child_tables = Column(JSON, default=list)
    key_columns = Column(JSON, default=list)
    
    # Business context
    business_processes = Column(JSON, default=list)
    typical_queries = Column(JSON, default=list)
    join_patterns = Column(JSON, default=list)
    
    # User inputs
    user_notes = Column(Text, nullable=True)
    business_rules = Column(Text, nullable=True)
    usage_context = Column(Text, nullable=True)
    
    # Metadata
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    confidence_score = Column(Float, default=0.0)
    is_selected = Column(Boolean, default=False)


class PlaygroundColumnAnalysis(Base):
    """Streamlined column analysis results"""
    __tablename__ = "playground_column_analysis"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), ForeignKey("playground_analysis_sessions.session_id"), nullable=False, index=True)
    table_name = Column(String(255), nullable=False)
    
    # Column identification
    column_name = Column(String(255), nullable=False)
    data_type = Column(String(100), nullable=False)
    is_nullable = Column(Boolean, default=True)
    
    # AI-generated analysis (simplified, no enum mapping)
    business_description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # identifier, timestamp, status, amount, etc.
    
    # Sample data analysis (simplified)
    sample_values = Column(JSON, default=list)
    distinct_count = Column(Integer, nullable=True)
    is_categorical = Column(Boolean, default=False)
    
    # Relationships
    foreign_key_target = Column(String(255), nullable=True)
    referenced_by = Column(JSON, default=list)
    
    # User inputs
    user_notes = Column(Text, nullable=True)
    business_rules = Column(Text, nullable=True)
    usage_context = Column(Text, nullable=True)
    
    # Metadata
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    confidence_score = Column(Float, default=0.0)
    is_selected = Column(Boolean, default=False)


class PlaygroundQueryAnalysis(Base):
    """SQL queries and QnA analysis for knowledge base enrichment"""
    __tablename__ = "playground_query_analysis"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), ForeignKey("playground_analysis_sessions.session_id"), nullable=False, index=True)
    
    # Query information
    query_type = Column(String(50), nullable=False)  # sql_query, natural_language, qna
    original_query = Column(Text, nullable=False)
    processed_query = Column(Text, nullable=True)
    
    # LLM analysis
    query_intent = Column(JSON, default=dict)
    business_context = Column(Text, nullable=True)
    tables_involved = Column(JSON, default=list)
    columns_involved = Column(JSON, default=list)
    
    # Knowledge enrichment
    knowledge_extracted = Column(JSON, default=dict)
    business_rules_discovered = Column(JSON, default=list)
    patterns_identified = Column(JSON, default=list)
    
    # Vector storage reference
    vector_id = Column(String(255), nullable=True)
    embedding_stored = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    analyzed_by = Column(String(100), default="llm_analyzer")
    confidence_score = Column(Float, default=0.0)


class PlaygroundKnowledgeBase(Base):
    """Enhanced knowledge base entries from analysis"""
    __tablename__ = "playground_knowledge_base"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), ForeignKey("playground_analysis_sessions.session_id"), nullable=False, index=True)
    
    # Knowledge entry
    entry_type = Column(String(50), nullable=False)  # business_rule, pattern, context, relationship
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    
    # Context
    related_tables = Column(JSON, default=list)
    related_columns = Column(JSON, default=list)
    related_queries = Column(JSON, default=list)
    
    # Enrichment data
    business_impact = Column(Text, nullable=True)
    usage_examples = Column(JSON, default=list)
    validation_rules = Column(JSON, default=list)
    
    # Vector storage
    vector_id = Column(String(255), nullable=True)
    embedding_stored = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    source = Column(String(100), nullable=False)  # analysis, user_input, llm_discovery
    confidence_score = Column(Float, default=0.0)
