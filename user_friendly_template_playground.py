#!/usr/bin/env python3
"""
User-Friendly Enhanced Context Template Playground
Beautiful layout with comprehensive error handling and schema validation
"""

import streamlit as st
import sys
import os
from pathlib import Path
import asyncio
import json
import pandas as pd
from datetime import datetime
import uuid
import traceback

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

# Page config
st.set_page_config(
    page_title="MiFiX.AI Retrieval Configuration",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        margin: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🎯 Enhanced Context Template Playground</h1>
    <p>Test your templates with intelligent error handling and schema validation</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'templates_loaded' not in st.session_state:
    st.session_state.templates_loaded = False
if 'selected_connection' not in st.session_state:
    st.session_state.selected_connection = None
if 'templates' not in st.session_state:
    st.session_state.templates = []

def safe_import():
    """Safely import required modules with error handling"""
    try:
        from app.core.database import SessionLocal, engine, Base
        from app.models.database.context_template_models import ConnectionContextTemplateModel
        from app.models.database.business_rules_models import BusinessRuleModel
        from app.services.context_template_service import context_template_service
        from app.agents.configurator.business_rules_persistence import BusinessRulesDatabase
        from app.agents.configurator.rule_enhanced_query_generator import RuleEnhancedQueryGenerator
        from app.agents.configurator.vector_storage import SchemaVectorStore
        from app.core.config import settings
        import httpx
        
        return {
            'SessionLocal': SessionLocal,
            'engine': engine,
            'Base': Base,
            'ConnectionContextTemplateModel': ConnectionContextTemplateModel,
            'BusinessRuleModel': BusinessRuleModel,
            'context_template_service': context_template_service,
            'BusinessRulesDatabase': BusinessRulesDatabase,
            'RuleEnhancedQueryGenerator': RuleEnhancedQueryGenerator,
            'SchemaVectorStore': SchemaVectorStore,
            'settings': settings,
            'httpx': httpx,
            'success': True,
            'error': None
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }

def create_missing_tables():
    """Create missing database tables with better error handling"""
    imports = safe_import()
    if not imports['success']:
        return False, f"Import error: {imports['error']}"
    
    try:
        # Create all tables
        imports['Base'].metadata.create_all(bind=imports['engine'])
        
        # Verify critical tables exist
        from sqlalchemy import inspect
        inspector = inspect(imports['engine'])
        existing_tables = inspector.get_table_names()
        
        required_tables = ['business_rules', 'connection_context_templates']
        missing_tables = [t for t in required_tables if t not in existing_tables]
        
        if missing_tables:
            return False, f"Missing tables: {missing_tables}"
        
        return True, "All tables created successfully"
        
    except Exception as e:
        return False, f"Database error: {str(e)}"

def load_templates_safely():
    """Load templates with comprehensive error handling"""
    imports = safe_import()
    if not imports['success']:
        return [], f"Import error: {imports['error']}"
    
    try:
        with imports['SessionLocal']() as session:
            templates = session.query(imports['ConnectionContextTemplateModel']).all()
            
            if not templates:
                return [], "No templates found in database"
            
            template_data = []
            for template in templates:
                try:
                    template_info = {
                        'id': str(template.id),
                        'connection_id': str(template.connection_id),
                        'template_name': template.template_name or 'Unnamed Template',
                        'version': template.template_version or '1.0',
                        'is_active': template.is_active,
                        'created_at': template.created_at,
                        'usage_count': template.usage_count or 0,
                        'success_rate': template.success_rate or 0.0,
                        'business_rules_size': len(template.business_rules_template or ''),
                        'schema_context_size': len(template.schema_context_template or ''),
                        'domain_prompts_size': len(template.domain_specific_prompts or ''),
                        'has_enhanced_content': bool(template.business_rules_template and template.schema_context_template)
                    }
                    template_data.append(template_info)
                except Exception as e:
                    st.warning(f"Error processing template {template.id}: {e}")
                    continue
            
            return template_data, None
            
    except Exception as e:
        return [], f"Database query error: {str(e)}"

def test_enhanced_context_safely(connection_id, question, domain_hint="financial"):
    """Test enhanced context with comprehensive error handling"""
    imports = safe_import()
    if not imports['success']:
        return {
            'success': False,
            'error': f"Import error: {imports['error']}",
            'error_type': 'import_error'
        }
    
    try:
        # Test context service
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        enhanced_context = loop.run_until_complete(
            imports['context_template_service'].get_enhanced_context_for_query(
                connection_id=connection_id,
                natural_language_question=question,
                domain_hint=domain_hint
            )
        )
        
        if not enhanced_context:
            return {
                'success': False,
                'error': 'No enhanced context found for this connection',
                'error_type': 'no_context',
                'suggestion': 'Check if template exists and is active for this connection'
            }
        
        # Initialize components with proper error handling
        try:
            vector_store = imports['SchemaVectorStore']()
            
            # Check if OpenAI API key is available
            if not hasattr(imports['settings'], 'OPENAI_API_KEY') or not imports['settings'].OPENAI_API_KEY:
                return {
                    'success': False,
                    'error': 'OpenAI API key not configured',
                    'error_type': 'config_error',
                    'suggestion': 'Set OPENAI_API_KEY in your environment variables'
                }
            
            from openai import OpenAI
            llm = OpenAI(api_key=imports['settings'].OPENAI_API_KEY)
            
            # Initialize business rules database
            rules_db = imports['BusinessRulesDatabase']()
            
            # Initialize query generator with all required parameters
            query_generator = imports['RuleEnhancedQueryGenerator'](
                llm=llm, 
                vector_store=vector_store,
                rules_db=rules_db  # This was missing!
            )
            
            # Generate SQL
            test_query = loop.run_until_complete(
                query_generator.convert_natural_language_to_sql(
                    connection_id=connection_id,
                    natural_language_question=question,
                    domain_hint=domain_hint
                )
            )
            
            return {
                'success': True,
                'enhanced_context': enhanced_context,
                'generated_sql': test_query.sql_query if test_query else None,
                'query_intent': enhanced_context.get('query_intent', {}),
                'context_stats': {
                    'business_rules_chars': len(enhanced_context.get('business_rules', '')),
                    'schema_context_chars': len(enhanced_context.get('schema_context', '')),
                    'domain_prompts_chars': len(enhanced_context.get('domain_prompts', '')),
                    'total_context_chars': sum([
                        len(enhanced_context.get('business_rules', '')),
                        len(enhanced_context.get('schema_context', '')),
                        len(enhanced_context.get('domain_prompts', ''))
                    ])
                }
            }
            
        except Exception as init_error:
            return {
                'success': False,
                'error': f'Component initialization error: {str(init_error)}',
                'error_type': 'initialization_error',
                'suggestion': 'Check database connection and API key configuration'
            }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Context generation error: {str(e)}',
            'error_type': 'generation_error',
            'traceback': traceback.format_exc()
        }

