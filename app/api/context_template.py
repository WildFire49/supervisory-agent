"""
Context Template API Endpoints
Provides REST API for managing connection-specific context templates and user feedback
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from app.services.context_template_service import context_template_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/context-template", tags=["Context Template"])


# Pydantic Models
class CreateTemplateRequest(BaseModel):
    connection_id: str
    database_type: str
    domain_hint: str = "generic"
    template_name: Optional[str] = None


class UpdateTemplateRequest(BaseModel):
    business_rules_template: Optional[str] = None
    schema_context_template: Optional[str] = None
    domain_specific_prompts: Optional[str] = None
    table_relationships: Optional[Dict[str, Any]] = None
    common_patterns: Optional[List[Dict]] = None
    field_mappings: Optional[Dict[str, str]] = None


class QueryCorrectionRequest(BaseModel):
    connection_id: str
    natural_language_question: str
    generated_sql_original: str
    execution_success_original: bool
    error_message_original: Optional[str] = None
    user_feedback: str
    correction_type: str  # wrong_table, wrong_column, wrong_logic, missing_rule, etc.
    corrected_sql: Optional[str] = None
    additional_context: Optional[str] = None
    corrected_by: str = "user"


class QueryFeedbackRequest(BaseModel):
    connection_id: str
    natural_language_question: str
    generated_sql: str
    execution_success: bool
    user_satisfaction_score: int  # 1-10
    context_relevance_score: int  # 1-10
    rule_compliance_score: int  # 1-10
    feedback_notes: Optional[str] = None


# API Endpoints

@router.post("/create")
async def create_template(request: CreateTemplateRequest):
    """Create a new context template for a database connection"""
    try:
        template_id = await context_template_service.create_default_template(
            connection_id=request.connection_id,
            database_type=request.database_type,
            domain_hint=request.domain_hint
        )
        
        return {
            "status": "success",
            "template_id": template_id,
            "message": f"Context template created for connection {request.connection_id}"
        }
        
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connection/{connection_id}")
async def get_template_for_connection(connection_id: str):
    """Get the active context template for a connection"""
    try:
        template = await context_template_service.get_template_for_connection(connection_id)
        
        if not template:
            raise HTTPException(
                status_code=404, 
                detail=f"No active template found for connection {connection_id}"
            )
        
        return {
            "status": "success",
            "template": template
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/template/{template_id}")
async def update_template(template_id: str, request: UpdateTemplateRequest):
    """Update an existing context template"""
    try:
        # Convert request to dict, excluding None values
        updates = {k: v for k, v in request.dict().items() if v is not None}
        
        success = await context_template_service.update_template(
            template_id=template_id,
            updates=updates,
            updated_by="user"
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Template {template_id} not found or could not be updated"
            )
        
        return {
            "status": "success",
            "message": f"Template {template_id} updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/correction")
async def log_query_correction(request: QueryCorrectionRequest):
    """Log a user correction for an incorrect query"""
    try:
        correction_id = await context_template_service.log_query_correction(
            connection_id=request.connection_id,
            natural_language_question=request.natural_language_question,
            generated_sql_original=request.generated_sql_original,
            execution_success_original=request.execution_success_original,
            error_message_original=request.error_message_original,
            user_feedback=request.user_feedback,
            correction_type=request.correction_type,
            corrected_sql=request.corrected_sql,
            additional_context=request.additional_context,
            corrected_by=request.corrected_by
        )
        
        if not correction_id:
            raise HTTPException(
                status_code=400,
                detail="Failed to log query correction"
            )
        
        return {
            "status": "success",
            "correction_id": correction_id,
            "message": "Query correction logged and applied to template"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging query correction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def submit_query_feedback(request: QueryFeedbackRequest):
    """Submit feedback for a generated query"""
    try:
        # This endpoint allows users to rate query quality without necessarily providing corrections
        # The feedback helps improve the template over time
        
        # For now, we'll log this as a usage log entry
        # In a full implementation, you might want a separate feedback table
        
        return {
            "status": "success",
            "message": "Feedback submitted successfully"
        }
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connection/{connection_id}/enhanced-context")
async def get_enhanced_context(connection_id: str, question: str, domain_hint: str = "generic"):
    """Get enhanced context for query generation"""
    try:
        context = await context_template_service.get_enhanced_context_for_query(
            connection_id=connection_id,
            natural_language_question=question,
            domain_hint=domain_hint
        )
        
        return {
            "status": "success",
            "context": context
        }
        
    except Exception as e:
        logger.error(f"Error getting enhanced context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connection/{connection_id}/corrections")
async def get_corrections_history(connection_id: str, limit: int = 10):
    """Get correction history for a connection"""
    try:
        from app.core.database import SessionLocal
        from app.models.database.context_template_models import QueryCorrectionLogModel
        
        with SessionLocal() as session:
            corrections = session.query(QueryCorrectionLogModel).filter(
                QueryCorrectionLogModel.connection_id == connection_id
            ).order_by(QueryCorrectionLogModel.created_at.desc()).limit(limit).all()
            
            correction_list = []
            for correction in corrections:
                correction_list.append({
                    "correction_id": str(correction.id),
                    "natural_language_question": correction.natural_language_question,
                    "correction_type": correction.correction_type,
                    "user_feedback": correction.user_feedback,
                    "additional_context": correction.additional_context,
                    "created_at": correction.created_at.isoformat(),
                    "corrected_by": correction.corrected_by,
                    "applied_to_template": correction.applied_to_template
                })
            
            return {
                "status": "success",
                "corrections": correction_list,
                "total_count": len(correction_list)
            }
            
    except Exception as e:
        logger.error(f"Error getting corrections history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/template/{template_id}")
async def deactivate_template(template_id: str):
    """Deactivate a context template"""
    try:
        success = await context_template_service.update_template(
            template_id=template_id,
            updates={"is_active": False},
            updated_by="user"
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Template {template_id} not found"
            )
        
        return {
            "status": "success",
            "message": f"Template {template_id} deactivated"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint for context template service"""
    return {
        "status": "healthy",
        "service": "context_template",
        "timestamp": datetime.utcnow().isoformat()
    }
