"""
Database persistence layer for configurator data.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import uuid
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Text, Integer, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from .models import (
    DatabaseConnection, DatabaseSchema, UserSchemaInput, 
    ConfigurationSession, TestQuery, RetrievalConfiguration
)

logger = logging.getLogger(__name__)

Base = declarative_base()


class DatabaseConnectionModel(Base):
    """SQLAlchemy model for database connections."""
    __tablename__ = "retrieval_database_connections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    database_type = Column(String, nullable=False)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    database_name = Column(String, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)  # Should be encrypted in production
    ssl_enabled = Column(Boolean, default=False)
    connection_params = Column(JSONB, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DatabaseSchemaModel(Base):
    """SQLAlchemy model for database schemas."""
    __tablename__ = "retrieval_database_schemas"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    database_name = Column(String, nullable=False)
    schema_data = Column(JSONB, nullable=False)  # Complete schema as JSON
    schema_notes = Column(Text)
    version = Column(String, default="1.0")
    gathered_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserSchemaInputModel(Base):
    """SQLAlchemy model for user schema input."""
    __tablename__ = "retrieval_user_schema_inputs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    input_data = Column(JSONB, nullable=False)  # Complete user input as JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConfigurationSessionModel(Base):
    """SQLAlchemy model for configuration sessions."""
    __tablename__ = "retrieval_configuration_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String, nullable=False, unique=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    connection_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    status = Column(String, nullable=False, default="in_progress")
    current_step = Column(String, nullable=False)
    session_data = Column(JSONB, default={})
    schema_gathered = Column(Boolean, default=False)
    user_input_collected = Column(Boolean, default=False)
    vector_db_indexed = Column(Boolean, default=False)
    test_queries_generated = Column(Boolean, default=False)
    completion_percentage = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TestQueryModel(Base):
    """SQLAlchemy model for test queries."""
    __tablename__ = "retrieval_test_queries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_id = Column(String, nullable=False, unique=True, index=True)
    connection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    sql_query = Column(Text, nullable=False)
    natural_language_question = Column(Text, nullable=False)
    expected_result_type = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=False)
    validated = Column(Boolean, nullable=True)
    validation_notes = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class RetrievalConfigurationModel(Base):
    """SQLAlchemy model for complete retrieval configurations."""
    __tablename__ = "retrieval_configurations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_id = Column(String, nullable=False, unique=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    connection_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    configuration_data = Column(JSONB, nullable=False)  # Complete config as JSON
    vector_embeddings_id = Column(String, nullable=True)
    status = Column(String, nullable=False, default="configuring")
    is_production_ready = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConfiguratorDatabase:
    """Database operations for the configurator system."""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or settings.DATABASE_URL
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get database session."""
        return self.SessionLocal()
    
    # Database Connection operations
    async def create_database_connection(self, user_id: str, connection: DatabaseConnection) -> str:
        """Create a new database connection."""
        try:
            with self.get_session() as session:
                db_connection = DatabaseConnectionModel(
                    id=uuid.uuid4() if not connection.id else uuid.UUID(connection.id),
                    user_id=user_id,
                    name=connection.name,
                    database_type=connection.database_type.value,
                    host=connection.host,
                    port=connection.port,
                    database_name=connection.database_name,
                    username=connection.username,
                    password=connection.password,  # TODO: Encrypt in production
                    ssl_enabled=connection.ssl_enabled,
                    connection_params=connection.connection_params or {}
                )
                session.add(db_connection)
                session.commit()
                session.refresh(db_connection)
                
                logger.info(f"Created database connection {db_connection.id} for user {user_id}")
                return str(db_connection.id)
                
        except SQLAlchemyError as e:
            logger.error(f"Error creating database connection: {str(e)}")
            raise
    
    async def get_database_connection(self, connection_id: str) -> Optional[DatabaseConnection]:
        """Get database connection by ID."""
        try:
            with self.get_session() as session:
                db_connection = session.query(DatabaseConnectionModel).filter(
                    DatabaseConnectionModel.id == uuid.UUID(connection_id)
                ).first()
                
                if not db_connection:
                    return None
                
                return DatabaseConnection(
                    id=str(db_connection.id),
                    name=db_connection.name,
                    database_type=db_connection.database_type,
                    host=db_connection.host,
                    port=db_connection.port,
                    database_name=db_connection.database_name,
                    username=db_connection.username,
                    password=db_connection.password,
                    ssl_enabled=db_connection.ssl_enabled,
                    connection_params=db_connection.connection_params,
                    created_at=db_connection.created_at,
                    updated_at=db_connection.updated_at,
                    is_active=db_connection.is_active
                )
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting database connection: {str(e)}")
            return None
    
    async def list_user_connections(self, user_id: str) -> List[DatabaseConnection]:
        """List all connections for a user."""
        try:
            with self.get_session() as session:
                connections = session.query(DatabaseConnectionModel).filter(
                    DatabaseConnectionModel.user_id == user_id,
                    DatabaseConnectionModel.is_active == True
                ).all()
                
                return [
                    DatabaseConnection(
                        id=str(conn.id),
                        name=conn.name,
                        database_type=conn.database_type,
                        host=conn.host,
                        port=conn.port,
                        database_name=conn.database_name,
                        username=conn.username,
                        password=conn.password,
                        ssl_enabled=conn.ssl_enabled,
                        connection_params=conn.connection_params,
                        created_at=conn.created_at,
                        updated_at=conn.updated_at,
                        is_active=conn.is_active
                    )
                    for conn in connections
                ]
                
        except SQLAlchemyError as e:
            logger.error(f"Error listing user connections: {str(e)}")
            return []
    
    # Configuration Session operations
    async def create_configuration_session(self, user_id: str, connection_id: str = None) -> str:
        """Create a new configuration session."""
        try:
            session_id = str(uuid.uuid4())
            
            with self.get_session() as session:
                config_session = ConfigurationSessionModel(
                    session_id=session_id,
                    user_id=user_id,
                    connection_id=uuid.UUID(connection_id) if connection_id else None,
                    status="in_progress",
                    current_step="connection_setup"
                )
                session.add(config_session)
                session.commit()
                
                logger.info(f"Created configuration session {session_id} for user {user_id}")
                return session_id
                
        except SQLAlchemyError as e:
            logger.error(f"Error creating configuration session: {str(e)}")
            raise
    
    async def update_configuration_session(
        self, 
        session_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update configuration session."""
        try:
            with self.get_session() as session:
                config_session = session.query(ConfigurationSessionModel).filter(
                    ConfigurationSessionModel.session_id == session_id
                ).first()
                
                if not config_session:
                    return False
                
                for key, value in updates.items():
                    if hasattr(config_session, key):
                        setattr(config_session, key, value)
                
                config_session.updated_at = datetime.utcnow()
                session.commit()
                
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error updating configuration session: {str(e)}")
            return False
    
    async def get_configuration_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration session by ID."""
        try:
            with self.get_session() as session:
                config_session = session.query(ConfigurationSessionModel).filter(
                    ConfigurationSessionModel.session_id == session_id
                ).first()
                
                if not config_session:
                    return None
                
                return {
                    "session_id": config_session.session_id,
                    "user_id": config_session.user_id,
                    "connection_id": str(config_session.connection_id) if config_session.connection_id else None,
                    "status": config_session.status,
                    "current_step": config_session.current_step,
                    "session_data": config_session.session_data,
                    "schema_gathered": config_session.schema_gathered,
                    "user_input_collected": config_session.user_input_collected,
                    "vector_db_indexed": config_session.vector_db_indexed,
                    "test_queries_generated": config_session.test_queries_generated,
                    "completion_percentage": config_session.completion_percentage,
                    "created_at": config_session.created_at,
                    "updated_at": config_session.updated_at
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting configuration session: {str(e)}")
            return None
    
    # Schema operations
    async def store_database_schema(self, connection_id: str, schema: DatabaseSchema) -> bool:
        """Store database schema."""
        try:
            with self.get_session() as session:
                # Convert schema to dict for JSON storage
                schema_data = {
                    "connection_id": schema.connection_id,
                    "database_name": schema.database_name,
                    "tables": [table.dict() for table in schema.tables],
                    "views": schema.views,
                    "functions": schema.functions,
                    "procedures": schema.procedures,
                    "enums": schema.enums,
                    "custom_types": schema.custom_types,
                    "relationships": schema.relationships,
                    "schema_notes": schema.schema_notes,
                    "gathered_at": schema.gathered_at.isoformat(),
                    "version": schema.version
                }
                
                db_schema = DatabaseSchemaModel(
                    connection_id=uuid.UUID(connection_id),
                    database_name=schema.database_name,
                    schema_data=schema_data,
                    schema_notes=schema.schema_notes,
                    version=schema.version,
                    gathered_at=schema.gathered_at
                )
                session.add(db_schema)
                session.commit()
                
                logger.info(f"Stored database schema for connection {connection_id}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error storing database schema: {str(e)}")
            return False
    
    # Test Query operations
    async def store_test_queries(self, test_queries: List[TestQuery]) -> bool:
        """Store test queries."""
        try:
            with self.get_session() as session:
                for query in test_queries:
                    db_query = TestQueryModel(
                        query_id=query.query_id,
                        connection_id=uuid.UUID(query.connection_id),
                        sql_query=query.sql_query,
                        natural_language_question=query.description,
                        expected_result_type=query.expected_result_type,
                        confidence_score=query.confidence_score,
                        validated=getattr(query, 'validated', None),
                        validation_notes=str(query.validation_notes) if query.validation_notes else None,
                        generated_at=query.created_at
                    )
                    session.add(db_query)
                
                session.commit()
                logger.info(f"Stored {len(test_queries)} test queries")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error storing test queries: {str(e)}")
            return False
    
    async def store_test_query(self, connection_id: str, test_query: TestQuery) -> str:
        """Store a single test query and return its ID."""
        try:
            with self.get_session() as session:
                db_query = TestQueryModel(
                    query_id=test_query.query_id,
                    connection_id=uuid.UUID(connection_id),
                    sql_query=test_query.sql_query,
                    natural_language_question=test_query.description,
                    expected_result_type=test_query.expected_result_type,
                    confidence_score=test_query.confidence_score,
                    validated=getattr(test_query, 'validated', None),
                    validation_notes=str(test_query.validation_notes) if test_query.validation_notes else None,
                    generated_at=test_query.created_at
                )
                session.add(db_query)
                session.commit()
                
                logger.info(f"Stored test query: {test_query.query_id}")
                return test_query.query_id
                
        except SQLAlchemyError as e:
            logger.error(f"Error storing test query: {str(e)}")
            raise
    
    async def get_test_queries(self, connection_id: str) -> List[TestQuery]:
        """Get test queries for a connection."""
        try:
            with self.get_session() as session:
                queries = session.query(TestQueryModel).filter(
                    TestQueryModel.connection_id == uuid.UUID(connection_id)
                ).all()
                
                return [
                    TestQuery(
                        query_id=query.query_id,
                        connection_id=str(query.connection_id),
                        sql_query=query.sql_query,
                        description=query.natural_language_question,
                        expected_result_type=query.expected_result_type,
                        confidence_score=query.confidence_score,
                        business_context=query.validation_notes or "",
                        validation_notes=[query.validation_notes] if query.validation_notes else [],
                        created_at=query.generated_at or datetime.now()
                    )
                    for query in queries
                ]
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting test queries: {str(e)}")
            return []


# Global instance
configurator_db = ConfiguratorDatabase()
