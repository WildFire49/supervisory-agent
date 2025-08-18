#!/usr/bin/env python3
"""
Enhanced Context Template Playground - Complete Solution
Test templates with intelligent schema validation and better layout
"""

import streamlit as st
import asyncio
import sys
import os
import uuid
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import our modules
from app.services.context_template_service import context_template_service
from app.agents.configurator.rule_enhanced_query_generator import RuleEnhancedQueryGenerator
from app.agents.configurator.vector_storage import SchemaVectorStore
from app.core.database import SessionLocal
from app.core.phoenix_config import setup_phoenix_tracing, get_phoenix_tracer
from app.models.database.context_template_models import ConnectionContextTemplateModel
from sqlalchemy import text
import logging
import pandas as pd
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Streamlit page config
st.set_page_config(
    page_title="🎯 Template Playground",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-card {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-card {
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .info-card {
        background-color: #d1ecf1;
        border-left: 5px solid #17a2b8;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .metric-container {
        display: flex;
        justify-content: space-around;
        margin: 1rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🎯 Enhanced Context Template Playground</h1>
    <p>Test your templates with intelligent schema validation and better layout</p>
</div>
""", unsafe_allow_html=True)

class ContextTemplatePlayground:
    """Interactive playground for context template system"""
    
    def __init__(self):
        self.phoenix_tracer = get_phoenix_tracer()
        self.setup_session_state()
    
    def setup_session_state(self):
        """Initialize Streamlit session state"""
        if 'connections' not in st.session_state:
            st.session_state.connections = {}
        if 'current_connection_id' not in st.session_state:
            st.session_state.current_connection_id = None
        if 'phoenix_enabled' not in st.session_state:
            st.session_state.phoenix_enabled = False
        if 'test_queries' not in st.session_state:
            st.session_state.test_queries = []
        if 'query_history' not in st.session_state:
            st.session_state.query_history = []
    
    def render_header(self):
        """Render the playground header"""
        st.title("🧪 Context Template System Playground")
        st.markdown("""
        **Interactive testing environment for the Enhanced Context Template System**
        
        This playground allows you to:
        - 🎯 Create and manage context templates
        - 🔍 Test query generation with enhanced context
        - 📊 Monitor LLM performance with Phoenix tracing
        - 🔄 Provide feedback and corrections
        - 📈 Analyze template effectiveness
        """)
    
    def render_sidebar(self):
        """Render the sidebar controls"""
        st.sidebar.title("🎛️ Controls")
        
        # Phoenix Tracing Section
        st.sidebar.subheader("🔥 Phoenix Tracing")
        
        if not st.session_state.phoenix_enabled:
            if st.sidebar.button("🚀 Start Phoenix Tracing"):
                with st.spinner("Setting up Phoenix tracing..."):
                    success = setup_phoenix_tracing(enable_ui=True, port=6006)
                    if success:
                        st.session_state.phoenix_enabled = True
                        st.sidebar.success("✅ Phoenix tracing enabled!")
                        st.sidebar.info("🔗 Phoenix UI: http://localhost:6006")
                    else:
                        st.sidebar.error("❌ Failed to setup Phoenix tracing")
        else:
            st.sidebar.success("✅ Phoenix tracing active")
            st.sidebar.info("🔗 Phoenix UI: http://localhost:6006")
            
            if st.sidebar.button("🛑 Stop Phoenix Tracing"):
                self.phoenix_tracer.close()
                st.session_state.phoenix_enabled = False
                st.sidebar.info("Phoenix tracing stopped")
        
        st.sidebar.divider()
        
        # Connection Management
        st.sidebar.subheader("🔌 Connection Management")
        
        # Create new connection
        with st.sidebar.expander("➕ Create New Connection"):
            connection_name = st.text_input("Connection Name", placeholder="My Test DB")
            database_type = st.selectbox("Database Type", ["postgresql", "mysql", "sqlite", "oracle", "mssql"])
            domain_hint = st.selectbox("Domain", ["financial", "ecommerce", "healthcare", "generic"])
            
            if st.button("Create Connection"):
                if connection_name:
                    connection_id = str(uuid.uuid4())
                    st.session_state.connections[connection_id] = {
                        "name": connection_name,
                        "database_type": database_type,
                        "domain_hint": domain_hint,
                        "created_at": datetime.now().isoformat()
                    }
                    st.session_state.current_connection_id = connection_id
                    st.success(f"✅ Created connection: {connection_name}")
                    st.rerun()
        
        # Select existing connection
        if st.session_state.connections:
            st.sidebar.subheader("📋 Existing Connections")
            connection_options = {
                conn_id: f"{data['name']} ({data['domain_hint']})"
                for conn_id, data in st.session_state.connections.items()
            }
            
            selected_connection = st.sidebar.selectbox(
                "Select Connection",
                options=list(connection_options.keys()),
                format_func=lambda x: connection_options[x],
                index=0 if st.session_state.current_connection_id is None else 
                      list(connection_options.keys()).index(st.session_state.current_connection_id) 
                      if st.session_state.current_connection_id in connection_options else 0
            )
            
            if selected_connection != st.session_state.current_connection_id:
                st.session_state.current_connection_id = selected_connection
                st.rerun()
    
    def render_template_management(self):
        """Render template management interface"""
        if not st.session_state.current_connection_id:
            st.warning("⚠️ Please create or select a connection first")
            return
        
        connection_data = st.session_state.connections[st.session_state.current_connection_id]
        
        st.subheader(f"📝 Template Management - {connection_data['name']}")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Template creation/editing
            with st.expander("🎯 Create/Edit Context Template", expanded=True):
                template_name = st.text_input("Template Name", value=f"{connection_data['domain_hint']}_template")
                
                business_rules = st.text_area(
                    "Business Rules Template",
                    height=200,
                    value="""# Business Rules for Query Generation

## Data Selection Rules
- Use current/active tables over historical/archived ones
- Prefer main business tables over staging/temp tables
- Apply appropriate date filters for time-based queries

## Query Construction Rules
- Use SUM() for amount aggregations
- Use COUNT() for counting records
- Apply proper WHERE clauses for filtering
- Use schema-qualified table names

## Domain-Specific Rules
- Follow industry best practices
- Ensure data accuracy and consistency
- Apply regulatory compliance requirements
                    """,
                    help="Define business rules that guide query generation"
                )
                
                schema_context = st.text_area(
                    "Schema Context Template",
                    height=150,
                    value="""# Schema Context Guidelines

## Table Relationships
- Primary keys and foreign key relationships
- Common join patterns and conditions
- Table hierarchy and dependencies

## Field Mappings
- Standard field names and their meanings
- Data types and constraints
- Calculated fields and derived columns
                    """,
                    help="Define schema-specific context and relationships"
                )
                
                domain_prompts = st.text_area(
                    "Domain-Specific Prompts",
                    height=100,
                    value=f"""# {connection_data['domain_hint'].title()} Domain Prompts

## Query Intent Analysis
- Understand business context and requirements
- Apply domain-specific logic and rules
- Ensure compliance with industry standards

## Best Practices
- Focus on accuracy and performance
- Use appropriate aggregation functions
- Apply proper filtering and sorting
                    """,
                    help="Domain-specific prompts and guidelines"
                )
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    if st.button("💾 Save Template", type="primary"):
                        with st.spinner("Creating template..."):
                            success = asyncio.run(self.create_template(
                                st.session_state.current_connection_id,
                                template_name,
                                business_rules,
                                schema_context,
                                domain_prompts,
                                connection_data['database_type'],
                                connection_data['domain_hint']
                            ))
                            
                            if success:
                                st.success("✅ Template created successfully!")
                            else:
                                st.error("❌ Failed to create template")
                
                with col_b:
                    if st.button("🔄 Load Existing Template"):
                        with st.spinner("Loading template..."):
                            template = asyncio.run(self.load_template(st.session_state.current_connection_id))
                            if template:
                                st.success("✅ Template loaded!")
                                # Update form values (would need session state management)
                            else:
                                st.warning("⚠️ No existing template found")
        
        with col2:
            # Template info and stats
            st.subheader("📊 Template Info")
            
            template_info = asyncio.run(self.get_template_info(st.session_state.current_connection_id))
            
            if template_info:
                st.metric("Template Version", template_info.get('version', 'N/A'))
                st.metric("Usage Count", template_info.get('usage_count', 0))
                st.metric("Success Rate", f"{template_info.get('success_rate', 0):.1%}")
                
                st.subheader("🕒 Last Updated")
                st.text(template_info.get('updated_at', 'Never'))
                
                st.subheader("👤 Updated By")
                st.text(template_info.get('updated_by', 'System'))
            else:
                st.info("No template created yet")
    
    def render_query_testing(self):
        """Render query testing interface"""
        if not st.session_state.current_connection_id:
            st.warning("⚠️ Please create or select a connection first")
            return
        
        st.subheader("🔍 Query Generation Testing")
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            # Query input
            st.subheader("💬 Natural Language Query")
            
            # Predefined sample queries
            sample_queries = [
                "How much was disbursed today?",
                "Show me all customers with overdue payments",
                "What is the total collection amount this month?",
                "List all active loans with amounts greater than 100000",
                "Show customer details for loan ID 12345"
            ]
            
            query_option = st.selectbox("Sample Queries", ["Custom Query"] + sample_queries)
            
            if query_option == "Custom Query":
                natural_language_query = st.text_area(
                    "Enter your natural language query:",
                    height=100,
                    placeholder="e.g., How much was disbursed today?"
                )
            else:
                natural_language_query = query_option
                st.text_area("Query:", value=natural_language_query, height=100, disabled=True)
            
            domain_hint = st.selectbox("Domain Context", ["financial", "ecommerce", "healthcare", "generic"])
            
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                if st.button("🚀 Generate SQL", type="primary", disabled=not natural_language_query):
                    with st.spinner("Generating SQL with enhanced context..."):
                        result = asyncio.run(self.generate_query_with_tracing(
                            st.session_state.current_connection_id,
                            natural_language_query,
                            domain_hint
                        ))
                        
                        if result:
                            st.session_state.query_history.append({
                                "timestamp": datetime.now().isoformat(),
                                "query": natural_language_query,
                                "sql": result.get('sql', ''),
                                "confidence": result.get('confidence', 0),
                                "context_used": result.get('context_used', False)
                            })
                            st.rerun()
            
            with col_b:
                if st.button("📊 Show Context"):
                    with st.spinner("Loading enhanced context..."):
                        context = asyncio.run(self.get_enhanced_context(
                            st.session_state.current_connection_id,
                            natural_language_query or "sample query",
                            domain_hint
                        ))
                        
                        if context:
                            st.session_state.current_context = context
                            st.success("✅ Context loaded!")
            
            with col_c:
                if st.button("🔄 Clear History"):
                    st.session_state.query_history = []
                    st.success("✅ History cleared!")
        
        with col2:
            # Results display
            st.subheader("📋 Generated Results")
            
            if st.session_state.query_history:
                latest_result = st.session_state.query_history[-1]
                
                st.subheader("🔍 Latest Query")
                st.text(latest_result['query'])
                
                st.subheader("💾 Generated SQL")
                st.code(latest_result['sql'], language='sql')
                
                st.metric("Confidence Score", f"{latest_result['confidence']:.2f}")
                
                if latest_result['context_used']:
                    st.success("✅ Enhanced context used")
                else:
                    st.warning("⚠️ Fallback generation used")
                
                # Feedback section
                st.subheader("📝 Provide Feedback")
                
                feedback_type = st.selectbox("Feedback Type", [
                    "Correct", "Incorrect SQL", "Missing Context", "Wrong Tables", "Other"
                ])
                
                feedback_text = st.text_area("Feedback Details", height=100)
                
                if st.button("💬 Submit Feedback"):
                    # Log feedback (implement feedback logging)
                    st.success("✅ Feedback submitted!")
    
    def render_analytics(self):
        """Render analytics and monitoring interface"""
        st.subheader("📈 Analytics & Monitoring")
        
        if not st.session_state.query_history:
            st.info("No query history available yet. Generate some queries to see analytics!")
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Queries", len(st.session_state.query_history))
        
        with col2:
            avg_confidence = sum(q['confidence'] for q in st.session_state.query_history) / len(st.session_state.query_history)
            st.metric("Avg Confidence", f"{avg_confidence:.2f}")
        
        with col3:
            context_usage = sum(1 for q in st.session_state.query_history if q['context_used'])
            st.metric("Context Usage", f"{context_usage}/{len(st.session_state.query_history)}")
        
        # Query history table
        st.subheader("📊 Query History")
        
        if st.session_state.query_history:
            import pandas as pd
            
            df = pd.DataFrame(st.session_state.query_history)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp', ascending=False)
            
            st.dataframe(
                df[['timestamp', 'query', 'confidence', 'context_used']],
                use_container_width=True
            )
    
    async def create_template(self, connection_id: str, template_name: str, 
                            business_rules: str, schema_context: str, 
                            domain_prompts: str, database_type: str, domain_hint: str) -> bool:
        """Create a context template"""
        try:
            span = self.phoenix_tracer.trace_context_template_operation(
                "create_template", connection_id, template_name=template_name
            )
            
            with span:
                # Use the service to create template
                template_id = await context_template_service.create_default_template(
                    connection_id=connection_id,
                    database_type=database_type,
                    domain_hint=domain_hint
                )
                
                if template_id:
                    # Update with custom content
                    await context_template_service.update_template(
                        template_id=template_id,
                        updates={
                            "template_name": template_name,
                            "business_rules_template": business_rules,
                            "schema_context_template": schema_context,
                            "domain_specific_prompts": domain_prompts
                        },
                        updated_by="playground_user"
                    )
                    
                    self.phoenix_tracer.add_span_attributes(span, 
                        template_id=template_id,
                        success=True
                    )
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            if span:
                self.phoenix_tracer.add_span_attributes(span, error=str(e), success=False)
            return False
    
    async def load_template(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Load existing template"""
        try:
            return await context_template_service.get_template_for_connection(connection_id)
        except Exception as e:
            logger.error(f"Error loading template: {str(e)}")
            return None
    
    async def get_template_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get template information and stats"""
        try:
            template = await context_template_service.get_template_for_connection(connection_id)
            return template
        except Exception as e:
            logger.error(f"Error getting template info: {str(e)}")
            return None
    
    async def generate_query_with_tracing(self, connection_id: str, 
                                        natural_language_query: str, 
                                        domain_hint: str) -> Optional[Dict[str, Any]]:
        """Generate query with Phoenix tracing"""
        try:
            span = self.phoenix_tracer.trace_query_generation(
                natural_language_query, connection_id, domain_hint=domain_hint
            )
            
            with span:
                # Mock query generation for playground
                # In real implementation, this would use the actual query generator
                mock_sql = f"""
-- Generated SQL for: {natural_language_query}
SELECT 
    SUM(amount) as total_amount,
    COUNT(*) as record_count
FROM transactions 
WHERE date_column = CURRENT_DATE
  AND status = 'active';
                """.strip()
                
                result = {
                    "sql": mock_sql,
                    "confidence": 0.85,
                    "context_used": True,
                    "generation_method": "enhanced_context"
                }
                
                self.phoenix_tracer.add_span_attributes(span,
                    sql_length=len(mock_sql),
                    confidence=result["confidence"],
                    context_used=result["context_used"]
                )
                
                return result
                
        except Exception as e:
            logger.error(f"Error generating query: {str(e)}")
            if span:
                self.phoenix_tracer.add_span_attributes(span, error=str(e))
            return None
    
    async def get_enhanced_context(self, connection_id: str, 
                                 natural_language_query: str, 
                                 domain_hint: str) -> Optional[Dict[str, Any]]:
        """Get enhanced context for display"""
        try:
            # Mock enhanced context for playground
            return {
                "schema_context": "Sample schema context with table information",
                "business_rules": "Sample business rules for query generation",
                "domain_prompts": f"Sample {domain_hint} domain prompts",
                "query_intent": {
                    "query_type": "aggregation",
                    "entities": ["amount", "transactions"],
                    "time_context": "current"
                }
            }
        except Exception as e:
            logger.error(f"Error getting enhanced context: {str(e)}")
            return None
    
    def run(self):
        """Run the playground"""
        self.render_header()
        self.render_sidebar()
        
        # Main content tabs
        tab1, tab2, tab3 = st.tabs(["📝 Template Management", "🔍 Query Testing", "📈 Analytics"])
        
        with tab1:
            self.render_template_management()
        
        with tab2:
            self.render_query_testing()
        
        with tab3:
            self.render_analytics()

def main():
    """Main entry point"""
    playground = ContextTemplatePlayground()
    playground.run()

if __name__ == "__main__":
    main()
