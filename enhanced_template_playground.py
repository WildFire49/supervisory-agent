#!/usr/bin/env python3
"""
Enhanced Context Template Playground with Template Loading and Version-Based Testing
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

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

try:
    from app.core.database import SessionLocal, engine, Base
    from app.models.database.context_template_models import ConnectionContextTemplateModel
    from app.models.database.business_rules_models import BusinessRuleModel, BusinessRuleTemplateModel
    from app.services.context_template_service import context_template_service
    from app.agents.configurator.rule_enhanced_query_generator import RuleEnhancedQueryGenerator
    from app.agents.configurator.vector_storage import SchemaVectorStore
    from app.core.config import settings
    import httpx
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error("Please make sure you're running from the correct virtual environment")
    st.stop()

# Page config
st.set_page_config(
    page_title="MiFiX.AI Configurator Playground",
    page_icon="🎯",
    layout="wide"
)

st.title("MiFiX.AI Configurator Playground")
st.markdown("**Test queries with specific template versions and see enhanced context in action**")

# Initialize session state
if 'selected_connection' not in st.session_state:
    st.session_state.selected_connection = None
if 'selected_template_version' not in st.session_state:
    st.session_state.selected_template_version = None

def create_missing_tables():
    """Create missing business rules tables if they don't exist"""
    try:
        # Import all models to ensure they're registered
        from app.models.database.business_rules_models import (
            BusinessRuleModel, BusinessRuleTemplateModel
        )
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        return True
    except Exception as e:
        st.error(f"Error creating tables: {e}")
        return False

def load_available_templates():
    """Load all available templates from database"""
    try:
        with SessionLocal() as session:
            templates = session.query(ConnectionContextTemplateModel).all()
            
            template_data = []
            for template in templates:
                template_data.append({
                    'id': str(template.id),
                    'connection_id': str(template.connection_id),
                    'template_name': template.template_name,
                    'version': template.template_version,
                    'is_active': template.is_active,
                    'created_at': template.created_at,
                    'usage_count': template.usage_count,
                    'success_rate': template.success_rate,
                    'business_rules_size': len(template.business_rules_template or ''),
                    'schema_context_size': len(template.schema_context_template or ''),
                    'domain_prompts_size': len(template.domain_specific_prompts or '')
                })
            
            return template_data
    except Exception as e:
        st.error(f"Error loading templates: {e}")
        return []

def get_template_details(template_id):
    """Get detailed template information"""
    try:
        with SessionLocal() as session:
            template = session.query(ConnectionContextTemplateModel).filter(
                ConnectionContextTemplateModel.id == template_id
            ).first()
            
            if template:
                return {
                    'id': str(template.id),
                    'connection_id': str(template.connection_id),
                    'template_name': template.template_name,
                    'version': template.template_version,
                    'business_rules': template.business_rules_template or '',
                    'schema_context': template.schema_context_template or '',
                    'domain_prompts': template.domain_specific_prompts or '',
                    'field_mappings': template.field_mappings or {},
                    'table_relationships': template.table_relationships or {},
                    'is_active': template.is_active,
                    'usage_count': template.usage_count,
                    'success_rate': template.success_rate,
                    'created_at': template.created_at
                }
            return None
    except Exception as e:
        st.error(f"Error getting template details: {e}")
        return None

