"""
Business Rules Database Persistence Layer
Handles storage and retrieval of business rules and templates
"""

import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_

from app.core.database import engine
from app.models.database.business_rules_models import (
    BusinessRuleModel, BusinessRuleTemplateModel, 
    RuleValidationLogModel, RuleExtractionLogModel
)
from app.models.business_rules import (
    BusinessRule, BusinessRuleTemplate, RuleValidationResult,
    RuleCategory, RuleSeverity
)

logger = logging.getLogger(__name__)


class BusinessRulesDatabase:
    """Database operations for business rules"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    # Business Rules CRUD Operations
    
    async def store_business_rule(self, business_rule: BusinessRule) -> bool:
        """Store a business rule in the database"""
        try:
            with self.get_session() as session:
                db_rule = BusinessRuleModel(
                    rule_id=business_rule.rule_id,
                    connection_id=uuid.UUID(business_rule.connection_id),
                    category=business_rule.category.value,
                    severity=business_rule.severity.value,
                    title=business_rule.title,
                    description=business_rule.description,
                    trigger_patterns=business_rule.trigger_patterns,
                    table_patterns=business_rule.table_patterns,
                    column_patterns=business_rule.column_patterns,
                    allowed_tables=business_rule.allowed_tables,
                    forbidden_tables=business_rule.forbidden_tables,
                    required_joins=business_rule.required_joins,
                    date_field_mappings=business_rule.date_field_mappings,
                    sql_transformations=business_rule.sql_transformations,
                    confidence_score=business_rule.confidence_score,
                    positive_examples=business_rule.positive_examples,
                    negative_examples=business_rule.negative_examples,
                    created_at=business_rule.created_at,
                    updated_at=business_rule.updated_at
                )
                
                session.add(db_rule)
                session.commit()
                
                logger.info(f"Stored business rule: {business_rule.rule_id}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error storing business rule: {str(e)}")
            return False
    
    async def store_business_rules(self, business_rules: List[BusinessRule]) -> int:
        """Store multiple business rules and return count of successful stores"""
        stored_count = 0
        for rule in business_rules:
            if await self.store_business_rule(rule):
                stored_count += 1
        return stored_count
    
    async def get_business_rules(
        self, 
        connection_id: str,
        category: Optional[RuleCategory] = None,
        severity: Optional[RuleSeverity] = None
    ) -> List[BusinessRule]:
        """Get business rules for a connection"""
        try:
            with self.get_session() as session:
                query = session.query(BusinessRuleModel).filter(
                    BusinessRuleModel.connection_id == uuid.UUID(connection_id)
                )
                
                if category:
                    query = query.filter(BusinessRuleModel.category == category.value)
                
                if severity:
                    query = query.filter(BusinessRuleModel.severity == severity.value)
                
                db_rules = query.all()
                
                # Convert to BusinessRule objects
                business_rules = []
                for db_rule in db_rules:
                    business_rule = BusinessRule(
                        rule_id=db_rule.rule_id,
                        connection_id=str(db_rule.connection_id),
                        category=RuleCategory(db_rule.category),
                        severity=RuleSeverity(db_rule.severity),
                        title=db_rule.title,
                        description=db_rule.description,
                        trigger_patterns=db_rule.trigger_patterns or [],
                        table_patterns=db_rule.table_patterns or [],
                        column_patterns=db_rule.column_patterns or [],
                        allowed_tables=db_rule.allowed_tables or [],
                        forbidden_tables=db_rule.forbidden_tables or [],
                        required_joins=db_rule.required_joins or [],
                        date_field_mappings=db_rule.date_field_mappings or {},
                        sql_transformations=db_rule.sql_transformations or [],
                        confidence_score=db_rule.confidence_score,
                        positive_examples=db_rule.positive_examples or [],
                        negative_examples=db_rule.negative_examples or [],
                        created_at=db_rule.created_at,
                        updated_at=db_rule.updated_at
                    )
                    business_rules.append(business_rule)
                
                logger.info(f"Retrieved {len(business_rules)} business rules for connection {connection_id}")
                return business_rules
                
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving business rules: {str(e)}")
            return []
    
    async def get_applicable_rules(
        self, 
        connection_id: str, 
        query_context: str
    ) -> List[BusinessRule]:
        """Get business rules applicable to a specific query context"""
        try:
            all_rules = await self.get_business_rules(connection_id)
            applicable_rules = []
            
            query_context_lower = query_context.lower()
            
            for rule in all_rules:
                # Check if any trigger patterns match the query context
                if any(pattern.lower() in query_context_lower for pattern in rule.trigger_patterns):
                    applicable_rules.append(rule)
                    continue
                
                # Check table patterns
                if any(pattern.lower() in query_context_lower for pattern in rule.table_patterns):
                    applicable_rules.append(rule)
                    continue
                
                # Check column patterns
                if any(pattern.lower() in query_context_lower for pattern in rule.column_patterns):
                    applicable_rules.append(rule)
            
            logger.info(f"Found {len(applicable_rules)} applicable rules for context")
            return applicable_rules
            
        except Exception as e:
            logger.error(f"Error finding applicable rules: {str(e)}")
            return []
    
    # Business Rule Templates CRUD Operations
    
    async def store_business_rule_template(self, template: BusinessRuleTemplate) -> bool:
        """Store a business rule template"""
        try:
            with self.get_session() as session:
                db_template = BusinessRuleTemplateModel(
                    template_id=template.template_id,
                    name=template.name,
                    description=template.description,
                    domain=template.domain,
                    extraction_patterns=template.extraction_patterns,
                    created_at=template.created_at,
                    updated_at=template.updated_at
                )
                
                session.add(db_template)
                session.commit()
                
                # Store associated default rules
                for rule in template.default_rules:
                    await self.store_business_rule(rule)
                
                logger.info(f"Stored business rule template: {template.template_id}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error storing business rule template: {str(e)}")
            return False
    
    async def get_business_rule_templates(self, domain: Optional[str] = None) -> List[BusinessRuleTemplate]:
        """Get business rule templates, optionally filtered by domain"""
        try:
            with self.get_session() as session:
                query = session.query(BusinessRuleTemplateModel)
                
                if domain:
                    query = query.filter(BusinessRuleTemplateModel.domain == domain)
                
                db_templates = query.all()
                
                templates = []
                for db_template in db_templates:
                    template = BusinessRuleTemplate(
                        template_id=db_template.template_id,
                        name=db_template.name,
                        description=db_template.description,
                        domain=db_template.domain,
                        extraction_patterns=db_template.extraction_patterns or [],
                        created_at=db_template.created_at,
                        updated_at=db_template.updated_at
                    )
                    templates.append(template)
                
                logger.info(f"Retrieved {len(templates)} business rule templates")
                return templates
                
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving business rule templates: {str(e)}")
            return []
    
    # Validation and Extraction Logging
    
    async def log_rule_validation(
        self, 
        connection_id: str,
        query_id: Optional[str],
        validation_result: RuleValidationResult,
        original_sql: str,
        processing_time_ms: Optional[float] = None
    ) -> bool:
        """Log rule validation results"""
        try:
            with self.get_session() as session:
                log_entry = RuleValidationLogModel(
                    connection_id=uuid.UUID(connection_id),
                    query_id=query_id,
                    original_sql=original_sql,
                    corrected_sql=validation_result.corrected_sql,
                    is_valid=validation_result.is_valid,
                    violated_rules=[rule.rule_id for rule in validation_result.violated_rules],
                    warnings=validation_result.warnings,
                    suggestions=validation_result.suggestions,
                    processing_time_ms=processing_time_ms
                )
                
                session.add(log_entry)
                session.commit()
                
                logger.info(f"Logged rule validation for connection {connection_id}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error logging rule validation: {str(e)}")
            return False
    
    async def log_rule_extraction(
        self,
        connection_id: str,
        schema_context_hash: str,
        domain_hints: List[str],
        extracted_rule_ids: List[str],
        confidence_score: float,
        extraction_notes: str,
        processing_time_ms: Optional[float] = None,
        llm_model_used: Optional[str] = None
    ) -> bool:
        """Log rule extraction results"""
        try:
            with self.get_session() as session:
                log_entry = RuleExtractionLogModel(
                    connection_id=uuid.UUID(connection_id),
                    schema_context_hash=schema_context_hash,
                    domain_hints=domain_hints,
                    extracted_rules_count=len(extracted_rule_ids),
                    confidence_score=confidence_score,
                    extraction_notes=extraction_notes,
                    processing_time_ms=processing_time_ms,
                    llm_model_used=llm_model_used,
                    extracted_rule_ids=extracted_rule_ids
                )
                
                session.add(log_entry)
                session.commit()
                
                logger.info(f"Logged rule extraction for connection {connection_id}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error logging rule extraction: {str(e)}")
            return False
    
    # Utility Methods
    
    async def delete_business_rules(self, connection_id: str) -> bool:
        """Delete all business rules for a connection"""
        try:
            with self.get_session() as session:
                session.query(BusinessRuleModel).filter(
                    BusinessRuleModel.connection_id == uuid.UUID(connection_id)
                ).delete()
                session.commit()
                
                logger.info(f"Deleted business rules for connection {connection_id}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error deleting business rules: {str(e)}")
            return False
    
    async def get_rule_statistics(self, connection_id: str) -> Dict[str, Any]:
        """Get statistics about business rules for a connection"""
        try:
            with self.get_session() as session:
                total_rules = session.query(BusinessRuleModel).filter(
                    BusinessRuleModel.connection_id == uuid.UUID(connection_id)
                ).count()
                
                category_counts = {}
                severity_counts = {}
                
                rules = session.query(BusinessRuleModel).filter(
                    BusinessRuleModel.connection_id == uuid.UUID(connection_id)
                ).all()
                
                for rule in rules:
                    category_counts[rule.category] = category_counts.get(rule.category, 0) + 1
                    severity_counts[rule.severity] = severity_counts.get(rule.severity, 0) + 1
                
                return {
                    "total_rules": total_rules,
                    "category_distribution": category_counts,
                    "severity_distribution": severity_counts,
                    "average_confidence": sum(rule.confidence_score for rule in rules) / len(rules) if rules else 0
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting rule statistics: {str(e)}")
            return {"total_rules": 0, "category_distribution": {}, "severity_distribution": {}, "average_confidence": 0}
