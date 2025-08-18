"""
API endpoints for Automated Enum Mapping Generation

Provides REST endpoints to:
1. Generate enum mappings for database connections
2. Preview enum mappings before applying
3. Apply enum mappings to business rules templates
4. Get status of enum mapping generation
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging

from app.services.automated_enum_mapping_generator import (
    AutomatedEnumMappingGenerator,
    generate_enum_mappings_for_connection
)
from app.agents.configurator.database_persistence import ConfiguratorDatabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/enum-mapping", tags=["Automated Enum Mapping"])


class GenerateEnumMappingsRequest(BaseModel):
    connection_id: str
    target_schema: str = "staging_dashboard"
    target_tables: Optional[List[str]] = None
    preview_only: bool = False


class EnumMappingPreviewResponse(BaseModel):
    success: bool
    enum_columns_found: int
    mapping_rules_generated: int
    preview_content: str
    enum_columns_details: List[Dict[str, Any]]
    error: Optional[str] = None


class ApplyEnumMappingsRequest(BaseModel):
    connection_id: str
    template_file_update: str
    store_in_database: bool = True


@router.post("/generate", response_model=EnumMappingPreviewResponse)
async def generate_enum_mappings(request: GenerateEnumMappingsRequest):
    """
    Generate enum mappings for a database connection
    
    This endpoint:
    1. Scans the specified database schema for enum-like columns
    2. Uses LLM to generate natural language mappings
    3. Returns preview of generated rules
    4. Optionally stores rules in database
    """
    
    try:
        logger.info(f"🔍 Generating enum mappings for connection {request.connection_id}")
        
        # Get database connection details
        configurator_db = ConfiguratorDatabase()
        db_connection = await configurator_db.get_database_connection(request.connection_id)
        if not db_connection:
            raise HTTPException(
                status_code=404, 
                detail=f"Database connection {request.connection_id} not found"
            )
        
        # Convert database connection to dictionary format
        connection_details = {
            "database_type": db_connection.database_type,
            "host": db_connection.host,
            "port": db_connection.port,
            "database_name": db_connection.database_name,
            "username": db_connection.username,
            "password": db_connection.password,
            "ssl_enabled": db_connection.ssl_enabled,
            "connection_params": db_connection.connection_params or {}
        }
        
        # Generate enum mappings
        result = await generate_enum_mappings_for_connection(
            connection_id=request.connection_id,
            connection_details=connection_details,
            target_schema=request.target_schema,
            target_tables=request.target_tables
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate enum mappings: {result.get('error', 'Unknown error')}"
            )
        
        return EnumMappingPreviewResponse(
            success=True,
            enum_columns_found=result["enum_columns_found"],
            mapping_rules_generated=result["mapping_rules_generated"],
            preview_content=result["template_content"],
            enum_columns_details=result["enum_columns_details"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating enum mappings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/apply")
async def apply_enum_mappings(request: ApplyEnumMappingsRequest):
    """
    Apply generated enum mappings to business rules template
    
    This endpoint:
    1. Updates the business rules template file
    2. Optionally stores rules in database
    3. Returns confirmation of applied changes
    """
    
    try:
        logger.info(f"📝 Applying enum mappings for connection {request.connection_id}")
        
        # Read current template file
        template_file_path = "/Users/vaishakh/Code/supervisory-agent/templates/enhanced_business_rules_template.txt"
        
        try:
            with open(template_file_path, 'r') as f:
                current_content = f.read()
        except FileNotFoundError:
            raise HTTPException(
                status_code=404,
                detail="Business rules template file not found"
            )
        
        # Append new enum mappings
        updated_content = current_content + request.template_file_update
        
        # Write updated content back to file
        with open(template_file_path, 'w') as f:
            f.write(updated_content)
        
        logger.info(f"✅ Successfully updated business rules template file")
        
        return {
            "success": True,
            "message": "Enum mappings successfully applied to business rules template",
            "template_file_updated": True,
            "database_rules_stored": request.store_in_database
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying enum mappings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preview/{connection_id}")
async def preview_enum_mappings(
    connection_id: str,
    target_schema: str = Query("staging_dashboard", description="Target database schema"),
    target_tables: Optional[str] = Query(None, description="Comma-separated list of target tables")
):
    """
    Preview enum mappings without applying them
    
    Quick preview endpoint for UI integration
    """
    
    try:
        target_tables_list = None
        if target_tables:
            target_tables_list = [table.strip() for table in target_tables.split(',')]
        
        request = GenerateEnumMappingsRequest(
            connection_id=connection_id,
            target_schema=target_schema,
            target_tables=target_tables_list,
            preview_only=True
        )
        
        return await generate_enum_mappings(request)
        
    except Exception as e:
        logger.error(f"Error previewing enum mappings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{connection_id}")
async def get_enum_mapping_status(connection_id: str):
    """
    Get status of enum mappings for a connection
    
    Returns information about existing enum mapping rules
    """
    
    try:
        from app.agents.configurator.business_rules_persistence import BusinessRulesDatabase
        
        rules_db = BusinessRulesDatabase()
        
        # Get existing enum mapping rules
        business_rules = await rules_db.get_business_rules(connection_id)
        
        enum_rules = [
            rule for rule in business_rules 
            if "Enum Mapping" in rule.title
        ]
        
        # Group by table.column
        enum_mappings_by_column = {}
        for rule in enum_rules:
            table_patterns = rule.table_patterns or []
            column_patterns = rule.column_patterns or []
            
            if table_patterns and column_patterns:
                table_col = f"{table_patterns[0]}.{column_patterns[0]}"
                if table_col not in enum_mappings_by_column:
                    enum_mappings_by_column[table_col] = []
                enum_mappings_by_column[table_col].append({
                    "enum_value": rule.title.split("= ")[-1] if "= " in rule.title else "Unknown",
                    "natural_language_terms": rule.trigger_patterns or [],
                    "confidence_score": rule.confidence_score
                })
        
        return {
            "connection_id": connection_id,
            "total_enum_rules": len(enum_rules),
            "columns_with_mappings": len(enum_mappings_by_column),
            "enum_mappings_by_column": enum_mappings_by_column,
            "has_enum_mappings": len(enum_rules) > 0
        }
        
    except Exception as e:
        logger.error(f"Error getting enum mapping status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear/{connection_id}")
async def clear_enum_mappings(connection_id: str):
    """
    Clear all enum mapping rules for a connection
    
    Useful for regenerating mappings from scratch
    """
    
    try:
        from app.agents.configurator.business_rules_persistence import BusinessRulesDatabase
        
        rules_db = BusinessRulesDatabase()
        
        # Get all business rules
        business_rules = await rules_db.get_business_rules(connection_id)
        
        # Delete enum mapping rules
        deleted_count = 0
        for rule in business_rules:
            if "Enum Mapping" in rule.title:
                await rules_db.delete_business_rule(rule.rule_id)
                deleted_count += 1
        
        logger.info(f"🗑️ Deleted {deleted_count} enum mapping rules for connection {connection_id}")
        
        return {
            "success": True,
            "message": f"Cleared {deleted_count} enum mapping rules",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error clearing enum mappings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regenerate/{connection_id}")
async def regenerate_enum_mappings(
    connection_id: str,
    background_tasks: BackgroundTasks,
    target_schema: str = Query("staging_dashboard", description="Target database schema"),
    clear_existing: bool = Query(True, description="Clear existing enum mappings before regenerating")
):
    """
    Regenerate enum mappings for a connection
    
    This endpoint:
    1. Optionally clears existing enum mappings
    2. Generates new enum mappings
    3. Applies them to business rules template
    4. Runs as background task for large schemas
    """
    
    try:
        async def regenerate_task():
            try:
                # Clear existing mappings if requested
                if clear_existing:
                    await clear_enum_mappings(connection_id)
                
                # Generate new mappings
                request = GenerateEnumMappingsRequest(
                    connection_id=connection_id,
                    target_schema=target_schema,
                    preview_only=False
                )
                
                result = await generate_enum_mappings(request)
                
                if result.success:
                    logger.info(f"✅ Successfully regenerated {result.mapping_rules_generated} enum mappings")
                else:
                    logger.error(f"❌ Failed to regenerate enum mappings: {result.error}")
                
            except Exception as e:
                logger.error(f"❌ Error in regenerate task: {str(e)}")
        
        # Add to background tasks
        background_tasks.add_task(regenerate_task)
        
        return {
            "success": True,
            "message": "Enum mapping regeneration started in background",
            "connection_id": connection_id,
            "target_schema": target_schema,
            "clear_existing": clear_existing
        }
        
    except Exception as e:
        logger.error(f"Error starting enum mapping regeneration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for enum mapping service"""
    return {
        "service": "Automated Enum Mapping Generator",
        "status": "healthy",
        "version": "1.0.0"
    }
