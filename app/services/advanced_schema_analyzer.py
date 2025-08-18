"""
Advanced Schema Intelligence System
Senior Dev Implementation: LLM-powered column/table analysis with user editing
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import asyncio
import json
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class ColumnAnalysis:
    """Column-level analysis results"""
    column_name: str
    data_type: str
    is_nullable: bool
    
    # LLM-generated insights
    business_description: str = ""
    category: str = ""  # e.g., "identifier", "timestamp", "status", "amount"
    sample_values: List[str] = None
    distinct_count: Optional[int] = None
    enum_values: List[str] = None
    
    # Relationships
    foreign_key_target: Optional[str] = None
    referenced_by: List[str] = None
    
    # User editable fields
    user_notes: str = ""
    business_rules: str = ""
    usage_context: str = ""
    
    # Metadata
    analyzed_at: datetime = None
    confidence_score: float = 0.0

@dataclass
class TableAnalysis:
    """Table-level analysis results"""
    table_name: str
    schema_name: str
    row_count: Optional[int] = None
    
    # Enhanced LLM-generated insights
    business_description: str = ""
    primary_purpose: str = ""  # e.g., "customer lifecycle tracking", "transaction processing", "reference data"
    data_category: str = ""    # e.g., "operational", "analytical", "reference", "transactional"
    
    # Enhanced analysis fields
    key_columns: List[str] = None  # Most important columns and their business significance
    business_processes: List[str] = None  # Business processes this table supports
    data_quality_notes: List[str] = None  # Data quality or business rule considerations
    
    # Relationships
    parent_tables: List[str] = None
    child_tables: List[str] = None
    related_tables: List[str] = None
    
    # Usage patterns
    typical_queries: List[str] = None
    join_patterns: List[str] = None
    
    # User editable fields
    user_notes: str = ""
    business_rules: str = ""
    usage_context: str = ""
    
    # Metadata
    analyzed_at: datetime = None
    confidence_score: float = 0.0
    columns: List[ColumnAnalysis] = None

class AdvancedSchemaAnalyzer:
    """
    Senior Dev Implementation: Intelligent schema analysis with LLM insights
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",  # Cost-effective for analysis
            temperature=0.1,      # Low temperature for consistent analysis
            api_key=settings.OPENAI_API_KEY
        )
        
    async def analyze_table_on_demand(
        self, 
        connection_details: Dict[str, Any],
        table_name: str,
        schema_name: str = None
    ) -> TableAnalysis:
        """
        On-demand table analysis with LLM insights
        Triggered when user selects a table
        """
        
        logger.info(f"🔍 Analyzing table: {schema_name}.{table_name}")
        
        try:
            # Step 1: Get table metadata
            table_metadata = await self._get_table_metadata(
                connection_details, table_name, schema_name
            )
            
            # Step 2: Analyze relationships
            relationships = await self._analyze_table_relationships(
                connection_details, table_name, schema_name
            )
            
            # Step 3: LLM analysis for business context with column details
            llm_analysis = await self._llm_analyze_table(
                table_name, table_metadata, relationships, table_metadata.get("columns", [])
            )
            
            # Step 4: Create comprehensive analysis with enhanced fields
            analysis = TableAnalysis(
                table_name=table_name,
                schema_name=schema_name or "public",
                row_count=table_metadata.get("row_count"),
                business_description=llm_analysis.get("business_description", ""),
                primary_purpose=llm_analysis.get("primary_purpose", ""),
                data_category=llm_analysis.get("data_category", ""),
                key_columns=llm_analysis.get("key_columns", []),
                business_processes=llm_analysis.get("business_processes", []),
                data_quality_notes=llm_analysis.get("data_quality_notes", []),
                parent_tables=relationships.get("parent_tables", []),
                child_tables=relationships.get("child_tables", []),
                related_tables=relationships.get("related_tables", []),
                typical_queries=llm_analysis.get("typical_queries", []),
                join_patterns=llm_analysis.get("join_patterns", []),
                analyzed_at=datetime.utcnow(),
                confidence_score=llm_analysis.get("confidence_score", 0.8)
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing table {table_name}: {str(e)}")
            # Return basic analysis on error
            return TableAnalysis(
                table_name=table_name,
                schema_name=schema_name or "public",
                business_description=f"Error during analysis: {str(e)}",
                analyzed_at=datetime.utcnow(),
                confidence_score=0.0
            )
    
    async def analyze_column_on_demand(
        self,
        connection_details: Dict[str, Any],
        table_name: str,
        column_name: str,
        schema_name: str = None
    ) -> ColumnAnalysis:
        """
        On-demand column analysis with sample data and LLM insights
        Triggered when user selects a column
        """
        
        logger.info(f"🔍 Analyzing column: {schema_name}.{table_name}.{column_name}")
        
        try:
            # Step 1: Get column metadata
            column_metadata = await self._get_column_metadata(
                connection_details, table_name, column_name, schema_name
            )
            
            # Step 2: Sample data analysis
            sample_analysis = await self._analyze_column_samples(
                connection_details, table_name, column_name, schema_name
            )
            
            # Step 3: LLM analysis for business context
            llm_analysis = await self._llm_analyze_column(
                table_name, column_name, column_metadata, sample_analysis
            )
            
            # Step 4: Create comprehensive analysis
            analysis = ColumnAnalysis(
                column_name=column_name,
                data_type=column_metadata.get("data_type", "unknown"),
                is_nullable=column_metadata.get("is_nullable", True),
                business_description=llm_analysis.get("business_description", ""),
                category=llm_analysis.get("category", ""),
                sample_values=sample_analysis.get("sample_values", []),
                distinct_count=sample_analysis.get("distinct_count"),
                enum_values=sample_analysis.get("enum_values", []),
                foreign_key_target=column_metadata.get("foreign_key_target"),
                analyzed_at=datetime.utcnow(),
                confidence_score=llm_analysis.get("confidence_score", 0.8)
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing column {column_name}: {str(e)}")
            # Return basic analysis on error
            return ColumnAnalysis(
                column_name=column_name,
                data_type="unknown",
                is_nullable=True,
                business_description=f"Error during analysis: {str(e)}",
                analyzed_at=datetime.utcnow(),
                confidence_score=0.0
            )
    
    async def _get_table_metadata(
        self, 
        connection_details: Dict[str, Any], 
        table_name: str, 
        schema_name: str
    ) -> Dict[str, Any]:
        """Get basic table metadata"""
        
        try:
            from urllib.parse import quote_plus
            import sqlalchemy as sa
            from sqlalchemy import create_engine, text
            
            # Build connection
            username = quote_plus(connection_details['username'])
            password = quote_plus(connection_details['password'])
            host = connection_details['host']
            port = connection_details['port']
            database = connection_details['database_name']
            
            connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
            engine = create_engine(connection_string, pool_timeout=30)
            
            metadata = {}
            
            with engine.connect() as conn:
                # Get row count
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {schema_name}.{table_name}"))
                    metadata["row_count"] = result.scalar()
                except:
                    metadata["row_count"] = None
                
                # Get table size
                try:
                    result = conn.execute(text(f"""
                        SELECT pg_size_pretty(pg_total_relation_size('{schema_name}.{table_name}'))
                    """))
                    metadata["table_size"] = result.scalar()
                except:
                    metadata["table_size"] = None
                
                # Get column information for enhanced analysis
                try:
                    result = conn.execute(text("""
                        SELECT 
                            column_name,
                            data_type,
                            is_nullable,
                            column_default
                        FROM information_schema.columns 
                        WHERE table_schema = :schema_name 
                        AND table_name = :table_name
                        ORDER BY ordinal_position
                    """), {
                        "schema_name": schema_name or "public",
                        "table_name": table_name
                    })
                    
                    columns = []
                    for row in result:
                        columns.append({
                            "column_name": row[0],
                            "data_type": row[1],
                            "nullable": row[2] == "YES",
                            "default": row[3]
                        })
                    metadata["columns"] = columns
                except Exception as e:
                    logger.warning(f"Could not get column info for {table_name}: {str(e)}")
                    metadata["columns"] = []
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting table metadata: {str(e)}")
            return {}
    
    async def _get_column_metadata(
        self, 
        connection_details: Dict[str, Any], 
        table_name: str, 
        column_name: str,
        schema_name: str
    ) -> Dict[str, Any]:
        """Get basic column metadata including data type, nullable, foreign keys"""
        
        try:
            from sqlalchemy import create_engine, text
            
            # Create database connection - handle both 'database' and 'database_name' keys
            database = connection_details.get('database', connection_details.get('database_name', ''))
            engine = create_engine(
                f"postgresql://{connection_details['username']}:{connection_details['password']}@"
                f"{connection_details['host']}:{connection_details['port']}/{database}"
            )
            
            with engine.connect() as conn:
                # Get column metadata
                result = conn.execute(text("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length,
                        numeric_precision,
                        numeric_scale
                    FROM information_schema.columns 
                    WHERE table_schema = :schema_name 
                    AND table_name = :table_name
                    AND column_name = :column_name
                """), {
                    "schema_name": schema_name or "public",
                    "table_name": table_name,
                    "column_name": column_name
                })
                
                row = result.fetchone()
                if not row:
                    return {"data_type": "unknown", "is_nullable": True}
                
                metadata = {
                    "data_type": row[1],
                    "is_nullable": row[2] == "YES",
                    "column_default": row[3],
                    "character_maximum_length": row[4],
                    "numeric_precision": row[5],
                    "numeric_scale": row[6]
                }
                
                # Check for foreign key relationships
                fk_result = conn.execute(text("""
                    SELECT 
                        ccu.table_schema || '.' || ccu.table_name || '.' || ccu.column_name as target
                    FROM information_schema.table_constraints tc 
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage ccu 
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_schema = :schema_name
                        AND tc.table_name = :table_name
                        AND kcu.column_name = :column_name
                """), {
                    "schema_name": schema_name or "public",
                    "table_name": table_name,
                    "column_name": column_name
                })
                
                fk_row = fk_result.fetchone()
                if fk_row:
                    metadata["foreign_key_target"] = fk_row[0]
                
                return metadata
                
        except Exception as e:
            logger.error(f"Error getting column metadata: {str(e)}")
            return {"data_type": "unknown", "is_nullable": True}
    
    async def _analyze_table_relationships(
        self,
        connection_details: Dict[str, Any],
        table_name: str,
        schema_name: str
    ) -> Dict[str, List[str]]:
        """Analyze table relationships (foreign keys, references)"""
        
        try:
            from urllib.parse import quote_plus
            import sqlalchemy as sa
            from sqlalchemy import create_engine, text
            
            # Build connection
            username = quote_plus(connection_details['username'])
            password = quote_plus(connection_details['password'])
            host = connection_details['host']
            port = connection_details['port']
            database = connection_details['database_name']
            
            connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
            engine = create_engine(connection_string, pool_timeout=30)
            
            relationships = {
                "parent_tables": [],
                "child_tables": [],
                "related_tables": []
            }
            
            with engine.connect() as conn:
                # Find parent tables (tables this table references)
                parent_query = text(f"""
                    SELECT DISTINCT 
                        ccu.table_name as parent_table
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage ccu 
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_name = '{table_name}'
                        AND tc.table_schema = '{schema_name}'
                """)
                
                result = conn.execute(parent_query)
                relationships["parent_tables"] = [row[0] for row in result]
                
                # Find child tables (tables that reference this table)
                child_query = text(f"""
                    SELECT DISTINCT 
                        tc.table_name as child_table
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage ccu 
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND ccu.table_name = '{table_name}'
                        AND ccu.table_schema = '{schema_name}'
                """)
                
                result = conn.execute(child_query)
                relationships["child_tables"] = [row[0] for row in result]
            
            return relationships
            
        except Exception as e:
            logger.error(f"Error analyzing relationships: {str(e)}")
            return {"parent_tables": [], "child_tables": [], "related_tables": []}
    
    async def _analyze_column_samples(
        self,
        connection_details: Dict[str, Any],
        table_name: str,
        column_name: str,
        schema_name: str
    ) -> Dict[str, Any]:
        """Analyze column sample data for patterns and enums"""
        
        try:
            from urllib.parse import quote_plus
            import sqlalchemy as sa
            from sqlalchemy import create_engine, text
            
            # Build connection
            username = quote_plus(connection_details['username'])
            password = quote_plus(connection_details['password'])
            host = connection_details['host']
            port = connection_details['port']
            database = connection_details['database_name']
            
            connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
            engine = create_engine(connection_string, pool_timeout=30)
            
            analysis = {}
            
            with engine.connect() as conn:
                # Get distinct count
                try:
                    result = conn.execute(text(f"""
                        SELECT COUNT(DISTINCT {column_name}) 
                        FROM {schema_name}.{table_name}
                    """))
                    analysis["distinct_count"] = result.scalar()
                except:
                    analysis["distinct_count"] = None
                
                # Get sample values (top 10)
                try:
                    result = conn.execute(text(f"""
                        SELECT DISTINCT {column_name}
                        FROM {schema_name}.{table_name}
                        WHERE {column_name} IS NOT NULL
                        ORDER BY {column_name}
                        LIMIT 10
                    """))
                    analysis["sample_values"] = [str(row[0]) for row in result]
                except:
                    analysis["sample_values"] = []
                
                # Check if it looks like an enum (low distinct count)
                if analysis.get("distinct_count", 0) <= 20:
                    try:
                        result = conn.execute(text(f"""
                            SELECT DISTINCT {column_name}, COUNT(*) as freq
                            FROM {schema_name}.{table_name}
                            WHERE {column_name} IS NOT NULL
                            GROUP BY {column_name}
                            ORDER BY freq DESC
                            LIMIT 20
                        """))
                        analysis["enum_values"] = [str(row[0]) for row in result]
                    except:
                        analysis["enum_values"] = []
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing column samples: {str(e)}")
            return {"sample_values": [], "distinct_count": None, "enum_values": []}
    
    async def _llm_analyze_table(
        self,
        table_name: str,
        metadata: Dict[str, Any],
        relationships: Dict[str, List[str]],
        columns_info: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """LLM analysis for table business context with detailed column analysis"""
        
        # Build detailed column information for context
        columns_context = ""
        if columns_info:
            columns_context = "\n\nCOLUMN DETAILS:\n"
            for col in columns_info[:20]:  # Limit to first 20 columns for prompt size
                col_name = col.get('column_name', 'unknown')
                col_type = col.get('data_type', 'unknown')
                nullable = "NULL" if col.get('nullable', True) else "NOT NULL"
                default = f" DEFAULT {col.get('default')}" if col.get('default') else ""
                columns_context += f"- {col_name} ({col_type}) {nullable}{default}\n"
        
        prompt = f"""
        Analyze this database table and provide comprehensive business insights including column-level context:
        
        TABLE: {table_name}
        ROW COUNT: {metadata.get('row_count', 'Unknown')}
        TABLE SIZE: {metadata.get('table_size', 'Unknown')}
        
        RELATIONSHIPS:
        - Parent Tables (this table references): {', '.join(relationships.get('parent_tables', []))}
        - Child Tables (reference this table): {', '.join(relationships.get('child_tables', []))}
        {columns_context}
        
        Based on the table name, column structure, and relationships, provide a detailed analysis.
        For tables like 'customer_life_cycle', include insights about:
        - What stages/phases are tracked
        - How customer progression is monitored
        - Key metrics and status indicators
        - Relationship to other business processes
        - Data usage patterns and business value
        
        Provide a JSON response with:
        {{
            "business_description": "Comprehensive description (3-5 sentences) including what this table stores, key columns and their business meaning, how it relates to other tables, and its role in business processes. Include specific column insights where relevant.",
            "primary_purpose": "Main purpose (e.g., 'customer lifecycle tracking', 'transaction processing', 'reference data')",
            "data_category": "Category (e.g., 'operational', 'analytical', 'reference', 'transactional')",
            "key_columns": ["List 3-5 most important columns and their business significance"],
            "business_processes": ["Business processes this table supports"],
            "typical_queries": ["Common query patterns with specific column references"],
            "join_patterns": ["How this table is typically joined with others, including specific columns"],
            "data_quality_notes": ["Important data quality or business rule considerations"],
            "confidence_score": 0.8
        }}
        """
        
        try:
            response = await self.llm.ainvoke(prompt)
            
            # Validate response content
            if not response or not hasattr(response, 'content') or not response.content:
                logger.warning(f"Empty LLM response for table {table_name}")
                raise ValueError("Empty LLM response")
            
            # Clean and validate JSON content
            content = response.content.strip()
            if not content:
                logger.warning(f"Empty content in LLM response for table {table_name}")
                raise ValueError("Empty content in response")
            
            # Remove markdown code blocks if present
            if content.startswith('```json'):
                content = content[7:]  # Remove ```json
            if content.startswith('```'):
                content = content[3:]   # Remove ```
            if content.endswith('```'):
                content = content[:-3]  # Remove closing ```
            
            content = content.strip()
            
            # Try to parse JSON
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError as json_err:
                logger.error(f"JSON parsing error for table {table_name}: {str(json_err)}")
                logger.error(f"Raw content after cleanup: {content[:200]}...")
                raise json_err
                
        except Exception as e:
            logger.error(f"LLM table analysis error for {table_name}: {str(e)}")
            return {
                "business_description": f"Table: {table_name}",
                "primary_purpose": "Unknown",
                "data_category": "Unknown",
                "typical_queries": [],
                "join_patterns": [],
                "confidence_score": 0.0
            }
    
    async def _llm_analyze_column(
        self,
        table_name: str,
        column_name: str,
        metadata: Dict[str, Any],
        sample_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """LLM analysis for column business context"""
        
        prompt = f"""
        Analyze this database column and provide business insights:
        
        COLUMN: {table_name}.{column_name}
        DATA TYPE: {metadata.get('data_type', 'Unknown')}
        NULLABLE: {metadata.get('is_nullable', True)}
        DISTINCT VALUES: {sample_analysis.get('distinct_count', 'Unknown')}
        
        SAMPLE VALUES: {', '.join(sample_analysis.get('sample_values', [])[:5])}
        
        {f"ENUM VALUES: {', '.join(sample_analysis.get('enum_values', []))}" if sample_analysis.get('enum_values') else ""}
        
        Provide a JSON response with:
        {{
            "business_description": "Clear description of what this column represents",
            "category": "Column category (e.g., 'identifier', 'timestamp', 'status', 'amount', 'name')",
            "confidence_score": 0.8
        }}
        """
        
        try:
            response = await self.llm.ainvoke(prompt)
            
            # Validate response content
            if not response or not hasattr(response, 'content') or not response.content:
                logger.warning(f"Empty LLM response for column {column_name}")
                raise ValueError("Empty LLM response")
            
            # Clean and validate JSON content
            content = response.content.strip()
            if not content:
                logger.warning(f"Empty content in LLM response for column {column_name}")
                raise ValueError("Empty content in response")
            
            # Remove markdown code blocks if present
            if content.startswith('```json'):
                content = content[7:]  # Remove ```json
            if content.startswith('```'):
                content = content[3:]   # Remove ```
            if content.endswith('```'):
                content = content[:-3]  # Remove closing ```
            
            content = content.strip()
            
            # Try to parse JSON
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError as json_err:
                logger.error(f"JSON parsing error for column {column_name}: {str(json_err)}")
                logger.error(f"Raw content after cleanup: {content[:200]}...")
                raise json_err
                
        except Exception as e:
            logger.error(f"LLM column analysis error for {column_name}: {str(e)}")
            return {
                "business_description": f"Column: {column_name}",
                "category": "Unknown",
                "confidence_score": 0.0
            }

# Factory function
def create_schema_analyzer() -> AdvancedSchemaAnalyzer:
    """Create schema analyzer instance"""
    return AdvancedSchemaAnalyzer()
