#!/usr/bin/env python3
"""
Enhanced Context Template Playground - Complete Solution
Better layout, schema validation, and intuitive results display
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
sys.path.append(str(Path(__file__).parent.parent))

# Page config
st.set_page_config(
    page_title="🎯 Template Playground",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling and layout
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
    .warning-card {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
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
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    .metric-card {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .results-container {
        background: #ffffff;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        padding-left: 20px;
        padding-right: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🎯 Enhanced Context Template Playground</h1>
    <p>Test your templates with intelligent schema validation and intuitive layout</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'templates_loaded' not in st.session_state:
    st.session_state.templates_loaded = False
if 'selected_connection' not in st.session_state:
    st.session_state.selected_connection = None
if 'templates' not in st.session_state:
    st.session_state.templates = []
if 'last_test_result' not in st.session_state:
    st.session_state.last_test_result = None

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
    """Create missing database tables"""
    imports = safe_import()
    if not imports['success']:
        return False, f"Import error: {imports['error']}"
    
    try:
        imports['Base'].metadata.create_all(bind=imports['engine'])
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
                    continue
            
            return template_data, None
            
    except Exception as e:
        return [], f"Database query error: {str(e)}"

def test_api_with_schema_validation(connection_id, question, domain_hint="financial"):
    """Test API endpoint with schema validation and better error reporting"""
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
                
                # Analyze the error for schema issues
                error_analysis = {}
                if not result.get('execution_success', False) and result.get('error_message'):
                    error_msg = result['error_message']
                    
                    if "does not exist" in error_msg:
                        error_analysis = {
                            'type': 'schema_mismatch',
                            'description': 'Column or table does not exist in database',
                            'suggestion': 'Update your template with correct column names',
                            'fix_needed': True
                        }
                        
                        # Extract the problematic column/table
                        if "column" in error_msg and "does not exist" in error_msg:
                            import re
                            match = re.search(r'column ([^\s]+) does not exist', error_msg)
                            if match:
                                error_analysis['problematic_column'] = match.group(1)
                    
                    elif "permission denied" in error_msg:
                        error_analysis = {
                            'type': 'permission_error',
                            'description': 'Database permission issue',
                            'suggestion': 'Check database connection credentials',
                            'fix_needed': False
                        }
                    
                    else:
                        error_analysis = {
                            'type': 'unknown_error',
                            'description': 'Unknown database error',
                            'suggestion': 'Check database connection and query syntax',
                            'fix_needed': False
                        }
                
                return {
                    'success': True,
                    'response': result,
                    'has_sql_error': not result.get('execution_success', False),
                    'error_message': result.get('error_message'),
                    'error_analysis': error_analysis,
                    'generated_sql': result.get('generated_sql'),
                    'execution_time': result.get('execution_time_ms', 0),
                    'row_count': result.get('row_count', 0)
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

# Main layout - using tabs for better organization
tab1, tab2, tab3 = st.tabs(["🎯 Template Testing", "📋 Template Management", "🔧 Setup & Debug"])

with tab1:
    # Template Testing - Main functionality
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📋 Select Template")
        
        # Load templates button
        if st.button("🔄 Load Templates", help="Refresh template list from database"):
            with st.spinner("Loading templates..."):
                templates, error = load_templates_safely()
                if error:
                    st.error(f"❌ {error}")
                    if "Import error" in error:
                        st.info("💡 **Tip:** Activate your virtual environment: `source venv/bin/activate`")
                else:
                    st.session_state.templates = templates
                    st.session_state.templates_loaded = True
                    st.success(f"✅ Loaded {len(templates)} templates")
        
        # Template selection
        if st.session_state.templates_loaded and st.session_state.templates:
            template_options = []
            for i, template in enumerate(st.session_state.templates):
                status = "🟢" if template['is_active'] else "🔴"
                enhanced = "⭐" if template['has_enhanced_content'] else "📝"
                template_options.append(f"{status} {template['template_name']} v{template['version']} {enhanced}")
            
            selected_idx = st.selectbox(
                "Choose Template:",
                range(len(template_options)),
                format_func=lambda x: template_options[x],
                help="Select a template to test queries against"
            )
            
            if selected_idx is not None:
                selected_template = st.session_state.templates[selected_idx]
                st.session_state.selected_connection = selected_template['connection_id']
                
                # Template info card
                st.markdown("### 📊 Template Info")
                
                # Metrics in a grid
                col1a, col1b = st.columns(2)
                with col1a:
                    st.metric("Usage Count", selected_template['usage_count'])
                    st.metric("Business Rules", f"{selected_template['business_rules_size']} chars")
                with col1b:
                    st.metric("Success Rate", f"{selected_template['success_rate']:.1%}")
                    st.metric("Schema Context", f"{selected_template['schema_context_size']} chars")
                
                if selected_template['has_enhanced_content']:
                    st.success("✅ Enhanced template")
                else:
                    st.warning("⚠️ Basic template")
        
        elif st.session_state.templates_loaded:
            st.warning("⚠️ No templates found")
        else:
            st.info("👆 Click 'Load Templates' to start")
    
    with col2:
        st.subheader("🧪 Query Testing")
        
        if st.session_state.selected_connection:
            # Question categories
            question_categories = {
                "📊 Collection Analysis": [
                    "How much EMI was collected today?",
                    "Which field officer has the highest collection percentage for this month?",
                    "Show me all customers who made payments in the last 7 days"
                ],
                "📈 Performance Reports": [
                    "What is the total outstanding amount across all loans?",
                    "Show me all overdue customers with more than 30 days past due",
                    "Which customers have the highest outstanding amounts?"
                ],
                "📋 Status Queries": [
                    "List all active loans with their current status",
                    "Show me loan disbursement summary for this month",
                    "Generate a collection performance report"
                ]
            }
            
            selected_category = st.selectbox("Question Category:", list(question_categories.keys()))
            selected_question = st.selectbox("Select Question:", question_categories[selected_category])
            
            # Custom question
            custom_question = st.text_area(
                "Or enter custom question:", 
                height=80,
                help="Enter your own natural language question"
            )
            
            question_to_test = custom_question.strip() if custom_question.strip() else selected_question
            
            # Domain context
            domain_hint = st.selectbox(
                "Domain Context:", 
                ["financial", "banking", "lending", "generic"],
                help="Choose domain for better query generation"
            )
            
            # Test button
            if st.button("🚀 Test Query", type="primary", help="Test the selected question"):
                with st.spinner("Testing query..."):
                    result = test_api_with_schema_validation(
                        st.session_state.selected_connection,
                        question_to_test,
                        domain_hint
                    )
                    st.session_state.last_test_result = result

# Results display in main area (below the testing interface)
if st.session_state.last_test_result:
    st.markdown("---")
    st.subheader("📊 Test Results")
    
    result = st.session_state.last_test_result
    
    if result['success']:
        response = result['response']
        
        # Status overview
        col_status1, col_status2, col_status3, col_status4 = st.columns(4)
        
        with col_status1:
            status_color = "🟢" if response.get('execution_success') else "🔴"
            st.metric("Status", f"{status_color} {response.get('status', 'unknown')}")
        
        with col_status2:
            st.metric("Execution Time", f"{result.get('execution_time', 0):.2f} ms")
        
        with col_status3:
            st.metric("Row Count", result.get('row_count', 0))
        
        with col_status4:
            success_icon = "✅" if response.get('execution_success') else "❌"
            st.metric("SQL Success", success_icon)
        
        # Error analysis if there's a SQL error
        if result.get('has_sql_error') and result.get('error_analysis'):
            error_analysis = result['error_analysis']
            
            if error_analysis['type'] == 'schema_mismatch':
                st.markdown("""
                <div class="error-card">
                    <h4>🔍 Schema Mismatch Detected</h4>
                    <p><strong>Issue:</strong> {}</p>
                    <p><strong>Suggestion:</strong> {}</p>
                </div>
                """.format(error_analysis['description'], error_analysis['suggestion']), unsafe_allow_html=True)
                
                if 'problematic_column' in error_analysis:
                    st.info(f"💡 **Problematic column:** `{error_analysis['problematic_column']}`")
                    st.info("**Fix:** Update your template's schema context with the correct column names from your actual database.")
            
            else:
                st.error(f"❌ {result.get('error_message', 'Unknown error')}")
        
        # Generated SQL display
        if result.get('generated_sql'):
            st.subheader("🔍 Generated SQL")
            st.code(result['generated_sql'], language='sql')
            
            # Schema validation hints
            if result.get('has_sql_error'):
                st.markdown("""
                <div class="">
                    <h4>🛠️ Schema Validation Tips</h4>
                    <ul>
                        <li>Check if all column names in the SQL exist in your actual database</li>
                        <li>Verify table relationships and foreign key columns</li>
                        <li>Update your template's schema context with correct column names</li>
                        <li>Test the SQL directly in your database to confirm the issue</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
        
        # Success case
        if not result.get('has_sql_error'):
            st.success("🎉 Query executed successfully! The enhanced context template is working correctly.")
    
    else:
        st.error(f"❌ {result['error']}")
        if result.get('suggestion'):
            st.info(f"💡 **Suggestion:** {result['suggestion']}")

with tab2:
    st.subheader("📋 Template Management")
    st.info("Template management features coming soon...")

with tab3:
    st.subheader("🔧 Setup & Debug")
    
    col_setup1, col_setup2 = st.columns(2)
    
    with col_setup1:
        st.markdown("### 📊 Database Setup")
        if st.button("🛠️ Create Missing Tables"):
            with st.spinner("Creating tables..."):
                success, message = create_missing_tables()
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
    
    with col_setup2:
        st.markdown("### 🔧 Troubleshooting")
        st.markdown("""
        **Common Issues:**
        - **Import Errors:** `source venv/bin/activate`
        - **No Templates:** Run configuration workflow
        - **API Connection:** `uvicorn app.main:app --reload`
        - **Schema Mismatch:** Update template column names
        """)

# Footer
st.markdown("---")
st.markdown("**🎯 Enhanced Context Template Playground** - One file, intuitive layout, comprehensive testing!")
