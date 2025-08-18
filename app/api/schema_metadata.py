"""
Schema Metadata API
Provides endpoints to view stored schema analysis data and raw metadata
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import logging

from app.agents.configurator.schema_analysis_storage import SchemaAnalysisStorage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/schema-metadata", tags=["Schema Metadata"])


@router.get("/sessions/{session_id}/summary")
async def get_analysis_session_summary(session_id: str):
    """Get comprehensive summary of a schema analysis session"""
    try:
        storage = SchemaAnalysisStorage()
        summary = await storage.get_analysis_session_summary(session_id)
        
        if "error" in summary:
            raise HTTPException(status_code=404, detail=summary["error"])
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting session summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections/{connection_id}/analysis-history")
async def get_connection_analysis_history(connection_id: str):
    """Get analysis history for a connection"""
    try:
        storage = SchemaAnalysisStorage()
        history = await storage.get_connection_analysis_history(connection_id)
        
        return {
            "connection_id": connection_id,
            "analysis_sessions": history
        }
        
    except Exception as e:
        logger.error(f"Error getting analysis history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/tables")
async def get_stored_table_metadata(session_id: str):
    """Get detailed table metadata stored during analysis"""
    try:
        storage = SchemaAnalysisStorage()
        
        # Get table analysis data from the database
        with storage.get_session() as session:
            from app.models.database.schema_analysis_models import TableAnalysisModel
            
            tables = session.query(TableAnalysisModel).filter(
                TableAnalysisModel.session_id == session_id
            ).all()
            
            table_metadata = []
            for table in tables:
                table_metadata.append({
                    "id": table.id,
                    "table_name": table.table_name,
                    "schema_name": table.schema_name,
                    "full_table_name": table.full_table_name,
                    "table_type": table.table_type,
                    "row_count": table.row_count,
                    "column_count": table.column_count,
                    "raw_columns_info": table.columns_info,  # Raw column metadata
                    "primary_keys": table.primary_keys,
                    "foreign_keys": table.foreign_keys,
                    "indexes": table.indexes,
                    "inferred_business_purpose": table.inferred_business_purpose,
                    "naming_patterns": table.naming_patterns,
                    "data_quality_notes": table.data_quality_notes,
                    "analysis_confidence": table.analysis_confidence,
                    "analyzed_at": table.analyzed_at.isoformat() if table.analyzed_at else None
                })
            
            return {
                "session_id": session_id,
                "total_tables": len(table_metadata),
                "tables": table_metadata
            }
        
    except Exception as e:
        logger.error(f"Error getting table metadata: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/relationships")
async def get_stored_relationship_metadata(session_id: str):
    """Get detailed relationship metadata stored during analysis"""
    try:
        storage = SchemaAnalysisStorage()
        
        with storage.get_session() as session:
            from app.models.database.schema_analysis_models import RelationshipAnalysisModel
            
            relationships = session.query(RelationshipAnalysisModel).filter(
                RelationshipAnalysisModel.session_id == session_id
            ).all()
            
            relationship_metadata = []
            for rel in relationships:
                relationship_metadata.append({
                    "id": rel.id,
                    "from_table": rel.from_table,
                    "to_table": rel.to_table,
                    "relationship_type": rel.relationship_type,
                    "from_columns": rel.from_columns,
                    "to_columns": rel.to_columns,
                    "confidence_score": rel.confidence_score,
                    "relationship_strength": rel.relationship_strength,
                    "business_meaning": rel.business_meaning,
                    "discovery_method": rel.discovery_method,
                    "analyzed_at": rel.analyzed_at.isoformat() if rel.analyzed_at else None
                })
            
            return {
                "session_id": session_id,
                "total_relationships": len(relationship_metadata),
                "relationships": relationship_metadata
            }
        
    except Exception as e:
        logger.error(f"Error getting relationship metadata: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/business-contexts")
async def get_stored_business_contexts(session_id: str):
    """Get business context analysis stored during schema analysis"""
    try:
        storage = SchemaAnalysisStorage()
        
        with storage.get_session() as session:
            from app.models.database.schema_analysis_models import BusinessContextAnalysisModel
            
            contexts = session.query(BusinessContextAnalysisModel).filter(
                BusinessContextAnalysisModel.session_id == session_id
            ).all()
            
            context_metadata = []
            for context in contexts:
                context_metadata.append({
                    "id": context.id,
                    "context_name": context.context_name,
                    "context_type": context.context_type,
                    "confidence_score": context.confidence_score,
                    "description": context.description,
                    "related_tables": context.related_tables,
                    "key_entities": context.key_entities,
                    "business_processes": context.business_processes,
                    "naming_conventions": context.naming_conventions,
                    "data_flow_patterns": context.data_flow_patterns,
                    "temporal_patterns": context.temporal_patterns,
                    "analysis_method": context.analysis_method,
                    "analyzed_at": context.analyzed_at.isoformat() if context.analyzed_at else None
                })
            
            return {
                "session_id": session_id,
                "total_contexts": len(context_metadata),
                "business_contexts": context_metadata
            }
        
    except Exception as e:
        logger.error(f"Error getting business contexts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/complete-analysis")
async def get_complete_analysis_data(session_id: str):
    """Get complete analysis data including raw metadata and documentation"""
    try:
        storage = SchemaAnalysisStorage()
        
        # Get session summary
        summary = await storage.get_analysis_session_summary(session_id)
        
        if "error" in summary:
            raise HTTPException(status_code=404, detail=summary["error"])
        
        # Get all detailed data
        with storage.get_session() as session:
            from app.models.database.schema_analysis_models import (
                TableAnalysisModel, RelationshipAnalysisModel, BusinessContextAnalysisModel
            )
            
            # Get tables with raw metadata
            tables = session.query(TableAnalysisModel).filter(
                TableAnalysisModel.session_id == session_id
            ).all()
            
            # Get relationships
            relationships = session.query(RelationshipAnalysisModel).filter(
                RelationshipAnalysisModel.session_id == session_id
            ).all()
            
            # Get business contexts
            contexts = session.query(BusinessContextAnalysisModel).filter(
                BusinessContextAnalysisModel.session_id == session_id
            ).all()
            
            return {
                "session_summary": summary,
                "raw_metadata": {
                    "tables": [
                        {
                            "table_name": table.table_name,
                            "schema_name": table.schema_name,
                            "row_count": table.row_count,
                            "raw_columns": table.columns_info,  # Raw column metadata from database
                            "primary_keys": table.primary_keys,
                            "foreign_keys": table.foreign_keys,
                            "table_type": table.table_type
                        }
                        for table in tables
                    ],
                    "relationships": [
                        {
                            "from_table": rel.from_table,
                            "to_table": rel.to_table,
                            "relationship_type": rel.relationship_type,
                            "from_columns": rel.from_columns,
                            "to_columns": rel.to_columns,
                            "discovery_method": rel.discovery_method
                        }
                        for rel in relationships
                    ]
                },
                "documentation": {
                    "business_purposes": {
                        table.table_name: table.inferred_business_purpose
                        for table in tables
                    },
                    "naming_patterns": {
                        table.table_name: table.naming_patterns
                        for table in tables
                    },
                    "business_contexts": [
                        {
                            "name": context.context_name,
                            "type": context.context_type,
                            "description": context.description,
                            "related_tables": context.related_tables,
                            "confidence": context.confidence_score
                        }
                        for context in contexts
                    ],
                    "relationship_meanings": {
                        f"{rel.from_table}->{rel.to_table}": rel.business_meaning
                        for rel in relationships
                    }
                },
                "analysis_metadata": {
                    "total_tables_analyzed": len(tables),
                    "total_relationships_found": len(relationships),
                    "total_business_contexts": len(contexts),
                    "analysis_session_id": session_id
                }
            }
        
    except Exception as e:
        logger.error(f"Error getting complete analysis data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections/{connection_id}/latest-analysis")
async def get_latest_analysis_for_connection(connection_id: str):
    """Get the latest analysis data for a connection"""
    try:
        storage = SchemaAnalysisStorage()
        
        # Get analysis history to find latest session
        history = await storage.get_connection_analysis_history(connection_id)
        
        if not history:
            raise HTTPException(status_code=404, detail="No analysis sessions found for this connection")
        
        # Get the latest session
        latest_session = history[0]  # History is ordered by started_at desc
        session_id = latest_session["session_id"]
        
        # Get complete analysis data for latest session
        return await get_complete_analysis_data(session_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
