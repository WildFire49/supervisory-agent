"""
Database utilities for connecting to and analyzing various database types.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text, inspect, MetaData
from sqlalchemy.exc import SQLAlchemyError
import pymongo
from pymongo.errors import ConnectionFailure
import pandas as pd
from .models import DatabaseConnection, DatabaseType, TableSchema, DatabaseSchema

logger = logging.getLogger(__name__)


class DatabaseConnector:
    """Handles connections to various database types."""
    
    def __init__(self):
        self.connections: Dict[str, Any] = {}
    
    def build_connection_string(self, db_config: DatabaseConnection) -> str:
        """Build connection string based on database type."""
        # URL-encode username and password to handle special characters like @, :, etc.
        encoded_username = quote_plus(db_config.username)
        encoded_password = quote_plus(db_config.password)
        
        if db_config.database_type == DatabaseType.POSTGRESQL:
            return f"postgresql://{encoded_username}:{encoded_password}@{db_config.host}:{db_config.port}/{db_config.database_name}"
        elif db_config.database_type == DatabaseType.MYSQL:
            return f"mysql+pymysql://{encoded_username}:{encoded_password}@{db_config.host}:{db_config.port}/{db_config.database_name}"
        elif db_config.database_type == DatabaseType.SQLITE:
            return f"sqlite:///{db_config.database_name}"
        elif db_config.database_type == DatabaseType.ORACLE:
            return f"oracle+cx_oracle://{encoded_username}:{encoded_password}@{db_config.host}:{db_config.port}/{db_config.database_name}"
        elif db_config.database_type == DatabaseType.MSSQL:
            return f"mssql+pyodbc://{encoded_username}:{encoded_password}@{db_config.host}:{db_config.port}/{db_config.database_name}?driver=ODBC+Driver+17+for+SQL+Server"
        else:
            raise ValueError(f"Unsupported database type: {db_config.database_type}")
    
    async def test_connection(self, db_config: DatabaseConnection) -> Tuple[bool, Optional[str]]:
        """Test database connection."""
        try:
            if db_config.database_type == DatabaseType.MONGODB:
                return await self._test_mongodb_connection(db_config)
            else:
                return await self._test_sql_connection(db_config)
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False, str(e)
    
    async def _test_sql_connection(self, db_config: DatabaseConnection) -> Tuple[bool, Optional[str]]:
        """Test SQL database connection."""
        try:
            connection_string = self.build_connection_string(db_config)
            engine = create_engine(connection_string, pool_timeout=10, pool_recycle=300)
            
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            
            self.connections[db_config.id] = engine
            return True, None
        except SQLAlchemyError as e:
            return False, f"SQL connection error: {str(e)}"
    
    async def _test_mongodb_connection(self, db_config: DatabaseConnection) -> Tuple[bool, Optional[str]]:
        """Test MongoDB connection."""
        try:
            connection_string = f"mongodb://{db_config.username}:{db_config.password}@{db_config.host}:{db_config.port}/{db_config.database_name}"
            client = pymongo.MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
            
            self.connections[db_config.id] = client
            return True, None
        except ConnectionFailure as e:
            return False, f"MongoDB connection error: {str(e)}"


class SchemaAnalyzer:
    """Analyzes database schema and extracts metadata."""
    
    def __init__(self, connector: DatabaseConnector):
        self.connector = connector
    
    async def analyze_database_schema(self, connection_id: str, db_config: DatabaseConnection) -> DatabaseSchema:
        """Analyze complete database schema."""
        if db_config.database_type == DatabaseType.MONGODB:
            return await self._analyze_mongodb_schema(connection_id, db_config)
        else:
            return await self._analyze_sql_schema(connection_id, db_config)
    
    async def _analyze_sql_schema(self, connection_id: str, db_config: DatabaseConnection) -> DatabaseSchema:
        """Analyze SQL database schema."""
        engine = self.connector.connections.get(connection_id)
        if not engine:
            raise ValueError(f"No active connection found for {connection_id}")
        
        inspector = inspect(engine)
        metadata = MetaData()
        metadata.reflect(bind=engine)
        
        tables = []
        
        # For PostgreSQL, check specific schema if provided, otherwise all schemas
        if db_config.database_type == DatabaseType.POSTGRESQL:
            # Check if a specific schema is requested in connection_params
            target_schema = None
            if hasattr(db_config, 'connection_params') and db_config.connection_params:
                target_schema = db_config.connection_params.get('schema')
            
            if target_schema:
                # Focus only on the specified schema
                schema_names = [target_schema]
                logger.info(f"Analyzing specific PostgreSQL schema: {target_schema}")
            else:
                # Get all schema names if no specific schema is requested
                schema_names = inspector.get_schema_names()
                logger.info(f"Found PostgreSQL schemas: {schema_names}")
            
            for schema_name in schema_names:
                # Skip system schemas (unless specifically requested)
                if not target_schema and schema_name in ['information_schema', 'pg_catalog', 'pg_toast']:
                    continue
                    
                try:
                    schema_tables = inspector.get_table_names(schema=schema_name)
                    logger.info(f"Schema '{schema_name}': {len(schema_tables)} tables")
                    
                    for table_name in schema_tables:
                        table_schema = await self._analyze_table_schema(inspector, table_name, engine, schema_name)
                        tables.append(table_schema)
                except Exception as e:
                    logger.warning(f"Could not analyze schema '{schema_name}': {str(e)}")
                    # If this is the target schema and we can't access it, raise the error
                    if target_schema and schema_name == target_schema:
                        raise Exception(f"Cannot access specified schema '{schema_name}': {str(e)}")
        else:
            # For other databases, use the original logic
            for table_name in inspector.get_table_names():
                table_schema = await self._analyze_table_schema(inspector, table_name, engine)
                tables.append(table_schema)
        
        # Get views
        views = []
        try:
            if db_config.database_type == DatabaseType.POSTGRESQL:
                # For PostgreSQL, check views in specified schema or all schemas
                target_schema = None
                if hasattr(db_config, 'connection_params') and db_config.connection_params:
                    target_schema = db_config.connection_params.get('schema')
                
                if target_schema:
                    schema_names = [target_schema]
                else:
                    schema_names = inspector.get_schema_names()
                
                for schema_name in schema_names:
                    if not target_schema and schema_name in ['information_schema', 'pg_catalog', 'pg_toast']:
                        continue
                    try:
                        schema_views = inspector.get_view_names(schema=schema_name)
                        for view_name in schema_views:
                            view_ref = f"{schema_name}.{view_name}" if schema_name else view_name
                            view_info = {
                                "name": view_ref,
                                "columns": inspector.get_columns(view_name, schema=schema_name),
                                "definition": await self._get_view_definition(engine, view_name, schema_name)
                            }
                            views.append(view_info)
                    except Exception as e:
                        logger.warning(f"Could not analyze views in schema '{schema_name}': {str(e)}")
            else:
                # For other databases, use the original logic
                view_names = inspector.get_view_names()
                for view_name in view_names:
                    view_info = {
                        "name": view_name,
                        "columns": inspector.get_columns(view_name),
                        "definition": await self._get_view_definition(engine, view_name)
                    }
                    views.append(view_info)
        except Exception as e:
            logger.warning(f"Could not retrieve views: {str(e)}")
        
        # Get enums and custom types
        enums = await self._get_database_enums(engine, db_config.database_type)
        custom_types = await self._get_custom_types(engine, db_config.database_type)
        
        # Analyze relationships
        relationships = await self._analyze_relationships(inspector, tables)
        
        return DatabaseSchema(
            connection_id=connection_id,
            database_name=db_config.database_name,
            tables=tables,
            views=views,
            functions=[],  # Will be implemented based on DB type
            procedures=[],  # Will be implemented based on DB type
            enums=enums,
            custom_types=custom_types,
            relationships=relationships,
            gathered_at=pd.Timestamp.now()
        )
    
    async def _analyze_table_schema(self, inspector, table_name: str, engine, schema_name: str = None) -> TableSchema:
        """Analyze individual table schema."""
        # Use schema-qualified table name for PostgreSQL
        table_ref = table_name if schema_name is None else f"{schema_name}.{table_name}"
        
        columns = inspector.get_columns(table_name, schema=schema_name)
        primary_keys = inspector.get_pk_constraint(table_name, schema=schema_name)['constrained_columns']
        foreign_keys = inspector.get_foreign_keys(table_name, schema=schema_name)
        indexes = inspector.get_indexes(table_name, schema=schema_name)
        
        # Get table comment
        table_comment = None
        try:
            table_info = inspector.get_table_comment(table_name, schema=schema_name)
            table_comment = table_info.get('text')
        except:
            pass
        
        # Get row count
        row_count = None
        try:
            with engine.connect() as conn:
                # Use schema-qualified table name for the query
                query_table_name = table_ref if schema_name else table_name
                result = conn.execute(text(f"SELECT COUNT(*) FROM {query_table_name}"))
                row_count = result.scalar()
        except:
            pass
        
        return TableSchema(
            table_name=table_ref,  # Store the schema-qualified name
            schema_name=schema_name,
            columns=columns,
            primary_keys=primary_keys,
            foreign_keys=foreign_keys,
            indexes=indexes,
            constraints=[],  # Will be enhanced
            table_comment=table_comment,
            row_count=row_count
        )
    
    async def _analyze_mongodb_schema(self, connection_id: str, db_config: DatabaseConnection) -> DatabaseSchema:
        """Analyze MongoDB schema."""
        client = self.connector.connections.get(connection_id)
        if not client:
            raise ValueError(f"No active connection found for {connection_id}")
        
        db = client[db_config.database_name]
        collections = db.list_collection_names()
        
        tables = []
        for collection_name in collections:
            collection = db[collection_name]
            
            # Sample documents to infer schema
            sample_docs = list(collection.find().limit(100))
            schema_info = self._infer_mongodb_schema(sample_docs)
            
            table_schema = TableSchema(
                table_name=collection_name,
                columns=schema_info['fields'],
                primary_keys=['_id'],
                foreign_keys=[],
                indexes=list(collection.list_indexes()),
                constraints=[],
                row_count=collection.count_documents({})
            )
            tables.append(table_schema)
        
        return DatabaseSchema(
            connection_id=connection_id,
            database_name=db_config.database_name,
            tables=tables,
            views=[],
            functions=[],
            procedures=[],
            enums=[],
            custom_types=[],
            relationships=[],
            gathered_at=pd.Timestamp.now()
        )
    
    def _infer_mongodb_schema(self, documents: List[Dict]) -> Dict[str, Any]:
        """Infer schema from MongoDB documents."""
        fields = {}
        
        for doc in documents:
            for key, value in doc.items():
                if key not in fields:
                    fields[key] = {
                        'name': key,
                        'type': type(value).__name__,
                        'nullable': False,
                        'examples': []
                    }
                
                if value is not None and len(fields[key]['examples']) < 5:
                    fields[key]['examples'].append(str(value)[:100])
        
        return {'fields': list(fields.values())}
    
    async def _get_database_enums(self, engine, db_type: DatabaseType) -> List[Dict[str, Any]]:
        """Get database enums based on database type."""
        enums = []
        
        if db_type == DatabaseType.POSTGRESQL:
            try:
                with engine.connect() as conn:
                    result = conn.execute(text("""
                        SELECT t.typname as enum_name, 
                               array_agg(e.enumlabel ORDER BY e.enumsortorder) as enum_values
                        FROM pg_type t 
                        JOIN pg_enum e ON t.oid = e.enumtypid  
                        GROUP BY t.typname
                    """))
                    
                    for row in result:
                        enums.append({
                            'name': row.enum_name,
                            'values': row.enum_values,
                            'type': 'enum'
                        })
            except Exception as e:
                logger.warning(f"Could not retrieve PostgreSQL enums: {str(e)}")
        
        return enums
    
    async def _get_custom_types(self, engine, db_type: DatabaseType) -> List[Dict[str, Any]]:
        """Get custom database types."""
        custom_types = []
        
        if db_type == DatabaseType.POSTGRESQL:
            try:
                with engine.connect() as conn:
                    result = conn.execute(text("""
                        SELECT typname, typtype, typlen 
                        FROM pg_type 
                        WHERE typtype = 'c' AND typname !~ '^_'
                    """))
                    
                    for row in result:
                        custom_types.append({
                            'name': row.typname,
                            'type': 'composite',
                            'length': row.typlen
                        })
            except Exception as e:
                logger.warning(f"Could not retrieve PostgreSQL custom types: {str(e)}")
        
        return custom_types
    
    async def _analyze_relationships(self, inspector, tables: List[TableSchema]) -> List[Dict[str, Any]]:
        """Analyze relationships between tables."""
        relationships = []
        
        for table in tables:
            for fk in table.foreign_keys:
                relationship = {
                    'source_table': table.table_name,
                    'source_columns': fk['constrained_columns'],
                    'target_table': fk['referred_table'],
                    'target_columns': fk['referred_columns'],
                    'relationship_type': 'foreign_key',
                    'constraint_name': fk.get('name', '')
                }
                relationships.append(relationship)
        
        return relationships
    
    async def _get_view_definition(self, engine, view_name: str, schema_name: str = None) -> Optional[str]:
        """Get view definition SQL."""
        try:
            with engine.connect() as conn:
                # This is PostgreSQL specific - would need to be adapted for other DBs
                if schema_name:
                    result = conn.execute(text(f"""
                        SELECT definition 
                        FROM pg_views 
                        WHERE viewname = '{view_name}' AND schemaname = '{schema_name}'
                    """))
                else:
                    result = conn.execute(text(f"""
                        SELECT definition 
                        FROM pg_views 
                        WHERE viewname = '{view_name}'
                    """))
                row = result.fetchone()
                return row.definition if row else None
        except:
            return None
