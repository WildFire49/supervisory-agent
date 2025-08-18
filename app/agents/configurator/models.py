"""
Database models for the retrieval agent configurator system.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from app.models.business_rules import TestQuery


class DatabaseType(str, Enum):
    """Supported database types for configuration."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    ORACLE = "oracle"
    MSSQL = "mssql"
    MONGODB = "mongodb"


class DatabaseConnection(BaseModel):
    """Database connection configuration model."""
    id: Optional[str] = None
    name: str
    database_type: DatabaseType
    host: str
    port: int
    database_name: str
    username: str
    password: str
    ssl_enabled: bool = False
    connection_params: Optional[Dict[str, Any]] = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True


class TableSchema(BaseModel):
    """Table schema information model."""
    table_name: str
    schema_name: Optional[str] = None
    columns: List[Dict[str, Any]]
    primary_keys: List[str]
    foreign_keys: List[Dict[str, Any]]
    indexes: List[Dict[str, Any]]
    constraints: List[Dict[str, Any]]
    table_comment: Optional[str] = None
    row_count: Optional[int] = None


class DatabaseSchema(BaseModel):
    """Complete database schema model."""
    connection_id: str
    database_name: str
    tables: List[TableSchema]
    views: List[Dict[str, Any]]
    functions: List[Dict[str, Any]]
    procedures: List[Dict[str, Any]]
    enums: List[Dict[str, Any]]
    custom_types: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    schema_notes: Optional[str] = None
    gathered_at: datetime
    version: str = "1.0"


class UserSchemaInput(BaseModel):
    """User input for schema clarification and relationships."""
    connection_id: str
    table_relationships: Optional[List[Dict[str, Any]]] = []
    business_rules: Optional[List[str]] = []
    column_descriptions: Optional[Dict[str, str]] = {}
    table_descriptions: Optional[Dict[str, str]] = {}
    data_quality_notes: Optional[List[str]] = []
    performance_notes: Optional[List[str]] = []
    security_considerations: Optional[List[str]] = []
    additional_context: Optional[str] = None


class ConfigurationSession(BaseModel):
    """Configuration session tracking model."""
    session_id: str
    user_id: str
    connection_id: str
    status: str  # "in_progress", "completed", "failed"
    current_step: str
    schema_gathered: bool = False
    user_input_collected: bool = False
    vector_db_indexed: bool = False
    test_queries_generated: bool = False
    created_at: datetime
    updated_at: datetime
    completion_percentage: float = 0.0



class QueryExecutionResult(BaseModel):
    """Result of query execution with performance metrics."""
    query_id: str
    connection_id: Optional[str] = None
    sql_query: str
    natural_language_question: Optional[str] = None
    execution_success: bool
    results: List[Dict[str, Any]] = []
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
    row_count: int = 0
    accuracy_score: float = 0.0
    confidence_score: float = 0.0
    rule_compliance_score: float = 0.0
    performance_score: float = 0.0
    executed_at: datetime = Field(default_factory=datetime.now)


class RetrievalConfiguration(BaseModel):
    """Complete retrieval agent configuration."""
    config_id: str
    user_id: str
    connection_id: str
    database_schema: DatabaseSchema
    user_input: UserSchemaInput
    test_queries: List[TestQuery]
    vector_embeddings_id: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    is_production_ready: bool = False
