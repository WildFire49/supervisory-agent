"""
SQL Query and QnA Knowledge Analyzer
LLM-powered query understanding and knowledge base enrichment
"""

import logging
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from langchain_openai import ChatOpenAI
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)


class QueryKnowledgeAnalyzer:
    """
    Analyzes SQL queries and natural language QnA to enrich knowledge base
    Stores insights in vector DB for enhanced context
    """
    
    def __init__(self):
        logger.info("Initializing QueryKnowledgeAnalyzer")
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY
        )
        logger.info("LLM client initialized for query analysis")
    
    def analyze_sql_query(self, session_id: str, sql_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze SQL query to extract business knowledge"""
        logger.info(f"Analyzing SQL query for session {session_id}")
        logger.debug(f"SQL Query: {sql_query[:100]}...")
        
        try:
            # Run LLM analysis
            analysis_result = asyncio.run(self._llm_analyze_sql_query(sql_query, context))
            logger.info(f"SQL query analysis completed with confidence {analysis_result.get('confidence_score', 0.0)}")
            
            # Store in database
            query_id = self._store_query_analysis(session_id, "sql_query", sql_query, analysis_result)
            logger.info(f"SQL query analysis stored with ID: {query_id}")
            
            # Extract and store knowledge entries
            knowledge_entries = self._extract_knowledge_from_analysis(session_id, analysis_result, "sql_query")
            logger.info(f"Extracted {len(knowledge_entries)} knowledge entries from SQL query")
            
            return {
                'query_id': query_id,
                'analysis': analysis_result,
                'knowledge_entries': knowledge_entries
            }
            
        except Exception as e:
            logger.error(f"SQL query analysis failed: {str(e)}")
            raise
    
    def analyze_natural_language_qna(self, session_id: str, question: str, answer: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze natural language Q&A to extract business knowledge"""
        logger.info(f"Analyzing natural language Q&A for session {session_id}")
        logger.debug(f"Question: {question[:100]}...")
        
        try:
            # Run LLM analysis
            analysis_result = asyncio.run(self._llm_analyze_qna(question, answer, context))
            logger.info(f"Q&A analysis completed with confidence {analysis_result.get('confidence_score', 0.0)}")
            
            # Store in database
            query_text = f"Q: {question}" + (f"\nA: {answer}" if answer else "")
            query_id = self._store_query_analysis(session_id, "natural_language", query_text, analysis_result)
            logger.info(f"Q&A analysis stored with ID: {query_id}")
            
            # Extract and store knowledge entries
            knowledge_entries = self._extract_knowledge_from_analysis(session_id, analysis_result, "qna")
            logger.info(f"Extracted {len(knowledge_entries)} knowledge entries from Q&A")
            
            return {
                'query_id': query_id,
                'analysis': analysis_result,
                'knowledge_entries': knowledge_entries
            }
            
        except Exception as e:
            logger.error(f"Q&A analysis failed: {str(e)}")
            raise
    
    async def _llm_analyze_sql_query(self, sql_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """LLM analysis of SQL query for business insights"""
        logger.debug("Starting LLM analysis of SQL query")
        
        try:
            context_info = ""
            if context:
                context_info = f"Database Context: {json.dumps(context, indent=2)}"
            
            prompt = f"""
            Analyze this SQL query to extract business knowledge and insights:
            
            SQL QUERY:
            {sql_query}
            
            {context_info}
            
            Provide a comprehensive JSON analysis:
            {{
                "query_intent": {{
                    "primary_purpose": "What is the main business purpose of this query?",
                    "business_question": "What business question is this query trying to answer?",
                    "data_scope": "What data scope/timeframe does this query cover?"
                }},
                "business_context": "Detailed business context and meaning of this query",
                "tables_involved": ["list", "of", "table", "names"],
                "columns_involved": ["list", "of", "column", "names"],
                "business_rules_discovered": [
                    "Business rule 1 discovered from query logic",
                    "Business rule 2 discovered from joins/filters"
                ],
                "patterns_identified": [
                    "Pattern 1: e.g., date filtering pattern",
                    "Pattern 2: e.g., aggregation pattern"
                ],
                "knowledge_extracted": {{
                    "relationships": "Key table relationships revealed",
                    "constraints": "Business constraints or validation rules",
                    "calculations": "Business calculations or formulas used",
                    "filters": "Common filtering patterns or business logic"
                }},
                "confidence_score": 0.8
            }}
            
            Focus on extracting actionable business knowledge that can improve future query generation.
            """
            
            response = await self.llm.ainvoke(prompt)
            content = self._clean_json_response(response.content)
            result = json.loads(content)
            
            logger.debug("LLM SQL query analysis completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"LLM SQL query analysis failed: {str(e)}")
            return {
                "query_intent": {"primary_purpose": "Unknown", "business_question": "Unknown"},
                "business_context": f"SQL Query: {sql_query[:100]}...",
                "tables_involved": [],
                "columns_involved": [],
                "business_rules_discovered": [],
                "patterns_identified": [],
                "knowledge_extracted": {},
                "confidence_score": 0.0
            }
    
    async def _llm_analyze_qna(self, question: str, answer: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """LLM analysis of Q&A for business insights"""
        logger.debug("Starting LLM analysis of Q&A")
        
        try:
            context_info = ""
            if context:
                context_info = f"Database Context: {json.dumps(context, indent=2)}"
            
            answer_info = f"ANSWER: {answer}" if answer else "ANSWER: Not provided"
            
            prompt = f"""
            Analyze this business question and answer to extract knowledge:
            
            QUESTION: {question}
            {answer_info}
            
            {context_info}
            
            Provide a comprehensive JSON analysis:
            {{
                "query_intent": {{
                    "primary_purpose": "What business need does this question address?",
                    "business_domain": "What business domain/area is this about?",
                    "urgency_level": "How urgent/important is this type of question?"
                }},
                "business_context": "Detailed business context and implications",
                "tables_involved": ["likely", "tables", "needed"],
                "columns_involved": ["likely", "columns", "needed"],
                "business_rules_discovered": [
                    "Business rule 1 implied by the question",
                    "Business rule 2 from the context"
                ],
                "patterns_identified": [
                    "Pattern 1: e.g., reporting pattern",
                    "Pattern 2: e.g., operational query pattern"
                ],
                "knowledge_extracted": {{
                    "business_processes": "Business processes this question relates to",
                    "stakeholders": "Who typically asks this type of question",
                    "frequency": "How often this type of question comes up",
                    "related_questions": "Other questions that might follow"
                }},
                "confidence_score": 0.8
            }}
            
            Focus on understanding the business need and extracting reusable knowledge.
            """
            
            response = await self.llm.ainvoke(prompt)
            content = self._clean_json_response(response.content)
            result = json.loads(content)
            
            logger.debug("LLM Q&A analysis completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"LLM Q&A analysis failed: {str(e)}")
            return {
                "query_intent": {"primary_purpose": "Unknown", "business_domain": "Unknown"},
                "business_context": f"Question: {question[:100]}...",
                "tables_involved": [],
                "columns_involved": [],
                "business_rules_discovered": [],
                "patterns_identified": [],
                "knowledge_extracted": {},
                "confidence_score": 0.0
            }
    
    def _clean_json_response(self, content: str) -> str:
        """Clean LLM response to extract valid JSON"""
        content = content.strip()
        
        # Remove markdown code blocks
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        
        return content.strip()
    
    def _store_query_analysis(self, session_id: str, query_type: str, query_text: str, analysis: Dict[str, Any]) -> str:
        """Store query analysis in database"""
        logger.debug(f"Storing query analysis for session {session_id}")
        
        try:
            from app.models.database.playground_analysis_models import PlaygroundQueryAnalysis
            from app.core.database import SessionLocal
            import uuid
            
            query_id = str(uuid.uuid4())
            
            with SessionLocal() as db_session:
                query_analysis = PlaygroundQueryAnalysis(
                    id=query_id,
                    session_id=session_id,
                    query_type=query_type,
                    original_query=query_text,
                    query_intent=analysis.get('query_intent', {}),
                    business_context=analysis.get('business_context', ''),
                    tables_involved=analysis.get('tables_involved', []),
                    columns_involved=analysis.get('columns_involved', []),
                    knowledge_extracted=analysis.get('knowledge_extracted', {}),
                    business_rules_discovered=analysis.get('business_rules_discovered', []),
                    patterns_identified=analysis.get('patterns_identified', []),
                    confidence_score=analysis.get('confidence_score', 0.0)
                )
                
                db_session.add(query_analysis)
                db_session.commit()
                
                logger.debug(f"Query analysis stored with ID: {query_id}")
                return query_id
                
        except Exception as e:
            logger.error(f"Failed to store query analysis: {str(e)}")
            raise
    
    def _extract_knowledge_from_analysis(self, session_id: str, analysis: Dict[str, Any], source: str) -> List[str]:
        """Extract and store knowledge entries from analysis"""
        logger.debug(f"Extracting knowledge entries from {source} analysis")
        
        try:
            from app.models.database.playground_analysis_models import PlaygroundKnowledgeBase
            from app.core.database import SessionLocal
            import uuid
            
            knowledge_entries = []
            
            with SessionLocal() as db_session:
                # Extract business rules
                for rule in analysis.get('business_rules_discovered', []):
                    if rule and rule.strip():
                        entry_id = str(uuid.uuid4())
                        knowledge_entry = PlaygroundKnowledgeBase(
                            id=entry_id,
                            session_id=session_id,
                            entry_type="business_rule",
                            title=f"Business Rule from {source}",
                            description=rule,
                            related_tables=analysis.get('tables_involved', []),
                            related_columns=analysis.get('columns_involved', []),
                            source=source,
                            confidence_score=analysis.get('confidence_score', 0.0)
                        )
                        db_session.add(knowledge_entry)
                        knowledge_entries.append(entry_id)
                
                # Extract patterns
                for pattern in analysis.get('patterns_identified', []):
                    if pattern and pattern.strip():
                        entry_id = str(uuid.uuid4())
                        knowledge_entry = PlaygroundKnowledgeBase(
                            id=entry_id,
                            session_id=session_id,
                            entry_type="pattern",
                            title=f"Pattern from {source}",
                            description=pattern,
                            related_tables=analysis.get('tables_involved', []),
                            related_columns=analysis.get('columns_involved', []),
                            source=source,
                            confidence_score=analysis.get('confidence_score', 0.0)
                        )
                        db_session.add(knowledge_entry)
                        knowledge_entries.append(entry_id)
                
                # Extract business context as knowledge
                business_context = analysis.get('business_context', '')
                if business_context and business_context.strip():
                    entry_id = str(uuid.uuid4())
                    knowledge_entry = PlaygroundKnowledgeBase(
                        id=entry_id,
                        session_id=session_id,
                        entry_type="context",
                        title=f"Business Context from {source}",
                        description=business_context,
                        related_tables=analysis.get('tables_involved', []),
                        related_columns=analysis.get('columns_involved', []),
                        source=source,
                        confidence_score=analysis.get('confidence_score', 0.0)
                    )
                    db_session.add(knowledge_entry)
                    knowledge_entries.append(entry_id)
                
                db_session.commit()
                
                logger.debug(f"Stored {len(knowledge_entries)} knowledge entries")
                return knowledge_entries
                
        except Exception as e:
            logger.error(f"Failed to extract knowledge entries: {str(e)}")
            return []
    
    def get_session_knowledge(self, session_id: str) -> Dict[str, Any]:
        """Retrieve all knowledge entries for a session"""
        logger.info(f"Retrieving knowledge entries for session {session_id}")
        
        try:
            from app.models.database.playground_analysis_models import (
                PlaygroundQueryAnalysis, PlaygroundKnowledgeBase
            )
            from app.core.database import SessionLocal
            
            with SessionLocal() as db_session:
                # Get query analyses
                queries = db_session.query(PlaygroundQueryAnalysis).filter(
                    PlaygroundQueryAnalysis.session_id == session_id
                ).all()
                
                # Get knowledge entries
                knowledge_entries = db_session.query(PlaygroundKnowledgeBase).filter(
                    PlaygroundKnowledgeBase.session_id == session_id
                ).all()
                
                # Format response
                knowledge_data = {
                    'queries_analyzed': len(queries),
                    'knowledge_entries': len(knowledge_entries),
                    'queries': [],
                    'business_rules': [],
                    'patterns': [],
                    'contexts': []
                }
                
                # Add query summaries
                for query in queries:
                    knowledge_data['queries'].append({
                        'id': str(query.id),
                        'type': query.query_type,
                        'query': query.original_query[:100] + "..." if len(query.original_query) > 100 else query.original_query,
                        'business_context': query.business_context,
                        'tables_involved': query.tables_involved,
                        'confidence_score': query.confidence_score
                    })
                
                # Categorize knowledge entries
                for entry in knowledge_entries:
                    entry_data = {
                        'id': str(entry.id),
                        'title': entry.title,
                        'description': entry.description,
                        'related_tables': entry.related_tables,
                        'source': entry.source,
                        'confidence_score': entry.confidence_score
                    }
                    
                    if entry.entry_type == 'business_rule':
                        knowledge_data['business_rules'].append(entry_data)
                    elif entry.entry_type == 'pattern':
                        knowledge_data['patterns'].append(entry_data)
                    elif entry.entry_type == 'context':
                        knowledge_data['contexts'].append(entry_data)
                
                logger.info(f"Retrieved knowledge data: {knowledge_data['queries_analyzed']} queries, {knowledge_data['knowledge_entries']} entries")
                return knowledge_data
                
        except Exception as e:
            logger.error(f"Failed to retrieve session knowledge: {str(e)}")
            return {}
    
    def store_in_vector_db(self, session_id: str, entry_id: str) -> bool:
        """Store knowledge entry in vector database for enhanced context"""
        logger.info(f"Storing knowledge entry {entry_id} in vector DB")
        
        try:
            # This would integrate with your existing vector storage system
            # For now, we'll just mark it as stored
            from app.models.database.playground_analysis_models import PlaygroundKnowledgeBase
            from app.core.database import SessionLocal
            
            with SessionLocal() as db_session:
                entry = db_session.query(PlaygroundKnowledgeBase).filter(
                    PlaygroundKnowledgeBase.id == entry_id
                ).first()
                
                if entry:
                    # TODO: Integrate with actual vector storage
                    entry.vector_id = f"vector_{entry_id}"
                    entry.embedding_stored = True
                    db_session.commit()
                    
                    logger.info(f"Knowledge entry {entry_id} marked as stored in vector DB")
                    return True
                else:
                    logger.warning(f"Knowledge entry {entry_id} not found")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to store in vector DB: {str(e)}")
            return False


def create_query_analyzer() -> QueryKnowledgeAnalyzer:
    """Factory function to create query analyzer instance"""
    logger.info("Creating QueryKnowledgeAnalyzer instance")
    return QueryKnowledgeAnalyzer()
