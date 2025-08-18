"""
Automated Enum Mapping Rule Generator

This service automatically:
1. Scans database schemas to find enum-like columns
2. Extracts distinct values from those columns  
3. Generates natural language mapping rules
4. Updates business rules templates automatically
5. Creates user-friendly synonyms for enum values

Senior Engineer Implementation: Production-ready with error handling,
logging, and integration with existing schema analysis infrastructure.
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.advanced_schema_analyzer import AdvancedSchemaAnalyzer
from app.agents.configurator.business_rules_persistence import BusinessRulesDatabase
from app.models.business_rules import BusinessRule, RuleCategory, RuleSeverity
import logging

logger = logging.getLogger(__name__)


@dataclass
class EnumColumn:
    """Represents a column with enum-like characteristics"""
    table_name: str
    column_name: str
    schema_name: str
    enum_values: List[str]
    distinct_count: int
    sample_values: List[str]
    business_context: str = ""
    confidence_score: float = 0.0


@dataclass
class EnumMappingRule:
    """Represents a generated enum mapping rule"""
    table_name: str
    column_name: str
    enum_value: str
    natural_language_terms: List[str]
    description: str
    confidence_score: float


class AutomatedEnumMappingGenerator:
    """
    Automated enum mapping rule generator with LLM intelligence
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,  # Low temperature for consistent analysis
            api_key=settings.OPENAI_API_KEY
        )
        self.schema_analyzer = AdvancedSchemaAnalyzer()
        self.rules_db = BusinessRulesDatabase()
        
        # Enum detection thresholds
        self.MAX_ENUM_DISTINCT_COUNT = 50  # Max distinct values to consider as enum
        self.MIN_ENUM_CONFIDENCE = 0.7     # Minimum confidence to generate rules
        
    async def scan_and_generate_enum_mappings(
        self, 
        connection_id: str,
        connection_details: Dict[str, Any],
        target_schema: str = "staging_dashboard",
        target_tables: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point: Scan database and generate enum mapping rules
        """
        
        logger.info(f"🔍 Starting automated enum mapping generation for connection {connection_id}")
        
        try:
            # Step 1: Discover enum columns
            enum_columns = await self._discover_enum_columns(
                connection_details, target_schema, target_tables
            )
            
            logger.info(f"📊 Found {len(enum_columns)} potential enum columns")
            
            # Step 2: Generate mapping rules for each enum column
            all_mapping_rules = []
            for enum_column in enum_columns:
                mapping_rules = await self._generate_mapping_rules_for_column(enum_column)
                all_mapping_rules.extend(mapping_rules)
            
            logger.info(f"📝 Generated {len(all_mapping_rules)} enum mapping rules")
            
            # Step 3: Create business rules template content
            template_content = await self._create_business_rules_template(all_mapping_rules)
            
            # Step 4: Store as business rules in database
            business_rules = await self._convert_to_business_rules(
                connection_id, all_mapping_rules
            )
            
            for rule in business_rules:
                await self.rules_db.store_business_rule(rule)
            
            # Step 5: Generate template file update
            template_file_update = await self._generate_template_file_update(all_mapping_rules)
            
            return {
                "success": True,
                "enum_columns_found": len(enum_columns),
                "mapping_rules_generated": len(all_mapping_rules),
                "business_rules_stored": len(business_rules),
                "template_content": template_content,
                "template_file_update": template_file_update,
                "enum_columns_details": [
                    {
                        "table": col.table_name,
                        "column": col.column_name,
                        "enum_count": len(col.enum_values),
                        "confidence": col.confidence_score
                    }
                    for col in enum_columns
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Error in automated enum mapping generation: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "enum_columns_found": 0,
                "mapping_rules_generated": 0
            }
    
    async def _discover_enum_columns(
        self,
        connection_details: Dict[str, Any],
        target_schema: str,
        target_tables: Optional[List[str]] = None
    ) -> List[EnumColumn]:
        """
        Discover columns that look like enums across the database
        """
        
        enum_columns = []
        
        try:
            # Get list of tables to analyze
            tables_to_scan = target_tables or await self._get_all_tables(
                connection_details, target_schema
            )
            
            logger.info(f"🔍 Scanning {len(tables_to_scan)} tables for enum columns")
            
            for table_name in tables_to_scan:
                table_enum_columns = await self._analyze_table_for_enums(
                    connection_details, target_schema, table_name
                )
                enum_columns.extend(table_enum_columns)
            
            return enum_columns
            
        except Exception as e:
            logger.error(f"Error discovering enum columns: {str(e)}")
            return []
    
    async def _get_all_tables(
        self, 
        connection_details: Dict[str, Any], 
        schema_name: str
    ) -> List[str]:
        """Get all table names in the specified schema"""
        
        try:
            # Build connection
            username = quote_plus(connection_details['username'])
            password = quote_plus(connection_details['password'])
            host = connection_details['host']
            port = connection_details['port']
            database = connection_details['database_name']
            
            connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
            engine = create_engine(connection_string, pool_timeout=30)
            
            with engine.connect() as conn:
                result = conn.execute(text(f"""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = '{schema_name}'
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """))
                
                return [row[0] for row in result]
                
        except Exception as e:
            logger.error(f"Error getting table list: {str(e)}")
            return []
    
    async def _analyze_table_for_enums(
        self,
        connection_details: Dict[str, Any],
        schema_name: str,
        table_name: str
    ) -> List[EnumColumn]:
        """
        Analyze a single table to find enum-like columns
        """
        
        enum_columns = []
        
        try:
            # Get all columns for this table
            columns = await self._get_table_columns(
                connection_details, schema_name, table_name
            )
            
            # Analyze each column for enum characteristics
            for column_name, column_type in columns:
                # Skip obviously non-enum columns
                if self._should_skip_column(column_name, column_type):
                    continue
                
                # Analyze column samples
                sample_analysis = await self.schema_analyzer._analyze_column_samples(
                    connection_details, table_name, column_name, schema_name
                )
                
                # Check if this looks like an enum
                if self._is_enum_candidate(sample_analysis, column_type):
                    # Get business context via LLM
                    business_context = await self._analyze_enum_business_context(
                        table_name, column_name, sample_analysis
                    )
                    
                    enum_column = EnumColumn(
                        table_name=table_name,
                        column_name=column_name,
                        schema_name=schema_name,
                        enum_values=sample_analysis.get("enum_values", []),
                        distinct_count=sample_analysis.get("distinct_count", 0),
                        sample_values=sample_analysis.get("sample_values", []),
                        business_context=business_context.get("business_context", ""),
                        confidence_score=business_context.get("confidence_score", 0.0)
                    )
                    
                    enum_columns.append(enum_column)
                    logger.info(f"✅ Found enum column: {table_name}.{column_name} ({len(enum_column.enum_values)} values)")
            
            return enum_columns
            
        except Exception as e:
            logger.error(f"Error analyzing table {table_name} for enums: {str(e)}")
            return []
    
    async def _get_table_columns(
        self,
        connection_details: Dict[str, Any],
        schema_name: str,
        table_name: str
    ) -> List[Tuple[str, str]]:
        """Get all columns for a table with their data types"""
        
        try:
            username = quote_plus(connection_details['username'])
            password = quote_plus(connection_details['password'])
            host = connection_details['host']
            port = connection_details['port']
            database = connection_details['database_name']
            
            connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
            engine = create_engine(connection_string, pool_timeout=30)
            
            with engine.connect() as conn:
                result = conn.execute(text(f"""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = '{schema_name}'
                    AND table_name = '{table_name}'
                    ORDER BY ordinal_position
                """))
                
                return [(row[0], row[1]) for row in result]
                
        except Exception as e:
            logger.error(f"Error getting columns for {table_name}: {str(e)}")
            return []
    
    def _should_skip_column(self, column_name: str, column_type: str) -> bool:
        """Determine if a column should be skipped for enum analysis"""
        
        # Skip ID columns
        if column_name.lower().endswith('_id') or column_name.lower() == 'id':
            return True
        
        # Skip timestamp/date columns
        if 'timestamp' in column_type.lower() or 'date' in column_type.lower():
            return True
        
        # Skip numeric types that are likely not enums
        if column_type.lower() in ['integer', 'bigint', 'decimal', 'numeric', 'real', 'double precision']:
            return True
        
        # Skip text fields that are likely not enums
        if column_name.lower() in ['name', 'description', 'notes', 'comment', 'address', 'email']:
            return True
        
        return False
    
    def _is_enum_candidate(self, sample_analysis: Dict[str, Any], column_type: str) -> bool:
        """Determine if a column is a good enum candidate"""
        
        distinct_count = sample_analysis.get("distinct_count", 0)
        enum_values = sample_analysis.get("enum_values", [])
        
        # Must have reasonable distinct count
        if distinct_count == 0 or distinct_count > self.MAX_ENUM_DISTINCT_COUNT:
            return False
        
        # Must have actual enum values
        if not enum_values or len(enum_values) < 2:
            return False
        
        # Check for enum-like patterns
        has_enum_pattern = any([
            # All caps with underscores (common enum pattern)
            all(val.isupper() and '_' in val for val in enum_values[:5] if isinstance(val, str)),
            # Status-like values
            any(word in str(val).lower() for val in enum_values[:3] 
                for word in ['active', 'inactive', 'pending', 'approved', 'rejected', 'success', 'failed']),
            # Level/stage-like values
            any(word in str(val).lower() for val in enum_values[:3]
                for word in ['level', 'stage', 'step', 'phase']),
            # Boolean-like values
            set(str(val).lower() for val in enum_values) <= {'true', 'false', 'yes', 'no', '1', '0'}
        ])
        
        return has_enum_pattern
    
    async def _analyze_enum_business_context(
        self,
        table_name: str,
        column_name: str,
        sample_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use LLM to analyze the business context of an enum column"""
        
        enum_values = sample_analysis.get("enum_values", [])
        
        prompt = f"""
        Analyze this database enum column and provide business context:
        
        TABLE: {table_name}
        COLUMN: {column_name}
        ENUM VALUES: {', '.join(enum_values[:10])}
        
        Based on the table name, column name, and enum values, determine:
        1. What business concept this column represents
        2. How users might refer to these values in natural language
        3. The confidence that this is a meaningful enum for query generation
        
        Respond in JSON format:
        {{
            "business_context": "Clear description of what this enum represents",
            "user_friendly_concept": "How users would describe this (e.g., 'customer status', 'loan stage')",
            "confidence_score": 0.85,
            "is_query_relevant": true
        }}
        """
        
        try:
            response = await self.llm.ainvoke(prompt)
            result = json.loads(response.content)
            return result
        except Exception as e:
            logger.error(f"LLM enum analysis error: {str(e)}")
            return {
                "business_context": f"Enum column: {column_name}",
                "user_friendly_concept": column_name.replace('_', ' '),
                "confidence_score": 0.5,
                "is_query_relevant": True
            }
    
    async def _generate_mapping_rules_for_column(
        self, 
        enum_column: EnumColumn
    ) -> List[EnumMappingRule]:
        """Generate natural language mapping rules for an enum column"""
        
        mapping_rules = []
        
        try:
            # Use LLM to generate natural language mappings for each enum value
            for enum_value in enum_column.enum_values:
                natural_language_terms = await self._generate_natural_language_terms(
                    enum_column, enum_value
                )
                
                rule = EnumMappingRule(
                    table_name=enum_column.table_name,
                    column_name=enum_column.column_name,
                    enum_value=enum_value,
                    natural_language_terms=natural_language_terms,
                    description=f"Maps natural language terms to {enum_value} in {enum_column.table_name}.{enum_column.column_name}",
                    confidence_score=enum_column.confidence_score
                )
                
                mapping_rules.append(rule)
            
            return mapping_rules
            
        except Exception as e:
            logger.error(f"Error generating mapping rules for {enum_column.table_name}.{enum_column.column_name}: {str(e)}")
            return []
    
    async def _generate_natural_language_terms(
        self, 
        enum_column: EnumColumn, 
        enum_value: str
    ) -> List[str]:
        """Generate natural language terms that users might use for an enum value"""
        
        prompt = f"""
        Generate natural language terms that users might use to refer to this database enum value:
        
        TABLE: {enum_column.table_name}
        COLUMN: {enum_column.column_name}
        ENUM VALUE: "{enum_value}"
        BUSINESS CONTEXT: {enum_column.business_context}
        
        Generate 3-7 natural language terms that users might say when they want to query for this enum value.
        Include variations, synonyms, and common abbreviations.
        
        Examples:
        - For "BANK_ACCOUNT_DETAILS" → ["bank account details", "account details", "banking details", "account setup"]
        - For "DISBURSEMENT" → ["disbursement", "disburse", "loan disbursement", "fund release"]
        - For "EKYC" → ["kyc", "ekyc", "know your customer", "customer verification"]
        
        Respond with a JSON array of strings:
        ["term1", "term2", "term3", ...]
        """
        
        try:
            response = await self.llm.ainvoke(prompt)
            terms = json.loads(response.content)
            
            # Add the original enum value in lowercase as a fallback
            if enum_value.lower() not in [term.lower() for term in terms]:
                terms.append(enum_value.lower().replace('_', ' '))
            
            return terms
            
        except Exception as e:
            logger.error(f"Error generating natural language terms for {enum_value}: {str(e)}")
            # Fallback: basic transformation
            return [
                enum_value.lower().replace('_', ' '),
                enum_value.lower(),
                enum_value.replace('_', ' ')
            ]
    
    async def _create_business_rules_template(
        self, 
        mapping_rules: List[EnumMappingRule]
    ) -> str:
        """Create business rules template content from mapping rules"""
        
        # Group rules by table and column
        grouped_rules = {}
        for rule in mapping_rules:
            table_col = f"{rule.table_name}.{rule.column_name}"
            if table_col not in grouped_rules:
                grouped_rules[table_col] = []
            grouped_rules[table_col].append(rule)
        
        template_content = []
        template_content.append("## AUTOMATED ENUM MAPPING RULES")
        template_content.append("# Generated automatically by AutomatedEnumMappingGenerator")
        template_content.append(f"# Generated at: {datetime.now().isoformat()}")
        template_content.append("")
        
        for table_col, rules in grouped_rules.items():
            table_name, column_name = table_col.split('.', 1)
            
            template_content.append(f"### 🔤 {table_name.title()} {column_name.title()} Enum Mappings")
            template_content.append(f"**Table**: `{table_name}`")
            template_content.append(f"**Column**: `{column_name}`")
            template_content.append("")
            
            template_content.append("#### ✅ EXACT Enum Values (Case Sensitive):")
            for rule in rules:
                template_content.append(f"- `{rule.enum_value}` - {rule.description}")
            template_content.append("")
            
            template_content.append("#### 🔄 Natural Language to Enum Mapping Rules:")
            template_content.append("```sql")
            for rule in rules:
                terms_str = '" or "'.join(rule.natural_language_terms)
                template_content.append(f"-- User says: \"{terms_str}\"")
                template_content.append(f"-- SQL should use: WHERE {column_name} = '{rule.enum_value}'")
                template_content.append("")
            template_content.append("```")
            template_content.append("")
        
        return "\n".join(template_content)
    
    async def _convert_to_business_rules(
        self, 
        connection_id: str, 
        mapping_rules: List[EnumMappingRule]
    ) -> List[BusinessRule]:
        """Convert mapping rules to BusinessRule objects for database storage"""
        
        business_rules = []
        
        for rule in mapping_rules:
            # Create SQL transformation rule
            sql_transformations = [{
                "pattern": f"natural_language_terms",
                "replacement": f"WHERE {rule.column_name} = '{rule.enum_value}'",
                "natural_language_terms": rule.natural_language_terms,
                "enum_value": rule.enum_value
            }]
            
            business_rule = BusinessRule(
                connection_id=connection_id,
                category=RuleCategory.VALIDATION,
                severity=RuleSeverity.WARNING,
                title=f"Enum Mapping: {rule.table_name}.{rule.column_name} = {rule.enum_value}",
                description=rule.description,
                trigger_patterns=rule.natural_language_terms,
                table_patterns=[rule.table_name],
                column_patterns=[rule.column_name],
                sql_transformations=sql_transformations,
                confidence_score=rule.confidence_score,
                positive_examples=[
                    f"SELECT * FROM {rule.table_name} WHERE {rule.column_name} = '{rule.enum_value}'"
                ],
                negative_examples=[
                    f"SELECT * FROM {rule.table_name} WHERE {rule.column_name} = '{rule.enum_value.lower()}'"
                ]
            )
            
            business_rules.append(business_rule)
        
        return business_rules
    
    async def _generate_template_file_update(
        self, 
        mapping_rules: List[EnumMappingRule]
    ) -> str:
        """Generate the exact text to append to the business rules template file"""
        
        template_content = await self._create_business_rules_template(mapping_rules)
        
        return f"""

{template_content}

### 🚨 CRITICAL Automated Enum Validation Rules:
1. **Case Sensitivity**: All enum values MUST match exactly as stored in database
2. **Exact Match**: Never use LIKE or partial matching for enum values  
3. **Multi-Match Logic**: When user term could map to multiple enums, use OR conditions
4. **Fuzzy Matching**: Apply intelligent mapping for common variations and synonyms
5. **Validation**: Always validate enum exists before using in WHERE clause
6. **Auto-Generated**: These rules were generated automatically - verify before production use

### 📝 Example Auto-Generated Corrected Queries:
```sql
-- ❌ WRONG: User input taken literally
SELECT COUNT(*) FROM staging_dashboard.customer_life_cycle_fed 
WHERE level = 'bank account details';

-- ✅ CORRECT: Apply automated enum mapping
SELECT COUNT(*) FROM staging_dashboard.customer_life_cycle_fed 
WHERE level = 'BANK_ACCOUNT_DETAILS';
```
"""


# Convenience function for easy integration
async def generate_enum_mappings_for_connection(
    connection_id: str,
    connection_details: Dict[str, Any],
    target_schema: str = "staging_dashboard",
    target_tables: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Convenience function to generate enum mappings for a database connection
    """
    
    generator = AutomatedEnumMappingGenerator()
    return await generator.scan_and_generate_enum_mappings(
        connection_id, connection_details, target_schema, target_tables
    )
