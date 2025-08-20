"""
Schema Analysis Data Storage Models
Stores all schema gathering information for analysis and logs
"""

from sqlalchemy import Column, String, Text, Float, DateTime, Boolean, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class SchemaAnalysisSessionModel(Base):
    """Database model for schema analysis sessions"""
    __tablename__ = "schema_analysis_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    connection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Session metadata
    database_type = Column(String(50), nullable=False)
    database_name = Column(String(255), nullable=True)
    host = Column(String(255), nullable=True)
    port = Column(Integer, nullable=True)
    
    # Analysis progress
    status = Column(String(50), default="started")  # started, analyzing, completed, failed
    total_tables_discovered = Column(Integer, default=0)
    total_views_discovered = Column(Integer, default=0)
    total_schemas_discovered = Column(Integer, default=0)
    total_relationships_discovered = Column(Integer, default=0)
    
    # Timing information
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    total_analysis_time_ms = Column(Float, nullable=True)
    
    # Analysis results summary
    analysis_summary = Column(JSON, default=dict)
    discovered_patterns = Column(JSON, default=list)
    potential_business_contexts = Column(JSON, default=list)
    
    # Error information
    error_message = Column(Text, nullable=True)
    warnings = Column(JSON, default=list)


class TableAnalysisModel(Base):
    """Database model for individual table analysis results"""
    __tablename__ = "table_analysis_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), ForeignKey("schema_analysis_sessions.session_id"), nullable=False, index=True)
    
    # Table identification
    schema_name = Column(String(255), nullable=True)
    table_name = Column(String(255), nullable=False)
    full_table_name = Column(String(512), nullable=False)  # schema.table_name
    table_type = Column(String(50), nullable=False)  # table, view, materialized_view
    
    # Table metadata
    row_count = Column(Integer, nullable=True)
    column_count = Column(Integer, default=0)
    size_bytes = Column(Integer, nullable=True)
    
    # Column information (stored as JSON)
    columns_info = Column(JSON, default=list)  # [{name, type, nullable, default, etc.}]
    primary_keys = Column(JSON, default=list)
    foreign_keys = Column(JSON, default=list)
    indexes = Column(JSON, default=list)
    
    # Business context analysis
    inferred_business_purpose = Column(Text, nullable=True)
    naming_patterns = Column(JSON, default=list)
    potential_relationships = Column(JSON, default=list)
    data_quality_notes = Column(JSON, default=list)
    
    # Enhanced AI-powered analysis results
    ai_business_description = Column(Text, nullable=True)  # LLM-generated business description
    primary_purpose = Column(String(500), nullable=True)  # AI-identified primary purpose
    data_category = Column(String(100), nullable=True)    # AI-identified category
    parent_tables = Column(JSON, default=list)           # Parent table relationships
    child_tables = Column(JSON, default=list)            # Child table relationships
    key_columns = Column(JSON, default=list)             # AI-identified key columns
    business_processes = Column(JSON, default=list)      # Supported business processes
    typical_queries = Column(JSON, default=list)         # Common query patterns
    join_patterns = Column(JSON, default=list)           # Join relationship patterns
    
    # Column-level analysis (comprehensive)
    columns_analysis = Column(JSON, default=list)        # Detailed column analysis with enums
    enum_columns = Column(JSON, default=list)            # Columns with enum values
    sample_data = Column(JSON, default=list)             # Sample rows for context
    
    # Analysis versioning and caching
    analysis_version = Column(String(50), default="1.0") # Version for cache invalidation
    connection_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Source connection
    schema_hash = Column(String(255), nullable=True)     # Hash of table schema for change detection
    
    # Analysis metadata
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    analysis_confidence = Column(Float, default=0.0)
    analysis_duration_ms = Column(Float, nullable=True)  # Time taken for analysis


class RelationshipAnalysisModel(Base):
    """Database model for relationship analysis between tables"""
    __tablename__ = "relationship_analysis_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), ForeignKey("schema_analysis_sessions.session_id"), nullable=False, index=True)
    
    # Relationship identification
    from_table = Column(String(512), nullable=False)
    to_table = Column(String(512), nullable=False)
    relationship_type = Column(String(50), nullable=False)  # foreign_key, inferred, semantic
    
    # Relationship details
    from_columns = Column(JSON, default=list)
    to_columns = Column(JSON, default=list)
    constraint_name = Column(String(255), nullable=True)
    
    # Analysis results
    confidence_score = Column(Float, default=0.0)
    relationship_strength = Column(String(20), default="weak")  # weak, medium, strong
    business_meaning = Column(Text, nullable=True)
    
    # Metadata
    discovered_at = Column(DateTime, default=datetime.utcnow)
    discovery_method = Column(String(50), nullable=False)  # constraint, naming, data_analysis


