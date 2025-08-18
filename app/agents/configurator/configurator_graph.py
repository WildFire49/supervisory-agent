"""
Configurator graph for the retrieval agent system.
Handles database connection, schema analysis, and configuration setup.
"""
import logging
from typing import TypedDict, List, Optional, Dict, Any
from datetime import datetime
import json
import uuid
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

from app.core.config import settings
from .models import (
    DatabaseConnection, DatabaseType, DatabaseSchema, UserSchemaInput,
    ConfigurationSession, RetrievalConfiguration
)
from app.models.business_rules import TestQuery
from .database_utils import DatabaseConnector, SchemaAnalyzer
from .vector_storage import SchemaVectorStore
from .schema_analysis_storage import SchemaAnalysisStorage
from .query_generator import QueryGenerator, SchemaUnderstandingValidator
from .column_description_generator import ColumnDescriptionGenerator

logger = logging.getLogger(__name__)


class ConfiguratorState(TypedDict):
    """State for the configurator graph."""
    user_id: str
    session_id: str
    current_step: str
    database_connection: Optional[DatabaseConnection]
    connection_test_result: Optional[Dict[str, Any]]
    database_schema: Optional[DatabaseSchema]
    user_input: Optional[UserSchemaInput]
    test_queries: Optional[List[TestQuery]]
    vector_storage_result: Optional[bool]
    configuration_complete: bool
    error_message: Optional[str]
    response: Dict[str, Any]
    messages: List[Dict[str, Any]]


