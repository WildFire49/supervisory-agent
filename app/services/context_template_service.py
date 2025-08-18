"""
Context Template Service
Manages editable business rules and schema context templates per database connection
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from app.core.database import SessionLocal
from app.models.database.context_template_models import (
    ConnectionContextTemplateModel,
    QueryCorrectionLogModel,
    TemplateUsageLogModel
)

logger = logging.getLogger(__name__)


class ContextTemplateService:
    """Service for managing connection-specific context templates"""
    
    def __init__(self):
        self.templates_dir = Path("templates/connections")
        self.templates_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_default_template(
        self,
        connection_id: str,
        database_type: str,
        domain_hint: str = "generic"
    ) -> str:
        """Create a default context template for a new connection"""
        
        try:
            # Load base templates
            base_rules = self._load_base_business_rules()
            base_schema = self._load_base_schema_rules()
            
            # Generate domain-specific prompts
            domain_prompts = self._generate_domain_prompts(domain_hint, database_type)
            
            with SessionLocal() as session:
                # Create new template
                template = ConnectionContextTemplateModel(
                    connection_id=connection_id,
                    template_name=f"{domain_hint}_{database_type}_template",
                    business_rules_template=base_rules,
                    schema_context_template=base_schema,
                    domain_specific_prompts=domain_prompts,
                    table_relationships={},
                    common_patterns=[],
                    field_mappings={},
                    created_by="system"
                )
                
                session.add(template)
                session.commit()
                
                # Save to file system as well
                await self._save_template_to_file(template)
                
                logger.info(f"Created default template for connection {connection_id}")
                return str(template.id)
                
        except Exception as e:
            logger.error(f"Error creating default template: {str(e)}")
            raise
    
    async def get_template_for_connection(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get the active template for a connection"""
        
        try:
            with SessionLocal() as session:
                template = session.query(ConnectionContextTemplateModel).filter(
                    ConnectionContextTemplateModel.connection_id == connection_id,
                    ConnectionContextTemplateModel.is_active == True
                ).order_by(ConnectionContextTemplateModel.created_at.desc()).first()
                
                if not template:
                    return None
                
                return {
                    "template_id": str(template.id),
                    "connection_id": str(template.connection_id),
                    "template_name": template.template_name,
                    "business_rules": template.business_rules_template,
                    "schema_context": template.schema_context_template,
                    "domain_prompts": template.domain_specific_prompts,
                    "table_relationships": template.table_relationships,
                    "common_patterns": template.common_patterns,
                    "field_mappings": template.field_mappings,
                    "user_corrections": template.user_corrections,
                    "success_patterns": template.success_patterns,
                    "version": template.template_version,
                    "usage_count": template.usage_count,
                    "success_rate": template.success_rate
                }
                
        except Exception as e:
            logger.error(f"Error getting template for connection {connection_id}: {str(e)}")
            return None
    
    async def update_template(
        self,
        template_id: str,
        updates: Dict[str, Any],
        updated_by: str = "user"
    ) -> bool:
        """Update an existing template"""
        
        try:
            with SessionLocal() as session:
                template = session.query(ConnectionContextTemplateModel).filter(
                    ConnectionContextTemplateModel.id == template_id
                ).first()
                
                if not template:
                    logger.error(f"Template {template_id} not found")
                    return False
                
                # Update fields
                for key, value in updates.items():
                    if hasattr(template, key):
                        setattr(template, key, value)
                
                template.updated_by = updated_by
                template.updated_at = datetime.utcnow()
                
                # Increment version
                current_version = float(template.template_version)
                template.template_version = str(current_version + 0.1)
                
                session.commit()
                
                # Update file system
                await self._save_template_to_file(template)
                
                logger.info(f"Updated template {template_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating template {template_id}: {str(e)}")
            return False
    
    async def log_query_correction(
        self,
        connection_id: str,
        natural_language_question: str,
        generated_sql_original: str,
        execution_success_original: bool,
        error_message_original: str,
        user_feedback: str,
        correction_type: str,
        corrected_sql: str = None,
        additional_context: str = None,
        corrected_by: str = "user"
    ) -> str:
        """Log a user correction for a query"""
        
        try:
            with SessionLocal() as session:
                # Get template for this connection
                template = session.query(ConnectionContextTemplateModel).filter(
                    ConnectionContextTemplateModel.connection_id == connection_id,
                    ConnectionContextTemplateModel.is_active == True
                ).first()
                
                if not template:
                    logger.error(f"No active template found for connection {connection_id}")
                    return None
                
                # Create correction log
                correction = QueryCorrectionLogModel(
                    connection_id=connection_id,
                    template_id=template.id,
                    natural_language_question=natural_language_question,
                    generated_sql_original=generated_sql_original,
                    execution_success_original=execution_success_original,
                    error_message_original=error_message_original,
                    user_feedback=user_feedback,
                    corrected_sql=corrected_sql,
                    correction_type=correction_type,
                    additional_context=additional_context,
                    corrected_by=corrected_by
                )
                
                session.add(correction)
                session.commit()
                
                # Update template with user feedback
                await self._apply_correction_to_template(template.id, correction)
                
                logger.info(f"Logged query correction for connection {connection_id}")
                return str(correction.id)
                
        except Exception as e:
            logger.error(f"Error logging query correction: {str(e)}")
            return None
    
    async def get_enhanced_context_for_query(
        self,
        connection_id: str,
        natural_language_question: str,
        domain_hint: str = "generic"
    ) -> Dict[str, Any]:
        """Get enhanced context for query generation"""
        
        template = await self.get_template_for_connection(connection_id)
        if not template:
            logger.warning(f"No template found for connection {connection_id}")
            return {}
        
        # Analyze question to determine relevant context
        relevant_rules = self._extract_relevant_rules(
            natural_language_question, 
            template["business_rules"]
        )
        
        relevant_schema = self._extract_relevant_schema(
            natural_language_question,
            template["schema_context"]
        )
        
        # Get similar successful patterns
        similar_patterns = self._find_similar_patterns(
            natural_language_question,
            template["success_patterns"]
        )
        
        # Build enhanced context
        context = {
            "business_rules": relevant_rules,
            "schema_context": relevant_schema,
            "domain_prompts": template["domain_prompts"],
            "table_relationships": template["table_relationships"],
            "field_mappings": template["field_mappings"],
            "similar_patterns": similar_patterns,
            "user_corrections": template["user_corrections"][-5:],  # Last 5 corrections
            "query_intent": self._analyze_query_intent(natural_language_question, domain_hint)
        }
        
        return context
    
    def _load_base_business_rules(self) -> str:
        """Load base business rules template"""
        try:
            rules_path = Path("templates/rules.txt")
            if rules_path.exists():
                return rules_path.read_text()
            return "# No base business rules found"
        except Exception as e:
            logger.error(f"Error loading base business rules: {str(e)}")
            return "# Error loading business rules"
    
    def _load_base_schema_rules(self) -> str:
        """Load base schema rules template"""
        try:
            schema_path = Path("templates/schema-rules.txt")
            if schema_path.exists():
                return schema_path.read_text()
            return "# No base schema rules found"
        except Exception as e:
            logger.error(f"Error loading base schema rules: {str(e)}")
            return "# Error loading schema rules"
    
    def _generate_domain_prompts(self, domain_hint: str, database_type: str) -> str:
        """Generate domain-specific prompts"""
        
        prompts = {
            "financial": """
# Financial Domain Query Guidelines

## Key Principles:
1. Always distinguish between COLLECTION and DISBURSEMENT contexts
2. Use proper date filtering with DATE() functions for timestamp columns
3. Apply ROUND() with ::numeric casting for percentage calculations
4. Follow strict table selection rules based on query intent

## Collection Queries:
- Use loan_emi_mapping, collection_details, collection_user, employee, office_branches
- Never use *_fed tables for collection metrics
- Always use collection_due_date for date filtering

## Disbursement Queries:
- Use disbursement_details_fed, loan_life_cycle_fed, customer_life_cycle_fed
- Apply proper lifecycle stage mappings
- Use disbursed_date with DATE() casting

## Common Patterns:
- Top performers: GROUP BY + ORDER BY + LIMIT
- Monthly comparisons: DATE_TRUNC('month', date_column)
- Percentage calculations: ROUND((numerator/denominator * 100)::numeric, 2)
""",
            "generic": f"""
# Generic Database Query Guidelines

## Database Type: {database_type}

## Key Principles:
1. Always validate table and column names against schema
2. Use proper JOIN conditions based on foreign key relationships
3. Apply appropriate date/time filtering
4. Handle NULL values appropriately

## Query Patterns:
- Aggregations: Use proper GROUP BY clauses
- Filtering: Use indexed columns when possible
- Sorting: Consider performance implications of ORDER BY
"""
        }
        
        return prompts.get(domain_hint, prompts["generic"])
    
    def _extract_relevant_rules(self, question: str, business_rules: str) -> str:
        """Extract relevant business rules based on question content"""
        
        # Simple keyword-based extraction (can be enhanced with NLP)
        keywords = question.lower().split()
        
        relevant_sections = []
        current_section = []
        
        for line in business_rules.split('\n'):
            if line.startswith('#') and current_section:
                # Check if current section is relevant
                section_text = '\n'.join(current_section).lower()
                if any(keyword in section_text for keyword in keywords):
                    relevant_sections.extend(current_section)
                current_section = [line]
            else:
                current_section.append(line)
        
        # Check last section
        if current_section:
            section_text = '\n'.join(current_section).lower()
            if any(keyword in section_text for keyword in keywords):
                relevant_sections.extend(current_section)
        
        return '\n'.join(relevant_sections) if relevant_sections else business_rules[:1000]
    
    def _extract_relevant_schema(self, question: str, schema_context: str) -> str:
        """Extract relevant schema context based on question content"""
        
        # Extract table names mentioned in question or inferred
        keywords = question.lower().split()
        
        relevant_sections = []
        current_table_section = []
        
        for line in schema_context.split('\n'):
            if line.startswith('CREATE TABLE') and current_table_section:
                # Check if current table section is relevant
                section_text = '\n'.join(current_table_section).lower()
                if any(keyword in section_text for keyword in keywords):
                    relevant_sections.extend(current_table_section)
                current_table_section = [line]
            else:
                current_table_section.append(line)
        
        # Check last section
        if current_table_section:
            section_text = '\n'.join(current_table_section).lower()
            if any(keyword in section_text for keyword in keywords):
                relevant_sections.extend(current_table_section)
        
        return '\n'.join(relevant_sections) if relevant_sections else schema_context[:2000]
    
    def _find_similar_patterns(self, question: str, success_patterns: List[Dict]) -> List[Dict]:
        """Find similar successful query patterns"""
        
        # Simple similarity matching (can be enhanced with embeddings)
        question_words = set(question.lower().split())
        
        similar = []
        for pattern in success_patterns:
            pattern_words = set(pattern.get('question', '').lower().split())
            similarity = len(question_words & pattern_words) / len(question_words | pattern_words)
            
            if similarity > 0.3:  # 30% similarity threshold
                similar.append({
                    **pattern,
                    'similarity_score': similarity
                })
        
        return sorted(similar, key=lambda x: x['similarity_score'], reverse=True)[:3]
    
    def _analyze_query_intent(self, question: str, domain_hint: str) -> Dict[str, Any]:
        """Analyze query intent to provide better context"""
        
        intent = {
            "query_type": "unknown",
            "entities": [],
            "time_context": None,
            "aggregation_type": None,
            "domain_context": domain_hint
        }
        
        question_lower = question.lower()
        
        # Determine query type
        if any(word in question_lower for word in ['top', 'highest', 'maximum', 'best']):
            intent["query_type"] = "ranking"
        elif any(word in question_lower for word in ['total', 'sum', 'count', 'average']):
            intent["query_type"] = "aggregation"
        elif any(word in question_lower for word in ['compare', 'vs', 'versus', 'difference']):
            intent["query_type"] = "comparison"
        elif any(word in question_lower for word in ['list', 'show', 'display', 'get']):
            intent["query_type"] = "listing"
        
        # Extract time context
        if any(word in question_lower for word in ['today', 'this month', 'current month']):
            intent["time_context"] = "current_period"
        elif any(word in question_lower for word in ['yesterday', 'last month', 'previous']):
            intent["time_context"] = "previous_period"
        elif any(word in question_lower for word in ['year', 'annual', 'yearly']):
            intent["time_context"] = "yearly"
        
        # Extract entities (basic)
        entities = []
        if 'field officer' in question_lower or 'fo' in question_lower:
            entities.append('field_officer')
        if 'branch manager' in question_lower or 'bm' in question_lower:
            entities.append('branch_manager')
        if 'collection' in question_lower:
            entities.append('collection')
        if 'disbursement' in question_lower:
            entities.append('disbursement')
        
        intent["entities"] = entities
        
        return intent
    
    async def _apply_correction_to_template(self, template_id: str, correction: QueryCorrectionLogModel):
        """Apply user correction to template"""
        
        try:
            # Extract learnings from correction
            learning = {
                "correction_type": correction.correction_type,
                "user_feedback": correction.user_feedback,
                "question_pattern": correction.natural_language_question,
                "additional_context": correction.additional_context,
                "timestamp": correction.created_at.isoformat()
            }
            
            # Update template with new learning
            updates = {
                "user_corrections": learning  # This will be appended in the update logic
            }
            
            await self.update_template(template_id, updates, "system_learning")
            
        except Exception as e:
            logger.error(f"Error applying correction to template: {str(e)}")
    
    async def _save_template_to_file(self, template: ConnectionContextTemplateModel):
        """Save template to file system for backup/versioning"""
        
        try:
            file_path = self.templates_dir / f"{template.connection_id}_{template.template_version}.json"
            
            template_data = {
                "template_id": str(template.id),
                "connection_id": str(template.connection_id),
                "template_name": template.template_name,
                "version": template.template_version,
                "business_rules": template.business_rules_template,
                "schema_context": template.schema_context_template,
                "domain_prompts": template.domain_specific_prompts,
                "table_relationships": template.table_relationships,
                "common_patterns": template.common_patterns,
                "field_mappings": template.field_mappings,
                "user_corrections": template.user_corrections,
                "success_patterns": template.success_patterns,
                "created_at": template.created_at.isoformat(),
                "updated_at": template.updated_at.isoformat()
            }
            
            with open(file_path, 'w') as f:
                json.dump(template_data, f, indent=2)
                
            logger.info(f"Saved template to file: {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving template to file: {str(e)}")


# Global instance
context_template_service = ContextTemplateService()
