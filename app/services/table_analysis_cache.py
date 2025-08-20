"""
Table Analysis Cache Service
Provides persistent storage and retrieval of table analysis results to avoid recomputation.
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import uuid

from app.core.database import SessionLocal
from app.models.database.schema_analysis_models import TableAnalysisModel
from app.services.advanced_schema_analyzer import TableAnalysis, ColumnAnalysis
import logging

logger = logging.getLogger(__name__)


class TableAnalysisCache:
    """Service for caching and retrieving table analysis results"""
    
    def __init__(self):
        self.cache_validity_hours = 24 * 7  # Cache valid for 7 days
    
    def _generate_schema_hash(self, table_metadata: Dict[str, Any]) -> str:
        """Generate a hash of table schema for change detection"""
        try:
            # Create a consistent representation of table schema
            schema_data = {
                'columns': sorted([
                    {
                        'name': col.get('name', ''),
                        'type': str(col.get('type', '')),
                        'nullable': col.get('nullable', True),
                        'primary_key': col.get('primary_key', False)
                    }
                    for col in table_metadata.get('columns', [])
                ], key=lambda x: x['name']),
                'table_name': table_metadata.get('table_name', ''),
                'schema_name': table_metadata.get('schema_name', '')
            }
            
            # Generate hash
            schema_str = json.dumps(schema_data, sort_keys=True)
            return hashlib.sha256(schema_str.encode()).hexdigest()[:32]
        except Exception as e:
            logger.warning(f"Failed to generate schema hash: {e}")
            return f"fallback_{datetime.now().strftime('%Y%m%d')}"
    
    def get_cached_analysis(
        self, 
        connection_id: str, 
        schema_name: str, 
        table_name: str,
        table_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[TableAnalysis]:
        """Retrieve cached table analysis if available and valid"""
        try:
            with SessionLocal() as session:
                # Find the most recent analysis for this table
                cached_result = session.query(TableAnalysisModel).filter(
                    and_(
                        TableAnalysisModel.connection_id == uuid.UUID(connection_id),
                        TableAnalysisModel.schema_name == schema_name,
                        TableAnalysisModel.table_name == table_name
                    )
                ).order_by(desc(TableAnalysisModel.analyzed_at)).first()
                
                if not cached_result:
                    logger.info(f"No cached analysis found for {schema_name}.{table_name}")
                    return None
                
                # Check if cache is still valid (within validity period)
                cache_age = datetime.utcnow() - cached_result.analyzed_at
                if cache_age > timedelta(hours=self.cache_validity_hours):
                    logger.info(f"Cached analysis for {schema_name}.{table_name} is expired ({cache_age})")
                    return None
                
                # Check if schema has changed (if metadata provided)
                if table_metadata:
                    current_hash = self._generate_schema_hash(table_metadata)
                    if cached_result.schema_hash and cached_result.schema_hash != current_hash:
                        logger.info(f"Schema changed for {schema_name}.{table_name}, cache invalid")
                        return None
                
                # Convert cached result back to TableAnalysis object
                logger.info(f"✅ Found valid cached analysis for {schema_name}.{table_name}")
                return self._convert_from_db_model(cached_result)
                
        except Exception as e:
            logger.error(f"Error retrieving cached analysis: {e}")
            return None
    
    def save_analysis(
        self, 
        connection_id: str,
        table_analysis: TableAnalysis,
        table_metadata: Optional[Dict[str, Any]] = None,
        analysis_duration_ms: Optional[float] = None
    ) -> bool:
        """Save table analysis results to cache"""
        try:
            with SessionLocal() as session:
                # Generate schema hash
                schema_hash = None
                if table_metadata:
                    schema_hash = self._generate_schema_hash(table_metadata)
                
                # Generate session_id for this analysis session
                session_id = f"playground_{connection_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                
                # Create session record if it doesn't exist
                from app.models.database.schema_analysis_models import SchemaAnalysisSessionModel
                existing_session = session.query(SchemaAnalysisSessionModel).filter_by(session_id=session_id).first()
                if not existing_session:
                    session_record = SchemaAnalysisSessionModel(
                        session_id=session_id,
                        connection_id=uuid.UUID(connection_id),
                        database_type="postgresql",  # Default
                        status="analyzing",
                        started_at=datetime.utcnow()
                    )
                    session.add(session_record)
                    session.flush()  # Ensure session is created before table analysis
                
                # Convert TableAnalysis to database model
                db_model = TableAnalysisModel(
                    session_id=session_id,
                    connection_id=uuid.UUID(connection_id),
                    schema_name=table_analysis.schema_name,
                    table_name=table_analysis.table_name,
                    full_table_name=f"{table_analysis.schema_name}.{table_analysis.table_name}",
                    table_type="table",  # Default to table
                    
                    # Enhanced AI analysis results
                    ai_business_description=table_analysis.business_description,
                    primary_purpose=table_analysis.primary_purpose,
                    data_category=table_analysis.data_category,
                    parent_tables=table_analysis.parent_tables,
                    child_tables=table_analysis.child_tables,
                    key_columns=table_analysis.key_columns,
                    business_processes=table_analysis.business_processes,
                    typical_queries=table_analysis.typical_queries,
                    join_patterns=table_analysis.join_patterns,
                    
                    # Column analysis
                    columns_analysis=self._serialize_columns_analysis(table_analysis.columns),
                    enum_columns=[col.column_name for col in table_analysis.columns if col.enum_values],
                    sample_data=table_analysis.sample_data,
                    
                    # Metadata
                    row_count=table_analysis.row_count,
                    column_count=len(table_analysis.columns),
                    analysis_confidence=table_analysis.confidence_score,
                    analysis_duration_ms=analysis_duration_ms,
                    schema_hash=schema_hash,
                    analysis_version="2.0",  # Enhanced version
                    analyzed_at=datetime.utcnow()
                )
                
                session.add(db_model)
                session.commit()
                
                logger.info(f"✅ Saved analysis for {table_analysis.schema_name}.{table_analysis.table_name} to cache")
                return True
                
        except Exception as e:
            logger.error(f"Error saving analysis to cache: {e}")
            return False
    
    def _serialize_columns_analysis(self, columns: List[ColumnAnalysis]) -> List[Dict[str, Any]]:
        """Convert ColumnAnalysis objects to JSON-serializable format"""
        return [
            {
                'column_name': col.column_name,
                'data_type': col.data_type,
                'is_nullable': col.is_nullable,
                'business_description': col.business_description,
                'category': getattr(col, 'category', ''),
                'sample_values': col.sample_values or [],
                'distinct_count': col.distinct_count,
                'enum_values': col.enum_values or [],
                'foreign_key_target': getattr(col, 'foreign_key_target', None),
                'referenced_by': getattr(col, 'referenced_by', []),
                'user_notes': getattr(col, 'user_notes', ''),
                'business_rules': getattr(col, 'business_rules', ''),
                'usage_context': getattr(col, 'usage_context', ''),
                'confidence_score': col.confidence_score
            }
            for col in columns
        ]
    
    def _convert_from_db_model(self, db_model: TableAnalysisModel) -> TableAnalysis:
        """Convert database model back to TableAnalysis object"""
        # Convert columns analysis back to ColumnAnalysis objects
        columns = []
        if db_model.columns_analysis:
            for col_data in db_model.columns_analysis:
                column_analysis = ColumnAnalysis(
                    column_name=col_data.get('column_name', ''),
                    data_type=col_data.get('data_type', ''),
                    is_nullable=col_data.get('is_nullable', True),
                    business_description=col_data.get('business_description', ''),
                    category=col_data.get('category', ''),
                    sample_values=col_data.get('sample_values', []),
                    distinct_count=col_data.get('distinct_count', 0),
                    enum_values=col_data.get('enum_values', []),
                    foreign_key_target=col_data.get('foreign_key_target'),
                    referenced_by=col_data.get('referenced_by', []),
                    user_notes=col_data.get('user_notes', ''),
                    business_rules=col_data.get('business_rules', ''),
                    usage_context=col_data.get('usage_context', ''),
                    confidence_score=col_data.get('confidence_score', 0.0)
                )
                columns.append(column_analysis)
        
        # Create TableAnalysis object
        return TableAnalysis(
            table_name=db_model.table_name,
            schema_name=db_model.schema_name,
            business_description=db_model.ai_business_description or "",
            primary_purpose=db_model.primary_purpose or "",
            data_category=db_model.data_category or "",
            parent_tables=db_model.parent_tables or [],
            child_tables=db_model.child_tables or [],
            key_columns=db_model.key_columns or [],
            business_processes=db_model.business_processes or [],
            typical_queries=db_model.typical_queries or [],
            join_patterns=db_model.join_patterns or [],
            columns=columns,
            sample_data=db_model.sample_data or [],
            row_count=db_model.row_count,
            confidence_score=db_model.analysis_confidence or 0.0
        )
    
    def clear_cache_for_connection(self, connection_id: str) -> int:
        """Clear all cached analyses for a specific connection"""
        try:
            with SessionLocal() as session:
                deleted_count = session.query(TableAnalysisModel).filter(
                    TableAnalysisModel.connection_id == uuid.UUID(connection_id)
                ).delete()
                session.commit()
                
                logger.info(f"Cleared {deleted_count} cached analyses for connection {connection_id}")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0
    
    def get_cache_stats(self, connection_id: str) -> Dict[str, Any]:
        """Get cache statistics for a connection"""
        try:
            with SessionLocal() as session:
                analyses = session.query(TableAnalysisModel).filter(
                    TableAnalysisModel.connection_id == uuid.UUID(connection_id)
                ).all()
                
                if not analyses:
                    return {'total_cached': 0, 'valid_cached': 0, 'expired_cached': 0}
                
                now = datetime.utcnow()
                valid_count = 0
                expired_count = 0
                
                for analysis in analyses:
                    cache_age = now - analysis.analyzed_at
                    if cache_age <= timedelta(hours=self.cache_validity_hours):
                        valid_count += 1
                    else:
                        expired_count += 1
                
                return {
                    'total_cached': len(analyses),
                    'valid_cached': valid_count,
                    'expired_cached': expired_count,
                    'cache_validity_hours': self.cache_validity_hours
                }
                
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'error': str(e)}


# Global cache instance
table_analysis_cache = TableAnalysisCache()