class ConfiguratorGraph:
    """Main configurator graph for retrieval agent setup."""
    
    def __init__(self):
        self.llm = ChatOpenAI(model=settings.LLM_MODEL_NAME, temperature=0, api_key=settings.OPENAI_API_KEY)
        self.db_connector = DatabaseConnector()
        self.schema_analyzer = SchemaAnalyzer(self.db_connector)
        self.vector_store = SchemaVectorStore()
        self.query_generator = QueryGenerator(self.llm, self.vector_store)
        self.schema_validator = SchemaUnderstandingValidator(self.llm)
        self.schema_storage = SchemaAnalysisStorage()
        self.column_description_generator = ColumnDescriptionGenerator(self.llm)
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the configurator workflow graph."""
        workflow = StateGraph(ConfiguratorState)
        
        # Add nodes
        workflow.add_node("connection_setup", self._connection_setup_node)
        workflow.add_node("test_connection", self._test_connection_node)
        workflow.add_node("schema_analysis", self._schema_analysis_node)
        workflow.add_node("user_input_collection", self._user_input_collection_node)
        workflow.add_node("vector_storage", self._vector_storage_node)
        workflow.add_node("query_generation", self._query_generation_node)
        workflow.add_node("validation", self._validation_node)
        workflow.add_node("completion", self._completion_node)
        workflow.add_node("error_handler", self._error_handler_node)
        
        # Set entry point
        workflow.set_entry_point("connection_setup")
        
        # Add edges
        workflow.add_conditional_edges(
            "connection_setup",
            self._route_after_connection_setup,
            {
                "test_connection": "test_connection",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "test_connection",
            self._route_after_connection_test,
            {
                "schema_analysis": "schema_analysis",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "schema_analysis",
            self._route_after_schema_analysis,
            {
                "user_input_collection": "user_input_collection",
                "error": "error_handler"
            }
        )
        
        workflow.add_edge("user_input_collection", "vector_storage")
        
        workflow.add_conditional_edges(
            "vector_storage",
            self._route_after_vector_storage,
            {
                "query_generation": "query_generation",
                "error": "error_handler"
            }
        )
        
        workflow.add_edge("query_generation", "validation")
        workflow.add_edge("validation", "completion")
        workflow.add_edge("completion", END)
        workflow.add_edge("error_handler", END)
        
        return workflow.compile()
    
    async def _connection_setup_node(self, state: ConfiguratorState) -> ConfiguratorState:
        """Handle database connection setup."""
        try:
            logger.info(f"Setting up database connection for session {state['session_id']}")
            
            # If connection already exists, validate it
            if state.get('database_connection'):
                state['current_step'] = "connection_ready"
                state['response'] = {
                    "step": "connection_setup",
                    "status": "success",
                    "message": "Database connection configuration ready",
                    "data": {
                        "connection_name": state['database_connection'].name,
                        "database_type": state['database_connection'].database_type,
                        "database_name": state['database_connection'].database_name
                    }
                }
            else:
                # Request connection details from user
                state['current_step'] = "awaiting_connection_details"
                state['response'] = {
                    "step": "connection_setup",
                    "status": "input_required",
                    "message": "Please provide database connection details",
                    "required_fields": [
                        {"name": "connection_name", "type": "string", "description": "Name for this connection"},
                        {"name": "database_type", "type": "enum", "options": list(DatabaseType), "description": "Database type"},
                        {"name": "host", "type": "string", "description": "Database host"},
                        {"name": "port", "type": "integer", "description": "Database port"},
                        {"name": "database_name", "type": "string", "description": "Database name"},
                        {"name": "username", "type": "string", "description": "Database username"},
                        {"name": "password", "type": "string", "description": "Database password"},
                        {"name": "ssl_enabled", "type": "boolean", "description": "Enable SSL connection"}
                    ]
                }
            
            return state
            
        except Exception as e:
            logger.error(f"Error in connection setup: {str(e)}")
            state['error_message'] = f"Connection setup failed: {str(e)}"
            state['current_step'] = "error"
            return state
    
    async def _test_connection_node(self, state: ConfiguratorState) -> ConfiguratorState:
        """Test database connection."""
        try:
            logger.info(f"Testing database connection for session {state['session_id']}")
            
            db_connection = state['database_connection']
            if not db_connection:
                raise ValueError("No database connection configuration found")
            
            # Test the connection
            success, error_msg = await self.db_connector.test_connection(db_connection)
            
            state['connection_test_result'] = {
                "success": success,
                "error_message": error_msg,
                "tested_at": datetime.now().isoformat()
            }
            
            if success:
                state['current_step'] = "connection_tested"
                state['response'] = {
                    "step": "test_connection",
                    "status": "success",
                    "message": "Database connection successful",
                    "data": {
                        "connection_name": db_connection.name,
                        "database_type": db_connection.database_type,
                        "tested_at": state['connection_test_result']['tested_at']
                    }
                }
            else:
                state['error_message'] = f"Connection test failed: {error_msg}"
                state['current_step'] = "connection_failed"
            
            return state
            
        except Exception as e:
            logger.error(f"Error testing connection: {str(e)}")
            state['error_message'] = f"Connection test error: {str(e)}"
            state['current_step'] = "error"
            return state
    
    async def _schema_analysis_node(self, state: ConfiguratorState) -> ConfiguratorState:
        """Analyze database schema and store metadata in PostgreSQL."""
        try:
            logger.info(f"Analyzing database schema for session {state['session_id']}")
            
            db_connection = state['database_connection']
            if not db_connection:
                raise ValueError("No database connection found")
            
            # Start analysis session in storage
            analysis_session_id = await self.schema_storage.start_analysis_session(
                connection_id=str(db_connection.id),
                database_type=db_connection.database_type,
                database_name=db_connection.database_name,
                host=db_connection.host,
                port=db_connection.port
            )
            
            # Analyze schema
            schema = await self.schema_analyzer.analyze_database_schema(
                db_connection.id, db_connection
            )
            
            # Enrich columns with LLM-generated descriptions and metadata (feature-flagged)
            schema = await self.column_description_generator.enrich_and_apply(
                schema=schema, connection_id=str(db_connection.id)
            )
            
            # Store detailed table analysis in PostgreSQL
            tables_stored = 0
            relationships_stored = 0
            
            for table in schema.tables:
                # Prepare table data for storage
                # Build enriched column and FK payloads for persistence
                enriched_columns = []
                # Build quick lookup for PK/FK determination
                pk_names = set(getattr(table, 'primary_keys', []) or [])
                fk_cols = set()
                try:
                    for fk in (getattr(table, 'foreign_keys', []) or []):
                        if isinstance(fk, dict):
                            for c in fk.get('constrained_columns', []) or []:
                                fk_cols.add(c)
                        else:
                            c = getattr(fk, 'from_column', None)
                            if c:
                                fk_cols.add(c)
                except Exception:
                    pass

                for col in table.columns:
                    name = col.get("name", "") or col.get("column_name", "")
                    enriched_columns.append({
                        "name": name,
                        # Preserve original analyzer fields where available
                        "type": str(col.get("type", "")),
                        "data_type": col.get("data_type") or str(col.get("type", "")),
                        "is_nullable": col.get("is_nullable", col.get("nullable", True)),
                        "default_value": col.get("default_value", col.get("default")),
                        "max_length": col.get("max_length"),
                        "comment": col.get("comment"),
                        # Derived flags
                        "is_primary_key": (name in pk_names) or bool(col.get("is_primary_key", False)),
                        "is_foreign_key": (name in fk_cols) or bool(col.get("is_foreign_key", False)),
                        # LLM enrichment (if present)
                        "llm_description": col.get("llm_description"),
                        "semantic_role": col.get("semantic_role"),
                        "sensitivity": col.get("sensitivity"),
                        "unit": col.get("unit"),
                        "aliases": col.get("aliases"),
                        "business_rules": col.get("business_rules"),
                        "quality_notes": col.get("quality_notes"),
                    })

                # Robust FK mapping for storage
                serialized_fks = []
                try:
                    for fk in (getattr(table, 'foreign_keys', []) or []):
                        if isinstance(fk, dict):
                            serialized_fks.append({
                                "column": ",".join(fk.get('constrained_columns', []) or []),
                                "references_table": fk.get('referred_table') or fk.get('referred_table_name'),
                                "references_column": ",".join(fk.get('referred_columns', []) or []),
                            })
                        else:
                            serialized_fks.append({
                                "column": getattr(fk, 'from_column', None),
                                "references_table": getattr(fk, 'to_table', None),
                                "references_column": getattr(fk, 'to_column', None),
                            })
                except Exception:
                    pass

                table_data = {
                    "schema_name": table.schema_name,
                    "table_name": table.table_name,
                    "table_type": getattr(table, 'table_type', 'table'),
                    "row_count": table.row_count,
                    "columns": enriched_columns,
                    "primary_keys": list(pk_names),
                    "foreign_keys": serialized_fks,
                }
                
                # Store table analysis
                success = await self.schema_storage.store_table_analysis(
                    session_id=analysis_session_id,
                    table_data=table_data,
                    business_purpose=self._infer_business_purpose(table.table_name),
                    naming_patterns=self._extract_naming_patterns(table.table_name),
                    confidence=0.8
                )
                
                if success:
                    tables_stored += 1
            
            # Store relationship analysis
            for relationship in schema.relationships:
                success = await self.schema_storage.store_relationship_analysis(
                    session_id=analysis_session_id,
                    from_table=relationship.from_table,
                    to_table=relationship.to_table,
                    relationship_type=relationship.relationship_type,
                    from_columns=[relationship.from_column],
                    to_columns=[relationship.to_column],
                    confidence_score=0.9,
                    business_meaning=self._infer_relationship_meaning(relationship),
                    discovery_method="foreign_key_constraint"
                )
                
                if success:
                    relationships_stored += 1
            
            # Store business context analysis
            business_contexts = self._analyze_business_contexts(schema)
            contexts_stored = 0
            
            for context in business_contexts:
                success = await self.schema_storage.store_business_context_analysis(
                    session_id=analysis_session_id,
                    context_name=context["name"],
                    context_type=context["type"],
                    description=context["description"],
                    related_tables=context["tables"],
                    key_entities=context["entities"],
                    business_processes=context["processes"],
                    confidence_score=context["confidence"]
                )
                
                if success:
                    contexts_stored += 1
            
            # Complete analysis session
            await self.schema_storage.complete_analysis_session(
                session_id=analysis_session_id,
                status="completed",
                total_tables=len(schema.tables),
                total_views=len(schema.views),
                total_schemas=len(set(table.schema_name for table in schema.tables if table.schema_name)),
                total_relationships=len(schema.relationships),
                analysis_summary={
                    "tables_stored": tables_stored,
                    "relationships_stored": relationships_stored,
                    "contexts_stored": contexts_stored,
                    "database_type": db_connection.database_type,
                    "analysis_session_id": analysis_session_id
                },
                discovered_patterns=self._extract_schema_patterns(schema),
                potential_contexts=[ctx["name"] for ctx in business_contexts]
            )
            
            state['database_schema'] = schema
            state['analysis_session_id'] = analysis_session_id  # Store for later reference
            state['current_step'] = "schema_analyzed"
            state['response'] = {
                "step": "schema_analysis",
                "status": "success",
                "message": "Database schema analyzed and metadata stored successfully",
                "data": {
                    "database_name": schema.database_name,
                    "table_count": len(schema.tables),
                    "view_count": len(schema.views),
                    "relationship_count": len(schema.relationships),
                    "enum_count": len(schema.enums),
                    "analysis_session_id": analysis_session_id,
                    "metadata_stored": {
                        "tables_stored": tables_stored,
                        "relationships_stored": relationships_stored,
                        "contexts_stored": contexts_stored
                    },
                    "tables": [
                        {
                            "name": table.table_name,
                            "schema": table.schema_name,
                            "column_count": len(table.columns),
                            "row_count": table.row_count,
                            "has_foreign_keys": len(table.foreign_keys) > 0,
                            "business_purpose": self._infer_business_purpose(table.table_name)
                        }
                        for table in schema.tables
                    ]
                }
            }
            
            logger.info(f"Schema analysis completed: {tables_stored} tables, {relationships_stored} relationships, {contexts_stored} contexts stored")
            return state
            
        except Exception as e:
            logger.error(f"Error analyzing schema: {str(e)}")
            state['error_message'] = f"Schema analysis failed: {str(e)}"
            state['current_step'] = "error"
            return state
    
    def _infer_business_purpose(self, table_name: str) -> str:
        """Infer business purpose from table name"""
        table_lower = table_name.lower()
        
        if any(keyword in table_lower for keyword in ['disburs', 'disburse']):
            return "Loan disbursement tracking and management"
        elif any(keyword in table_lower for keyword in ['collect', 'payment', 'repay']):
            return "Collection and payment processing"
        elif any(keyword in table_lower for keyword in ['loan', 'credit']):
            return "Loan management and lifecycle"
        elif any(keyword in table_lower for keyword in ['customer', 'client', 'user']):
            return "Customer relationship management"
        elif any(keyword in table_lower for keyword in ['transaction', 'txn']):
            return "Transaction processing and audit"
        elif any(keyword in table_lower for keyword in ['audit', 'log', 'history']):
            return "Audit trail and historical tracking"
        else:
            return "General business data management"
    
    def _extract_naming_patterns(self, table_name: str) -> list:
        """Extract naming patterns from table name"""
        patterns = []
        
        if '_' in table_name:
            patterns.append("snake_case")
        if table_name.endswith('_data'):
            patterns.append("data_suffix")
        if table_name.endswith('_details'):
            patterns.append("details_suffix")
        if table_name.endswith('_logs'):
            patterns.append("logs_suffix")
        if table_name.startswith('staging_'):
            patterns.append("staging_prefix")
        if any(char.isupper() for char in table_name):
            patterns.append("mixed_case")
            
        return patterns
    
    def _infer_relationship_meaning(self, relationship) -> str:
        """Infer business meaning of relationship"""
        from_table = relationship.from_table.lower()
        to_table = relationship.to_table.lower()
        
        if 'loan' in from_table and 'customer' in to_table:
            return "Loan belongs to customer"
        elif 'disburs' in from_table and 'loan' in to_table:
            return "Disbursement linked to loan"
        elif 'collect' in from_table and 'loan' in to_table:
            return "Collection linked to loan"
        else:
            return f"Foreign key relationship between {relationship.from_table} and {relationship.to_table}"
    
    def _analyze_business_contexts(self, schema) -> list:
        """Analyze and identify business contexts from schema with intelligent table prioritization"""
        contexts = []
        
        # Analyze table relationships and data freshness patterns
        table_intelligence = self._analyze_table_intelligence(schema)
        
        # Financial/Lending context with intelligent table selection
        financial_tables = [t for t in schema.tables if any(keyword in t.table_name.lower() 
                           for keyword in ['loan', 'disburs', 'collect', 'payment', 'credit'])]
        if financial_tables:
            # Categorize financial tables by priority and freshness
            disbursement_tables = self._categorize_tables_by_function(financial_tables, 'disbursement', table_intelligence)
            collection_tables = self._categorize_tables_by_function(financial_tables, 'collection', table_intelligence)
            loan_tables = self._categorize_tables_by_function(financial_tables, 'loan', table_intelligence)
            
            contexts.append({
                "name": "Financial Operations",
                "type": "business_domain",
                "description": "Loan management, disbursements, and collections",
                "tables": [t.table_name for t in financial_tables],
                "entities": ["loans", "disbursements", "collections", "payments"],
                "processes": ["loan_origination", "disbursement_processing", "collection_management"],
                "confidence": 0.9,
                "table_categories": {
                    "disbursement_tables": disbursement_tables,
                    "collection_tables": collection_tables,
                    "loan_tables": loan_tables
                },
                "selection_rules": self._generate_table_selection_rules(disbursement_tables, collection_tables, loan_tables)
            })
        
        # Customer context
        customer_tables = [t for t in schema.tables if any(keyword in t.table_name.lower() 
                          for keyword in ['customer', 'client', 'user', 'person'])]
        if customer_tables:
            contexts.append({
                "name": "Customer Management",
                "type": "business_domain",
                "description": "Customer data and relationship management",
                "tables": [t.table_name for t in customer_tables],
                "entities": ["customers", "profiles", "contacts"],
                "processes": ["customer_onboarding", "profile_management", "relationship_tracking"],
                "confidence": 0.8
            })
        
        # Audit/Logging context
        audit_tables = [t for t in schema.tables if any(keyword in t.table_name.lower() 
                       for keyword in ['audit', 'log', 'history', 'track'])]
        if audit_tables:
            contexts.append({
                "name": "Audit and Compliance",
                "type": "operational",
                "description": "Audit trails, logging, and compliance tracking",
                "tables": [t.table_name for t in audit_tables],
                "entities": ["audit_logs", "change_history", "compliance_records"],
                "processes": ["audit_logging", "compliance_monitoring", "change_tracking"],
                "confidence": 0.7
            })
        
        return contexts
    
    def _extract_schema_patterns(self, schema) -> list:
        """Extract common patterns from schema"""
        patterns = []
        
        # Naming patterns
        if any('_' in t.table_name for t in schema.tables):
            patterns.append("snake_case_naming")
        if any(t.table_name.startswith('staging_') for t in schema.tables):
            patterns.append("staging_prefix_pattern")
        if any(t.table_name.endswith('_data') for t in schema.tables):
            patterns.append("data_suffix_pattern")
        
        # Schema organization
        schemas = set(t.schema_name for t in schema.tables if t.schema_name)
        if len(schemas) > 1:
            patterns.append("multi_schema_organization")
        
        # Common column patterns
        all_columns = [col.get("name", "").lower() for t in schema.tables for col in t.columns if col.get("name")]
        if any('created_at' in col for col in all_columns):
            patterns.append("timestamp_tracking")
        if any('id' in col for col in all_columns):
            patterns.append("id_based_keys")
        
        return patterns
    
    def _analyze_table_intelligence(self, schema) -> dict:
        """Analyze table intelligence including data freshness, priority, and relationships"""
        intelligence = {}
        
        for table in schema.tables:
            table_name = table.table_name.lower()
            
            # Analyze data freshness indicators
            freshness_score = self._calculate_table_freshness_score(table)
            
            # Analyze table priority based on naming patterns
            priority_score = self._calculate_table_priority_score(table)
            
            # Analyze table purpose and function
            table_function = self._identify_table_function(table)
            
            # Check for migration/staging indicators
            is_legacy = self._is_legacy_table(table)
            is_staging = self._is_staging_table(table)
            is_current = self._is_current_operational_table(table)
            
            intelligence[table.table_name] = {
                "freshness_score": freshness_score,
                "priority_score": priority_score,
                "table_function": table_function,
                "is_legacy": is_legacy,
                "is_staging": is_staging,
                "is_current": is_current,
                "row_count": table.row_count or 0,
                "schema_name": table.schema_name
            }
        
        return intelligence
    
    def _calculate_table_freshness_score(self, table) -> float:
        """Calculate how fresh/current a table is likely to be"""
        table_name = table.table_name.lower()
        score = 0.5  # Base score
        
        # Positive indicators (more fresh)
        if any(indicator in table_name for indicator in ['current', 'active', 'live', 'prod']):
            score += 0.3
        if table.schema_name and 'prod' in table.schema_name.lower():
            score += 0.2
        if not any(indicator in table_name for indicator in ['staging', 'temp', 'backup', 'old', 'archive']):
            score += 0.2
        
        # Negative indicators (less fresh)
        if any(indicator in table_name for indicator in ['mifix', 'migrat', 'backup', 'old', 'archive', 'hist']):
            score -= 0.4
        if any(indicator in table_name for indicator in ['staging', 'temp', 'test']):
            score -= 0.2
        if table_name.startswith('staging_'):
            score -= 0.3
        
        return max(0.0, min(1.0, score))
    
    def _calculate_table_priority_score(self, table) -> float:
        """Calculate table priority for business operations"""
        table_name = table.table_name.lower()
        score = 0.5  # Base score
        
        # High priority indicators
        if any(indicator in table_name for indicator in ['details', 'main', 'master', 'core']):
            score += 0.3
        if table.row_count and table.row_count > 1000:  # Tables with significant data
            score += 0.2
        if not table.schema_name or table.schema_name.lower() in ['public', 'main', 'prod']:
            score += 0.1
        
        # Lower priority indicators
        if any(indicator in table_name for indicator in ['log', 'audit', 'temp', 'cache']):
            score -= 0.2
        if table_name.endswith('_backup') or table_name.endswith('_old'):
            score -= 0.3
        
        return max(0.0, min(1.0, score))
    
    def _identify_table_function(self, table) -> str:
        """Identify the primary function/purpose of a table"""
        table_name = table.table_name.lower()
        
        # Core business functions
        if any(keyword in table_name for keyword in ['disburs', 'disburse']):
            return 'disbursement'
        elif any(keyword in table_name for keyword in ['collect', 'payment', 'repay']):
            return 'collection'
        elif any(keyword in table_name for keyword in ['loan', 'credit']):
            return 'loan_management'
        elif any(keyword in table_name for keyword in ['customer', 'client', 'user']):
            return 'customer_management'
        elif any(keyword in table_name for keyword in ['order', 'purchase', 'sale']):
            return 'order_management'
        elif any(keyword in table_name for keyword in ['product', 'item', 'inventory']):
            return 'product_management'
        elif any(keyword in table_name for keyword in ['transaction', 'txn']):
            return 'transaction_processing'
        elif any(keyword in table_name for keyword in ['audit', 'log', 'history']):
            return 'audit_logging'
        else:
            return 'general_data'
    
    def _is_legacy_table(self, table) -> bool:
        """Check if table appears to be legacy/old data"""
        table_name = table.table_name.lower()
        return any(indicator in table_name for indicator in [
            'mifix', 'migrat', 'backup', 'old', 'archive', 'hist', 'legacy'
        ])
    
    def _is_staging_table(self, table) -> bool:
        """Check if table is in staging/temporary area"""
        table_name = table.table_name.lower()
        schema_name = (table.schema_name or '').lower()
        return (
            table_name.startswith('staging_') or 
            'staging' in schema_name or
            any(indicator in table_name for indicator in ['temp', 'tmp', 'test'])
        )
    
    def _is_current_operational_table(self, table) -> bool:
        """Check if table appears to be current operational data"""
        return (
            not self._is_legacy_table(table) and 
            not self._is_staging_table(table) and
            self._calculate_table_freshness_score(table) > 0.6
        )
    
    def _categorize_tables_by_function(self, tables, function_type: str, intelligence: dict) -> dict:
        """Categorize tables by function with priority ranking"""
        function_tables = []
        
        for table in tables:
            table_intel = intelligence.get(table.table_name, {})
            table_function = table_intel.get('table_function', '')
            
            # Match function type (e.g., 'disbursement' matches 'disburs')
            if function_type.lower() in table_function.lower() or any(
                keyword in table.table_name.lower() 
                for keyword in self._get_function_keywords(function_type)
            ):
                function_tables.append({
                    "table_name": table.table_name,
                    "schema_name": table.schema_name,
                    "freshness_score": table_intel.get('freshness_score', 0.5),
                    "priority_score": table_intel.get('priority_score', 0.5),
                    "is_current": table_intel.get('is_current', False),
                    "is_legacy": table_intel.get('is_legacy', False),
                    "is_staging": table_intel.get('is_staging', False),
                    "row_count": table_intel.get('row_count', 0),
                    "overall_score": (
                        table_intel.get('freshness_score', 0.5) * 0.4 +
                        table_intel.get('priority_score', 0.5) * 0.3 +
                        (0.3 if table_intel.get('is_current', False) else 0)
                    )
                })
        
        # Sort by overall score (highest first)
        function_tables.sort(key=lambda x: x['overall_score'], reverse=True)
        
        return {
            "primary_tables": [t for t in function_tables if t['overall_score'] > 0.7],
            "secondary_tables": [t for t in function_tables if 0.4 <= t['overall_score'] <= 0.7],
            "legacy_tables": [t for t in function_tables if t['overall_score'] < 0.4 or t['is_legacy']],
            "all_tables": function_tables
        }
    
    def _get_function_keywords(self, function_type: str) -> list:
        """Get keywords for different function types"""
        keyword_map = {
            'disbursement': ['disburs', 'disburse', 'payout', 'fund_transfer'],
            'collection': ['collect', 'payment', 'repay', 'recovery'],
            'loan': ['loan', 'credit', 'lending'],
            'customer': ['customer', 'client', 'user', 'member'],
            'order': ['order', 'purchase', 'sale', 'transaction'],
            'product': ['product', 'item', 'inventory', 'catalog'],
            'payment': ['payment', 'transaction', 'billing']
        }
        return keyword_map.get(function_type.lower(), [function_type.lower()])
    
    def _generate_table_selection_rules(self, disbursement_tables: dict, collection_tables: dict, loan_tables: dict) -> dict:
        """Generate intelligent table selection rules for query generation"""
        return {
            "disbursement_queries": {
                "preferred_tables": [t['table_name'] for t in disbursement_tables.get('primary_tables', [])],
                "fallback_tables": [t['table_name'] for t in disbursement_tables.get('secondary_tables', [])],
                "avoid_tables": [t['table_name'] for t in disbursement_tables.get('legacy_tables', [])],
                "selection_logic": "Prefer current operational tables over staging or legacy tables"
            },
            "collection_queries": {
                "preferred_tables": [t['table_name'] for t in collection_tables.get('primary_tables', [])],
                "fallback_tables": [t['table_name'] for t in collection_tables.get('secondary_tables', [])],
                "avoid_tables": [t['table_name'] for t in collection_tables.get('legacy_tables', [])],
                "selection_logic": "Prefer current operational tables over staging or legacy tables"
            },
            "loan_queries": {
                "preferred_tables": [t['table_name'] for t in loan_tables.get('primary_tables', [])],
                "fallback_tables": [t['table_name'] for t in loan_tables.get('secondary_tables', [])],
                "avoid_tables": [t['table_name'] for t in loan_tables.get('legacy_tables', [])],
                "selection_logic": "Prefer current operational tables over staging or legacy tables"
            },
            "general_rules": {
                "prioritize_current_over_legacy": True,
                "avoid_staging_for_business_queries": True,
                "prefer_high_row_count_tables": True,
                "consider_schema_context": True
            }
        }
    
    async def _user_input_collection_node(self, state: ConfiguratorState) -> ConfiguratorState:
        """Collect additional user input about the schema."""
        try:
            logger.info(f"Collecting user input for session {state['session_id']}")
            
            schema = state['database_schema']
            if not schema:
                raise ValueError("No database schema found")
            
            # If user input already provided, use it
            if state.get('user_input'):
                state['current_step'] = "user_input_collected"
                state['response'] = {
                    "step": "user_input_collection",
                    "status": "success",
                    "message": "User input collected successfully"
                }
            else:
                # Request user input
                state['current_step'] = "awaiting_user_input"
                state['response'] = {
                    "step": "user_input_collection",
                    "status": "input_required",
                    "message": "Please provide additional context about your database",
                    "schema_summary": {
                        "tables": [table.table_name for table in schema.tables],
                        "relationships": len(schema.relationships)
                    },
                    "input_fields": [
                        {
                            "name": "business_rules",
                            "type": "array",
                            "description": "Business rules that govern your data"
                        },
                        {
                            "name": "table_descriptions",
                            "type": "object",
                            "description": "Descriptions for each table (table_name: description)"
                        },
                        {
                            "name": "column_descriptions",
                            "type": "object",
                            "description": "Descriptions for important columns (table.column: description)"
                        },
                        {
                            "name": "data_quality_notes",
                            "type": "array",
                            "description": "Notes about data quality or known issues"
                        },
                        {
                            "name": "additional_context",
                            "type": "string",
                            "description": "Any additional context about your database"
                        }
                    ]
                }
            
            return state
            
        except Exception as e:
            logger.error(f"Error collecting user input: {str(e)}")
            state['error_message'] = f"User input collection failed: {str(e)}"
            state['current_step'] = "error"
            return state
    
    async def _vector_storage_node(self, state: ConfiguratorState) -> ConfiguratorState:
        """Store schema information in vector database."""
        try:
            logger.info(f"Storing schema in vector database for session {state['session_id']}")
            
            schema = state['database_schema']
            user_input = state['user_input']
            
            if not schema:
                raise ValueError("No database schema found")
            
            # Store in vector database
            success = await self.vector_store.store_database_schema(
                schema.connection_id, schema, user_input
            )
            
            state['vector_storage_result'] = success
            
            if success:
                state['current_step'] = "vector_stored"
                state['response'] = {
                    "step": "vector_storage",
                    "status": "success",
                    "message": "Schema information stored in vector database",
                    "data": {
                        "connection_id": schema.connection_id,
                        "documents_stored": len(schema.tables) + 3  # tables + overview + relationships + types
                    }
                }
            else:
                state['error_message'] = "Failed to store schema in vector database"
                state['current_step'] = "vector_storage_failed"
            
            return state
            
        except Exception as e:
            logger.error(f"Error storing in vector database: {str(e)}")
            state['error_message'] = f"Vector storage failed: {str(e)}"
            state['current_step'] = "error"
            return state
    
    async def _query_generation_node(self, state: ConfiguratorState) -> ConfiguratorState:
        """Generate test queries to validate understanding."""
        try:
            logger.info(f"Generating test queries for session {state['session_id']}")
            
            schema = state['database_schema']
            user_input = state['user_input']
            
            if not schema:
                raise ValueError("No database schema found")
            
            # Generate test queries
            test_queries = await self.query_generator.generate_test_queries(
                schema.connection_id, schema, user_input, num_queries=10
            )
            
            state['test_queries'] = test_queries
            state['current_step'] = "queries_generated"
            state['response'] = {
                "step": "query_generation",
                "status": "success",
                "message": "Test queries generated successfully",
                "data": {
                    "query_count": len(test_queries),
                    "average_confidence": sum(q.confidence_score for q in test_queries) / len(test_queries) if test_queries else 0,
                    "sample_queries": [
                        {
                            "question": q.natural_language_question,
                            "sql": q.sql_query,
                            "confidence": q.confidence_score
                        }
                        for q in test_queries[:3]  # Show first 3 as samples
                    ]
                }
            }
            
            return state
            
        except Exception as e:
            logger.error(f"Error generating queries: {str(e)}")
            state['error_message'] = f"Query generation failed: {str(e)}"
            state['current_step'] = "error"
            return state
    
    async def _validation_node(self, state: ConfiguratorState) -> ConfiguratorState:
        """Validate the configuration and generate confidence report."""
        try:
            logger.info(f"Validating configuration for session {state['session_id']}")
            
            schema = state['database_schema']
            user_input = state['user_input']
            test_queries = state['test_queries']
            
            if not all([schema, test_queries]):
                raise ValueError("Missing required data for validation")
            
            # Generate confidence report
            confidence_report = await self.query_generator.generate_confidence_report(
                schema.connection_id, test_queries
            )
            
            # Validate schema understanding
            understanding_validation = await self.schema_validator.validate_schema_understanding(
                schema, user_input or UserSchemaInput(connection_id=schema.connection_id), test_queries
            )
            
            state['current_step'] = "validated"
            state['response'] = {
                "step": "validation",
                "status": "success",
                "message": "Configuration validated successfully",
                "data": {
                    "confidence_report": confidence_report,
                    "understanding_validation": understanding_validation,
                    "ready_for_production": confidence_report.get('overall_confidence', 0) > 0.7
                }
            }
            
            return state
            
        except Exception as e:
            logger.error(f"Error in validation: {str(e)}")
            state['error_message'] = f"Validation failed: {str(e)}"
            state['current_step'] = "error"
            return state
    
    async def _completion_node(self, state: ConfiguratorState) -> ConfiguratorState:
        """Complete the configuration process."""
        try:
            logger.info(f"Completing configuration for session {state['session_id']}")
            
            state['configuration_complete'] = True
            state['current_step'] = "completed"
            state['response'] = {
                "step": "completion",
                "status": "success",
                "message": "Retrieval agent configuration completed successfully",
                "data": {
                    "session_id": state['session_id'],
                    "connection_id": state['database_schema'].connection_id if state['database_schema'] else None,
                    "configuration_ready": True,
                    "next_steps": [
                        "Test the retrieval agent with sample queries",
                        "Deploy to production environment",
                        "Monitor query performance and accuracy"
                    ]
                }
            }
            
            return state
            
        except Exception as e:
            logger.error(f"Error in completion: {str(e)}")
            state['error_message'] = f"Completion failed: {str(e)}"
            state['current_step'] = "error"
            return state
    
    async def _error_handler_node(self, state: ConfiguratorState) -> ConfiguratorState:
        """Handle errors in the configuration process."""
        logger.error(f"Error in configuration session {state['session_id']}: {state.get('error_message', 'Unknown error')}")
        
        state['configuration_complete'] = False
        state['response'] = {
            "step": "error",
            "status": "error",
            "message": state.get('error_message', 'An unknown error occurred'),
            "data": {
                "session_id": state['session_id'],
                "failed_step": state.get('current_step', 'unknown'),
                "recovery_suggestions": [
                    "Check database connection details",
                    "Verify database permissions",
                    "Review error logs for more details"
                ]
            }
        }
        
        return state
    
    # Routing functions
    def _route_after_connection_setup(self, state: ConfiguratorState) -> str:
        """Route after connection setup."""
        if state.get('error_message'):
            return "error"
        return "test_connection"
    
    def _route_after_connection_test(self, state: ConfiguratorState) -> str:
        """Route after connection test."""
        if state.get('error_message') or not state.get('connection_test_result', {}).get('success'):
            return "error"
        return "schema_analysis"
    
    def _route_after_schema_analysis(self, state: ConfiguratorState) -> str:
        """Route after schema analysis."""
        if state.get('error_message'):
            return "error"
        return "user_input_collection"
    
    def _route_after_vector_storage(self, state: ConfiguratorState) -> str:
        """Route after vector storage."""
        if state.get('error_message') or not state.get('vector_storage_result'):
            return "error"
        return "query_generation"
    
    async def run_configuration(self, initial_state: ConfiguratorState) -> ConfiguratorState:
        """Run the complete configuration process."""
        try:
            result = await self.graph.ainvoke(initial_state)
            return result
        except Exception as e:
            logger.error(f"Error running configuration: {str(e)}")
            return {
                **initial_state,
                "error_message": str(e),
                "configuration_complete": False,
                "response": {
                    "step": "error",
                    "status": "error",
                    "message": f"Configuration failed: {str(e)}"
                }
            }


# Factory function to create configurator graph
def create_configurator_graph() -> ConfiguratorGraph:
    """Create and return a configurator graph instance."""
    return ConfiguratorGraph()
