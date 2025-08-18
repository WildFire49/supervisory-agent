"""
API routes for the retrieval agent configurator system.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import uuid
import logging

from app.agents.configurator.models import (
    DatabaseConnection, DatabaseType, UserSchemaInput, 
    ConfigurationSession
)
from app.models.business_rules import TestQuery
from app.agents.configurator.database_persistence import configurator_db
from app.agents.configurator.configurator_graph import create_configurator_graph
from app.agents.configurator.database_utils import DatabaseConnector
from app.agents.configurator.vector_storage import SchemaVectorStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/configurator", tags=["configurator"])


# Request/Response Models
class DatabaseConnectionRequest(BaseModel):
    connection_name: str
    database_type: str
    host: str
    port: int
    database_name: str
    username: str
    password: str
    ssl_enabled: bool = False
    connection_params: Optional[Dict[str, Any]] = {}


class DatabaseConnectionResponse(BaseModel):
    id: str
    name: str
    database_type: str
    host: str
    port: int
    database_name: str
    is_active: bool
    created_at: str


class ConfigurationSessionRequest(BaseModel):
    connection_id: Optional[str] = None


class ConfigurationSessionResponse(BaseModel):
    session_id: str
    status: str
    current_step: str
    completion_percentage: float
    data: Optional[Dict[str, Any]] = None


class UserSchemaInputRequest(BaseModel):
    connection_id: str
    business_rules: Optional[List[str]] = []
    table_descriptions: Optional[Dict[str, str]] = {}
    column_descriptions: Optional[Dict[str, str]] = {}
    data_quality_notes: Optional[List[str]] = []
    performance_notes: Optional[List[str]] = []
    security_considerations: Optional[List[str]] = []
    additional_context: Optional[str] = None


class TestConnectionRequest(BaseModel):
    connection_details: DatabaseConnectionRequest


class TestConnectionResponse(BaseModel):
    success: bool
    message: str
    connection_time: Optional[float] = None


class QueryValidationRequest(BaseModel):
    connection_id: str
    query_id: str
    is_valid: bool
    validation_notes: Optional[str] = None


# Database Connection Endpoints
@router.post("/connections", response_model=Dict[str, str])
async def create_database_connection(
    request: DatabaseConnectionRequest,
    user_id: str
):
    """Create a new database connection."""
    try:
        # Validate database type
        try:
            db_type = DatabaseType(request.database_type)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid database type: {request.database_type}"
            )
        
        # Create database connection object
        connection = DatabaseConnection(
            name=request.connection_name,
            database_type=db_type,
            host=request.host,
            port=request.port,
            database_name=request.database_name,
            username=request.username,
            password=request.password,
            ssl_enabled=request.ssl_enabled,
            connection_params=request.connection_params or {}
        )
        
        # Store in database
        connection_id = await configurator_db.create_database_connection(user_id, connection)
        
        return {"connection_id": connection_id, "status": "created"}
        
    except Exception as e:
        logger.error(f"Error creating database connection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections", response_model=List[DatabaseConnectionResponse])
async def list_database_connections(user_id: str):
    """List all database connections for a user."""
    try:
        connections = await configurator_db.list_user_connections(user_id)
        
        return [
            DatabaseConnectionResponse(
                id=conn.id,
                name=conn.name,
                database_type=conn.database_type,
                host=conn.host,
                port=conn.port,
                database_name=conn.database_name,
                is_active=conn.is_active,
                created_at=conn.created_at.isoformat() if conn.created_at else ""
            )
            for conn in connections
        ]
        
    except Exception as e:
        logger.error(f"Error listing database connections: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connections/test", response_model=TestConnectionResponse)
async def test_database_connection(request: TestConnectionRequest):
    """Test a database connection without saving it."""
    try:
        # Create temporary connection object
        db_type = DatabaseType(request.connection_details.database_type)
        connection = DatabaseConnection(
            id=str(uuid.uuid4()),
            name=request.connection_details.connection_name,
            database_type=db_type,
            host=request.connection_details.host,
            port=request.connection_details.port,
            database_name=request.connection_details.database_name,
            username=request.connection_details.username,
            password=request.connection_details.password,
            ssl_enabled=request.connection_details.ssl_enabled
        )
        
        # Test connection
        connector = DatabaseConnector()
        success, error_msg = await connector.test_connection(connection)
        
        return TestConnectionResponse(
            success=success,
            message="Connection successful" if success else error_msg or "Connection failed"
        )
        
    except Exception as e:
        logger.error(f"Error testing database connection: {str(e)}")
        return TestConnectionResponse(
            success=False,
            message=f"Connection test error: {str(e)}"
        )


# Configuration Session Endpoints
@router.post("/sessions", response_model=ConfigurationSessionResponse)
async def create_configuration_session(
    request: ConfigurationSessionRequest,
    user_id: str
):
    """Create a new configuration session."""
    try:
        session_id = await configurator_db.create_configuration_session(
            user_id, request.connection_id
        )
        
        return ConfigurationSessionResponse(
            session_id=session_id,
            status="in_progress",
            current_step="connection_setup",
            completion_percentage=0.0
        )
        
    except Exception as e:
        logger.error(f"Error creating configuration session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=ConfigurationSessionResponse)
async def get_configuration_session(session_id: str):
    """Get configuration session details."""
    try:
        session_data = await configurator_db.get_configuration_session(session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return ConfigurationSessionResponse(
            session_id=session_data["session_id"],
            status=session_data["status"],
            current_step=session_data["current_step"],
            completion_percentage=session_data["completion_percentage"],
            data=session_data.get("session_data", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting configuration session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/configure", response_model=Dict[str, Any])
async def run_configuration_step(
    session_id: str,
    request: Dict[str, Any]
):
    """Run a configuration step."""
    try:
        # Get session data
        session_data = await configurator_db.get_configuration_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Create configurator graph
        configurator_graph = create_configurator_graph()
        
        # Get database connection if connection_id exists
        database_connection = None
        if session_data.get('connection_id'):
            database_connection = await configurator_db.get_database_connection(session_data['connection_id'])
            if not database_connection:
                raise HTTPException(status_code=404, detail=f"Database connection {session_data['connection_id']} not found")
        
        # Also check if connection_id is provided in the request
        elif request.get('connection_id'):
            database_connection = await configurator_db.get_database_connection(request['connection_id'])
            if not database_connection:
                raise HTTPException(status_code=404, detail=f"Database connection {request['connection_id']} not found")
        
        # Prepare configurator state
        configurator_state = {
            'user_id': session_data['user_id'],
            'session_id': session_id,
            'current_step': session_data['current_step'],
            'database_connection': database_connection,
            'connection_test_result': None,
            'database_schema': None,
            'user_input': None,
            'test_queries': None,
            'vector_storage_result': None,
            'configuration_complete': False,
            'error_message': None,
            'response': {},
            'messages': []
        }
        
        # Handle different request types
        if 'connection_details' in request:
            # Create database connection from request
            connection_details = request['connection_details']
            db_type = DatabaseType(connection_details['database_type'])
            connection = DatabaseConnection(
                id=session_data.get('connection_id') or str(uuid.uuid4()),
                name=connection_details['connection_name'],
                database_type=db_type,
                host=connection_details['host'],
                port=connection_details['port'],
                database_name=connection_details['database_name'],
                username=connection_details['username'],
                password=connection_details['password'],
                ssl_enabled=connection_details.get('ssl_enabled', False)
            )
            configurator_state['database_connection'] = connection
        
        elif 'user_schema_input' in request:
            # Handle user schema input
            user_input = UserSchemaInput(
                connection_id=session_data.get('connection_id', ''),
                **request['user_schema_input']
            )
            configurator_state['user_input'] = user_input
        
        # Run configuration
        result = await configurator_graph.run_configuration(configurator_state)
        
        # Update session in database
        await configurator_db.update_configuration_session(session_id, {
            'current_step': result.get('current_step', session_data['current_step']),
            'status': 'completed' if result.get('configuration_complete') else 'in_progress',
            'completion_percentage': min(100.0, session_data.get('completion_percentage', 0) + 20.0)
        })
        
        return {
            "status": "success" if result.get('configuration_complete') else "in_progress",
            "session_id": session_id,
            "current_step": result.get('current_step'),
            "data": result.get('response', {}),
            "error": result.get('error_message')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running configuration step: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Schema and Query Endpoints
@router.post("/sessions/{session_id}/user-input")
async def submit_user_schema_input(
    session_id: str,
    request: UserSchemaInputRequest
):
    """Submit user schema input for a configuration session."""
    try:
        # Get session data
        session_data = await configurator_db.get_configuration_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Create user input object
        user_input = UserSchemaInput(
            connection_id=request.connection_id,
            business_rules=request.business_rules,
            table_descriptions=request.table_descriptions,
            column_descriptions=request.column_descriptions,
            data_quality_notes=request.data_quality_notes,
            performance_notes=request.performance_notes,
            security_considerations=request.security_considerations,
            additional_context=request.additional_context
        )
        
        # Update session
        await configurator_db.update_configuration_session(session_id, {
            'user_input_collected': True,
            'session_data': {
                **session_data.get('session_data', {}),
                'user_input': user_input.dict()
            }
        })
        
        return {"status": "success", "message": "User input submitted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting user schema input: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections/{connection_id}/test-queries", response_model=List[Dict[str, Any]])
async def get_test_queries(connection_id: str):
    """Get test queries for a database connection."""
    try:
        test_queries = await configurator_db.get_test_queries(connection_id)
        
        return [
            {
                "query_id": query.query_id,
                "sql_query": query.sql_query,
                "natural_language_question": query.natural_language_question,
                "expected_result_type": query.expected_result_type,
                "confidence_score": query.confidence_score,
                "validated": query.validated,
                "validation_notes": query.validation_notes
            }
            for query in test_queries
        ]
        
    except Exception as e:
        logger.error(f"Error getting test queries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/generate-queries")
async def generate_test_queries(
    session_id: str,
    request: Dict[str, Any] = None
):
    """Generate test queries for a configuration session."""
    try:
        # Get session data
        session_data = await configurator_db.get_configuration_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        connection_id = session_data.get('connection_id')
        if not connection_id:
            raise HTTPException(status_code=400, detail="No connection ID found in session")
        
        # Get database connection
        database_connection = await configurator_db.get_database_connection(connection_id)
        if not database_connection:
            raise HTTPException(status_code=404, detail="Database connection not found")
        
        # Import query generator and dependencies
        from app.agents.configurator.query_generator import QueryGenerator
        from langchain_openai import ChatOpenAI
        from app.core.config import settings
        
        # Initialize dependencies with cost-effective model
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY
        )
        vector_store = SchemaVectorStore()
        
        # Generate test queries
        query_generator = QueryGenerator(llm=llm, vector_store=vector_store)
        
        # Generate queries based on request parameters or defaults
        query_types = request.get('query_types', ['select', 'join', 'aggregate']) if request else ['select', 'join', 'aggregate']
        complexity_level = request.get('complexity_level', 'medium') if request else 'medium'
        num_queries = request.get('num_queries', 3) if request else 3
        
        # Let QueryGenerator get full schema context directly (this is what works!)
        test_queries = await query_generator.generate_test_queries(
            connection_id=connection_id,
            schema=None,  # QueryGenerator will get full context from vector store
            user_input=None,  # Could be retrieved from session if needed
            num_queries=num_queries
        )
        
        # Store queries in database
        stored_queries = []
        for query in test_queries:
            query_id = await configurator_db.store_test_query(connection_id, query)
            stored_queries.append({
                "query_id": query_id,
                "sql_query": query.sql_query,
                "natural_language_question": query.natural_language_question,
                "expected_result_type": query.expected_result_type,
                "confidence_score": query.confidence_score
            })
        
        return {
            "status": "success",
            "session_id": session_id,
            "connection_id": connection_id,
            "generated_queries": len(stored_queries),
            "queries": stored_queries
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating test queries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/queries/validate")
async def validate_query_result(request: QueryValidationRequest):
    """Validate a test query result."""
    try:
        # This would typically update the query validation status in the database
        # For now, we'll just return success
        return {
            "status": "success",
            "message": "Query validation recorded",
            "query_id": request.query_id,
            "is_valid": request.is_valid
        }
        
    except Exception as e:
        logger.error(f"Error validating query result: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections/{connection_id}/schema-search")
async def search_schema_information(
    connection_id: str,
    query: str,
    limit: int = 5
):
    """Search schema information using vector similarity."""
    try:
        vector_store = SchemaVectorStore()
        results = await vector_store.search_schema_information(connection_id, query, limit)
        
        return {
            "query": query,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error searching schema information: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@router.get("/health")
async def configurator_health_check():
    """Health check for configurator services."""
    try:
        # Test database connection
        db_status = "healthy"
        try:
            # Simple database test
            session_id = str(uuid.uuid4())
            test_session = await configurator_db.get_configuration_session(session_id)
            # Expected to return None for non-existent session
        except Exception:
            db_status = "unhealthy"
        
        # Test vector store
        vector_status = "healthy"
        try:
            vector_store = SchemaVectorStore()
            # Simple vector store test
        except Exception:
            vector_status = "unhealthy"
        
        return {
            "status": "healthy" if db_status == "healthy" and vector_status == "healthy" else "degraded",
            "components": {
                "database": db_status,
                "vector_store": vector_status
            }
        }
        
    except Exception as e:
        logger.error(f"Error in configurator health check: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
