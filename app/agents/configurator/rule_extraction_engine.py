"""
Business Rules Extraction Engine
Uses LLM to automatically discover and extract domain-specific business rules from schema patterns
"""

import json
import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.models.business_rules import (
    BusinessRule, BusinessRuleTemplate, RuleCategory, RuleSeverity,
    RuleExtractionRequest, RuleExtractionResponse
)
from app.agents.configurator.vector_storage import SchemaVectorStore

logger = logging.getLogger(__name__)


class RuleExtractionEngine:
    """Engine for extracting business rules from database schemas using LLM"""
    
    def __init__(self, llm: ChatOpenAI, vector_store: SchemaVectorStore):
        self.llm = llm
        self.vector_store = vector_store
        
        # Rule extraction prompt template
        self.rule_extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert database analyst specializing in extracting business rules from database schemas.

Your task is to analyze the provided database schema and identify domain-specific business rules that should be enforced during query generation.

Focus on identifying these types of rules:

1. **TABLE_USAGE**: Which tables should/shouldn't be used together in specific contexts
2. **DATE_FILTERING**: Which date fields to use for filtering in different contexts
3. **JOIN_PATTERNS**: Required JOIN patterns between related tables
4. **DATA_PRECISION**: Precision requirements for calculations and data types
5. **VALIDATION**: Data validation rules and constraints
6. **LIFECYCLE**: Rules for lifecycle stage transitions and validations
7. **CONTEXT_SEPARATION**: Rules that separate different business contexts

Look for patterns like:
- Tables with similar purposes but different contexts (e.g., collection vs disbursement)
- Date fields that serve different purposes
- Required relationships between tables
- Naming conventions that indicate business logic
- Constraints and validation requirements

Return your analysis in JSON format with the following structure:
{{
  "extracted_rules": [
    {{
      "category": "table_usage|date_filtering|join_patterns|data_precision|validation|lifecycle|context_separation",
      "severity": "critical|warning|suggestion",
      "title": "Brief rule title",
      "description": "Detailed rule description",
      "trigger_patterns": ["keyword1", "keyword2"],
      "table_patterns": ["table_pattern1", "table_pattern2"],
      "column_patterns": ["column_pattern1", "column_pattern2"],
      "allowed_tables": ["table1", "table2"],
      "forbidden_tables": ["table3", "table4"],
      "required_joins": [
        {{"from_table": "table1", "to_table": "table2", "join_condition": "table1.id = table2.foreign_id"}}
      ],
      "date_field_mappings": {{"context1": "date_field1", "context2": "date_field2"}},
      "sql_transformations": [
        {{"type": "cast", "pattern": "ROUND(expression)", "replacement": "ROUND(expression::numeric, 2)"}}
      ],
      "positive_examples": ["Good SQL example"],
      "negative_examples": ["Bad SQL example"],
      "confidence_score": 0.9
    }}
  ],
  "domain_classification": "financial|healthcare|e-commerce|other",
  "confidence_score": 0.85,
  "extraction_notes": "Summary of extraction process and findings"
}}"""),
            ("human", """Analyze this database schema and extract business rules:

**Schema Context:**
{schema_context}

**Domain Hints:**
{domain_hints}

**Existing Rules (to avoid duplicates):**
{existing_rules}

**Table Relationships and Patterns:**
Look for:
- Tables with similar names but different suffixes (e.g., _fed, _details, _mapping)
- Date columns with different purposes
- Foreign key relationships
- Naming conventions that suggest business contexts
- Tables that seem to serve similar but distinct purposes

