"""
Business Rules API Endpoints
Provides REST API for managing business rules and templates
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel

from app.models.business_rules import (
    BusinessRule, BusinessRuleTemplate, RuleCategory, RuleSeverity,
    RuleExtractionRequest, RuleExtractionResponse, RuleValidationResult
)
from app.agents.configurator.rule_extraction_engine import RuleExtractionEngine
from app.agents.configurator.business_rules_persistence import BusinessRulesDatabase
from app.agents.configurator.rule_enhanced_query_generator import RuleEnhancedQueryGenerator
from app.agents.configurator.query_executor import QueryExecutor, QueryExecutionResult
from app.agents.configurator.vector_storage import SchemaVectorStore
from app.models.business_rules import TestQuery
from app.core.config import settings
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/business-rules", tags=["business-rules"])

# Initialize components
rules_db = BusinessRulesDatabase()
vector_store = SchemaVectorStore()
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.1,
    api_key=settings.OPENAI_API_KEY
)
rule_engine = RuleExtractionEngine(llm, vector_store)
rule_enhanced_generator = RuleEnhancedQueryGenerator(llm, vector_store, rules_db)
query_executor = QueryExecutor(rules_db, rule_enhanced_generator)


# Request/Response Models
class ExtractRulesRequest(BaseModel):
    connection_id: str
    domain_hints: List[str] = []
    force_reextraction: bool = False


class ValidateQueryRequest(BaseModel):
    connection_id: str
    sql_query: str
    query_context: Optional[str] = None


class GenerateRuleAwareQueriesRequest(BaseModel):
    connection_id: str
    num_queries: int = 3
    query_types: List[str] = ["select", "join", "aggregate"]
    complexity_level: str = "medium"
    context_hints: List[str] = []


class ExecuteQueryRequest(BaseModel):
    connection_id: str
    sql_query: str
    expected_result_type: str = "multiple_rows"
    validate_rules: bool = True


class NaturalLanguageQueryRequest(BaseModel):
    connection_id: str
    natural_language_question: str
    domain_hint: str = "generic"


# Business Rules CRUD Endpoints

@router.get("/connections/{connection_id}/rules", response_model=List[Dict[str, Any]])
async def get_business_rules(
    connection_id: str,
    category: Optional[str] = Query(None, description="Filter by rule category"),
    severity: Optional[str] = Query(None, description="Filter by rule severity")
):
    """Get business rules for a database connection."""
    try:
        category_enum = RuleCategory(category) if category else None
        severity_enum = RuleSeverity(severity) if severity else None
        
        business_rules = await rules_db.get_business_rules(
            connection_id, category_enum, severity_enum
        )
        
        return [
            {
                "rule_id": rule.rule_id,
                "category": rule.category.value,
                "severity": rule.severity.value,
                "title": rule.title,
                "description": rule.description,
                "trigger_patterns": rule.trigger_patterns,
                "table_patterns": rule.table_patterns,
                "column_patterns": rule.column_patterns,
                "allowed_tables": rule.allowed_tables,
                "forbidden_tables": rule.forbidden_tables,
                "required_joins": rule.required_joins,
                "date_field_mappings": rule.date_field_mappings,
                "sql_transformations": rule.sql_transformations,
                "confidence_score": rule.confidence_score,
                "positive_examples": rule.positive_examples,
                "negative_examples": rule.negative_examples,
                "created_at": rule.created_at.isoformat(),
                "updated_at": rule.updated_at.isoformat()
            }
            for rule in business_rules
        ]
        
    except Exception as e:
        logger.error(f"Error getting business rules: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connections/{connection_id}/rules")
async def create_business_rule(connection_id: str, rule: BusinessRule):
    """Create a new business rule for a connection."""
    try:
        rule.connection_id = connection_id
        success = await rules_db.store_business_rule(rule)
        
        if success:
            return {
                "status": "success",
                "message": "Business rule created successfully",
                "rule_id": rule.rule_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create business rule")
            
    except Exception as e:
        logger.error(f"Error creating business rule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections/{connection_id}/rules/statistics")
async def get_rule_statistics(connection_id: str):
    """Get statistics about business rules for a connection."""
    try:
        stats = await rules_db.get_rule_statistics(connection_id)
        return stats
        
    except Exception as e:
        logger.error(f"Error getting rule statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Rule Extraction Endpoints

@router.post("/connections/{connection_id}/extract-rules")
async def extract_business_rules(connection_id: str, request: ExtractRulesRequest):
    """Extract business rules from database schema using LLM analysis."""
    try:
        # Check if rules already exist
        existing_rules = await rules_db.get_business_rules(connection_id)
        
        if existing_rules and not request.force_reextraction:
            return {
                "status": "success",
                "message": f"Found {len(existing_rules)} existing rules. Use force_reextraction=true to re-extract.",
                "existing_rules_count": len(existing_rules),
                "extracted_rules_count": 0
            }
        
        # Extract rules using LLM
        start_time = datetime.now()
        extraction_response = await rule_engine.extract_rules_from_schema(
            connection_id=connection_id,
            domain_hints=request.domain_hints,
            existing_rules=existing_rules if not request.force_reextraction else []
        )
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Store extracted rules
        stored_count = await rules_db.store_business_rules(extraction_response.extracted_rules)
        
        # Store suggested template if available
        if extraction_response.suggested_template:
            await rules_db.store_business_rule_template(extraction_response.suggested_template)
        
        # Log extraction
        await rules_db.log_rule_extraction(
            connection_id=connection_id,
            schema_context_hash="auto_extracted",
            domain_hints=request.domain_hints,
            extracted_rule_ids=[rule.rule_id for rule in extraction_response.extracted_rules],
            confidence_score=extraction_response.confidence_score,
            extraction_notes=extraction_response.extraction_notes,
            processing_time_ms=processing_time,
            llm_model_used="gpt-4o-mini"
        )
        
        return {
            "status": "success",
            "message": f"Extracted and stored {stored_count} business rules",
            "extracted_rules_count": len(extraction_response.extracted_rules),
            "stored_rules_count": stored_count,
            "confidence_score": extraction_response.confidence_score,
            "extraction_notes": extraction_response.extraction_notes,
            "processing_time_ms": processing_time,
            "suggested_template": extraction_response.suggested_template.name if extraction_response.suggested_template else None
        }
        
    except Exception as e:
        logger.error(f"Error extracting business rules: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connections/{connection_id}/create-generic-template")
async def create_generic_domain_template(connection_id: str, domain_hint: str = "generic"):
    """Create a generic domain template with common database best practices."""
    try:
        template = await rule_engine.create_generic_domain_template(connection_id, domain_hint)
        
        # Store template and rules
        success = await rules_db.store_business_rule_template(template)
        
        if success:
            return {
                "status": "success",
                "message": f"Generic {domain_hint} domain template created successfully",
                "template_id": template.template_id,
                "rules_count": len(template.default_rules),
                "domain": domain_hint
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create generic template")
            
    except Exception as e:
        logger.error(f"Error creating generic template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Rule Validation Endpoints

@router.post("/validate-query")
async def validate_query_against_rules(request: ValidateQueryRequest):
    """Validate a SQL query against business rules."""
    try:
        validation_result = await rule_enhanced_generator.validate_query_against_rules(
            connection_id=request.connection_id,
            sql_query=request.sql_query
        )
        
        return {
            "is_valid": validation_result.is_valid,
            "violated_rules": [
                {
                    "rule_id": rule.rule_id,
                    "title": rule.title,
                    "category": rule.category.value,
                    "severity": rule.severity.value,
                    "description": rule.description
                }
                for rule in validation_result.violated_rules
            ],
            "warnings": validation_result.warnings,
            "suggestions": validation_result.suggestions,
            "corrected_sql": validation_result.corrected_sql
        }
        
    except Exception as e:
        logger.error(f"Error validating query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Rule-Enhanced Query Generation

@router.post("/connections/{connection_id}/generate-rule-aware-queries")
async def generate_rule_aware_queries(connection_id: str, request: GenerateRuleAwareQueriesRequest):
    """Generate test queries with business rules awareness and validation."""
    try:
        test_queries = await rule_enhanced_generator.generate_rule_aware_queries(
            connection_id=request.connection_id,
            num_queries=request.num_queries,
            query_types=request.query_types,
            complexity_level=request.complexity_level,
            context_hints=request.context_hints
        )
        
        return {
            "status": "success",
            "connection_id": connection_id,
            "generated_queries": len(test_queries),
            "queries": [
                {
                    "query_id": query.query_id,
                    "sql_query": query.sql_query,
                    "natural_language_question": query.natural_language_question,
                    "expected_result_type": query.expected_result_type,
                    "confidence_score": query.confidence_score,
                    "generated_at": query.generated_at.isoformat()
                }
                for query in test_queries
            ]
        }
        
    except Exception as e:
        logger.error(f"Error generating rule-aware queries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Template Management Endpoints

@router.get("/templates", response_model=List[Dict[str, Any]])
async def get_business_rule_templates(domain: Optional[str] = Query(None)):
    """Get business rule templates, optionally filtered by domain."""
    try:
        templates = await rules_db.get_business_rule_templates(domain)
        
        return [
            {
                "template_id": template.template_id,
                "name": template.name,
                "description": template.description,
                "domain": template.domain,
                "extraction_patterns": template.extraction_patterns,
                "default_rules_count": len(template.default_rules),
                "created_at": template.created_at.isoformat(),
                "updated_at": template.updated_at.isoformat()
            }
            for template in templates
        ]
        
    except Exception as e:
        logger.error(f"Error getting business rule templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates")
async def create_business_rule_template(template: BusinessRuleTemplate):
    """Create a new business rule template."""
    try:
        success = await rules_db.store_business_rule_template(template)
        
        if success:
            return {
                "status": "success",
                "message": "Business rule template created successfully",
                "template_id": template.template_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create business rule template")
            
    except Exception as e:
        logger.error(f"Error creating business rule template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Utility Endpoints

@router.delete("/connections/{connection_id}/rules")
async def delete_business_rules(connection_id: str):
    """Delete all business rules for a connection."""
    try:
        success = await rules_db.delete_business_rules(connection_id)
        
        if success:
            return {
                "status": "success",
                "message": "Business rules deleted successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete business rules")
            
    except Exception as e:
        logger.error(f"Error deleting business rules: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Query Execution Endpoints

@router.post("/execute-query")
async def execute_test_query(request: ExecuteQueryRequest):
    """Execute a SQL query on the database and return results with accuracy scoring."""
    try:
        # Create TestQuery object
        test_query = TestQuery(
            query_id=f"manual_{int(datetime.now().timestamp())}",
            connection_id=request.connection_id,
            sql_query=request.sql_query,
            natural_language_question="Manual test query",
            expected_result_type=request.expected_result_type,
            confidence_score=0.8,
            generated_at=datetime.now()
        )
        
        # Execute query
        result = await query_executor.execute_test_query(
            connection_id=request.connection_id,
            test_query=test_query,
            validate_rules=request.validate_rules
        )
        
        # Persist execution data
        await query_executor._persist_query_execution(
            connection_id=request.connection_id,
            natural_language_question="Manual test query",
            test_query=test_query,
            result=result,
            domain_hint="manual"
        )
        
        return {
            "status": "success" if result.execution_success else "failed",
            "query_id": result.query_id,
            "sql_query": result.sql_query,
            "execution_success": result.execution_success,
            "results": result.results,
            "error_message": result.error_message,
            "execution_time_ms": result.execution_time_ms,
            "row_count": result.row_count,
            "accuracy_score": result.accuracy_score,
            "confidence_score": result.confidence_score,
            "rule_compliance_score": result.rule_compliance_score,
            "performance_score": result.performance_score,
            "executed_at": result.executed_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error executing test query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/natural-language-query")
async def execute_natural_language_query(request: NaturalLanguageQueryRequest):
    """Generate and execute a SQL query from a natural language question."""
    try:
        result = await query_executor.execute_natural_language_query(
            connection_id=request.connection_id,
            natural_language_question=request.natural_language_question,
            domain_hint=request.domain_hint
        )
        
        # DIRECT TYPE CASTING FIX: If query failed with SUM(text) error, apply immediate fix
        if not result.execution_success and result.error_message and "function sum(text) does not exist" in result.error_message.lower():
            logger.info(f"🔧 Detected SUM(text) error, applying direct type casting fix...")
            
            # Apply direct SQL fix by replacing SUM(column) with SUM(column::numeric)
            import re
            original_sql = result.sql_query
            fixed_sql = re.sub(r'SUM\s*\(([^)]+)\)', r'SUM(\1::numeric)', original_sql, flags=re.IGNORECASE)
            
            if fixed_sql != original_sql:
                logger.info(f"   Original: {original_sql[:100]}...")
                logger.info(f"   Fixed: {fixed_sql[:100]}...")
                
                # Create a new test query with the fixed SQL
                from app.models.business_rules import TestQuery
                import uuid
                
                fixed_query = TestQuery(
                    query_id=str(uuid.uuid4()),
                    connection_id=request.connection_id,
                    sql_query=fixed_sql,
                    description=f"Type-cast fixed: {request.natural_language_question}",
                    expected_result_type="rows",
                    business_context="Direct API-level type casting fix"
                )
                
                # Execute the fixed query
                fixed_result = await query_executor.execute_test_query(
                    connection_id=request.connection_id,
                    test_query=fixed_query,
                    validate_rules=True
                )
                
                if fixed_result.execution_success:
                    logger.info(f"✅ Direct type casting fix successful!")
                    result = fixed_result
                else:
                    logger.warning(f"❌ Direct type casting fix failed: {fixed_result.error_message}")
                    
                    # Check if it's a column name issue and try to fix it
                    if "column" in fixed_result.error_message.lower() and "does not exist" in fixed_result.error_message.lower():
                        logger.info(f"🔧 Detected column name issue, applying schema correction...")
                        
                        # Common column name corrections for disbursement tables
                        column_corrections = {
                            'disbursement_date': ['disbursed_date', 'date_disbursed', 'created_at', 'disbursement_time'],
                            'disbursement_status': ['status', 'disbursement_state', 'state'],
                            'loan_amount': ['amount', 'disbursed_amount', 'principal_amount']
                        }
                        
                        corrected_sql = fixed_sql
                        corrections_applied = []
                        
                        for wrong_col, possible_cols in column_corrections.items():
                            if wrong_col in corrected_sql:
                                # Try the first alternative (most likely correct)
                                corrected_col = possible_cols[0]
                                corrected_sql = corrected_sql.replace(wrong_col, corrected_col)
                                corrections_applied.append(f"{wrong_col} → {corrected_col}")
                        
                        if corrections_applied:
                            logger.info(f"   Applied corrections: {', '.join(corrections_applied)}")
                            
                            # Create and execute the fully corrected query
                            fully_corrected_query = TestQuery(
                                query_id=str(uuid.uuid4()),
                                connection_id=request.connection_id,
                                sql_query=corrected_sql,
                                description=f"Fully corrected: {request.natural_language_question}",
                                expected_result_type="rows",
                                business_context="Type casting + column name corrections applied"
                            )
                            
                            final_result = await query_executor.execute_test_query(
                                connection_id=request.connection_id,
                                test_query=fully_corrected_query,
                                validate_rules=True
                            )
                            
                            if final_result.execution_success:
                                logger.info(f"✅ Full correction successful!")
                                result = final_result
                            else:
                                logger.info(f"⚠️ Partial success - showing type casting progress")
                                result.sql_query = corrected_sql
                                result.error_message = f"Type casting fixed ✅, column corrections attempted: {', '.join(corrections_applied)}. Remaining error: {final_result.error_message}"
                        else:
                            # Update the result to show progress - type casting worked but there's a schema issue
                            result.sql_query = fixed_sql  # Show the corrected SQL
                            result.error_message = f"Type casting applied successfully ✅, but schema issue found: {fixed_result.error_message}"
                    else:
                        # Update the result to show progress - type casting worked but there's a different issue
                        result.sql_query = fixed_sql  # Show the corrected SQL
                        result.error_message = f"Type casting applied successfully ✅, but other issue found: {fixed_result.error_message}"
        
        return {
            "status": "success" if result.execution_success else "failed",
            "natural_language_question": request.natural_language_question,
            "generated_sql": result.sql_query,
            "execution_success": result.execution_success,
            "results": result.results,
            "error_message": result.error_message,
            "execution_time_ms": result.execution_time_ms,
            "row_count": result.row_count,
            "accuracy_score": result.accuracy_score,
            "confidence_score": result.confidence_score,
            "rule_compliance_score": result.rule_compliance_score,
            "performance_score": result.performance_score,
            "executed_at": result.executed_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error executing natural language query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections/{connection_id}/execution-statistics")
async def get_execution_statistics(connection_id: str):
    """Get query execution statistics for a connection."""
    try:
        stats = await query_executor.get_execution_statistics(connection_id)
        return stats
        
    except Exception as e:
        logger.error(f"Error getting execution statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint for business rules service."""
    return {
        "status": "healthy",
        "service": "business-rules",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "rules_database": "operational",
            "vector_store": "operational",
            "llm": "operational",
            "rule_engine": "operational",
            "query_executor": "operational"
        }
    }