async def test_query_with_template(connection_id, template_version, natural_language_question, domain_hint="financial"):
    """Test a query using a specific template version"""
    try:
        # Get enhanced context for the query
        enhanced_context = await context_template_service.get_enhanced_context_for_query(
            connection_id=connection_id,
            natural_language_question=natural_language_question,
            domain_hint=domain_hint
        )
        
        if not enhanced_context:
            return {
                'success': False,
                'error': 'No enhanced context found for this connection',
                'enhanced_context': None,
                'generated_sql': None
            }
        
        # Initialize query generator
        vector_store = SchemaVectorStore()
        from openai import OpenAI
        llm = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        query_generator = RuleEnhancedQueryGenerator(llm=llm, vector_store=vector_store)
        
        # Generate SQL using enhanced context
        test_query = await query_generator.convert_natural_language_to_sql(
            connection_id=connection_id,
            natural_language_question=natural_language_question,
            domain_hint=domain_hint
        )
        
        return {
            'success': True,
            'enhanced_context': enhanced_context,
            'generated_sql': test_query.sql_query if test_query else None,
            'query_intent': enhanced_context.get('query_intent', {}),
            'business_rules_applied': len(enhanced_context.get('business_rules', '')),
            'schema_context_size': len(enhanced_context.get('schema_context', '')),
            'domain_prompts_size': len(enhanced_context.get('domain_prompts', ''))
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'enhanced_context': None,
            'generated_sql': None
        }

def test_api_endpoint(connection_id, natural_language_question, domain_hint="financial"):
    """Test the API endpoint directly"""
    try:
        api_url = "http://localhost:8000/business-rules/natural-language-query"
        
        payload = {
            "connection_id": connection_id,
            "natural_language_question": natural_language_question,
            "domain_hint": domain_hint
        }
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(api_url, json=payload)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'response': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f"API returned {response.status_code}: {response.text}"
                }
                
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# Main UI
col1, col2 = st.columns([1, 2])

with col1:
    st.header("🔧 Setup")
    
    # Create missing tables button
    if st.button("🛠️ Create Missing Tables"):
        with st.spinner("Creating missing database tables..."):
            if create_missing_tables():
                st.success("✅ Tables created successfully!")
            else:
                st.error("❌ Failed to create tables")
    
    st.header("📋 Template Selection")
    
    # Load templates button
    if st.button("🔄 Load Templates"):
        st.session_state.templates = load_available_templates()
    
    # Display available templates
    if 'templates' in st.session_state and st.session_state.templates:
        st.success(f"✅ Found {len(st.session_state.templates)} templates")
        
        # Create template selection dataframe
        df = pd.DataFrame(st.session_state.templates)
        
        # Template selection
        selected_template = st.selectbox(
            "Select Template:",
            options=df.index,
            format_func=lambda x: f"{df.iloc[x]['template_name']} v{df.iloc[x]['version']} ({'Active' if df.iloc[x]['is_active'] else 'Inactive'})"
        )
        
        if selected_template is not None:
            template_info = df.iloc[selected_template]
            st.session_state.selected_connection = template_info['connection_id']
            st.session_state.selected_template_version = template_info['version']
            
            # Display template info
            st.info(f"""
            **Template Details:**
            - Name: {template_info['template_name']}
            - Version: {template_info['version']}
            - Connection: {template_info['connection_id'][:8]}...
            - Business Rules: {template_info['business_rules_size']} chars
            - Schema Context: {template_info['schema_context_size']} chars
            - Domain Prompts: {template_info['domain_prompts_size']} chars
            - Usage Count: {template_info['usage_count']}
            - Success Rate: {template_info['success_rate']:.1%}
            """)
    else:
        st.warning("⚠️ No templates found. Click 'Load Templates' to refresh.")

