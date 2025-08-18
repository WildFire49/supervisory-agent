"""
Rule-Enhanced Query Generator
Integrates business rules validation and enforcement into query generation
"""

import json
import logging
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.models.business_rules import TestQuery
from app.models.business_rules import (
    BusinessRule, RuleValidationResult, RuleCategory, RuleSeverity
)
from app.agents.configurator.vector_storage import SchemaVectorStore
from app.agents.configurator.business_rules_persistence import BusinessRulesDatabase

logger = logging.getLogger(__name__)


class RuleEnhancedQueryGenerator:
    """Query generator with integrated business rules validation and enforcement"""
    
    def __init__(self, llm: ChatOpenAI, vector_store: SchemaVectorStore, rules_db: BusinessRulesDatabase):
        self.llm = llm
        self.vector_store = vector_store
        self.rules_db = rules_db
        
        # Enhanced query generation prompt with business rules
        self.rule_aware_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert SQL query generator with deep knowledge of business rules and domain-specific constraints.

Your task is to generate intelligent test queries that:
1. Follow all business rules and domain constraints
2. Demonstrate understanding of the database schema
3. Show proper table relationships and joins
4. Use appropriate date filtering and data precision
5. Respect context-specific table usage rules

**CRITICAL BUSINESS RULES TO FOLLOW:**
{business_rules}

**SCHEMA CONTEXT:**
{schema_context}

**USER CONTEXT:**
{user_context}

Generate {num_queries} diverse SQL queries that showcase different aspects of the database while strictly following the business rules.

Return your response in JSON format:
[
  {{
    "sql_query": "SELECT statement with proper joins and filters",
    "natural_language_question": "What business question does this query answer?",
    "expected_result_type": "single_value|multiple_rows|aggregated_data",
    "confidence_score": 0.85,
    "applied_rules": ["rule_id1", "rule_id2"],
    "query_category": "basic_select|join_query|aggregation|analytical"
  }}
]

**IMPORTANT REQUIREMENTS:**
- Always use schema-qualified table names (schema.table_name)
- Follow date filtering rules for the appropriate context
- Apply required JOIN patterns when crossing business contexts
- Use proper data type casting for calculations
- Respect table usage restrictions for different business contexts
- Generate queries with varying complexity levels
- Include confidence scores based on rule compliance"""),
            ("human", """Generate test queries for this database connection.

**Query Requirements:**
- Number of queries: {num_queries}
- Query types: {query_types}
- Complexity level: {complexity_level}

**Business Context Hints:**
{context_hints}

