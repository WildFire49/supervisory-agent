"""
Streamlined Schema Analyzer - Production Grade
Removes enum mapping, adds comprehensive logging, focuses on database persistence
"""

import logging
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from app.core.config import settings

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class StreamlinedTableAnalysis:
    """Simplified table analysis without enum complexity"""
    table_name: str
    schema_name: str
    business_description: str = ""
    primary_purpose: str = ""
    data_category: str = ""
    row_count: Optional[int] = None
    confidence_score: float = 0.0


@dataclass
class StreamlinedColumnAnalysis:
    """Simplified column analysis without enum mapping"""
    column_name: str
    data_type: str
    is_nullable: bool
    business_description: str = ""
    category: str = ""
    sample_values: List[str] = None
    distinct_count: Optional[int] = None
    confidence_score: float = 0.0


class StreamlinedSchemaAnalyzer:
    """
    Production-grade streamlined analyzer with comprehensive logging
    Focuses on database persistence over session state
    """
    
    def __init__(self):
        logger.info("Initializing StreamlinedSchemaAnalyzer")
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY
        )
        logger.info("LLM client initialized successfully")
    
    def create_analysis_session(self, connection_id: str, database_type: str, database_name: str) -> str:
        """Create new analysis session in database"""
        logger.info(f"Creating analysis session for connection {connection_id}")
        
        try:
            from app.models.database.playground_analysis_models import PlaygroundAnalysisSession
            from app.core.database import SessionLocal
            import uuid
            
            session_id = str(uuid.uuid4())
            
            with SessionLocal() as db_session:
                analysis_session = PlaygroundAnalysisSession(
                    session_id=session_id,
                    connection_id=connection_id,
                    database_type=database_type,
                    database_name=database_name,
                    status="started"
                )
                db_session.add(analysis_session)
                db_session.commit()
                
                logger.info(f"Analysis session created successfully: {session_id}")
                return session_id
                
        except Exception as e:
            logger.error(f"Failed to create analysis session: {str(e)}")
            raise
    
    def analyze_table_streamlined(self, session_id: str, connection_details: Dict[str, Any], 
                                table_name: str, schema_name: str = None) -> StreamlinedTableAnalysis:
        """Streamlined table analysis with database persistence"""
        logger.info(f"Starting streamlined table analysis for {table_name}")
        
        try:
            # Get basic metadata
            metadata = self._get_table_metadata_safe(connection_details, table_name, schema_name)
            logger.info(f"Retrieved metadata for table {table_name}: {len(metadata.get('columns', []))} columns")
            
            # Get sample data (limited)
            sample_data = self._get_sample_data_safe(connection_details, table_name, schema_name, limit=3)
            logger.info(f"Retrieved {len(sample_data)} sample rows for table {table_name}")
            
            # LLM analysis (simplified)
            llm_result = asyncio.run(self._llm_analyze_table_simple(table_name, metadata, sample_data))
            logger.info(f"LLM analysis completed for table {table_name} with confidence {llm_result.get('confidence_score', 0.0)}")
            
            # Create analysis object
            analysis = StreamlinedTableAnalysis(
                table_name=table_name,
                schema_name=schema_name or "public",
                business_description=llm_result.get('business_description', ''),
                primary_purpose=llm_result.get('primary_purpose', ''),
                data_category=llm_result.get('data_category', ''),
                row_count=metadata.get('row_count'),
                confidence_score=llm_result.get('confidence_score', 0.0)
            )
            
            # Store in database
            self._store_table_analysis(session_id, analysis, metadata)
            logger.info(f"Table analysis stored in database for {table_name}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Table analysis failed for {table_name}: {str(e)}")
            raise
    
    def analyze_column_streamlined(self, session_id: str, connection_details: Dict[str, Any],
                                 table_name: str, column_name: str, schema_name: str = None) -> StreamlinedColumnAnalysis:
        """Streamlined column analysis without enum mapping"""
        logger.info(f"Starting streamlined column analysis for {table_name}.{column_name}")
        
        try:
            # Get column metadata
            metadata = self._get_column_metadata_safe(connection_details, table_name, column_name, schema_name)
            logger.info(f"Retrieved metadata for column {column_name}: type={metadata.get('data_type')}")
            
            # Get sample values (simplified)
            sample_analysis = self._get_column_samples_safe(connection_details, table_name, column_name, schema_name)
            logger.info(f"Retrieved {len(sample_analysis.get('sample_values', []))} sample values for column {column_name}")
            
            # LLM analysis (no enum mapping)
            llm_result = asyncio.run(self._llm_analyze_column_simple(table_name, column_name, metadata, sample_analysis))
            logger.info(f"LLM analysis completed for column {column_name} with confidence {llm_result.get('confidence_score', 0.0)}")
            
            # Create analysis object
            analysis = StreamlinedColumnAnalysis(
                column_name=column_name,
                data_type=metadata.get('data_type', 'unknown'),
                is_nullable=metadata.get('is_nullable', True),
                business_description=llm_result.get('business_description', ''),
                category=llm_result.get('category', ''),
                sample_values=sample_analysis.get('sample_values', [])[:5],  # Limit to 5 samples
                distinct_count=sample_analysis.get('distinct_count'),
                confidence_score=llm_result.get('confidence_score', 0.0)
            )
            
            # Store in database
            self._store_column_analysis(session_id, table_name, analysis)
            logger.info(f"Column analysis stored in database for {column_name}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Column analysis failed for {table_name}.{column_name}: {str(e)}")
            raise
    
    def _get_table_metadata_safe(self, connection_details: Dict[str, Any], table_name: str, schema_name: str) -> Dict[str, Any]:
        """Safely get table metadata with error handling"""
        logger.debug(f"Getting metadata for table {table_name}")
        
        try:
            from sqlalchemy import create_engine, text
            from urllib.parse import quote_plus
            
            # Create engine
            username = quote_plus(str(connection_details.get('username', '')))
            password = quote_plus(str(connection_details.get('password', '')))
            host = connection_details.get('host', 'localhost')
            port = connection_details.get('port', 5432)
            database = connection_details.get('database_name', '')
            
            connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
            engine = create_engine(connection_string)
            
            with engine.connect() as conn:
                # Get basic table info
                schema_clause = f"AND table_schema = '{schema_name}'" if schema_name else ""
                
                # Get column information
                columns_query = text(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' {schema_clause}
                    ORDER BY ordinal_position
                """)
                
                columns_result = conn.execute(columns_query)
                columns = [dict(row._mapping) for row in columns_result]
                
                # Get row count
                try:
                    count_query = text(f"SELECT COUNT(*) as row_count FROM {table_name}")
                    count_result = conn.execute(count_query)
                    row_count = count_result.fetchone()[0]
                except:
                    row_count = None
                
                metadata = {
                    'columns': columns,
                    'row_count': row_count,
                    'column_count': len(columns)
                }
                
                logger.debug(f"Successfully retrieved metadata for table {table_name}")
                return metadata
                
        except Exception as e:
            logger.error(f"Failed to get table metadata for {table_name}: {str(e)}")
            return {'columns': [], 'row_count': None, 'column_count': 0}
    
    def _get_sample_data_safe(self, connection_details: Dict[str, Any], table_name: str, schema_name: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Safely get sample data with error handling"""
        logger.debug(f"Getting sample data for table {table_name}, limit={limit}")
        
        try:
            from sqlalchemy import create_engine, text
            from urllib.parse import quote_plus
            
            # Create engine
            username = quote_plus(str(connection_details.get('username', '')))
            password = quote_plus(str(connection_details.get('password', '')))
            host = connection_details.get('host', 'localhost')
            port = connection_details.get('port', 5432)
            database = connection_details.get('database_name', '')
            
            connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
            engine = create_engine(connection_string)
            
            with engine.connect() as conn:
                query = text(f"SELECT * FROM {table_name} LIMIT {limit}")
                result = conn.execute(query)
                sample_data = [dict(row._mapping) for row in result]
                
                logger.debug(f"Successfully retrieved {len(sample_data)} sample rows for table {table_name}")
                return sample_data
                
        except Exception as e:
            logger.error(f"Failed to get sample data for {table_name}: {str(e)}")
            return []
    
    def _get_column_metadata_safe(self, connection_details: Dict[str, Any], table_name: str, column_name: str, schema_name: str) -> Dict[str, Any]:
        """Safely get column metadata"""
        logger.debug(f"Getting metadata for column {table_name}.{column_name}")
        
        try:
            from sqlalchemy import create_engine, text
            from urllib.parse import quote_plus
            
            # Create engine
            username = quote_plus(str(connection_details.get('username', '')))
            password = quote_plus(str(connection_details.get('password', '')))
            host = connection_details.get('host', 'localhost')
            port = connection_details.get('port', 5432)
            database = connection_details.get('database_name', '')
            
            connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
            engine = create_engine(connection_string)
            
            with engine.connect() as conn:
                schema_clause = f"AND table_schema = '{schema_name}'" if schema_name else ""
                
                query = text(f"""
                    SELECT column_name, data_type, is_nullable, column_default,
                           character_maximum_length, numeric_precision, numeric_scale
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' AND column_name = '{column_name}' {schema_clause}
                """)
                
                result = conn.execute(query)
                row = result.fetchone()
                
                if row:
                    metadata = dict(row._mapping)
                    logger.debug(f"Successfully retrieved metadata for column {column_name}")
                    return metadata
                else:
                    logger.warning(f"No metadata found for column {column_name}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Failed to get column metadata for {column_name}: {str(e)}")
            return {}
    
    def _get_column_samples_safe(self, connection_details: Dict[str, Any], table_name: str, column_name: str, schema_name: str) -> Dict[str, Any]:
        """Safely get column sample values (simplified, no enum mapping)"""
        logger.debug(f"Getting sample values for column {table_name}.{column_name}")
        
        try:
            from sqlalchemy import create_engine, text
            from urllib.parse import quote_plus
            
            # Create engine
            username = quote_plus(str(connection_details.get('username', '')))
            password = quote_plus(str(connection_details.get('password', '')))
            host = connection_details.get('host', 'localhost')
            port = connection_details.get('port', 5432)
            database = connection_details.get('database_name', '')
            
            connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
            engine = create_engine(connection_string)
            
            with engine.connect() as conn:
                # Get sample values (limit to 10)
                sample_query = text(f"""
                    SELECT DISTINCT {column_name} 
                    FROM {table_name} 
                    WHERE {column_name} IS NOT NULL 
                    LIMIT 10
                """)
                
                sample_result = conn.execute(sample_query)
                sample_values = [str(row[0]) for row in sample_result if row[0] is not None]
                
                # Get distinct count
                try:
                    count_query = text(f"SELECT COUNT(DISTINCT {column_name}) as distinct_count FROM {table_name}")
                    count_result = conn.execute(count_query)
                    distinct_count = count_result.fetchone()[0]
                except:
                    distinct_count = None
                
                analysis = {
                    'sample_values': sample_values,
                    'distinct_count': distinct_count
                }
                
                logger.debug(f"Successfully retrieved sample analysis for column {column_name}: {len(sample_values)} samples")
                return analysis
                
        except Exception as e:
            logger.error(f"Failed to get column samples for {column_name}: {str(e)}")
            return {'sample_values': [], 'distinct_count': None}
    
    async def _llm_analyze_table_simple(self, table_name: str, metadata: Dict[str, Any], sample_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simplified LLM table analysis without enum complexity"""
        logger.debug(f"Starting LLM analysis for table {table_name}")
        
        try:
            columns_info = "\n".join([
                f"- {col['column_name']}: {col['data_type']}" 
                for col in metadata.get('columns', [])[:10]  # Limit to first 10 columns
            ])
            
            sample_info = ""
            if sample_data:
                sample_info = f"Sample data (first row): {dict(list(sample_data[0].items())[:5])}"
            
            prompt = f"""
            Analyze this database table for business context:
            
            TABLE: {table_name}
            ROW COUNT: {metadata.get('row_count', 'Unknown')}
            COLUMNS ({metadata.get('column_count', 0)}):
            {columns_info}
            
            {sample_info}
            
            Provide a concise JSON response:
            {{
                "business_description": "Clear, concise description of what this table stores and its business purpose",
                "primary_purpose": "Main business function (e.g., 'customer data', 'transaction log', 'reference data')",
                "data_category": "Category (e.g., 'operational', 'analytical', 'reference')",
                "confidence_score": 0.8
            }}
            
            Keep descriptions practical and focused on business value.
            """
            
            response = await self.llm.ainvoke(prompt)
            content = response.content.strip()
            
            # Clean JSON response
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            
            result = json.loads(content.strip())
            logger.debug(f"LLM analysis completed for table {table_name}")
            return result
            
        except Exception as e:
            logger.error(f"LLM table analysis failed for {table_name}: {str(e)}")
            return {
                "business_description": f"Table: {table_name}",
                "primary_purpose": "Unknown",
                "data_category": "Unknown",
                "confidence_score": 0.0
            }
    
    async def _llm_analyze_column_simple(self, table_name: str, column_name: str, metadata: Dict[str, Any], sample_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Simplified LLM column analysis without enum mapping"""
        logger.debug(f"Starting LLM analysis for column {table_name}.{column_name}")
        
        try:
            sample_values = sample_analysis.get('sample_values', [])
            distinct_count = sample_analysis.get('distinct_count')
            
            prompt = f"""
            Analyze this database column for business context:
            
            TABLE: {table_name}
            COLUMN: {column_name}
            DATA TYPE: {metadata.get('data_type', 'Unknown')}
            NULLABLE: {metadata.get('is_nullable', True)}
            DISTINCT VALUES: {distinct_count if distinct_count else 'Unknown'}
            SAMPLE VALUES: {', '.join(sample_values[:5])}
            
            Provide a concise JSON response:
            {{
                "business_description": "Clear description of what this column represents in business terms",
                "category": "Simple category (e.g., 'identifier', 'timestamp', 'status', 'amount', 'description')",
                "confidence_score": 0.8
            }}
            
            Keep descriptions practical and business-focused.
            """
            
            response = await self.llm.ainvoke(prompt)
            content = response.content.strip()
            
            # Clean JSON response
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            
            result = json.loads(content.strip())
            logger.debug(f"LLM analysis completed for column {column_name}")
            return result
            
        except Exception as e:
            logger.error(f"LLM column analysis failed for {column_name}: {str(e)}")
            return {
                "business_description": f"Column: {column_name}",
                "category": "Unknown",
                "confidence_score": 0.0
            }
    
    def _store_table_analysis(self, session_id: str, analysis: StreamlinedTableAnalysis, metadata: Dict[str, Any]):
        """Store table analysis in database"""
        logger.debug(f"Storing table analysis for {analysis.table_name}")
        
        try:
            from app.models.database.playground_analysis_models import PlaygroundTableAnalysis
            from app.core.database import SessionLocal
            
            with SessionLocal() as db_session:
                table_analysis = PlaygroundTableAnalysis(
                    session_id=session_id,
                    table_name=analysis.table_name,
                    schema_name=analysis.schema_name,
                    row_count=analysis.row_count,
                    column_count=metadata.get('column_count', 0),
                    business_description=analysis.business_description,
                    primary_purpose=analysis.primary_purpose,
                    data_category=analysis.data_category,
                    confidence_score=analysis.confidence_score
                )
                
                db_session.add(table_analysis)
                db_session.commit()
                
                logger.debug(f"Table analysis stored successfully for {analysis.table_name}")
                
        except Exception as e:
            logger.error(f"Failed to store table analysis for {analysis.table_name}: {str(e)}")
            raise
    
    def _store_column_analysis(self, session_id: str, table_name: str, analysis: StreamlinedColumnAnalysis):
        """Store column analysis in database"""
        logger.debug(f"Storing column analysis for {table_name}.{analysis.column_name}")
        
        try:
            from app.models.database.playground_analysis_models import PlaygroundColumnAnalysis
            from app.core.database import SessionLocal
            
            with SessionLocal() as db_session:
                column_analysis = PlaygroundColumnAnalysis(
                    session_id=session_id,
                    table_name=table_name,
                    column_name=analysis.column_name,
                    data_type=analysis.data_type,
                    is_nullable=analysis.is_nullable,
                    business_description=analysis.business_description,
                    category=analysis.category,
                    sample_values=analysis.sample_values,
                    distinct_count=analysis.distinct_count,
                    confidence_score=analysis.confidence_score
                )
                
                db_session.add(column_analysis)
                db_session.commit()
                
                logger.debug(f"Column analysis stored successfully for {analysis.column_name}")
                
        except Exception as e:
            logger.error(f"Failed to store column analysis for {analysis.column_name}: {str(e)}")
            raise
    
    def get_session_analysis(self, session_id: str) -> Dict[str, Any]:
        """Retrieve complete analysis for a session from database"""
        logger.info(f"Retrieving session analysis for {session_id}")
        
        try:
            from app.models.database.playground_analysis_models import (
                PlaygroundAnalysisSession, PlaygroundTableAnalysis, PlaygroundColumnAnalysis
            )
            from app.core.database import SessionLocal
            
            with SessionLocal() as db_session:
                # Get session info
                session = db_session.query(PlaygroundAnalysisSession).filter(
                    PlaygroundAnalysisSession.session_id == session_id
                ).first()
                
                if not session:
                    logger.warning(f"No session found for {session_id}")
                    return {}
                
                # Get table analyses
                table_analyses = db_session.query(PlaygroundTableAnalysis).filter(
                    PlaygroundTableAnalysis.session_id == session_id
                ).all()
                
                # Get column analyses
                column_analyses = db_session.query(PlaygroundColumnAnalysis).filter(
                    PlaygroundColumnAnalysis.session_id == session_id
                ).all()
                
                # Format response
                analysis_data = {
                    'session_info': {
                        'session_id': session.session_id,
                        'database_type': session.database_type,
                        'database_name': session.database_name,
                        'status': session.status,
                        'tables_analyzed': session.tables_analyzed,
                        'columns_analyzed': session.columns_analyzed
                    },
                    'tables': {},
                    'columns': {}
                }
                
                # Add table analyses
                for table in table_analyses:
                    analysis_data['tables'][table.table_name] = {
                        'business_description': table.business_description,
                        'primary_purpose': table.primary_purpose,
                        'data_category': table.data_category,
                        'row_count': table.row_count,
                        'confidence_score': table.confidence_score,
                        'user_notes': table.user_notes,
                        'business_rules': table.business_rules
                    }
                
                # Add column analyses
                for column in column_analyses:
                    if column.table_name not in analysis_data['columns']:
                        analysis_data['columns'][column.table_name] = {}
                    
                    analysis_data['columns'][column.table_name][column.column_name] = {
                        'business_description': column.business_description,
                        'category': column.category,
                        'data_type': column.data_type,
                        'sample_values': column.sample_values,
                        'confidence_score': column.confidence_score,
                        'user_notes': column.user_notes,
                        'business_rules': column.business_rules
                    }
                
                logger.info(f"Retrieved analysis for {len(analysis_data['tables'])} tables and {sum(len(cols) for cols in analysis_data['columns'].values())} columns")
                return analysis_data
                
        except Exception as e:
            logger.error(f"Failed to retrieve session analysis for {session_id}: {str(e)}")
            return {}


def create_streamlined_analyzer() -> StreamlinedSchemaAnalyzer:
    """Factory function to create analyzer instance"""
    logger.info("Creating StreamlinedSchemaAnalyzer instance")
    return StreamlinedSchemaAnalyzer()