def test_api_safely(connection_id, question, domain_hint="financial"):
    """Test API endpoint with better error handling"""
    imports = safe_import()
    if not imports['success']:
        return {
            'success': False,
            'error': f"Import error: {imports['error']}",
            'error_type': 'import_error'
        }
    
    try:
        api_url = "http://localhost:8000/business-rules/natural-language-query"
        
        payload = {
            "connection_id": connection_id,
            "natural_language_question": question,
            "domain_hint": domain_hint
        }
        
        with imports['httpx'].Client(timeout=30.0) as client:
            response = client.post(api_url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'response': result,
                    'has_sql_error': not result.get('execution_success', False),
                    'error_message': result.get('error_message')
                }
            else:
                return {
                    'success': False,
                    'error': f"API returned {response.status_code}: {response.text}",
                    'error_type': 'api_error',
                    'suggestion': 'Make sure FastAPI server is running on localhost:8000'
                }
                
    except imports['httpx'].ConnectError:
        return {
            'success': False,
            'error': 'Cannot connect to API server',
            'error_type': 'connection_error',
            'suggestion': 'Start your FastAPI server: uvicorn app.main:app --reload'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'API test error: {str(e)}',
            'error_type': 'request_error'
        }

# Sidebar for setup and configuration
with st.sidebar:
    st.header("🔧 Setup & Configuration")
    
    # Database setup
    st.subheader("📊 Database Setup")
    if st.button("🛠️ Create Missing Tables", help="Create required database tables"):
        with st.spinner("Creating database tables..."):
            success, message = create_missing_tables()
            if success:
                st.success(f"✅ {message}")
            else:
                st.error(f"❌ {message}")
    
    # Template loading
    st.subheader("📋 Template Management")
    if st.button("🔄 Load Templates", help="Refresh template list from database"):
        with st.spinner("Loading templates from database..."):
            templates, error = load_templates_safely()
            if error:
                st.error(f"❌ {error}")
                st.session_state.templates = []
                st.session_state.templates_loaded = False
            else:
                st.session_state.templates = templates
                st.session_state.templates_loaded = True
                st.success(f"✅ Loaded {len(templates)} templates")
    
    # Connection info
    if st.session_state.selected_connection:
        st.subheader("🔗 Active Connection")
        st.info(f"Connection: {st.session_state.selected_connection[:8]}...")

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📋 Template Selection")
    
    if st.session_state.templates_loaded and st.session_state.templates:
        # Create a nice template selection interface
        st.success(f"Found {len(st.session_state.templates)} templates")
        
        # Template selection with enhanced display
        template_options = []
        for i, template in enumerate(st.session_state.templates):
            status = "🟢 Active" if template['is_active'] else "🔴 Inactive"
            enhanced = "⭐ Enhanced" if template['has_enhanced_content'] else "📝 Basic"
            template_options.append(f"{template['template_name']} v{template['version']} ({status}, {enhanced})")
        
        selected_idx = st.selectbox(
            "Choose Template:",
            range(len(template_options)),
            format_func=lambda x: template_options[x],
            help="Select a template to test queries against"
        )
        
        if selected_idx is not None:
            selected_template = st.session_state.templates[selected_idx]
            st.session_state.selected_connection = selected_template['connection_id']
            
            # Display template details in a nice card format
            st.markdown("### 📊 Template Details")
            
            col1a, col1b, col1c = st.columns(3)
            with col1a:
                st.metric("Usage Count", selected_template['usage_count'])
            with col1b:
                st.metric("Success Rate", f"{selected_template['success_rate']:.1%}")
            with col1c:
                st.metric("Version", selected_template['version'])
            
            # Content size metrics
            st.markdown("### 📝 Content Size")
            col1d, col1e, col1f = st.columns(3)
            with col1d:
                st.metric("Business Rules", f"{selected_template['business_rules_size']} chars")
            with col1e:
                st.metric("Schema Context", f"{selected_template['schema_context_size']} chars")
            with col1f:
                st.metric("Domain Prompts", f"{selected_template['domain_prompts_size']} chars")
            
            # Template status
            if selected_template['has_enhanced_content']:
                st.success("✅ This template has enhanced content")
            else:
                st.warning("⚠️ This template uses basic content")
    
    elif st.session_state.templates_loaded:
        st.warning("⚠️ No templates found. Create templates first.")
    else:
        st.info("👆 Click 'Load Templates' to get started")

