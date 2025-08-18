"""
Schema Analysis Data Storage Service
Automatically stores all schema gathering information in database for analysis and logs
"""

import logging
import uuid
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import engine
from app.models.database.schema_analysis_models import (
    SchemaAnalysisSessionModel, TableAnalysisModel, RelationshipAnalysisModel,
    BusinessContextAnalysisModel, SchemaEvolutionLogModel, QueryGenerationLogModel,
    DataQualityAssessmentModel
)
# Using basic types instead of non-existent models

logger = logging.getLogger(__name__)


class SchemaAnalysisStorage:
    """Service for storing comprehensive schema analysis data"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    # Schema Analysis Session Management
    
    async def start_analysis_session(
        self, 
        connection_id: str,
        database_type: str,
        database_name: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None
    ) -> str:
        """Start a new schema analysis session and return session ID"""
        
        try:
            session_id = f"analysis_{connection_id}_{int(datetime.now().timestamp())}"
            
            with self.get_session() as session:
                analysis_session = SchemaAnalysisSessionModel(
                    session_id=session_id,
                    connection_id=uuid.UUID(connection_id),
                    database_type=database_type,
                    database_name=database_name,
                    host=host,
                    port=port,
                    status="started",
                    started_at=datetime.now()
                )
                
                session.add(analysis_session)
                session.commit()
                
                logger.info(f"Started schema analysis session: {session_id}")
                return session_id
                
        except SQLAlchemyError as e:
            logger.error(f"Error starting analysis session: {str(e)}")
            return f"fallback_{connection_id}_{int(datetime.now().timestamp())}"
    
    async def complete_analysis_session(
        self,
        session_id: str,
        status: str = "completed",
        total_tables: int = 0,
        total_views: int = 0,
        total_schemas: int = 0,
        total_relationships: int = 0,
        analysis_summary: Dict[str, Any] = None,
        discovered_patterns: List[str] = None,
        potential_contexts: List[str] = None,
        error_message: Optional[str] = None,
        warnings: List[str] = None
    ) -> bool:
        """Complete a schema analysis session with results"""
        
        try:
            with self.get_session() as session:
                analysis_session = session.query(SchemaAnalysisSessionModel).filter(
                    SchemaAnalysisSessionModel.session_id == session_id
                ).first()
                
                if analysis_session:
                    analysis_session.status = status
                    analysis_session.completed_at = datetime.now()
                    analysis_session.total_analysis_time_ms = (
                        (datetime.now() - analysis_session.started_at).total_seconds() * 1000
                    )
                    analysis_session.total_tables_discovered = total_tables
                    analysis_session.total_views_discovered = total_views
                    analysis_session.total_schemas_discovered = total_schemas
                    analysis_session.total_relationships_discovered = total_relationships
                    analysis_session.analysis_summary = analysis_summary or {}
                    analysis_session.discovered_patterns = discovered_patterns or []
                    analysis_session.potential_business_contexts = potential_contexts or []
                    analysis_session.error_message = error_message
                    analysis_session.warnings = warnings or []
                    
                    session.commit()
                    
                    logger.info(f"Completed schema analysis session: {session_id}")
                    return True
                else:
                    logger.warning(f"Analysis session not found: {session_id}")
                    return False
                    
        except SQLAlchemyError as e:
            logger.error(f"Error completing analysis session: {str(e)}")
            return False
    
    # Table Analysis Storage
    
    async def store_table_analysis(
        self,
        session_id: str,
        table_data: Dict[str, Any],
        business_purpose: Optional[str] = None,
        naming_patterns: List[str] = None,
        data_quality_notes: List[str] = None,
        confidence: float = 0.8
    ) -> bool:
        """Store detailed table analysis results"""
        
        try:
            with self.get_session() as session:
                # Extract data from table_data dict
                columns_info = table_data.get('columns', [])
                schema_name = table_data.get('schema_name', '')
                table_name = table_data.get('table_name', '')
                table_type = table_data.get('table_type', 'table')
                row_count = table_data.get('row_count', 0)
                
                # Extract keys
                primary_keys = table_data.get('primary_keys', [])
                foreign_keys = table_data.get('foreign_keys', [])
                
                table_analysis = TableAnalysisModel(
                    session_id=session_id,
                    schema_name=schema_name,
                    table_name=table_name,
                    full_table_name=f"{schema_name}.{table_name}" if schema_name else table_name,
                    table_type=table_type,
                    row_count=row_count,
                    column_count=len(columns_info),
                    columns_info=columns_info,
                    primary_keys=primary_keys,
                    foreign_keys=foreign_keys,
                    indexes=[],  # Could be enhanced to capture index information
                    inferred_business_purpose=business_purpose,
                    naming_patterns=naming_patterns or [],
                    data_quality_notes=data_quality_notes or [],
                    analysis_confidence=confidence
                )
                
                session.add(table_analysis)
                session.commit()
                
                logger.debug(f"Stored table analysis for {table_name}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error storing table analysis: {str(e)}")
            return False
    
    async def store_relationship_analysis(
        self,
        session_id: str,
        from_table: str,
        to_table: str,
        relationship_type: str,
        from_columns: List[str],
        to_columns: List[str],
        confidence_score: float = 0.8,
        business_meaning: Optional[str] = None,
        discovery_method: str = "constraint"
    ) -> bool:
        """Store relationship analysis between tables"""
        
        try:
            with self.get_session() as session:
                relationship_analysis = RelationshipAnalysisModel(
                    session_id=session_id,
                    from_table=from_table,
                    to_table=to_table,
                    relationship_type=relationship_type,
                    from_columns=from_columns,
                    to_columns=to_columns,
                    confidence_score=confidence_score,
                    relationship_strength="strong" if confidence_score > 0.8 else "medium" if confidence_score > 0.5 else "weak",
                    business_meaning=business_meaning,
                    discovery_method=discovery_method
                )
                
                session.add(relationship_analysis)
                session.commit()
                
                logger.debug(f"Stored relationship analysis: {from_table} -> {to_table}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error storing relationship analysis: {str(e)}")
            return False
    
    # Business Context Analysis Storage
    
    async def store_business_context_analysis(
        self,
        session_id: str,
        context_name: str,
        context_type: str,
        description: Optional[str] = None,
        related_tables: List[str] = None,
        key_entities: List[str] = None,
        business_processes: List[str] = None,
        naming_conventions: List[str] = None,
        confidence_score: float = 0.7,
        analysis_method: str = "llm_analysis"
    ) -> bool:
        """Store business context analysis results"""
        
        try:
            with self.get_session() as session:
                context_analysis = BusinessContextAnalysisModel(
                    session_id=session_id,
                    context_name=context_name,
                    context_type=context_type,
                    confidence_score=confidence_score,
                    description=description,
                    related_tables=related_tables or [],
                    key_entities=key_entities or [],
                    business_processes=business_processes or [],
                    naming_conventions=naming_conventions or [],
                    data_flow_patterns=[],
                    temporal_patterns=[],
                    analysis_method=analysis_method
                )
                
                session.add(context_analysis)
                session.commit()
                
                logger.debug(f"Stored business context analysis: {context_name}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error storing business context analysis: {str(e)}")
            return False
    
    # Query Generation Logging
    
    async def log_query_generation(
        self,
        connection_id: str,
        request_type: str,
        input_context: Optional[str] = None,
        generation_parameters: Dict[str, Any] = None,
        generated_queries_count: int = 0,
        successful_queries_count: int = 0,
        failed_queries_count: int = 0,
        average_confidence: float = 0.0,
        average_accuracy: float = 0.0,
        average_execution_time: float = 0.0,
        llm_model_used: Optional[str] = None,
        business_rules_applied: List[str] = None,
        generation_time_ms: Optional[float] = None,
        session_id: Optional[str] = None
    ) -> bool:
        """Log query generation activity"""
        
        try:
            with self.get_session() as session:
                query_log = QueryGenerationLogModel(
                    session_id=session_id,
                    connection_id=uuid.UUID(connection_id),
                    request_type=request_type,
                    input_context=input_context,
                    generation_parameters=generation_parameters or {},
                    generated_queries_count=generated_queries_count,
                    successful_queries_count=successful_queries_count,
                    failed_queries_count=failed_queries_count,
                    average_confidence_score=average_confidence,
                    average_accuracy_score=average_accuracy,
                    average_execution_time_ms=average_execution_time,
                    llm_model_used=llm_model_used,
                    business_rules_applied=business_rules_applied or [],
                    generation_time_ms=generation_time_ms
                )
                
                session.add(query_log)
                session.commit()
                
                logger.debug(f"Logged query generation activity: {request_type}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error logging query generation: {str(e)}")
            return False
    
    # Data Quality Assessment Storage
    
    async def store_data_quality_assessment(
        self,
        session_id: str,
        table_name: str,
        completeness_score: float = 0.0,
        consistency_score: float = 0.0,
        validity_score: float = 0.0,
        uniqueness_score: float = 0.0,
        null_analysis: Dict[str, Any] = None,
        data_type_issues: List[str] = None,
        constraint_violations: List[str] = None,
        quality_recommendations: List[str] = None,
        sample_size: Optional[int] = None,
        assessment_method: str = "automated"
    ) -> bool:
        """Store data quality assessment results"""
        
        try:
            with self.get_session() as session:
                quality_assessment = DataQualityAssessmentModel(
                    session_id=session_id,
                    table_name=table_name,
                    completeness_score=completeness_score,
                    consistency_score=consistency_score,
                    validity_score=validity_score,
                    uniqueness_score=uniqueness_score,
                    null_value_analysis=null_analysis or {},
                    data_type_issues=data_type_issues or [],
                    constraint_violations=constraint_violations or [],
                    outlier_detection=[],
                    quality_recommendations=quality_recommendations or [],
                    cleaning_suggestions=[],
                    sample_size=sample_size,
                    assessment_method=assessment_method
                )
                
                session.add(quality_assessment)
                session.commit()
                
                logger.debug(f"Stored data quality assessment for {table_name}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error storing data quality assessment: {str(e)}")
            return False
    
    # Analytics and Reporting
    
    async def get_analysis_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive summary of an analysis session"""
        
        try:
            with self.get_session() as session:
                # Get session info
                analysis_session = session.query(SchemaAnalysisSessionModel).filter(
                    SchemaAnalysisSessionModel.session_id == session_id
                ).first()
                
                if not analysis_session:
                    return {"error": "Session not found"}
                
                # Get table count
                table_count = session.query(TableAnalysisModel).filter(
                    TableAnalysisModel.session_id == session_id
                ).count()
                
                # Get relationship count
                relationship_count = session.query(RelationshipAnalysisModel).filter(
                    RelationshipAnalysisModel.session_id == session_id
                ).count()
                
                # Get business context count
                context_count = session.query(BusinessContextAnalysisModel).filter(
                    BusinessContextAnalysisModel.session_id == session_id
                ).count()
                
                return {
                    "session_id": session_id,
                    "connection_id": str(analysis_session.connection_id),
                    "database_type": analysis_session.database_type,
                    "status": analysis_session.status,
                    "started_at": analysis_session.started_at.isoformat(),
                    "completed_at": analysis_session.completed_at.isoformat() if analysis_session.completed_at else None,
                    "analysis_time_ms": analysis_session.total_analysis_time_ms,
                    "tables_discovered": analysis_session.total_tables_discovered,
                    "views_discovered": analysis_session.total_views_discovered,
                    "schemas_discovered": analysis_session.total_schemas_discovered,
                    "relationships_discovered": analysis_session.total_relationships_discovered,
                    "stored_table_analyses": table_count,
                    "stored_relationship_analyses": relationship_count,
                    "stored_business_contexts": context_count,
                    "analysis_summary": analysis_session.analysis_summary,
                    "discovered_patterns": analysis_session.discovered_patterns,
                    "potential_business_contexts": analysis_session.potential_business_contexts,
                    "warnings": analysis_session.warnings
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting analysis session summary: {str(e)}")
            return {"error": str(e)}
    
    async def get_connection_analysis_history(self, connection_id: str) -> List[Dict[str, Any]]:
        """Get analysis history for a connection"""
        
        try:
            with self.get_session() as session:
                sessions = session.query(SchemaAnalysisSessionModel).filter(
                    SchemaAnalysisSessionModel.connection_id == uuid.UUID(connection_id)
                ).order_by(SchemaAnalysisSessionModel.started_at.desc()).all()
                
                history = []
                for sess in sessions:
                    history.append({
                        "session_id": sess.session_id,
                        "status": sess.status,
                        "started_at": sess.started_at.isoformat(),
                        "completed_at": sess.completed_at.isoformat() if sess.completed_at else None,
                        "tables_discovered": sess.total_tables_discovered,
                        "analysis_time_ms": sess.total_analysis_time_ms
                    })
                
                return history
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting connection analysis history: {str(e)}")
            return []
