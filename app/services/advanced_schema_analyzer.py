"""
Advanced Schema Intelligence System
Senior Dev Implementation: LLM-powered column/table analysis with user editing
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone
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
    sample_data: List[Dict[str, Any]] = None  # Sample data for analysis

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
    
    def _create_engine(self, connection_details: Dict[str, Any]):
        """
        Create SQLAlchemy engine with robust connection string handling
        Production-grade connection logic consolidated in one place
        """
        from urllib.parse import quote_plus
        from sqlalchemy import create_engine
        
        try:
            # Extract and validate connection parameters
            username = str(connection_details.get('username', '')).strip()
            password = str(connection_details.get('password', '')).strip()
            host = str(connection_details.get('host', '')).strip()
            port = int(connection_details.get('port', 5432))
            database = str(connection_details.get('database_name', '')).strip()
            db_type = str(connection_details.get('database_type', 'postgresql')).strip().lower()
            
            # Validate required parameters
            if not all([username, password, host, database]):
                raise ValueError("Missing required connection parameters")
            
            # URL encode credentials to handle special characters
            username_encoded = quote_plus(username)
            password_encoded = quote_plus(password)
            
            # Build connection string based on database type
            if db_type == 'postgresql':
                connection_string = f"postgresql://{username_encoded}:{password_encoded}@{host}:{port}/{database}"
            elif db_type == 'mysql':
                connection_string = f"mysql+pymysql://{username_encoded}:{password_encoded}@{host}:{port}/{database}"
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
            
            # Create engine with production settings
            return create_engine(
                connection_string,
                pool_timeout=30,
                pool_recycle=300,
                pool_pre_ping=True,
                echo=False
            )
            
        except Exception as e:
            logger.error(f"Failed to create database engine: {str(e)}")
            logger.error(f"Connection details (sanitized): host={host}, port={port}, database={database}, user={username}")
            raise
        
    async def analyze_table_on_demand(
        self, 
        connection_details: Dict[str, Any],
        table_name: str,
        schema_name: str = None
    ) -> TableAnalysis:
        """
        Enhanced on-demand table analysis with comprehensive column analysis and sample data
        Automatically analyzes all columns, fetches first 2 rows, and provides complete summary
        """
        
        logger.info(f"🔍 Analyzing table: {schema_name}.{table_name} (Detailed Column Analysis Mode)")
        
        try:
            # Step 1: Get table metadata
            table_metadata = await self._get_table_metadata(
                connection_details, table_name, schema_name
            )
            
            # Step 2: Analyze relationships
            relationships = await self._analyze_table_relationships(
                connection_details, table_name, schema_name
            )
            
            # Step 3: Fetch first 2 rows of sample data for context
            sample_data = await self._fetch_sample_rows(
                connection_details, table_name, schema_name, limit=2
            )
            
            # Step 4: Automatically analyze ALL columns with sample data
            logger.info(f"📊 Auto-analyzing all columns for table {table_name}")
            columns_analysis = []
            columns_info = table_metadata.get("columns", [])
            
            for column_info in columns_info:
                column_name = column_info.get("column_name")
                if column_name:
                    try:
                        # Get column metadata and sample analysis
                        column_metadata = await self._get_column_metadata(
                            connection_details, table_name, column_name, schema_name
                        )
                        
                        # Analyze column samples for patterns and enums
                        sample_analysis = await self._analyze_column_samples(
                            connection_details, table_name, column_name, schema_name
                        )
                        
                        # LLM analysis for business context
                        llm_column_analysis = await self._llm_analyze_column(
                            table_name, column_name, column_metadata, sample_analysis
                        )
                        
                        # Create column analysis object
                        column_analysis = ColumnAnalysis(
                            column_name=column_name,
                            data_type=column_metadata.get("data_type", "Unknown"),
                            is_nullable=column_metadata.get("is_nullable", True),
                            business_description=llm_column_analysis.get("business_description", ""),
                            category=llm_column_analysis.get("category", ""),
                            sample_values=sample_analysis.get("sample_values", []),
                            distinct_count=sample_analysis.get("distinct_count"),
                            enum_values=sample_analysis.get("enum_values", []),
                            foreign_key_target=column_metadata.get("foreign_key_target"),
                            referenced_by=column_metadata.get("referenced_by", []),
                            analyzed_at=datetime.now(timezone.utc),
                            confidence_score=llm_column_analysis.get("confidence_score", 0.8)
                        )
                        
                        columns_analysis.append(column_analysis)
                        logger.info(f"✅ Analyzed column: {column_name}")
                        
                    except Exception as col_error:
                        logger.warning(f"⚠️ Error analyzing column {column_name}: {str(col_error)}")
                        # Add basic column info even if analysis fails
                        columns_analysis.append(ColumnAnalysis(
                            column_name=column_name,
                            data_type=column_info.get("data_type", "Unknown"),
                            is_nullable=column_info.get("is_nullable", True),
                            business_description=f"Analysis error: {str(col_error)}",
                            analyzed_at=datetime.now(timezone.utc),
                            confidence_score=0.0
                        ))
            
            # Step 5: Enhanced LLM analysis with column details and sample data
            llm_analysis = await self._llm_analyze_table_enhanced(
                table_name, table_metadata, relationships, columns_analysis, sample_data
            )
            
            # Step 6: Create comprehensive analysis with all column details
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
                analyzed_at=datetime.now(timezone.utc),
                confidence_score=llm_analysis.get("confidence_score", 0.8),
                columns=columns_analysis  # Include all column analyses
            )
            
            logger.info(f"✅ Complete table analysis finished: {len(columns_analysis)} columns analyzed")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing table {table_name}: {str(e)}")
            # Return basic analysis on error
            return TableAnalysis(
                table_name=table_name,
                schema_name=schema_name or "public",
                business_description=f"Error during analysis: {str(e)}",
                analyzed_at=datetime.now(timezone.utc),
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
            from sqlalchemy import text
            
            # Use consolidated connection method
            engine = self._create_engine(connection_details)
            
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
            
            # Use consolidated connection method
            engine = self._create_engine(connection_details)
            
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
    
    async def _fetch_sample_rows(
        self,
        connection_details: Dict[str, Any],
        table_name: str,
        schema_name: str,
        limit: int = 2
    ) -> List[Dict[str, Any]]:
        """Fetch first N rows from table for sample data analysis"""
        
        try:
            from sqlalchemy import text
            
            # Use consolidated connection method
            engine = self._create_engine(connection_details)
            
            # Build qualified table name
            if schema_name and schema_name.lower() != 'public':
                qualified_table = f'"{schema_name}"."{table_name}"'
            else:
                qualified_table = f'"{table_name}"'
            
            query = f"SELECT * FROM {qualified_table} LIMIT {limit}"
            
            with engine.connect() as conn:
                result = conn.execute(text(query))
                rows = result.fetchall()
                columns = result.keys()
                
                # Convert to list of dictionaries
                sample_data = []
                for row in rows:
                    row_dict = {}
                    for i, column in enumerate(columns):
                        value = row[i]
                        # Convert to string for JSON serialization
                        if value is not None:
                            row_dict[column] = str(value)
                        else:
                            row_dict[column] = None
                    sample_data.append(row_dict)
                
                logger.info(f"📊 Fetched {len(sample_data)} sample rows from {qualified_table}")
                return sample_data
                
        except Exception as e:
            logger.error(f"Error fetching sample rows from {table_name}: {str(e)}")
            return []

    async def _analyze_table_relationships(
        self,
        connection_details: Dict[str, Any],
        table_name: str,
        schema_name: str
    ) -> Dict[str, List[str]]:
        """Analyze table relationships (foreign keys, references)"""
        
        try:
            from sqlalchemy import text
            
            # Use consolidated connection method
            engine = self._create_engine(connection_details)
            
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
    
    async def _get_column_metadata(
        self, 
        connection_details: Dict[str, Any], 
        table_name: str, 
        column_name: str,
        schema_name: str
    ) -> Dict[str, Any]:
        """Get basic column metadata including data type, nullable, foreign keys"""
        
        try:
            from urllib.parse import quote_plus
            import sqlalchemy as sa
            from sqlalchemy import create_engine, text
            
            # Build connection string safely
            engine = self._create_engine(connection_details)
            
            analysis = {}
            
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
    
    async def _analyze_column_samples(
        self,
        connection_details: Dict[str, Any],
        table_name: str,
        column_name: str,
        schema_name: str
    ) -> Dict[str, Any]:
        """Analyze column sample data for patterns and enums"""
        
        try:
            from sqlalchemy import text
            
            # Use consolidated connection method
            engine = self._create_engine(connection_details)
            
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
                distinct_count = analysis.get("distinct_count")
                if distinct_count is not None and distinct_count <= 20:
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
    
    async def _llm_analyze_table_enhanced(
        self,
        table_name: str,
        metadata: Dict[str, Any],
        relationships: Dict[str, List[str]],
        columns_analysis: List[ColumnAnalysis],
        sample_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Enhanced LLM analysis with comprehensive column analysis and sample data"""
        
        # Prepare column summaries for LLM context
        column_summaries = []
        for col in columns_analysis:
            col_summary = f"- {col.column_name} ({col.data_type}): {col.business_description}"
            if col.category:
                col_summary += f" [Category: {col.category}]"
            if col.enum_values:
                col_summary += f" [Enum: {', '.join(col.enum_values[:3])}{'...' if len(col.enum_values) > 3 else ''}]"
            if col.distinct_count is not None and col.distinct_count <= 20:
                col_summary += f" [Distinct: {col.distinct_count}]"
            column_summaries.append(col_summary)
        
        # Prepare sample data for LLM context
        sample_data_str = ""
        if sample_data:
            sample_data_str = "\n\nSAMPLE DATA (First 2 rows):\n"
            for i, row in enumerate(sample_data, 1):
                sample_data_str += f"Row {i}: {dict(list(row.items())[:5])}{'...' if len(row) > 5 else ''}\n"
        
        # Prepare detailed enum analysis for LLM query generation
        enum_analysis = []
        categorical_columns = []
        
        for col in columns_analysis:
            if col.enum_values and len(col.enum_values) > 0:
                enum_vals = "', '".join(col.enum_values)
                enum_analysis.append(f"- **{col.column_name}** (ENUM): Valid values are ['{enum_vals}']. Use these exact values in WHERE clauses.")
            elif col.distinct_count and col.distinct_count <= 20 and col.sample_values:
                sample_vals = "', '".join(col.sample_values[:5])
                categorical_columns.append(f"- **{col.column_name}** (CATEGORICAL): Common values are ['{sample_vals}']. Use these for filtering.")
        
        enum_section = ""
        if enum_analysis:
            enum_section = f"\n\nENUM COLUMNS FOR QUERY GENERATION:\n" + "\n".join(enum_analysis)
        
        categorical_section = ""
        if categorical_columns:
            categorical_section = f"\n\nCATEGORICAL COLUMNS FOR QUERY GENERATION:\n" + "\n".join(categorical_columns)

        prompt = f"""
        Analyze this database table comprehensively for LLM query generation optimization:
        
        TABLE: {table_name}
        ROW COUNT: {metadata.get('row_count', 'Unknown')}
        
        RELATIONSHIPS:
        - Parent Tables: {', '.join(relationships.get('parent_tables', []))}
        - Child Tables: {', '.join(relationships.get('child_tables', []))}
        - Related Tables: {', '.join(relationships.get('related_tables', []))}
        
        DETAILED COLUMN ANALYSIS:
        {chr(10).join(column_summaries)}
        {sample_data_str}
        {enum_section}
        {categorical_section}
        
        Generate a comprehensive JSON response optimized for LLM query generation:
        {{
            "business_description": "CRITICAL: Write a detailed description optimized for LLM query generation. Include: (1) What this table represents in business terms, (2) Explicit mention of each ENUM column with their exact valid values in single quotes, (3) Key relationships and how to join with other tables, (4) Common filtering patterns and WHERE clause examples, (5) Business rules and constraints that affect queries. Format as: 'This table stores [purpose]. Key enum columns: [column_name] accepts ['value1', 'value2', 'value3'], [column2] accepts ['val1', 'val2']. Common queries filter by [patterns]. Joins typically use [relationships].'",
            "primary_purpose": "Main business function with query context (e.g., 'customer lifecycle tracking with status filtering', 'transaction processing with amount ranges')",
            "data_category": "Data classification with query implications (e.g., 'operational data for real-time filtering', 'analytical data for aggregations')",
            "key_columns": ["List most important columns with their query usage: 'column_name: used for [filtering/grouping/joining/ordering]'"],
            "business_processes": ["Business processes with query patterns: 'process_name: typically queries by [column] WHERE [condition]'"],
            "data_quality_notes": ["Query-relevant data quality notes: 'column_name may have nulls, use IS NOT NULL', 'enum_column only accepts [values]'"],
            "typical_queries": ["Specific query patterns: 'SELECT * FROM {table_name} WHERE enum_column = \\'value\\' AND date_column > \\'2024-01-01\\'"],
            "join_patterns": ["Exact join syntax: 'JOIN parent_table ON {table_name}.fk_column = parent_table.id'"],
            "confidence_score": 0.9
        }}
        
        CRITICAL: The business_description must be optimized for LLM query generation with explicit enum values in single quotes and specific query patterns.
        """
        
        try:
            response = await self.llm.ainvoke(prompt)
            content = response.content.strip()
            
            # Clean markdown code blocks
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            
            content = content.strip()
            result = json.loads(content)
            return result
            
        except Exception as e:
            logger.error(f"Enhanced LLM table analysis error for {table_name}: {str(e)}")
            return {
                "business_description": f"Table: {table_name} with {len(columns_analysis)} columns analyzed",
                "primary_purpose": "Data storage and management",
                "data_category": "Operational",
                "key_columns": [col.column_name for col in columns_analysis[:3]],
                "business_processes": ["Data management"],
                "data_quality_notes": ["Comprehensive column analysis completed"],
                "typical_queries": [f"SELECT * FROM {table_name}"],
                "join_patterns": ["Standard table joins"],
                "confidence_score": 0.7
            }

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
        """Enhanced LLM analysis for detailed column business context and enum values"""
        
        # Prepare detailed enum and distinct value information
        enum_info = ""
        distinct_info = ""
        sample_values = sample_analysis.get('sample_values', [])
        enum_values = sample_analysis.get('enum_values', [])
        distinct_count = sample_analysis.get('distinct_count')
        
        if enum_values:
            enum_info = f"\nENUM VALUES: {', '.join(enum_values)}"
            enum_info += f"\nTotal enum options: {len(enum_values)}"
        
        if distinct_count is not None:
            distinct_info = f"\nDISTINCT VALUES COUNT: {distinct_count}"
            if distinct_count <= 20 and not enum_values:
                distinct_info += f"\nAll distinct values: {', '.join(sample_values[:20])}"
        
        # Prepare data type details
        data_type_info = f"DATA TYPE: {metadata.get('data_type', 'Unknown')}"
        if metadata.get('character_maximum_length'):
            data_type_info += f" (max length: {metadata.get('character_maximum_length')})"
        if metadata.get('numeric_precision'):
            data_type_info += f" (precision: {metadata.get('numeric_precision')})"
        
        prompt = f"""
        Analyze this database column comprehensively for accurate LLM query generation:
        
        TABLE: {table_name}
        COLUMN: {column_name}
        {data_type_info}
        NULLABLE: {metadata.get('is_nullable', True)}
        DEFAULT VALUE: {metadata.get('column_default', 'None')}
        {distinct_info}
        {enum_info}
        
        SAMPLE VALUES: {', '.join(sample_values[:10])}
        
        {f"FOREIGN KEY TARGET: {metadata.get('foreign_key_target')}" if metadata.get('foreign_key_target') else ""}
        
        Provide a detailed JSON response optimized for LLM query generation:
        {{
            "business_description": "Detailed, meaningful description of what this column represents in business terms, including its purpose, typical usage patterns, and relationship to business processes. Be specific about what values represent and how they're used in queries.",
            "category": "Precise category (e.g., 'primary_identifier', 'foreign_key', 'status_enum', 'timestamp', 'amount', 'text_description', 'boolean_flag', 'code_reference')",
            "query_context": "How this column is typically used in queries - filtering, grouping, ordering, joining, etc.",
            "value_meaning": "What the values in this column actually represent in business terms",
            "enum_values_explicit": {enum_values if enum_values else "[]"},
            "distinct_values_sample": {sample_values[:10] if sample_values else "[]"},
            "is_categorical": {str(distinct_count is not None and distinct_count <= 50).lower()},
            "confidence_score": 0.9
        }}
        
        Focus on providing context that helps LLMs generate accurate queries with correct column usage and value filtering.
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