with col2:
    st.header("🧪 Query Testing")
    
    if st.session_state.selected_connection:
        # Test questions with better categorization
        st.markdown("### 💬 Test Questions")
        
        question_categories = {
            "📊 Collection Queries": [
                "How much EMI was collected today?",
                "Which field officer has the highest collection percentage for this month?",
                "Show me all customers who made payments in the last 7 days"
            ],
            "📈 Analysis Queries": [
                "What is the total outstanding amount across all loans?",
                "Show me all overdue customers with more than 30 days past due",
                "Which customers have the highest outstanding amounts?"
            ],
            "📋 Reporting Queries": [
                "List all active loans with their current status",
                "Show me loan disbursement summary for this month",
                "Generate a collection performance report"
            ]
        }
        
        selected_category = st.selectbox("Question Category:", list(question_categories.keys()))
        selected_question = st.selectbox("Select Question:", question_categories[selected_category])
        
        # Custom question option
        custom_question = st.text_area(
            "Or enter custom question:", 
            height=100,
            help="Enter your own natural language question"
        )
        
        question_to_test = custom_question.strip() if custom_question.strip() else selected_question
        
        # Domain hint selection
        domain_hint = st.selectbox(
            "Domain Context:", 
            ["financial", "banking", "lending", "generic"],
            help="Choose the domain context for better query generation"
        )
        
        # Testing buttons
        st.markdown("### 🚀 Run Tests")
        
        col2a, col2b = st.columns(2)
        
        with col2a:
            if st.button("🧠 Test Enhanced Context", help="Test the enhanced context generation"):
                with st.spinner("Generating enhanced context..."):
                    result = test_enhanced_context_safely(
                        st.session_state.selected_connection,
                        question_to_test,
                        domain_hint
                    )
                    
                    if result['success']:
                        st.success("✅ Enhanced context generated successfully!")
                        
                        # Display results in expandable sections
                        with st.expander("📊 Query Analysis", expanded=True):
                            intent = result.get('query_intent', {})
                            col_intent1, col_intent2 = st.columns(2)
                            with col_intent1:
                                st.write("**Query Type:**", intent.get('query_type', 'unknown'))
                                st.write("**Time Context:**", intent.get('time_context', 'current'))
                            with col_intent2:
                                st.write("**Entities:**", ', '.join(intent.get('entities', [])))
                                st.write("**Domain:**", intent.get('domain_context', domain_hint))
                        
                        with st.expander("📈 Context Statistics", expanded=True):
                            stats = result['context_stats']
                            col_stats1, col_stats2 = st.columns(2)
                            with col_stats1:
                                st.metric("Business Rules", f"{stats['business_rules_chars']} chars")
                                st.metric("Schema Context", f"{stats['schema_context_chars']} chars")
                            with col_stats2:
                                st.metric("Domain Prompts", f"{stats['domain_prompts_chars']} chars")
                                st.metric("Total Context", f"{stats['total_context_chars']} chars")
                        
                        if result['generated_sql']:
                            with st.expander("🔍 Generated SQL", expanded=True):
                                st.code(result['generated_sql'], language='sql')
                        
                    else:
                        st.error(f"❌ {result['error']}")
                        if result.get('error_type') == 'config_error':
                            st.info(f"💡 **Suggestion:** {result.get('suggestion', '')}")
                        elif result.get('error_type') == 'no_context':
                            st.info(f"💡 **Suggestion:** {result.get('suggestion', '')}")
        
        with col2b:
            if st.button("🌐 Test API Endpoint", help="Test the actual API endpoint"):
                with st.spinner("Testing API endpoint..."):
                    result = test_api_safely(
                        st.session_state.selected_connection,
                        question_to_test,
                        domain_hint
                    )
                    
                    if result['success']:
                        response = result['response']
                        
                        if result.get('has_sql_error'):
                            st.warning("⚠️ API call successful but SQL execution failed")
                            
                            # Show the error in a nice format
                            with st.expander("❌ Database Error Details", expanded=True):
                                error_msg = result.get('error_message', 'Unknown error')
                                st.error(error_msg)
                                
                                # Provide helpful suggestions based on error type
                                if "does not exist" in error_msg:
                                    st.info("💡 **Suggestion:** The generated SQL references columns or tables that don't exist in your database. This indicates a schema mismatch.")
                                elif "permission denied" in error_msg:
                                    st.info("💡 **Suggestion:** Database permission issue. Check your connection credentials.")
                                else:
                                    st.info("💡 **Suggestion:** Check your database schema and template configuration.")
                        else:
                            st.success("✅ API call and SQL execution successful!")
                        
                        # Display API response details
                        with st.expander("📊 API Response Details", expanded=True):
                            col_api1, col_api2 = st.columns(2)
                            with col_api1:
                                st.metric("Status", response.get('status', 'unknown'))
                                st.metric("Execution Success", "✅" if response.get('execution_success') else "❌")
                            with col_api2:
                                st.metric("Row Count", response.get('row_count', 0))
                                st.metric("Execution Time", f"{response.get('execution_time_ms', 0):.2f} ms")
                        
                        if response.get('generated_sql'):
                            with st.expander("🔍 Generated SQL", expanded=True):
                                st.code(response['generated_sql'], language='sql')
                        
                    else:
                        st.error(f"❌ {result['error']}")
                        if result.get('suggestion'):
                            st.info(f"💡 **Suggestion:** {result['suggestion']}")
    else:
        st.info("👈 Please select a template first")

# Footer with helpful information
st.markdown("---")
st.markdown("""
### 🔧 Troubleshooting Guide

**Common Issues:**
- **Import Errors:** Make sure you're running from the correct virtual environment (`source venv/bin/activate`)
- **No Templates Found:** Run the configuration workflow first to create templates
- **API Connection Failed:** Start your FastAPI server (`uvicorn app.main:app --reload`)
- **Database Errors:** Check your PostgreSQL connection and run table creation
- **Schema Mismatches:** Update your templates to match your actual database schema

**Need Help?** Check the logs in your FastAPI server console for detailed error information.
""")

st.markdown("**🎯 Enhanced Context Template Playground** - Making template testing user-friendly!")