with col2:
    st.header("🧪 Query Testing")
    
    if st.session_state.selected_connection:
        st.success(f"✅ Using template version {st.session_state.selected_template_version}")
        
        # Query input
        test_questions = [
            "How much EMI was collected today?",
            "Which field officer has the highest collection percentage for this month?",
            "Show me all overdue customers with more than 30 days past due",
            "What is the total outstanding amount across all loans?",
            "List customers who made payments in the last 7 days"
        ]
        
        selected_question = st.selectbox("Select Test Question:", test_questions)
        custom_question = st.text_area("Or enter custom question:", height=100)
        
        question_to_test = custom_question.strip() if custom_question.strip() else selected_question
        
        domain_hint = st.selectbox("Domain Hint:", ["financial", "generic", "banking", "lending"])
        
        col2a, col2b = st.columns(2)
        
        with col2a:
            if st.button("🧠 Test Enhanced Context"):
                with st.spinner("Testing enhanced context generation..."):
                    result = asyncio.run(test_query_with_template(
                        st.session_state.selected_connection,
                        st.session_state.selected_template_version,
                        question_to_test,
                        domain_hint
                    ))
                    
                    if result['success']:
                        st.success("✅ Enhanced context generated successfully!")
                        
                        # Display results
                        st.subheader("📊 Query Analysis")
                        intent = result.get('query_intent', {})
                        st.json({
                            'query_type': intent.get('query_type', 'unknown'),
                            'entities': intent.get('entities', []),
                            'time_context': intent.get('time_context', 'current'),
                            'domain_context': intent.get('domain_context', domain_hint)
                        })
                        
                        st.subheader("📋 Context Applied")
                        st.metric("Business Rules", f"{result['business_rules_applied']} chars")
                        st.metric("Schema Context", f"{result['schema_context_size']} chars")
                        st.metric("Domain Prompts", f"{result['domain_prompts_size']} chars")
                        
                        if result['generated_sql']:
                            st.subheader("🔍 Generated SQL")
                            st.code(result['generated_sql'], language='sql')
                        
                    else:
                        st.error(f"❌ Error: {result['error']}")
        
        with col2b:
            if st.button("🌐 Test API Endpoint"):
                with st.spinner("Testing API endpoint..."):
                    result = test_api_endpoint(
                        st.session_state.selected_connection,
                        question_to_test,
                        domain_hint
                    )
                    
                    if result['success']:
                        st.success("✅ API call successful!")
                        response = result['response']
                        
                        # Display API response
                        st.subheader("📊 API Response")
                        st.json({
                            'status': response.get('status', 'unknown'),
                            'execution_success': response.get('execution_success', False),
                            'row_count': response.get('row_count', 0),
                            'execution_time_ms': response.get('execution_time_ms', 0)
                        })
                        
                        if response.get('generated_sql'):
                            st.subheader("🔍 Generated SQL")
                            st.code(response['generated_sql'], language='sql')
                        
                        if response.get('error_message'):
                            st.error(f"Database Error: {response['error_message']}")
                        
                    else:
                        st.error(f"❌ API Error: {result['error']}")
    else:
        st.warning("⚠️ Please select a template first")

# Template Details Section
if st.session_state.selected_connection:
    st.header("📄 Template Details")
    
    if st.button("🔍 View Template Content"):
        with st.spinner("Loading template details..."):
            # Find the selected template ID
            if 'templates' in st.session_state:
                df = pd.DataFrame(st.session_state.templates)
                selected_template_row = df[df['connection_id'] == st.session_state.selected_connection].iloc[0]
                template_details = get_template_details(selected_template_row['id'])
                
                if template_details:
                    tabs = st.tabs(["Business Rules", "Schema Context", "Domain Prompts", "Metadata"])
                    
                    with tabs[0]:
                        st.subheader("📋 Business Rules Template")
                        st.text_area("Business Rules:", template_details['business_rules'], height=300, disabled=True)
                    
                    with tabs[1]:
                        st.subheader("🗄️ Schema Context Template")
                        st.text_area("Schema Context:", template_details['schema_context'], height=300, disabled=True)
                    
                    with tabs[2]:
                        st.subheader("🎯 Domain-Specific Prompts")
                        st.text_area("Domain Prompts:", template_details['domain_prompts'], height=300, disabled=True)
                    
                    with tabs[3]:
                        st.subheader("📊 Template Metadata")
                        st.json({
                            'template_name': template_details['template_name'],
                            'version': template_details['version'],
                            'connection_id': template_details['connection_id'],
                            'is_active': template_details['is_active'],
                            'usage_count': template_details['usage_count'],
                            'success_rate': template_details['success_rate'],
                            'created_at': str(template_details['created_at'])
                        })

# Footer
st.markdown("---")
st.markdown("**Template Playground** - Test your templates with version-specific queries")
st.markdown("Make sure your FastAPI server is running on `http://localhost:8000` for API testing")