class BusinessContextAnalysisModel(Base):
    """Database model for business context analysis results"""
    __tablename__ = "business_context_analysis"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), ForeignKey("schema_analysis_sessions.session_id"), nullable=False, index=True)
    
    # Context identification
    context_name = Column(String(255), nullable=False)
    context_type = Column(String(100), nullable=False)  # domain, workflow, process, etc.
    confidence_score = Column(Float, default=0.0)
    
    # Context details
    description = Column(Text, nullable=True)
    related_tables = Column(JSON, default=list)
    key_entities = Column(JSON, default=list)
    business_processes = Column(JSON, default=list)
    
    # Pattern analysis
    naming_conventions = Column(JSON, default=list)
    data_flow_patterns = Column(JSON, default=list)
    temporal_patterns = Column(JSON, default=list)
    
    # Metadata
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    analysis_method = Column(String(100), nullable=False)  # llm_analysis, pattern_matching, etc.


class SchemaEvolutionLogModel(Base):
    """Database model for tracking schema changes over time"""
    __tablename__ = "schema_evolution_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Change identification
    change_type = Column(String(50), nullable=False)  # table_added, table_removed, column_added, etc.
    affected_object = Column(String(512), nullable=False)
    change_details = Column(JSON, default=dict)
    
    # Change metadata
    detected_at = Column(DateTime, default=datetime.utcnow)
    previous_analysis_session = Column(String(255), nullable=True)
    current_analysis_session = Column(String(255), nullable=False)
    
    # Impact analysis
    impact_score = Column(Float, default=0.0)
    affected_queries = Column(JSON, default=list)
    affected_business_rules = Column(JSON, default=list)


class QueryGenerationLogModel(Base):
    """Database model for logging query generation activities"""
    __tablename__ = "query_generation_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), nullable=True, index=True)
    connection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Generation request
    request_type = Column(String(50), nullable=False)  # test_queries, natural_language, rule_aware
    input_context = Column(Text, nullable=True)
    generation_parameters = Column(JSON, default=dict)
    
    # Generation results
    generated_queries_count = Column(Integer, default=0)
    successful_queries_count = Column(Integer, default=0)
    failed_queries_count = Column(Integer, default=0)
    
    # Quality metrics
    average_confidence_score = Column(Float, default=0.0)
    average_accuracy_score = Column(Float, default=0.0)
    average_execution_time_ms = Column(Float, default=0.0)
    
    # Generation details
    llm_model_used = Column(String(100), nullable=True)
    business_rules_applied = Column(JSON, default=list)
    generation_time_ms = Column(Float, nullable=True)
    
    # Metadata
    generated_at = Column(DateTime, default=datetime.utcnow)
    generated_by = Column(String(100), default="system")


class QueryExecutionLogModel(Base):
    """Database model for individual query execution logs"""
    __tablename__ = "query_execution_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_id = Column(String(255), nullable=False, index=True)
    connection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Query details
    natural_language_query = Column(Text, nullable=True)
    generated_sql = Column(Text, nullable=False)
    query_intent = Column(JSON, default=dict)
    
    # Execution results
    execution_success = Column(Boolean, default=False)
    execution_time_ms = Column(Float, default=0.0)
    result_row_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    # Quality scores
    accuracy_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    rule_compliance_score = Column(Float, default=0.0)
    performance_score = Column(Float, default=0.0)
    
    # Metadata
    generated_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime, default=datetime.utcnow)
    domain_hint = Column(String(100), nullable=True)


class DataQualityAssessmentModel(Base):
    """Database model for data quality assessment results"""
    __tablename__ = "data_quality_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), ForeignKey("schema_analysis_sessions.session_id"), nullable=False, index=True)
    table_name = Column(String(512), nullable=False)
    
    # Quality metrics
    completeness_score = Column(Float, default=0.0)  # % of non-null values
    consistency_score = Column(Float, default=0.0)   # Data format consistency
    validity_score = Column(Float, default=0.0)      # Data type validity
    uniqueness_score = Column(Float, default=0.0)    # Duplicate detection
    
    # Detailed findings
    null_value_analysis = Column(JSON, default=dict)
    data_type_issues = Column(JSON, default=list)
    constraint_violations = Column(JSON, default=list)
    outlier_detection = Column(JSON, default=list)
    
    # Recommendations
    quality_recommendations = Column(JSON, default=list)
    cleaning_suggestions = Column(JSON, default=list)
    
    # Metadata
    assessed_at = Column(DateTime, default=datetime.utcnow)
    sample_size = Column(Integer, nullable=True)
    assessment_method = Column(String(100), nullable=False)