Please generate queries that demonstrate proper understanding of the business rules and schema relationships.""")
        ])
        
        # Rule validation prompt
        self.rule_validation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a business rules validator for SQL queries.

Analyze the provided SQL query against the business rules and identify any violations, warnings, or suggestions.

**BUSINESS RULES:**
{business_rules}

**SQL QUERY TO VALIDATE:**
{sql_query}

**QUERY CONTEXT:**
{query_context}

Return your validation in JSON format:
{{
  "is_valid": true/false,
  "violated_rules": [
    {{
      "rule_id": "rule_id",
      "violation_type": "critical|warning|suggestion",
      "description": "What rule was violated and why",
      "suggestion": "How to fix the violation"
    }}
  ],
  "warnings": ["Warning message 1", "Warning message 2"],
  "suggestions": ["Suggestion 1", "Suggestion 2"],
  "corrected_sql": "Corrected SQL query if violations found",
  "compliance_score": 0.85
}}"""),
            ("human", "Validate this query against the business rules and provide feedback.")
        ])
    
    async def generate_rule_aware_queries(
        self,
        connection_id: str,
        num_queries: int = 3,
        query_types: List[str] = None,
        complexity_level: str = "medium",
        context_hints: List[str] = None
    ) -> List[TestQuery]:
        """Generate queries with business rules awareness"""
        try:
            # Get applicable business rules
            business_rules = await self.rules_db.get_business_rules(connection_id)
            
            # Get schema context
            schema_context = await self.vector_store.get_all_schema_context(connection_id)
            
            # Format business rules for prompt
            rules_text = self._format_rules_for_prompt(business_rules)
            
            # Prepare context
            query_types_str = ", ".join(query_types or ["select", "join", "aggregate"])
            context_hints_str = ", ".join(context_hints or [])
            
            logger.info(f"Generating {num_queries} rule-aware queries with {len(business_rules)} business rules")
            
            # Generate queries using enhanced prompt
            response = await self.llm.ainvoke(
                self.rule_aware_prompt.format(
                    business_rules=rules_text,
                    schema_context=schema_context[:8000],  # Limit context size
                    user_context="",
                    num_queries=num_queries,
                    query_types=query_types_str,
                    complexity_level=complexity_level,
                    context_hints=context_hints_str
                )
            )
            
            # Parse response
            queries_data = self._parse_llm_response(response.content)
            
            # Convert to TestQuery objects and validate
            test_queries = []
            for i, query_data in enumerate(queries_data):
                # Create test query
                test_query = TestQuery(
                    query_id=f"rule_aware_{connection_id}_{i}_{int(datetime.now().timestamp())}",
                    connection_id=connection_id,
                    sql_query=query_data.get('sql_query', ''),
                    description=query_data.get('natural_language_question', ''),
                    expected_result_type=query_data.get('expected_result_type', 'unknown'),
                    confidence_score=float(query_data.get('confidence_score', 0.7)),
                    created_at=datetime.now()
                )
                
                # Validate against business rules
                validation_result = await self.validate_query_against_rules(
                    connection_id, test_query.sql_query, business_rules
                )
                
                # Adjust confidence based on rule compliance
                if validation_result.is_valid:
                    test_query.confidence_score = min(test_query.confidence_score * 1.1, 1.0)
                else:
                    test_query.confidence_score = max(test_query.confidence_score * 0.8, 0.3)
                    # Use corrected SQL if available
                    if validation_result.corrected_sql:
                        test_query.sql_query = validation_result.corrected_sql
                
                test_queries.append(test_query)
                
                # Log validation result
                await self.rules_db.log_rule_validation(
                    connection_id, test_query.query_id, validation_result, 
                    query_data.get('sql_query', '')
                )
            
            logger.info(f"Generated {len(test_queries)} rule-aware test queries")
            return test_queries
            
        except Exception as e:
            logger.error(f"Error generating rule-aware queries: {str(e)}")
            return []
    
    async def convert_natural_language_to_sql(
        self,
        connection_id: str,
        natural_language_question: str,
        domain_hint: str = "generic"
    ) -> Optional[TestQuery]:
        """Convert natural language question to SQL query using enhanced context templates"""
        try:
            # Import context template service
            from app.services.context_template_service import context_template_service
            
            # Get enhanced context from template system
            logger.info(f"Getting enhanced context for connection: {connection_id}")
            enhanced_context = await context_template_service.get_enhanced_context_for_query(
                connection_id=connection_id,
                natural_language_question=natural_language_question,
                domain_hint=domain_hint
            )
            
            if not enhanced_context:
                logger.warning(f"No enhanced context found for connection {connection_id}, falling back to basic method")
                return await self._fallback_query_generation(connection_id, natural_language_question, domain_hint)
            
            logger.info(f"Enhanced context retrieved successfully. Keys: {list(enhanced_context.keys())}")
            
            # Log context sizes for debugging
            for key, value in enhanced_context.items():
                if isinstance(value, str):
                    logger.debug(f"Context {key}: {len(value)} characters")
                elif isinstance(value, (list, dict)):
                    logger.debug(f"Context {key}: {len(value)} items")
            
            # Load enhanced prompt template
            prompt_template_str = self._load_enhanced_prompt_template()
            
            # Format the enhanced prompt with context
            formatted_prompt = prompt_template_str.format(
                schema_context=enhanced_context.get('schema_context', ''),
                business_rules=enhanced_context.get('business_rules', ''),
                domain_prompts=enhanced_context.get('domain_prompts', ''),
                table_relationships=self._format_relationships(enhanced_context.get('table_relationships', {})),
                field_mappings=self._format_field_mappings(enhanced_context.get('field_mappings', {})),
                similar_patterns=self._format_similar_patterns(enhanced_context.get('similar_patterns', [])),
                user_corrections=self._format_user_corrections(enhanced_context.get('user_corrections', [])),
                query_type=enhanced_context.get('query_intent', {}).get('query_type', 'unknown'),
                entities=', '.join(enhanced_context.get('query_intent', {}).get('entities', [])),
                time_context=enhanced_context.get('query_intent', {}).get('time_context', 'current'),
                domain_context=enhanced_context.get('query_intent', {}).get('domain_context', domain_hint),
                natural_language_question=natural_language_question,
                domain_hint=domain_hint,
                correction_patterns=self._format_correction_patterns(enhanced_context.get('user_corrections', []))
            )
            
            logger.info(f"Enhanced prompt formatted successfully. Length: {len(formatted_prompt)}")
            logger.debug(f"Enhanced context keys: {list(enhanced_context.keys())}")
            
            # Generate SQL using LLM
            response = await self.llm.ainvoke(formatted_prompt)
            sql_query = response.content.strip()
            
            # Clean up the SQL (remove markdown formatting if present)
            if sql_query.startswith('```sql'):
                sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
            elif sql_query.startswith('```'):
                sql_query = sql_query.replace('```', '').strip()
            
            # Create TestQuery object
            test_query = TestQuery(
                query_id=f"nl_query_{connection_id}_{int(datetime.now().timestamp())}",
                connection_id=connection_id,
                sql_query=sql_query,
                description=f"Generated from: {natural_language_question}",
                expected_result_type="rows",
                business_context=domain_hint,
                confidence_score=0.8,
                created_at=datetime.now()
            )
            
            logger.info(f"Successfully converted natural language to SQL: {sql_query[:100]}...")
            return test_query
            
        except Exception as e:
            logger.error(f"Error converting natural language to SQL: {str(e)}")
            return None
    
    def _load_enhanced_prompt_template(self) -> str:
        """Load the enhanced prompt template"""
        try:
            from pathlib import Path
            template_path = Path("templates/enhanced_query_prompt.txt")
            if template_path.exists():
                return template_path.read_text()
            else:
                # Fallback to basic template
                return self._get_basic_prompt_template()
        except Exception as e:
            logger.error(f"Error loading enhanced prompt template: {str(e)}")
            return self._get_basic_prompt_template()
    
    def _get_basic_prompt_template(self) -> str:
        """Fallback basic prompt template"""
        return """
You are an expert SQL query generator. Convert the natural language question to accurate SQL.

Schema Context: {schema_context}
Business Rules: {business_rules}
Question: {natural_language_question}
Domain: {domain_hint}

Generate only the SQL query:
"""
    
    def _format_relationships(self, relationships: dict) -> str:
        """Format table relationships for prompt"""
        if not relationships:
            return "No specific relationships defined"
        
        formatted = []
        for table, rels in relationships.items():
            formatted.append(f"- {table}: {rels}")
        return "\n".join(formatted)
    
    def _format_field_mappings(self, mappings: dict) -> str:
        """Format field mappings for prompt"""
        if not mappings:
            return "No field mappings defined"
        
        formatted = []
        for field, mapping in mappings.items():
            formatted.append(f"- {field} → {mapping}")
        return "\n".join(formatted)
    
    def _format_similar_patterns(self, patterns: list) -> str:
        """Format similar successful patterns"""
        if not patterns:
            return "No similar patterns found"
        
        formatted = []
        for pattern in patterns[:3]:  # Top 3 patterns
            formatted.append(f"- Question: {pattern.get('question', 'N/A')}")
            formatted.append(f"  SQL: {pattern.get('sql', 'N/A')[:100]}...")
            formatted.append(f"  Success Rate: {pattern.get('similarity_score', 0):.2f}")
        return "\n".join(formatted)
    
    def _format_user_corrections(self, corrections: list) -> str:
        """Format user corrections for context"""
        if not corrections:
            return "No user corrections available"
        
        formatted = []
        for correction in corrections[-3:]:  # Last 3 corrections
            formatted.append(f"- Issue: {correction.get('correction_type', 'N/A')}")
            formatted.append(f"  Feedback: {correction.get('user_feedback', 'N/A')}")
            if correction.get('additional_context'):
                formatted.append(f"  Context: {correction.get('additional_context')}")
        return "\n".join(formatted)
    
    def _format_correction_patterns(self, corrections: list) -> str:
        """Format correction patterns for learning"""
        if not corrections:
            return "No correction patterns available"
        
        patterns = {}
        for correction in corrections:
            pattern_type = correction.get('correction_type', 'unknown')
            if pattern_type not in patterns:
                patterns[pattern_type] = []
            patterns[pattern_type].append(correction.get('user_feedback', ''))
        
        formatted = []
        for pattern_type, feedbacks in patterns.items():
            formatted.append(f"- {pattern_type.replace('_', ' ').title()}: {'; '.join(feedbacks[:2])}")
        
        return "\n".join(formatted)
    
    async def _fallback_query_generation(self, connection_id: str, natural_language_question: str, domain_hint: str) -> Optional[TestQuery]:
        """Fallback to basic query generation when enhanced context is not available"""
        try:
            # Get basic schema context from vector store
            schema_results = await self.vector_store.search_schema_information(
                connection_id=connection_id,
                query=natural_language_question,
                limit=5
            )
            
            if not schema_results:
                logger.error(f"No schema context found for connection {connection_id}")
                return None
            
            # Basic prompt
            basic_prompt = f"""
Convert this natural language question to SQL using the provided schema:

Schema Context:
{schema_results[0].get('content', '') if schema_results else 'No schema available'}

Question: {natural_language_question}
Domain: {domain_hint}

Generate only the SQL query:
"""
            
            # Generate SQL
            response = await self.llm.ainvoke(basic_prompt)
            sql_query = response.content.strip()
            
            # Clean up SQL
            if sql_query.startswith('```sql'):
                sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
            elif sql_query.startswith('```'):
                sql_query = sql_query.replace('```', '').strip()
            
            # Create TestQuery
            test_query = TestQuery(
                query_id=f"fallback_query_{connection_id}_{int(datetime.now().timestamp())}",
                connection_id=connection_id,
                sql_query=sql_query,
                description=f"Fallback generation from: {natural_language_question}",
                expected_result_type="rows",
                confidence_score=0.6,  # Lower confidence for fallback
                business_context=domain_hint
            )
            
            return test_query
            
        except Exception as e:
            logger.error(f"Error in fallback query generation: {str(e)}")
            return None
    
    async def validate_query_against_rules(
        self,
        connection_id: str,
        sql_query: str,
        business_rules: List[BusinessRule] = None
    ) -> RuleValidationResult:
        """Validate a SQL query against business rules"""
        try:
            # Get business rules if not provided
            if business_rules is None:
                business_rules = await self.rules_db.get_business_rules(connection_id)
            
            # Get applicable rules based on query content
            applicable_rules = self._get_applicable_rules(sql_query, business_rules)
            
            if not applicable_rules:
                return RuleValidationResult(is_valid=True)
            
            # Format rules for validation prompt
            rules_text = self._format_rules_for_prompt(applicable_rules)
            
            # Validate using LLM
            response = await self.llm.ainvoke(
                self.rule_validation_prompt.format(
                    business_rules=rules_text,
                    sql_query=sql_query,
                    query_context=self._extract_query_context(sql_query)
                )
            )
            
            # Parse validation response
            validation_data = self._parse_llm_response(response.content)
            
            # Create validation result
            violated_rules = []
            for violation in validation_data.get('violated_rules', []):
                rule_id = violation.get('rule_id')
                rule = next((r for r in applicable_rules if r.rule_id == rule_id), None)
                if rule:
                    violated_rules.append(rule)
            
            result = RuleValidationResult(
                is_valid=validation_data.get('is_valid', True),
                violated_rules=violated_rules,
                warnings=validation_data.get('warnings', []),
                suggestions=validation_data.get('suggestions', []),
                corrected_sql=validation_data.get('corrected_sql')
            )
            
            logger.info(f"Query validation completed: valid={result.is_valid}, violations={len(result.violated_rules)}")
            return result
            
        except Exception as e:
            logger.error(f"Error validating query against rules: {str(e)}")
            return RuleValidationResult(is_valid=True)  # Default to valid on error
    
    def _format_rules_for_prompt(self, business_rules: List[BusinessRule]) -> str:
        """Format business rules for LLM prompt"""
        if not business_rules:
            return "No specific business rules defined."
        
        rules_text = []
        for rule in business_rules:
            rule_text = f"""
**{rule.title}** ({rule.category.value.upper()} - {rule.severity.value.upper()})
Description: {rule.description}
Triggers: {', '.join(rule.trigger_patterns) if rule.trigger_patterns else 'N/A'}
"""
            
            if rule.allowed_tables:
                rule_text += f"Allowed Tables: {', '.join(rule.allowed_tables)}\n"
            
            if rule.forbidden_tables:
                rule_text += f"Forbidden Tables: {', '.join(rule.forbidden_tables)}\n"
            
            if rule.required_joins:
                joins = [f"{j.get('from_table')} -> {j.get('to_table')}" for j in rule.required_joins]
                rule_text += f"Required Joins: {', '.join(joins)}\n"
            
            if rule.date_field_mappings:
                mappings = [f"{k}: {v}" for k, v in rule.date_field_mappings.items()]
                rule_text += f"Date Field Mappings: {', '.join(mappings)}\n"
            
            if rule.sql_transformations:
                rule_text += f"SQL Transformations: {len(rule.sql_transformations)} defined\n"
            
            if rule.positive_examples:
                rule_text += f"Good Example: {rule.positive_examples[0]}\n"
            
            if rule.negative_examples:
                rule_text += f"Bad Example: {rule.negative_examples[0]}\n"
            
            rules_text.append(rule_text)
        
        return "\n".join(rules_text)
    
    def _get_applicable_rules(self, sql_query: str, business_rules: List[BusinessRule]) -> List[BusinessRule]:
        """Get business rules applicable to a specific SQL query"""
        applicable_rules = []
        sql_lower = sql_query.lower()
        
        for rule in business_rules:
            # Check trigger patterns
            if any(pattern.lower() in sql_lower for pattern in rule.trigger_patterns):
                applicable_rules.append(rule)
                continue
            
            # Check table patterns
            if any(pattern.lower() in sql_lower for pattern in rule.table_patterns):
                applicable_rules.append(rule)
                continue
            
            # Check for table names in allowed/forbidden lists
            if rule.allowed_tables and any(table.lower() in sql_lower for table in rule.allowed_tables):
                applicable_rules.append(rule)
                continue
            
            if rule.forbidden_tables and any(table.lower() in sql_lower for table in rule.forbidden_tables):
                applicable_rules.append(rule)
        
        return applicable_rules
    
    def _extract_query_context(self, sql_query: str) -> str:
        """Extract context keywords from SQL query"""
        # Extract table names
        table_pattern = r'\b(?:FROM|JOIN)\s+(\w+\.\w+|\w+)'
        tables = re.findall(table_pattern, sql_query, re.IGNORECASE)
        
        # Extract common business context keywords
        context_keywords = []
        business_terms = [
            'collection', 'disbursement', 'loan', 'customer', 'emi', 'due', 'overdue',
            'credit', 'kyc', 'verification', 'approval', 'lifecycle', 'stage'
        ]
        
        sql_lower = sql_query.lower()
        for term in business_terms:
            if term in sql_lower:
                context_keywords.append(term)
        
        return f"Tables: {', '.join(tables)}, Context: {', '.join(context_keywords)}"
    
    def _parse_llm_response(self, response_content: str) -> Any:
        """Parse LLM response with fallback for wrapped JSON"""
        try:
            return json.loads(response_content)
        except json.JSONDecodeError:
            # Try to extract JSON from wrapped response
            json_match = re.search(r'(\[.*\]|\{.*\})', response_content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            logger.error(f"Could not parse LLM response: {response_content[:200]}...")
            return [] if response_content.strip().startswith('[') else {}
    
    async def _get_business_context_for_connection(self, connection_id: str) -> dict:
        """Get business context and table selection rules for a connection"""
        try:
            # This would typically come from the stored schema analysis
            # For now, we'll use a simplified approach
            schema_results = await self.vector_store.search_schema_information(
                connection_id=connection_id,
                query="business context table selection rules",
                limit=1
            )
            
            # Return default rules if no specific context found
            return {
                'selection_rules': {
                    'disbursement_queries': {
                        'preferred_tables': ['fed_disbursement_details', 'disbursement_details'],
                        'avoid_tables': ['mifix1_disbursement_data', 'staging_disbursement']
                    },
                    'collection_queries': {
                        'preferred_tables': ['collection_details', 'fed_collection_details'],
                        'avoid_tables': ['staging_collection', 'old_collection_data']
                    },
                    'general_rules': {
                        'prioritize_current_over_legacy': True,
                        'avoid_staging_for_business_queries': True
                    }
                }
            }
        except Exception as e:
            logger.error(f"Error getting business context: {str(e)}")
            return {}
    
    def _analyze_query_intent(self, natural_language_question: str) -> dict:
        """Analyze the intent and context of a natural language query"""
        question_lower = natural_language_question.lower()
        
        # Determine query type
        query_type = 'unknown'
        if any(word in question_lower for word in ['how much', 'total', 'sum', 'amount']):
            query_type = 'aggregation'
        elif any(word in question_lower for word in ['list', 'show', 'get', 'find']):
            query_type = 'selection'
        elif any(word in question_lower for word in ['count', 'how many']):
            query_type = 'count'
        
        # Determine business function
        business_function = 'general'
        if any(word in question_lower for word in ['disburs', 'disburse', 'payout']):
            business_function = 'disbursement'
        elif any(word in question_lower for word in ['collect', 'payment', 'repay']):
            business_function = 'collection'
        elif any(word in question_lower for word in ['loan', 'credit']):
            business_function = 'loan'
        elif any(word in question_lower for word in ['customer', 'client']):
            business_function = 'customer'
        
        # Determine time context
        time_context = 'current'
        if any(word in question_lower for word in ['today', 'current', 'now']):
            time_context = 'today'
        elif any(word in question_lower for word in ['yesterday', 'last']):
            time_context = 'recent'
        elif any(word in question_lower for word in ['month', 'year']):
            time_context = 'period'
        
        return {
            'type': query_type,
            'function': business_function,
            'time_context': time_context,
            'keywords': [word for word in question_lower.split() if len(word) > 3]
        }
    
    def _select_optimal_tables(self, schema_results: list, query_intent: dict, selection_rules: dict) -> list:
        """Select optimal tables based on query intent and business rules"""
        # Extract table information from schema results
        table_candidates = []
        
        for result in schema_results:
            table_name = result['metadata'].get('table_name', '')
            schema_name = result['metadata'].get('schema_name', '')
            
            # Calculate table score based on multiple factors
            score = self._calculate_table_score(
                table_name, 
                schema_name, 
                query_intent, 
                selection_rules,
                result.get('score', 0.5)  # Vector similarity score
            )
            
            table_candidates.append({
                'table_name': table_name,
                'schema_name': schema_name,
                'full_name': f"{schema_name}.{table_name}" if schema_name else table_name,
                'content': result['content'],
                'score': score,
                'metadata': result['metadata']
            })
        
        # Sort by score (highest first) and return top candidates
        table_candidates.sort(key=lambda x: x['score'], reverse=True)
        return table_candidates
    
    def _calculate_table_score(self, table_name: str, schema_name: str, query_intent: dict, selection_rules: dict, similarity_score: float) -> float:
        """Calculate a comprehensive score for table selection"""
        score = similarity_score * 0.3  # Base similarity score (30%)
        
        table_lower = table_name.lower()
        business_function = query_intent.get('function', 'general')
        
        # Business function relevance (40%)
        function_rules = selection_rules.get(f'{business_function}_queries', {})
        preferred_tables = [t.lower() for t in function_rules.get('preferred_tables', [])]
        avoid_tables = [t.lower() for t in function_rules.get('avoid_tables', [])]
        
        if any(preferred in table_lower for preferred in preferred_tables):
            score += 0.4
        elif any(avoid in table_lower for avoid in avoid_tables):
            score -= 0.3
        
        # Table freshness indicators (20%)
        if any(indicator in table_lower for indicator in ['mifix', 'staging', 'backup', 'old']):
            score -= 0.2
        elif any(indicator in table_lower for indicator in ['details', 'current', 'active']):
            score += 0.2
        
        # Schema context (10%)
        if schema_name and 'staging' in schema_name.lower():
            score -= 0.1
        elif schema_name and any(prod in schema_name.lower() for prod in ['prod', 'main']):
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _format_enhanced_schema_context(self, selected_tables: list, query_intent: dict) -> str:
        """Format schema context with table priorities and selection reasoning"""
        context_parts = []
        
        for i, table in enumerate(selected_tables[:5]):  # Top 5 tables
            priority = "PRIMARY" if i == 0 else "SECONDARY" if i < 3 else "FALLBACK"
            
            context_parts.append(
                f"**{priority} TABLE** (Score: {table['score']:.2f})\n"
                f"Table: {table['full_name']}\n"
                f"{table['content']}\n"
                f"Selection Reason: {'High relevance to ' + query_intent.get('function', 'query') + ' queries' if i == 0 else 'Alternative option'}\n"
            )
        
        return "\n".join(context_parts)
    
    def _format_table_selection_guidance(self, selected_tables: list, query_intent: dict) -> str:
        """Format table selection guidance for the LLM"""
        if not selected_tables:
            return "No specific table guidance available."
        
        primary_table = selected_tables[0]
        guidance = [
            f"RECOMMENDED: Use '{primary_table['full_name']}' as the primary table (Score: {primary_table['score']:.2f})",
            f"QUERY TYPE: {query_intent.get('type', 'unknown').title()} query for {query_intent.get('function', 'general')} function"
        ]
        
        if len(selected_tables) > 1:
            alternatives = [t['full_name'] for t in selected_tables[1:3]]
            guidance.append(f"ALTERNATIVES: {', '.join(alternatives)} (if primary table insufficient)")
        
        # Add specific warnings about tables to avoid
        avoid_tables = [t['table_name'] for t in selected_tables if 'mifix' in t['table_name'].lower() or 'staging' in t['table_name'].lower()]
        if avoid_tables:
            guidance.append(f"AVOID: {', '.join(avoid_tables)} (legacy/staging data)")
        
        return "\n".join(guidance)
