"""
Query generator for creating test queries and validating database understanding.
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
import uuid
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from .models import DatabaseSchema, UserSchemaInput
from app.models.business_rules import TestQuery
from .vector_storage import SchemaVectorStore

logger = logging.getLogger(__name__)


class QueryGenerator:
    """Generates test queries to validate database understanding."""
    
    def __init__(self, llm: ChatOpenAI, vector_store: SchemaVectorStore):
        self.llm = llm
        self.vector_store = vector_store
        
        self.query_generation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert SQL query generator. Your task is to create diverse test queries that demonstrate understanding of a database schema.

Given the database schema information, generate SQL queries that:
1. Test basic table access and column selection
2. Demonstrate understanding of relationships (JOINs)
3. Show knowledge of data types and constraints
4. Include aggregations and grouping where appropriate
5. Test edge cases and complex scenarios

For each query, provide:
- The SQL query
- A natural language description of what it does
- Expected result type (e.g., "single row", "multiple rows", "aggregated data")
- Confidence score (0.0-1.0) based on schema clarity

Generate queries of varying complexity levels:
- Simple: Basic SELECT statements
- Medium: JOINs and basic aggregations
- Complex: Subqueries, window functions, complex JOINs

Schema Context:
{schema_context}

User Context:
{user_context}

Generate {num_queries} diverse test queries in JSON format:
[
  {{
    "sql_query": "SELECT ...",
    "natural_language_question": "What are the...",
    "expected_result_type": "multiple rows",
    "confidence_score": 0.85,
    "complexity_level": "medium",
    "tests_concept": "foreign key relationships"
  }}
]"""),
            ("human", "Generate {num_queries} test queries for this database schema.")
        ])
    
    async def generate_test_queries(
        self, 
        connection_id: str, 
        schema: DatabaseSchema, 
        user_input: Optional[UserSchemaInput] = None,
        num_queries: int = 10
    ) -> List[TestQuery]:
        """Generate test queries for the database schema."""
        try:
            # Get schema context from vector store
            schema_context = await self.vector_store.get_all_schema_context(connection_id)
            
            # Prepare user context
            user_context = ""
            if user_input:
                if user_input.business_rules:
                    user_context += f"Business Rules:\n" + "\n".join([f"- {rule}" for rule in user_input.business_rules])
                if user_input.additional_context:
                    user_context += f"\n\nAdditional Context:\n{user_input.additional_context}"
            
            # Generate queries using LLM
            response = await self.llm.ainvoke(
                self.query_generation_prompt.format(
                    schema_context=schema_context,
                    user_context=user_context,
                    num_queries=num_queries
                )
            )
            
            # Parse response
            logger.info(f"GPT response content: {response.content[:500]}...")
            
            if not response.content or response.content.strip() == "":
                logger.error("GPT returned empty response")
                return []
                
            try:
                queries_data = json.loads(response.content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse GPT response as JSON: {e}")
                logger.error(f"Raw response: {response.content}")
                
                # Try to extract JSON from response if it's wrapped in text
                import re
                json_match = re.search(r'\[.*\]', response.content, re.DOTALL)
                if json_match:
                    try:
                        queries_data = json.loads(json_match.group())
                        logger.info("Successfully extracted JSON from wrapped response")
                    except json.JSONDecodeError:
                        logger.error("Could not extract valid JSON from response")
                        return []
                else:
                    logger.error("No JSON array found in response")
                    return []
            
            # Convert to TestQuery objects
            test_queries = []
            for i, query_data in enumerate(queries_data):
                test_query = TestQuery(
                    query_id=str(uuid.uuid4()),  # Generate unique UUID for each query
                    connection_id=connection_id,
                    sql_query=query_data.get('sql_query', ''),
                    description=query_data.get('natural_language_question', ''),
                    expected_result_type=query_data.get('expected_result_type', 'rows'),
                    confidence_score=float(query_data.get('confidence_score', 0.5)),
                    business_context=query_data.get('business_context', '')
                )
                test_queries.append(test_query)
            
            logger.info(f"Generated {len(test_queries)} test queries for connection {connection_id}")
            return test_queries
            
        except Exception as e:
            logger.error(f"Error generating test queries: {str(e)}")
            return []
    
    async def validate_query_results(
        self, 
        connection_id: str, 
        test_query: TestQuery, 
        actual_results: Any
    ) -> Tuple[bool, str]:
        """Validate if query results match expectations."""
        try:
            validation_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a database query validator. Analyze if the actual query results match the expected result type and make sense given the query.

Query: {sql_query}
Natural Language Question: {natural_language_question}
Expected Result Type: {expected_result_type}
Actual Results: {actual_results}

Provide validation in JSON format:
{{
  "is_valid": true/false,
  "validation_notes": "Explanation of validation result",
  "suggestions": "Any suggestions for improvement"
}}"""),
                ("human", "Validate this query result.")
            ])
            
            response = await self.llm.ainvoke(
                validation_prompt.format(
                    sql_query=test_query.sql_query,
                    natural_language_question=test_query.natural_language_question,
                    expected_result_type=test_query.expected_result_type,
                    actual_results=str(actual_results)[:1000]  # Limit result size
                )
            )
            
            validation_data = json.loads(response.content)
            
            return (
                validation_data.get('is_valid', False),
                validation_data.get('validation_notes', 'No validation notes provided')
            )
            
        except Exception as e:
            logger.error(f"Error validating query results: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    async def generate_confidence_report(
        self, 
        connection_id: str, 
        test_queries: List[TestQuery]
    ) -> Dict[str, Any]:
        """Generate a confidence report based on test queries."""
        try:
            total_queries = len(test_queries)
            if total_queries == 0:
                return {"overall_confidence": 0.0, "report": "No test queries generated"}
            
            # Calculate metrics
            avg_confidence = sum(q.confidence_score for q in test_queries) / total_queries
            validated_queries = [q for q in test_queries if q.validated is True]
            validation_rate = len(validated_queries) / total_queries if total_queries > 0 else 0
            
            # Categorize by complexity
            complexity_breakdown = {}
            for query in test_queries:
                # Determine complexity based on query content
                complexity = self._determine_query_complexity(query.sql_query)
                if complexity not in complexity_breakdown:
                    complexity_breakdown[complexity] = 0
                complexity_breakdown[complexity] += 1
            
            # Generate detailed report
            report_prompt = ChatPromptTemplate.from_messages([
                ("system", """Generate a comprehensive confidence report for database schema understanding based on test queries.

Metrics:
- Total Queries: {total_queries}
- Average Confidence: {avg_confidence:.2f}
- Validation Rate: {validation_rate:.2f}
- Complexity Breakdown: {complexity_breakdown}

Test Queries Summary:
{queries_summary}

Provide a detailed report in JSON format:
{{
  "overall_confidence": 0.85,
  "readiness_assessment": "production_ready/needs_improvement/not_ready",
  "strengths": ["List of strengths"],
  "weaknesses": ["List of weaknesses"],
  "recommendations": ["List of recommendations"],
  "risk_factors": ["List of potential risks"],
  "coverage_analysis": {{
    "tables_covered": 8,
    "relationships_tested": 5,
    "data_types_validated": 12
  }}
}}"""),
                ("human", "Generate confidence report for this database configuration.")
            ])
            
            queries_summary = "\n".join([
                f"- {q.natural_language_question} (Confidence: {q.confidence_score:.2f})"
                for q in test_queries[:10]  # Limit to first 10 for summary
            ])
            
            response = await self.llm.ainvoke(
                report_prompt.format(
                    total_queries=total_queries,
                    avg_confidence=avg_confidence,
                    validation_rate=validation_rate,
                    complexity_breakdown=complexity_breakdown,
                    queries_summary=queries_summary
                )
            )
            
            report_data = json.loads(response.content)
            
            # Add calculated metrics
            report_data.update({
                "metrics": {
                    "total_queries": total_queries,
                    "average_confidence": avg_confidence,
                    "validation_rate": validation_rate,
                    "complexity_breakdown": complexity_breakdown
                },
                "generated_at": datetime.now().isoformat()
            })
            
            return report_data
            
        except Exception as e:
            logger.error(f"Error generating confidence report: {str(e)}")
            return {
                "overall_confidence": 0.0,
                "readiness_assessment": "error",
                "error": str(e)
            }
    
    def _determine_query_complexity(self, sql_query: str) -> str:
        """Determine query complexity based on SQL content."""
        sql_lower = sql_query.lower()
        
        # Count complexity indicators
        complexity_score = 0
        
        if 'join' in sql_lower:
            complexity_score += 2
        if 'subquery' in sql_lower or '(' in sql_query:
            complexity_score += 3
        if any(func in sql_lower for func in ['group by', 'having', 'order by']):
            complexity_score += 1
        if any(func in sql_lower for func in ['window', 'over', 'partition']):
            complexity_score += 4
        if any(func in sql_lower for func in ['union', 'intersect', 'except']):
            complexity_score += 3
        
        if complexity_score >= 6:
            return "complex"
        elif complexity_score >= 2:
            return "medium"
        else:
            return "simple"


class SchemaUnderstandingValidator:
    """Validates the system's understanding of the database schema."""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
    
    async def validate_schema_understanding(
        self, 
        schema: DatabaseSchema, 
        user_input: UserSchemaInput,
        test_queries: List[TestQuery]
    ) -> Dict[str, Any]:
        """Validate overall schema understanding."""
        try:
            validation_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a database schema understanding validator. Analyze the extracted schema, user input, and generated test queries to assess how well the system understands the database.

Database Schema:
{schema_summary}

User Input:
{user_input_summary}

Generated Test Queries:
{queries_summary}

Provide a comprehensive validation in JSON format:
{{
  "understanding_score": 0.85,
  "schema_completeness": 0.90,
  "relationship_accuracy": 0.80,
  "query_relevance": 0.85,
  "missing_elements": ["List of potentially missing elements"],
  "validation_concerns": ["List of concerns"],
  "confidence_indicators": ["List of positive indicators"],
  "recommendations": ["List of recommendations for improvement"]
}}"""),
                ("human", "Validate the schema understanding.")
            ])
            
            # Prepare summaries
            schema_summary = f"""
Database: {schema.database_name}
Tables: {len(schema.tables)}
Relationships: {len(schema.relationships)}
Enums: {len(schema.enums)}
Custom Types: {len(schema.custom_types)}
"""
            
            user_input_summary = f"""
Business Rules: {len(user_input.business_rules or [])}
Column Descriptions: {len(user_input.column_descriptions or {})}
Table Descriptions: {len(user_input.table_descriptions or {})}
Additional Context: {'Yes' if user_input.additional_context else 'No'}
"""
            
            queries_summary = f"""
Total Queries: {len(test_queries)}
Average Confidence: {sum(q.confidence_score for q in test_queries) / len(test_queries) if test_queries else 0:.2f}
Query Types: {', '.join(set(q.expected_result_type for q in test_queries))}
"""
            
            response = await self.llm.ainvoke(
                validation_prompt.format(
                    schema_summary=schema_summary,
                    user_input_summary=user_input_summary,
                    queries_summary=queries_summary
                )
            )
            
            return json.loads(response.content)
            
        except Exception as e:
            logger.error(f"Error validating schema understanding: {str(e)}")
            return {
                "understanding_score": 0.0,
                "error": str(e)
            }