Please extract comprehensive business rules that would help generate better, more contextually appropriate SQL queries.""")
        ])
    
    async def extract_rules_from_schema(
        self, 
        connection_id: str,
        schema_context: Optional[str] = None,
        domain_hints: List[str] = None,
        existing_rules: List[BusinessRule] = None
    ) -> RuleExtractionResponse:
        """Extract business rules from database schema"""
        try:
            # Get schema context if not provided
            if not schema_context:
                schema_context = await self.vector_store.get_all_schema_context(connection_id)
            
            # Prepare existing rules summary
            existing_rules_summary = ""
            if existing_rules:
                existing_rules_summary = "\n".join([
                    f"- {rule.title}: {rule.description}" for rule in existing_rules
                ])
            
            # Prepare domain hints
            domain_hints_str = ", ".join(domain_hints or [])
            
            logger.info(f"Extracting business rules for connection {connection_id}")
            
            # Generate rules using LLM
            response = await self.llm.ainvoke(
                self.rule_extraction_prompt.format(
                    schema_context=schema_context[:10000],  # Limit context size
                    domain_hints=domain_hints_str,
                    existing_rules=existing_rules_summary
                )
            )
            
            # Parse response
            try:
                rules_data = json.loads(response.content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse rule extraction response: {e}")
                # Try to extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    rules_data = json.loads(json_match.group())
                else:
                    raise ValueError("Could not extract valid JSON from LLM response")
            
            # Convert to BusinessRule objects
            extracted_rules = []
            for rule_data in rules_data.get('extracted_rules', []):
                business_rule = BusinessRule(
                    connection_id=connection_id,
                    category=RuleCategory(rule_data.get('category', 'validation')),
                    severity=RuleSeverity(rule_data.get('severity', 'warning')),
                    title=rule_data.get('title', ''),
                    description=rule_data.get('description', ''),
                    trigger_patterns=rule_data.get('trigger_patterns', []),
                    table_patterns=rule_data.get('table_patterns', []),
                    column_patterns=rule_data.get('column_patterns', []),
                    allowed_tables=rule_data.get('allowed_tables', []),
                    forbidden_tables=rule_data.get('forbidden_tables', []),
                    required_joins=rule_data.get('required_joins', []),
                    date_field_mappings=rule_data.get('date_field_mappings', {}),
                    sql_transformations=rule_data.get('sql_transformations', []),
                    positive_examples=rule_data.get('positive_examples', []),
                    negative_examples=rule_data.get('negative_examples', []),
                    confidence_score=rule_data.get('confidence_score', 0.7)
                )
                extracted_rules.append(business_rule)
            
            # Create template suggestion if domain is identified
            suggested_template = None
            domain = rules_data.get('domain_classification', 'other')
            if domain != 'other' and extracted_rules:
                suggested_template = BusinessRuleTemplate(
                    name=f"{domain.title()} Domain Rules",
                    description=f"Business rules template for {domain} domain",
                    domain=domain,
                    default_rules=extracted_rules[:5]  # Top 5 rules as defaults
                )
            
            response_obj = RuleExtractionResponse(
                extracted_rules=extracted_rules,
                confidence_score=rules_data.get('confidence_score', 0.7),
                extraction_notes=rules_data.get('extraction_notes', ''),
                suggested_template=suggested_template
            )
            
            logger.info(f"Extracted {len(extracted_rules)} business rules with confidence {response_obj.confidence_score}")
            return response_obj
            
        except Exception as e:
            logger.error(f"Error extracting business rules: {str(e)}")
            return RuleExtractionResponse(
                extracted_rules=[],
                confidence_score=0.0,
                extraction_notes=f"Error during extraction: {str(e)}"
            )
    
    async def create_generic_domain_template(self, connection_id: str, domain_hint: str = "generic") -> BusinessRuleTemplate:
        """Create a generic template with common database patterns that work across domains"""
        
        # Create generic rules that apply to most database systems
        generic_rules = [
            BusinessRule(
                connection_id=connection_id,
                category=RuleCategory.DATA_PRECISION,
                severity=RuleSeverity.WARNING,
                title="Numeric Precision for Calculations",
                description="Cast numeric expressions to appropriate precision for calculations to avoid floating point errors",
                trigger_patterns=["round", "percentage", "decimal", "calculation", "sum", "avg"],
                sql_transformations=[{
                    "type": "numeric_cast",
                    "pattern": "ROUND(expression, digits)",
                    "replacement": "ROUND(expression::numeric, digits)"
                }],
                confidence_score=0.8
            ),
            
            BusinessRule(
                connection_id=connection_id,
                category=RuleCategory.DATE_FILTERING,
                severity=RuleSeverity.WARNING,
                title="Date Comparison Best Practices",
                description="Use DATE() function when comparing timestamp columns with date literals",
                trigger_patterns=["date", "current_date", "today", "yesterday"],
                sql_transformations=[{
                    "type": "date_cast",
                    "pattern": "timestamp_column = CURRENT_DATE",
                    "replacement": "DATE(timestamp_column) = CURRENT_DATE"
                }],
                confidence_score=0.7
            ),
            
            BusinessRule(
                connection_id=connection_id,
                category=RuleCategory.TABLE_USAGE,
                severity=RuleSeverity.SUGGESTION,
                title="Avoid SELECT * in Production Queries",
                description="Use explicit column names instead of SELECT * for better performance and maintainability",
                trigger_patterns=["select *", "select all"],
                sql_transformations=[{
                    "type": "column_explicit",
                    "pattern": "SELECT *",
                    "replacement": "SELECT column1, column2, column3"
                }],
                confidence_score=0.6
            ),
            
            BusinessRule(
                connection_id=connection_id,
                category=RuleCategory.JOIN_PATTERNS,
                severity=RuleSeverity.WARNING,
                title="Explicit JOIN Syntax",
                description="Use explicit JOIN syntax instead of comma-separated tables for better readability",
                trigger_patterns=["join", "inner join", "left join"],
                confidence_score=0.7
            ),
            
            BusinessRule(
                connection_id=connection_id,
                category=RuleCategory.VALIDATION,
                severity=RuleSeverity.SUGGESTION,
                title="NULL Handling in Aggregations",
                description="Consider NULL values when using aggregate functions like COUNT, SUM, AVG",
                trigger_patterns=["count", "sum", "avg", "null"],
                confidence_score=0.6
            )
        ]
        
        template = BusinessRuleTemplate(
            name=f"{domain_hint.title()} Domain Generic Rules",
            description=f"Generic database best practices and rules for {domain_hint} domain",
            domain=domain_hint,
            default_rules=generic_rules
        )
        
        return template
    
    def _calculate_schema_hash(self, schema_context: str) -> str:
        """Calculate hash of schema context for caching"""
        return hashlib.sha256(schema_context.encode()).hexdigest()
