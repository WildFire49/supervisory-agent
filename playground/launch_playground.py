#!/usr/bin/env python3
"""
Consolidated Template Playground - Production Grade UI
Main structure with incremental feature additions
"""

import importlib
import sys

# Auto-reload modules for development
if 'app.services.advanced_schema_analyzer' in sys.modules:
    importlib.reload(sys.modules['app.services.advanced_schema_analyzer'])
if 'app.services.smart_vector_strategy' in sys.modules:
    importlib.reload(sys.modules['app.services.smart_vector_strategy'])

import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
import uuid
import json
import asyncio
import time
from typing import Dict, List, Optional, Tuple, Any
import logging

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="MiFiX.AI Configurator",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark theme CSS styling with white tab backgrounds
st.markdown("""
<style>
    /* Dark theme base */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(102,126,234,0.3);
    }
    
    /* Dark theme cards */
    .success-card {
        background: linear-gradient(135deg, #1e3a2e 0%, #2d5a3d 100%);
        border-left: 5px solid #28a745;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(40,167,69,0.2);
        color: #d4edda;
    }
    .error-card {
        background: linear-gradient(135deg, #3a1e1e 0%, #5a2d2d 100%);
        border-left: 5px solid #dc3545;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(220,53,69,0.2);
        color: #f8d7da;
    }
    .warning-card {
        background: linear-gradient(135deg, #3a3a1e 0%, #5a5a2d 100%);
        border-left: 5px solid #ffc107;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(255,193,7,0.2);
        color: #fff3cd;
    }
    .info-card {
        background: linear-gradient(135deg, #1e2a3a 0%, #2d3d5a 100%);
        border-left: 5px solid #17a2b8;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(23,162,184,0.2);
        color: #d1ecf1;
    }
    
    /* Dark theme metric cards */
    .metric-card {
        background: linear-gradient(135deg, #262730 0%, #2f3349 100%);
        border: 1px solid #404040;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        transition: transform 0.2s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        color: #fafafa;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(102,126,234,0.2);
        border-color: #667eea;
    }
    
    /* Dark theme results container */
    .results-container {
        background: #1e1e1e;
        border: 1px solid #404040;
        border-radius: 12px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        color: #fafafa;
    }
    
    /* White tab backgrounds as requested */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #ffffff !important;
        padding: 0.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab"] {
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 600;
        color: #333333 !important;
        background: transparent;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: #667eea !important;
        color: white !important;
    }
    
    /* Template card styling */
    .template-card {
        background: #262730;
        border: 2px solid #404040;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
        color: #fafafa;
    }
    .template-card:hover {
        border-color: #667eea;
        box-shadow: 0 4px 20px rgba(102,126,234,0.2);
    }
    
    /* Query result grid */
    .query-result-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1.5rem;
        margin: 1rem 0;
    }
    @media (max-width: 768px) {
        .query-result-grid {
            grid-template-columns: 1fr;
        }
    }
    
    /* Dark theme for other elements */
    .stSelectbox > div > div {
        background-color: #262730;
        color: #fafafa;
    }
    .stTextArea > div > div > textarea {
        background-color: #262730;
        color: #fafafa;
        resize: vertical;
        line-height: 1.4;
    }
    /* Larger responsive textareas for templates */
    .large-textarea textarea {
        min-height: 40vh !important;
        resize: vertical;
        line-height: 1.4;
    }
    .medium-textarea textarea {
        min-height: 28vh !important;
        resize: vertical;
        line-height: 1.4;
    }
    @media (max-width: 768px) {
        .large-textarea textarea { min-height: 32vh !important; }
        .medium-textarea textarea { min-height: 24vh !important; }
    }
    .stButton > button {
        background-color: #667eea;
        color: white;
        border: none;
        border-radius: 8px;
    }
    .stButton > button:hover {
        background-color: #5a6fd8;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1> MiFiX.AI Configurator</h1>
    <p>Playground for template creation, editing, query testing, and schema validation</p>
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
if 'phoenix_enabled' not in st.session_state:
    st.session_state.phoenix_enabled = False
if 'api_server_status' not in st.session_state:
    st.session_state.api_server_status = None

def safe_import() -> Dict[str, Any]:
    """Safely import required modules with error handling"""
    import logging
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        import streamlit as st
        import pandas as pd
        import httpx
        import uuid
        from datetime import datetime, timezone
        
        logger.info("✅ Successfully imported core modules: streamlit, pandas, httpx, uuid, datetime")
        
        # Try to import database modules
        try:
            from app.models.database.context_template_models import ConnectionContextTemplateModel
            from app.models.database.business_rules_models import BusinessRuleModel
            from app.core.database import SessionLocal
            db_available = True
            logger.info("✅ Successfully imported database modules")
        except ImportError as e:
            db_available = False
            db_error = str(e)
            logger.error(f"❌ Database import failed: {db_error}")
        
        return {
            'success': True,
            'st': st,
            'pd': pd,
            'httpx': httpx,
            'uuid': uuid,
            'datetime': datetime,
            'timezone': timezone,
            'logger': logger,
            'db_available': db_available,
            'ConnectionContextTemplateModel': ConnectionContextTemplateModel if db_available else None,
            'BusinessRuleModel': BusinessRuleModel if db_available else None,
            'SessionLocal': SessionLocal if db_available else None,
            'db_error': db_error if not db_available else None
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }

def add_query_feedback_interface(result_data: Dict, question: str, connection_id: str):
    """Add user feedback interface for query corrections and template updates"""
    st.markdown("#### 🔧 Improve Query Results")
    st.markdown("Help improve future queries by providing corrections:")
    
    with st.expander("📝 Provide Query Corrections", expanded=False):
        feedback_form = st.form("query_feedback_form")
        
        with feedback_form:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Current Query:**")
                current_sql = result_data.get('generated_sql', '')
                st.code(current_sql, language='sql')
                
                # Correction type
                correction_type = st.selectbox(
                    "What needs to be corrected?",
                    [
                        "Wrong table name",
                        "Wrong column name", 
                        "Missing schema prefix",
                        "Wrong join logic",
                        "Incorrect filter conditions",
                        "Other schema issue"
                    ]
                )
            
            with col2:
                st.markdown("**Provide Corrections:**")
                
                # Specific corrections based on type
                if correction_type == "Wrong table name":
                    wrong_table = st.text_input("Wrong table name:", placeholder="e.g., disbursement_details_fed")
                    correct_table = st.text_input("Correct table name:", placeholder="e.g., staging_dashboard.fed_disbursement_details")
                    correction_details = f"Table: {wrong_table} → {correct_table}"
                    
                elif correction_type == "Wrong column name":
                    wrong_column = st.text_input("Wrong column name:", placeholder="e.g., sanctioned_amount")
                    correct_column = st.text_input("Correct column name:", placeholder="e.g., loan_amount")
                    correction_details = f"Column: {wrong_column} → {correct_column}"
                    
                elif correction_type == "Missing schema prefix":
                    table_name = st.text_input("Table name:", placeholder="e.g., fed_disbursement_details")
                    schema_prefix = st.text_input("Required schema:", placeholder="e.g., staging_dashboard")
                    correction_details = f"Schema: {table_name} → {schema_prefix}.{table_name}"
                    
                else:
                    correction_details = st.text_area(
                        "Describe the correction needed:",
                        placeholder="Explain what should be changed in the SQL or schema understanding...",
                        height=100
                    )
            
            # Additional context
            st.markdown("**Additional Context (Optional):**")
            additional_context = st.text_area(
                "Business rules or schema notes:",
                placeholder="e.g., 'Always use staging_dashboard schema for financial data' or 'disbursement_date should be used for time filters'",
                height=80
            )
            
            # Submit button
            submit_correction = st.form_submit_button("🚀 Update Template & Retry Query")
            
            if submit_correction and correction_details:
                with st.spinner("Logging correction and updating template..."):
                    # First log the correction properly
                    correction_logged = log_correction_to_service(
                        connection_id=connection_id,
                        question=question,
                        correction_type=correction_type,
                        correction_details=correction_details,
                        additional_context=additional_context,
                        original_sql=current_sql
                    )
                    
                    if correction_logged:
                        # Then update template
                        success, message = update_template_with_correction(
                            connection_id=connection_id,
                            question=question,
                            correction_type=correction_type,
                            correction_details=correction_details,
                            additional_context=additional_context,
                            original_sql=current_sql
                        )
                    else:
                        success, message = False, "Failed to log correction"
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.info("🔄 Template updated! Try your query again to see improvements.")
                        # Refresh templates
                        st.session_state.templates_loaded = False
                    else:
                        st.error(f"❌ {message}")

def log_correction_to_service(
    connection_id: str,
    question: str,
    correction_type: str,
    correction_details: str,
    additional_context: str,
    original_sql: str
) -> bool:
    """Log correction to the proper service layer before template update"""
    imports = safe_import()
    if not imports['success']:
        return False
    
    logger = imports['logger']
    
    try:
        # Import the service
        from app.services.context_template_service import ContextTemplateService
        import asyncio
        
        service = ContextTemplateService()
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        correction_id = loop.run_until_complete(
            service.log_query_correction(
                connection_id=connection_id,
                natural_language_question=question,
                generated_sql_original=original_sql,
                execution_success_original=False,  # Assuming failed if correcting
                error_message_original="User provided correction",
                user_feedback=correction_details,
                correction_type=correction_type,
                additional_context=additional_context,
                corrected_by="user"
            )
        )
        
        loop.close()
        
        if correction_id:
            logger.info(f"✅ Logged correction with ID: {correction_id}")
            return True
        else:
            logger.error("❌ Failed to log correction - no ID returned")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error logging correction: {str(e)}")
        return False

def update_template_with_correction(
    connection_id: str,
    question: str, 
    correction_type: str,
    correction_details: str,
    additional_context: str,
    original_sql: str
) -> Tuple[bool, str]:
    """Update template with user corrections and increment version"""
    imports = safe_import()
    if not imports['success']:
        return False, f"Import error: {imports['error']}"
    
    logger = imports['logger']
    
    try:
        logger.info(f"🔧 Updating template with user correction...")
        logger.info(f"   Connection: {connection_id}")
        logger.info(f"   Correction: {correction_type} - {correction_details}")
        
        if not imports['db_available']:
            return False, f"Database not available: {imports['db_error']}"
        
        with imports['SessionLocal']() as session:
            # Get current template
            template = session.query(imports['ConnectionContextTemplateModel']).filter_by(
                connection_id=connection_id
            ).order_by(imports['ConnectionContextTemplateModel'].created_at.desc()).first()
            
            if not template:
                return False, f"No template found for connection {connection_id}"
            
            # Parse current version and increment
            current_version = template.template_version or "1.0.0"
            version_parts = current_version.split('.')
            if len(version_parts) >= 3:
                patch_version = int(version_parts[2]) + 1
                new_version = f"{version_parts[0]}.{version_parts[1]}.{patch_version}"
            else:
                new_version = "1.0.1"
            
            # Create correction entry
            correction_entry = f"""
=== USER CORRECTION ({imports['datetime'].now().strftime('%Y-%m-%d %H:%M:%S')}) ===
Question: {question}
Correction Type: {correction_type}
Correction: {correction_details}
Original SQL: {original_sql}
Additional Context: {additional_context}
"""
            
            # Update template content
            updated_business_rules = (template.business_rules_template or "") + correction_entry
            updated_schema_context = (template.schema_context_template or "") + f"\n\nCORRECTION: {correction_details}"
            
            # Extract base template name (remove any existing version info)
            base_name = template.template_name
            if " (v" in base_name:
                base_name = base_name.split(" (v")[0]
            
            # Create new template version
            new_template = imports['ConnectionContextTemplateModel'](
                id=str(imports['uuid'].uuid4()),
                connection_id=connection_id,
                template_name=base_name,  # Keep base name clean
                template_version=new_version,
                business_rules_template=updated_business_rules,
                schema_context_template=updated_schema_context,
                domain_specific_prompts=template.domain_specific_prompts,
                is_active=True,
                created_at=imports['datetime'].utcnow()
            )
            
            # Deactivate old template
            template.is_active = False
            
            session.add(new_template)
            session.commit()
            
            logger.info(f"✅ Created new template version {new_version}")
            
            # Re-embed in vector DB
            try:
                from app.agents.configurator.vector_storage import SchemaVectorStore
                vector_store = SchemaVectorStore()
                
                # Create updated context for embedding
                updated_context = f"""
Connection: {connection_id}
Template Version: {new_version}
Business Rules: {updated_business_rules}
Schema Context: {updated_schema_context}
Domain: {template.domain_specific_prompts or ''}
Corrections Applied: {correction_details}
"""
                
                # Store in vector DB (this would need the proper schema object)
                logger.info(f"📊 Re-embedding updated template in vector DB...")
                # Note: This would need proper implementation with schema object
                
            except Exception as e:
                logger.warning(f"⚠️ Vector DB re-embedding failed: {str(e)}")
            
            return True, f"Template updated to version {new_version} with corrections"
                
    except Exception as e:
        logger.error(f"💥 Error updating template: {str(e)}")
        import traceback
        logger.error(f"📚 Full traceback: {traceback.format_exc()}")
        return False, f"Error: {str(e)}"

def fix_connection_id_mismatch(old_connection_id: str, new_connection_id: str) -> Tuple[bool, str]:
    """Fix connection ID mismatch between templates and database connections"""
    imports = safe_import()
    if not imports['success']:
        return False, f"Import error: {imports['error']}"
    
    logger = imports['logger']
    
    try:
        logger.info(f"🔧 Fixing connection ID mismatch...")
        logger.info(f"   Old (template): {old_connection_id}")
        logger.info(f"   New (database): {new_connection_id}")
        
        if not imports['db_available']:
            return False, f"Database not available: {imports['db_error']}"
        
        with imports['SessionLocal']() as session:
            # Update connection_context_templates
            templates_updated = session.query(imports['ConnectionContextTemplateModel']).filter(
                imports['ConnectionContextTemplateModel'].connection_id == old_connection_id
            ).update({
                imports['ConnectionContextTemplateModel'].connection_id: new_connection_id
            })
            
            # Update business_context_analysis if the model exists
            context_updated = 0
            try:
                from app.models.database.business_context_analysis_models import BusinessContextAnalysisModel
                context_updated = session.query(BusinessContextAnalysisModel).filter(
                    BusinessContextAnalysisModel.connection_id == old_connection_id
                ).update({
                    BusinessContextAnalysisModel.connection_id: new_connection_id
                })
            except ImportError:
                logger.info("BusinessContextAnalysisModel not found, skipping...")
            
            session.commit()
            
            logger.info(f"✅ Updated {templates_updated} templates")
            logger.info(f"✅ Updated {context_updated} business context records")
            
            return True, f"Fixed connection ID mismatch: {templates_updated} templates, {context_updated} contexts updated"
                
    except Exception as e:
        logger.error(f"💥 Error fixing connection ID mismatch: {str(e)}")
        import traceback
        logger.error(f"📚 Full traceback: {traceback.format_exc()}")
        return False, f"Error: {str(e)}"

def populate_business_rules_from_template(template_id: str, connection_id: str) -> Tuple[bool, str]:
    """Populate business rules from template context if missing"""
    imports = safe_import()
    if not imports['success']:
        return False, f"Import error: {imports['error']}"
    
    logger = imports['logger']
    
    try:
        logger.info(f"🚀 Populating business rules from template {template_id}...")
        
        if not imports['db_available']:
            return False, f"Database not available: {imports['db_error']}"
        
        with imports['SessionLocal']() as session:
            # Get the template
            template = session.query(imports['ConnectionContextTemplateModel']).filter_by(id=template_id).first()
            
            if not template:
                return False, f"Template {template_id} not found"
            
            # Check if business rules already exist for this connection
            from app.models.database.business_rules_models import BusinessRuleModel
            existing_rules = session.query(BusinessRuleModel).filter_by(connection_id=connection_id).count()
            
            if existing_rules > 0:
                logger.info(f"✅ Business rules already exist for connection {connection_id}")
                return True, f"Found {existing_rules} existing business rules"
            
            # Create basic business rules from template context
            if template.business_rules_template:
                rule = BusinessRuleModel(
                    rule_id=str(imports['uuid'].uuid4()),
                    connection_id=imports['uuid'].UUID(connection_id),
                    category="template_context",
                    severity="warning",
                    title="Template Business Rules",
                    description="Business rules extracted from template context",
                    trigger_patterns=["disbursement", "collection", "loan", "payment"],
                    table_patterns=[],
                    column_patterns=[],
                    allowed_tables=[],
                    forbidden_tables=[],
                    required_joins=[],
                    date_field_mappings={},
                    sql_transformations=[],
                    confidence_score=0.8,
                    positive_examples=[],
                    negative_examples=[]
                )
                
                session.add(rule)
                session.commit()
                
                logger.info(f"✅ Created business rule from template context")
                return True, "Business rules populated from template"
            else:
                return False, "No business rules context found in template"
                
    except Exception as e:
        logger.error(f"💥 Error populating business rules: {str(e)}")
        import traceback
        logger.error(f"📚 Full traceback: {traceback.format_exc()}")
        return False, f"Error: {str(e)}"

def get_available_connections(user_id: str = "vaishakh_configurator") -> Tuple[List[Dict], Optional[str]]:
    """Get available database connections from the configurator API"""
    imports = safe_import()
    if not imports['success']:
        return [], f"Import error: {imports['error']}"
    
    logger = imports['logger']
    
    try:
        logger.info(f"🔄 Loading available database connections for user: {user_id}")
        
        with imports['httpx'].Client(timeout=30.0) as client:
            # Add user_id as query parameter
            response = client.get(f"http://localhost:8000/configurator/connections?user_id={user_id}")
            
            logger.info(f"📡 Connections API response status: {response.status_code}")
            
            if response.status_code == 200:
                connections = response.json()
                logger.info(f"✅ Found {len(connections)} database connections for user {user_id}")
                return connections, None
            else:
                logger.warning(f"⚠️ API error: {response.status_code} - {response.text}")
                logger.info("🔄 Falling back to direct database access...")
                
                # Fallback to direct database access
                try:
                    from app.agents.configurator.database_persistence import ConfiguratorDatabase
                    import asyncio
                    
                    configurator_db = ConfiguratorDatabase()
                    connections_data = asyncio.run(configurator_db.list_user_connections(user_id))
                    
                    # Convert to API format
                    connections = [
                        {
                            'id': str(conn.id),
                            'name': conn.name,
                            'database_type': conn.database_type,
                            'host': conn.host,
                            'port': conn.port,
                            'database_name': conn.database_name,
                            'is_active': conn.is_active,
                            'created_at': conn.created_at.isoformat() if conn.created_at else ""
                        }
                        for conn in connections_data
                    ]
                    
                    logger.info(f"✅ Direct database access found {len(connections)} connections")
                    return connections, None
                    
                except Exception as db_error:
                    error_msg = f"Both API and direct database access failed. API: {response.status_code} - {response.text}, DB: {str(db_error)}"
                    logger.error(f"❌ {error_msg}")
                    return [], error_msg
                
    except imports['httpx'].ConnectError as e:
        error_msg = "Cannot connect to API server. Make sure it's running on localhost:8000"
        logger.error(f"🌐 Connection error: {str(e)}")
        return [], error_msg
    except Exception as e:
        error_msg = f"Connection loading error: {str(e)}"
        logger.error(f"💥 {error_msg}")
        import traceback
        logger.error(f"📚 Full traceback: {traceback.format_exc()}")
        return [], error_msg

def load_templates_safely() -> Tuple[List[Dict], Optional[str]]:
    """Load templates with comprehensive error handling and metrics from connection_context_templates table"""
    imports = safe_import()
    if not imports['success']:
        return [], f"Import error: {imports['error']}"
    
    logger = imports['logger']
    
    try:
        logger.info("🔄 Loading templates from connection_context_templates table...")
        
        if not imports['db_available']:
            return [], f"Database not available: {imports['db_error']}"
        
        with imports['SessionLocal']() as session:
            templates = session.query(imports['ConnectionContextTemplateModel']).order_by(
                imports['ConnectionContextTemplateModel'].created_at.desc()
            ).all()
            
            logger.info(f"📡 Found {len(templates)} templates in database")
            
            if not templates:
                return [], "No templates found in connection_context_templates table"
            
            template_data = []
            for template in templates:
                try:
                    # Handle datetime conversion safely
                    created_at = template.created_at
                    if isinstance(created_at, str):
                        try:
                            from datetime import datetime
                            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        except:
                            created_at = None
                    
                    template_info = {
                        'id': str(template.id),
                        'connection_id': str(template.connection_id),
                        'template_name': template.template_name or 'Unnamed Template',
                        'version': template.template_version or '1.0',
                        'is_active': template.is_active,
                        'created_at': created_at,
                        'usage_count': template.usage_count or 0,
                        'success_rate': getattr(template, 'success_rate', 0.0),
                        'business_rules_size': len(template.business_rules_template or ''),
                        'schema_context_size': len(template.schema_context_template or ''),
                        'domain_prompts_size': len(template.domain_specific_prompts or ''),
                        'has_enhanced_content': bool(template.business_rules_template and template.schema_context_template),
                        'business_rules_template': template.business_rules_template,
                        'schema_context_template': template.schema_context_template,
                        'domain_specific_prompts': template.domain_specific_prompts,
                        'database_type': getattr(template, 'database_type', 'postgresql'),
                        'domain_hint': getattr(template, 'domain_hint', 'financial'),
                        # Extract metadata if available
                        'selected_columns': [],
                        'schema_metadata': {}
                    }
                    
                    # Try to extract selected columns and schema metadata from table relationships or field mappings
                    if hasattr(template, 'table_relationships') and template.table_relationships:
                        template_info['schema_metadata'] = template.table_relationships
                    
                    if hasattr(template, 'field_mappings') and template.field_mappings:
                        # Extract selected columns from field mappings if available
                        if isinstance(template.field_mappings, dict):
                            template_info['selected_columns'] = list(template.field_mappings.keys())
                    
                    template_data.append(template_info)
                    logger.info(f"📋 Processed template: {template_info['template_name']} (ID: {template_info['id']})")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error processing template {template.id}: {e}")
                    continue
            
            logger.info(f"✅ Successfully loaded {len(template_data)} templates from database")
            return template_data, None
            
    except Exception as e:
        error_msg = f"Database query error: {str(e)}"
        logger.error(f"💥 {error_msg}")
        import traceback
        logger.error(f"📚 Full traceback: {traceback.format_exc()}")
        return [], error_msg

def create_missing_tables() -> Tuple[bool, str]:
    """Create missing database tables"""
    imports = safe_import()
    if not imports['success']:
        return False, f"Import error: {imports['error']}"
    
    try:
        imports['Base'].metadata.create_all(bind=imports['engine'])
        return True, "All tables created successfully"
    except Exception as e:
        return False, f"Database error: {str(e)}"

def test_api_with_enhanced_validation(connection_id: str, question: str, domain_hint: str = "financial") -> Dict[str, Any]:
    """Test API endpoint with enhanced schema validation and error reporting"""
    imports = safe_import()
    if not imports['success']:
        return {
            'success': False,
            'error': f"Import error: {imports['error']}",
            'error_type': 'import_error'
        }
    
    logger = imports['logger']
    
    try:
        api_url = "http://localhost:8000/business-rules/natural-language-query"
        
        payload = {
            "connection_id": connection_id,
            "natural_language_question": question,
            "domain_hint": domain_hint
        }
        
        logger.info(f"🚀 Starting natural language query processing...")
        logger.info(f"🔗 Connection ID: {connection_id}")
        logger.info(f"❓ Question: {question}")
        logger.info(f"🌐 Domain hint: {domain_hint}")
        logger.info(f"📡 API URL: {api_url}")
        logger.info(f"📦 Payload: {payload}")
        
        with imports['httpx'].Client(timeout=30.0) as client:
            logger.info(f"📞 Making API call...")
            response = client.post(api_url, json=payload)
            
            logger.info(f"📡 API Response status: {response.status_code}")
            logger.info(f"📝 API Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ API Response body: {result}")
                
                # Enhanced error analysis
                error_analysis = {}
                if not result.get('execution_success', False) and result.get('error_message'):
                    error_msg = result['error_message']
                    
                    if "does not exist" in error_msg:
                        error_analysis = {
                            'type': 'schema_mismatch',
                            'description': 'Column or table does not exist in database',
                            'suggestion': 'Update your template with correct column names from actual database schema',
                            'fix_needed': True,
                            'severity': 'high'
                        }
                        
                        # Extract problematic elements
                        import re
                        if "column" in error_msg:
                            match = re.search(r'column ([^\s]+) does not exist', error_msg)
                            if match:
                                error_analysis['problematic_column'] = match.group(1)
                        elif "table" in error_msg:
                            match = re.search(r'table "([^"]+)" does not exist', error_msg)
                            if match:
                                error_analysis['problematic_table'] = match.group(1)
                    
                    elif "permission denied" in error_msg:
                        error_analysis = {
                            'type': 'permission_error',
                            'description': 'Database permission issue',
                            'suggestion': 'Check database connection credentials and user permissions',
                            'fix_needed': False,
                            'severity': 'medium'
                        }
                    
                    elif "syntax error" in error_msg:
                        error_analysis = {
                            'type': 'sql_syntax_error',
                            'description': 'Generated SQL has syntax errors',
                            'suggestion': 'Review template business rules and schema context for accuracy',
                            'fix_needed': True,
                            'severity': 'high'
                        }
                    
                    else:
                        error_analysis = {
                            'type': 'unknown_error',
                            'description': 'Unknown database error',
                            'suggestion': 'Check database connection and query syntax',
                            'fix_needed': False,
                            'severity': 'medium'
                        }
                
                return {
                    'success': True,
                    'response': result,
                    'has_sql_error': not result.get('execution_success', False),
                    'error_message': result.get('error_message'),
                    'error_analysis': error_analysis,
                    'generated_sql': result.get('generated_sql'),
                    'execution_time': result.get('execution_time_ms', 0),
                    'row_count': result.get('row_count', 0),
                    'query_results': result.get('query_results', []),
                    'confidence_score': result.get('confidence_score', 0.0)
                }
            else:
                error_text = response.text
                logger.error(f"❌ API Error {response.status_code}: {error_text}")
                try:
                    error_json = response.json()
                    logger.error(f"📝 Error JSON: {error_json}")
                except:
                    logger.error(f"📝 Raw error text: {error_text}")
                
                return {
                    'success': False,
                    'error': f"API returned status {response.status_code}: {error_text}",
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

def check_api_server_status() -> Dict[str, Any]:
    """Check if the FastAPI server is running"""
    imports = safe_import()
    if not imports['success']:
        return {'status': 'error', 'message': f"Import error: {imports['error']}"}
    
    try:
        with imports['httpx'].Client(timeout=5.0) as client:
            response = client.get("http://localhost:8000/health")
            if response.status_code == 200:
                return {'status': 'running', 'message': 'API server is running', 'details': response.json()}
            else:
                return {'status': 'error', 'message': f'Server returned {response.status_code}'}
    except imports['httpx'].ConnectError:
        return {'status': 'offline', 'message': 'API server is not running'}
    except Exception as e:
        return {'status': 'error', 'message': f'Connection error: {str(e)}'}

def check_database_connection() -> Dict[str, Any]:
    """Check database connection status"""
    imports = safe_import()
    if not imports['success']:
        return {'status': 'error', 'message': f"Import error: {imports['error']}"}
    
    try:
        with imports['SessionLocal']() as session:
            # Simple query to test connection
            result = session.execute(imports['text']('SELECT 1'))
            result.fetchone()
            return {'status': 'connected', 'message': 'Database connection successful'}
    except Exception as e:
        return {'status': 'error', 'message': f'Database connection failed: {str(e)}'}

def setup_phoenix_tracing() -> Dict[str, Any]:
    """Setup Phoenix tracing for LLM observability"""
    try:
        import phoenix as px
        from openinference.instrumentation.openai import OpenAIInstrumentor
        from openinference.instrumentation.langchain import LangChainInstrumentor
        
        # Check if Phoenix is already running
        try:
            import requests
            response = requests.get("http://localhost:6006", timeout=2)
            if response.status_code == 200:
                return {'status': 'running', 'message': 'Phoenix is already running', 'url': 'http://localhost:6006'}
        except:
            pass
        
        # Start Phoenix session
        session = px.launch_app()
        
        # Setup instrumentors
        OpenAIInstrumentor().instrument()
        LangChainInstrumentor().instrument()
        
        return {
            'status': 'started', 
            'message': 'Phoenix tracing started successfully',
            'url': 'http://localhost:6006'
        }
    except ImportError:
        return {
            'status': 'missing', 
            'message': 'Phoenix not installed. Install with: pip install arize-phoenix'
        }
    except Exception as e:
        return {
            'status': 'error', 
            'message': f'Phoenix setup failed: {str(e)}'
        }

def create_new_template(connection_id: str, template_data: Dict[str, Any]) -> Tuple[bool, str]:
    """Create a new template in the database"""
    imports = safe_import()
    if not imports['success']:
        return False, f"Import error: {imports['error']}"
    
    try:
        with imports['SessionLocal']() as session:
            new_template = imports['ConnectionContextTemplateModel'](
                id=uuid.uuid4(),
                connection_id=uuid.UUID(connection_id),
                template_name=template_data['template_name'],
                template_version=template_data['version'],
                database_type=template_data.get('database_type', 'postgresql'),
                domain_hint=template_data.get('domain_hint', 'financial'),
                business_rules_template=template_data['business_rules'],
                schema_context_template=template_data['schema_context'],
                domain_specific_prompts=template_data['domain_prompts'],
                is_active=True,
                created_at=datetime.now(timezone.utc),
                usage_count=0,
                success_rate=0.0
            )
            
            session.add(new_template)
            session.commit()
            
            return True, f"Template '{template_data['template_name']}' created successfully"
            
    except Exception as e:
        return False, f"Error creating template: {str(e)}"

def update_template(template_id: str, template_data: Dict[str, Any]) -> Tuple[bool, str]:
    """Update an existing template in the database"""
    imports = safe_import()
    if not imports['success']:
        return False, f"Import error: {imports['error']}"
    
    try:
        with imports['SessionLocal']() as session:
            template = session.query(imports['ConnectionContextTemplateModel']).filter(
                imports['ConnectionContextTemplateModel'].id == uuid.UUID(template_id)
            ).first()
            
            if not template:
                return False, "Template not found"
            
            # Update template fields
            template.template_name = template_data['template_name']
            template.template_version = template_data['version']
            template.database_type = template_data.get('database_type', 'postgresql')
            template.domain_hint = template_data.get('domain_hint', 'financial')
            template.business_rules_template = template_data['business_rules']
            template.schema_context_template = template_data['schema_context']
            template.domain_specific_prompts = template_data['domain_prompts']
            template.updated_at = datetime.now(timezone.utc)
            
            session.commit()
            
            return True, f"Template '{template_data['template_name']}' updated successfully"
            
    except Exception as e:
        return False, f"Error updating template: {str(e)}"

def get_schema_analysis_for_template(connection_id: str) -> Dict[str, Any]:
    """Retrieve comprehensive schema analysis from vector DB, database models, and session state for template editing"""
    try:
        schema_data = {
            'tables_analysis': {},
            'columns_analysis': {},
            'vector_context': '',
            'selected_tables': [],
            'selected_columns': {},
            'schema_metadata': {},
            'database_analysis': {}
        }
        
        # Try to get from session state first (most recent analysis)
        if hasattr(st.session_state, 'analyzed_tables') and st.session_state.analyzed_tables:
            schema_data['tables_analysis'] = st.session_state.analyzed_tables
            
        if hasattr(st.session_state, 'analyzed_columns') and st.session_state.analyzed_columns:
            schema_data['columns_analysis'] = st.session_state.analyzed_columns
            
        if hasattr(st.session_state, 'selected_tables') and st.session_state.selected_tables:
            schema_data['selected_tables'] = st.session_state.selected_tables
            
        if hasattr(st.session_state, 'selected_columns') and st.session_state.selected_columns:
            schema_data['selected_columns'] = st.session_state.selected_columns
        
        # Try to get from database models (schema analysis results)
        try:
            imports = safe_import()
            if imports['success'] and imports['db_available']:
                with imports['SessionLocal']() as session:
                    # Import schema analysis models
                    from app.models.database.schema_analysis_models import (
                        TableAnalysisModel, 
                        SchemaAnalysisSessionModel
                    )
                    
                    # Get the latest schema analysis session for this connection
                    latest_session = session.query(SchemaAnalysisSessionModel).filter(
                        SchemaAnalysisSessionModel.connection_id == uuid.UUID(connection_id)
                    ).order_by(SchemaAnalysisSessionModel.started_at.desc()).first()
                    
                    if latest_session:
                        # Get table analysis results for this session
                        table_analyses = session.query(TableAnalysisModel).filter(
                            TableAnalysisModel.session_id == latest_session.session_id
                        ).all()
                        
                        # Process table analysis results
                        db_tables_analysis = {}
                        for table_analysis in table_analyses:
                            table_name = table_analysis.table_name
                            db_tables_analysis[table_name] = {
                                'business_description': table_analysis.ai_business_description or table_analysis.inferred_business_purpose,
                                'primary_purpose': table_analysis.primary_purpose,
                                'data_category': table_analysis.data_category,
                                'parent_tables': table_analysis.parent_tables or [],
                                'child_tables': table_analysis.child_tables or [],
                                'key_columns': table_analysis.key_columns or [],
                                'business_processes': table_analysis.business_processes or [],
                                'typical_queries': table_analysis.typical_queries or [],
                                'join_patterns': table_analysis.join_patterns or [],
                                'columns_info': table_analysis.columns_info or [],
                                'row_count': table_analysis.row_count,
                                'analyzed_at': table_analysis.analyzed_at
                            }
                        
                        schema_data['database_analysis'] = {
                            'session_info': {
                                'session_id': latest_session.session_id,
                                'database_type': latest_session.database_type,
                                'database_name': latest_session.database_name,
                                'total_tables': latest_session.total_tables_discovered,
                                'total_relationships': latest_session.total_relationships_discovered,
                                'analysis_summary': latest_session.analysis_summary,
                                'started_at': latest_session.started_at,
                                'completed_at': latest_session.completed_at
                            },
                            'tables': db_tables_analysis
                        }
                        
                        # Merge database analysis with session state if session state is empty
                        if not schema_data['tables_analysis'] and db_tables_analysis:
                            schema_data['tables_analysis'] = db_tables_analysis
                            
        except Exception as e:
            logger.warning(f"Could not retrieve database analysis: {e}")
        
        # Try to get from vector DB
        try:
            from app.agents.configurator.vector_storage import SchemaVectorStore
            vector_store = SchemaVectorStore()
            
            # Get all schema context from vector DB
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            vector_context = loop.run_until_complete(
                vector_store.get_all_schema_context(connection_id)
            )
            loop.close()
            
            if vector_context:
                schema_data['vector_context'] = vector_context
                
        except Exception as e:
            logger.warning(f"Could not retrieve vector context: {e}")
        
        return schema_data
        
    except Exception as e:
        logger.error(f"Error retrieving schema analysis: {e}")
        return {
            'tables_analysis': {},
            'columns_analysis': {},
            'vector_context': '',
            'selected_tables': [],
            'selected_columns': {},
            'schema_metadata': {},
            'database_analysis': {}
        }

def format_schema_analysis_for_display(schema_data: Dict[str, Any]) -> str:
    """Format schema analysis data for display in template edit view"""
    try:
        formatted_text = ""
        
        # Add database analysis session info if available
        if schema_data.get('database_analysis') and schema_data['database_analysis'].get('session_info'):
            session_info = schema_data['database_analysis']['session_info']
            formatted_text += "=== DATABASE ANALYSIS SESSION ===\n"
            formatted_text += f"Session ID: {session_info.get('session_id', 'Unknown')}\n"
            formatted_text += f"Database Type: {session_info.get('database_type', 'Unknown')}\n"
            formatted_text += f"Database Name: {session_info.get('database_name', 'Unknown')}\n"
            formatted_text += f"Total Tables Discovered: {session_info.get('total_tables', 0)}\n"
            formatted_text += f"Total Relationships: {session_info.get('total_relationships', 0)}\n"
            if session_info.get('started_at'):
                formatted_text += f"Analysis Started: {session_info['started_at']}\n"
            if session_info.get('completed_at'):
                formatted_text += f"Analysis Completed: {session_info['completed_at']}\n"
            formatted_text += "\n"
        
        # Add vector context if available
        if schema_data.get('vector_context'):
            formatted_text += "=== VECTOR DB SCHEMA CONTEXT ===\n"
            formatted_text += schema_data['vector_context'] + "\n\n"
        
        # Add database table analysis (from database models)
        if schema_data.get('database_analysis') and schema_data['database_analysis'].get('tables'):
            formatted_text += "=== DATABASE TABLE ANALYSIS ===\n"
            for table_name, analysis in schema_data['database_analysis']['tables'].items():
                formatted_text += f"\n** {table_name.upper()} **\n"
                if isinstance(analysis, dict):
                    if analysis.get('business_description'):
                        formatted_text += f"Business Description: {analysis['business_description']}\n"
                    if analysis.get('primary_purpose'):
                        formatted_text += f"Primary Purpose: {analysis['primary_purpose']}\n"
                    if analysis.get('data_category'):
                        formatted_text += f"Data Category: {analysis['data_category']}\n"
                    if analysis.get('row_count'):
                        formatted_text += f"Row Count: {analysis['row_count']:,}\n"
                    if analysis.get('key_columns'):
                        formatted_text += f"Key Columns: {', '.join(analysis['key_columns'])}\n"
                    if analysis.get('business_processes'):
                        formatted_text += f"Business Processes: {', '.join(analysis['business_processes'])}\n"
                    if analysis.get('parent_tables'):
                        formatted_text += f"Parent Tables: {', '.join(analysis['parent_tables'])}\n"
                    if analysis.get('child_tables'):
                        formatted_text += f"Child Tables: {', '.join(analysis['child_tables'])}\n"
                    if analysis.get('typical_queries'):
                        formatted_text += f"Typical Queries: {'; '.join(analysis['typical_queries'][:3])}\n"
                    if analysis.get('join_patterns'):
                        formatted_text += f"Join Patterns: {'; '.join(analysis['join_patterns'][:3])}\n"
                    
                    # Add column information from database analysis
                    if analysis.get('columns_info'):
                        formatted_text += f"Columns ({len(analysis['columns_info'])}):\n"
                        for col_info in analysis['columns_info'][:10]:  # Show first 10 columns
                            if isinstance(col_info, dict):
                                col_name = col_info.get('name', 'Unknown')
                                col_type = col_info.get('type', 'Unknown')
                                nullable = "NULL" if col_info.get('nullable', True) else "NOT NULL"
                                formatted_text += f"  - {col_name}: {col_type} {nullable}\n"
                        if len(analysis['columns_info']) > 10:
                            formatted_text += f"  ... and {len(analysis['columns_info']) - 10} more columns\n"
                formatted_text += "\n"
        
        # Add session state table analysis if different from database analysis
        if schema_data.get('tables_analysis') and not schema_data.get('database_analysis'):
            formatted_text += "=== SESSION TABLE ANALYSIS ===\n"
            for table_name, analysis in schema_data['tables_analysis'].items():
                formatted_text += f"\n** {table_name.upper()} **\n"
                if isinstance(analysis, dict):
                    if analysis.get('business_description'):
                        formatted_text += f"Business Description: {analysis['business_description']}\n"
                    if analysis.get('primary_purpose'):
                        formatted_text += f"Primary Purpose: {analysis['primary_purpose']}\n"
                    if analysis.get('data_category'):
                        formatted_text += f"Data Category: {analysis['data_category']}\n"
                    if analysis.get('user_notes'):
                        formatted_text += f"User Notes: {analysis['user_notes']}\n"
                    if analysis.get('business_rules'):
                        formatted_text += f"Business Rules: {analysis['business_rules']}\n"
                formatted_text += "\n"
        
        # Add column analysis with enums
        if schema_data.get('columns_analysis'):
            formatted_text += "=== COLUMN ANALYSIS & ENUMS ===\n"
            for table_name, columns in schema_data['columns_analysis'].items():
                formatted_text += f"\n** {table_name.upper()} COLUMNS **\n"
                if isinstance(columns, dict):
                    for col_name, col_analysis in columns.items():
                        formatted_text += f"\n- {col_name}:\n"
                        if isinstance(col_analysis, dict):
                            if col_analysis.get('business_description'):
                                formatted_text += f"  Description: {col_analysis['business_description']}\n"
                            if col_analysis.get('category'):
                                formatted_text += f"  Category: {col_analysis['category']}\n"
                            if col_analysis.get('enum_values'):
                                formatted_text += f"  Enum Values: {', '.join(col_analysis['enum_values'])}\n"
                            if col_analysis.get('sample_values'):
                                formatted_text += f"  Sample Values: {', '.join(col_analysis['sample_values'][:5])}\n"
                            if col_analysis.get('user_notes'):
                                formatted_text += f"  User Notes: {col_analysis['user_notes']}\n"
                            if col_analysis.get('business_rules'):
                                formatted_text += f"  Business Rules: {col_analysis['business_rules']}\n"
        
        # Add selected tables and columns info
        if schema_data.get('selected_tables'):
            formatted_text += f"\n=== SELECTED TABLES ===\n"
            formatted_text += f"Tables: {', '.join(schema_data['selected_tables'])}\n"
        
        if schema_data.get('selected_columns'):
            formatted_text += f"\n=== SELECTED COLUMNS ===\n"
            for table, columns in schema_data['selected_columns'].items():
                if columns:
                    formatted_text += f"{table}: {', '.join(columns)}\n"
        
        return formatted_text if formatted_text else "No schema analysis data available. Please run schema discovery first."
        
    except Exception as e:
        logger.error(f"Error formatting schema analysis: {e}")
        return f"Error formatting schema analysis: {str(e)}"

def delete_template(template_id: str) -> Tuple[bool, str]:
    """Delete a template from the database"""
    imports = safe_import()
    if not imports['success']:
        return False, f"Import error: {imports['error']}"
    
    try:
        with imports['SessionLocal']() as session:
            template = session.query(imports['ConnectionContextTemplateModel']).filter(
                imports['ConnectionContextTemplateModel'].id == uuid.UUID(template_id)
            ).first()
            
            if not template:
                return False, "Template not found"
            
            template_name = template.template_name
            session.delete(template)
            session.commit()
            
            return True, f"Template '{template_name}' deleted successfully"
            
    except Exception as e:
        return False, f"Error deleting template: {str(e)}"

def test_database_connection(connection_details: Dict[str, Any]) -> Tuple[bool, str]:
    """Test database connection with provided credentials"""
    imports = safe_import()
    if not imports['success']:
        return False, f"Import error: {imports['error']}"
    
    logger = imports['logger']
    
    try:
        logger.info(f"🔍 Testing database connection to {connection_details['host']}:{connection_details['port']}")
        logger.info(f"📊 Database: {connection_details['database_name']}, User: {connection_details['username']}")
        
        payload = {
            "connection_details": {
                "connection_name": connection_details['name'],
                "database_type": connection_details['database_type'],
                "host": connection_details['host'],
                "port": connection_details['port'],
                "database_name": connection_details['database_name'],
                "username": connection_details['username'],
                "password": connection_details['password'],
                "ssl_enabled": connection_details.get('ssl_enabled', False)
            }
        }
        
        logger.info(f"🌐 Making test connection API call...")
        
        with imports['httpx'].Client(timeout=30.0) as client:
            response = client.post("http://localhost:8000/configurator/connections/test", json=payload)
            
            logger.info(f"📡 Test response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Connection test result: {result}")
                return result['success'], result['message']
            else:
                error_text = response.text
                logger.warning(f"⚠️ Test API error {response.status_code}: {error_text}")
                logger.info("🔄 Falling back to direct database connection test...")
                
                # Fallback to direct database connection test
                try:
                    from urllib.parse import quote_plus
                    from sqlalchemy import create_engine, text
                    
                    # Build connection string
                    password_encoded = quote_plus(connection_details['password'])
                    username_encoded = quote_plus(connection_details['username'])
                    
                    if connection_details['database_type'] == 'postgresql':
                        connection_string = f"postgresql://{username_encoded}:{password_encoded}@{connection_details['host']}:{connection_details['port']}/{connection_details['database_name']}"
                    elif connection_details['database_type'] == 'mysql':
                        connection_string = f"mysql+pymysql://{username_encoded}:{password_encoded}@{connection_details['host']}:{connection_details['port']}/{connection_details['database_name']}"
                    else:
                        return False, f"Direct connection test not supported for {connection_details['database_type']}"
                    
                    # Test the connection
                    logger.info(f"🔌 Testing direct database connection...")
                    engine = create_engine(connection_string, pool_timeout=10, pool_recycle=300)
                    
                    with engine.connect() as conn:
                        # Simple test query
                        result = conn.execute(text("SELECT 1 as test"))
                        test_value = result.fetchone()[0]
                        
                        if test_value == 1:
                            logger.info(f"✅ Direct database connection test successful!")
                            return True, "Connection successful (direct database test)"
                        else:
                            return False, "Direct database test failed - unexpected result"
                            
                except Exception as db_error:
                    error_msg = f"Both API and direct database test failed. API: {response.status_code} - {error_text}, DB: {str(db_error)}"
                    logger.error(f"❌ {error_msg}")
                    return False, error_msg
                
    except imports['httpx'].ConnectError as e:
        logger.error(f"🌐 Connection error during test: {str(e)}")
        return False, "Cannot connect to API server. Make sure it's running on localhost:8000"
    except Exception as e:
        logger.error(f"💥 Unexpected error in connection test: {str(e)}")
        import traceback
        logger.error(f"📚 Full traceback: {traceback.format_exc()}")
        return False, f"Connection test error: {str(e)}"

def create_database_connection(connection_details: Dict[str, Any], user_id: str = "vaishakh_configurator") -> Tuple[bool, str, Optional[str]]:
    """Create a new database connection"""
    imports = safe_import()
    if not imports['success']:
        return False, f"Import error: {imports['error']}", None
    
    try:
        payload = {
            "connection_name": connection_details['name'],
            "database_type": connection_details['database_type'],
            "host": connection_details['host'],
            "port": connection_details['port'],
            "database_name": connection_details['database_name'],
            "username": connection_details['username'],
            "password": connection_details['password'],
            "ssl_enabled": connection_details.get('ssl_enabled', False),
            "connection_params": connection_details.get('connection_params', {})
        }
        
        with imports['httpx'].Client(timeout=30.0) as client:
            response = client.post(f"http://localhost:8000/configurator/connections?user_id={user_id}", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return True, "Connection created successfully", result['connection_id']
            else:
                imports['logger'].warning(f"⚠️ API error: {response.status_code} - {response.text}")
                imports['logger'].info("🔄 Falling back to direct database creation...")
                
                # Fallback to direct database creation
                try:
                    from app.agents.configurator.database_persistence import ConfiguratorDatabase
                    from app.agents.configurator.models import DatabaseConnection, DatabaseType
                    import asyncio
                    import uuid
                    from datetime import datetime, timezone
                    
                    configurator_db = ConfiguratorDatabase()
                    
                    # Create database connection object
                    connection_id = str(uuid.uuid4())
                    
                    # Map database type string to enum
                    db_type_mapping = {
                        'postgresql': DatabaseType.POSTGRESQL,
                        'mysql': DatabaseType.MYSQL,
                        'sqlite': DatabaseType.SQLITE,
                        'oracle': DatabaseType.ORACLE,
                        'mssql': DatabaseType.MSSQL,
                        'mongodb': DatabaseType.MONGODB
                    }
                    
                    db_type = db_type_mapping.get(connection_details['database_type'], DatabaseType.POSTGRESQL)
                    
                    db_connection = DatabaseConnection(
                        id=connection_id,
                        name=connection_details['name'],
                        database_type=db_type,
                        host=connection_details['host'],
                        port=connection_details['port'],
                        database_name=connection_details['database_name'],
                        username=connection_details['username'],
                        password=connection_details['password'],
                        ssl_enabled=connection_details.get('ssl_enabled', False),
                        connection_params=connection_details.get('connection_params', {}),
                        is_active=True,
                        created_by=user_id,
                        created_at=datetime.now(timezone.utc)
                    )
                    
                    # Save to database directly
                    saved_connection = asyncio.run(configurator_db.create_database_connection(user_id, db_connection))
                    
                    imports['logger'].info(f"✅ Direct database creation successful: {connection_id}")
                    return True, "Connection created successfully (direct database)", connection_id
                    
                except Exception as db_error:
                    error_msg = f"Both API and direct database creation failed. API: {response.status_code} - {response.text}, DB: {str(db_error)}"
                    imports['logger'].error(f"❌ {error_msg}")
                    return False, error_msg, None
                
    except imports['httpx'].ConnectError:
        return False, "Cannot connect to API server. Make sure it's running on localhost:8000", None
    except Exception as e:
        return False, f"Connection creation error: {str(e)}", None

def get_database_schema_direct(connection_details: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict]]:
    """Direct schema discovery without configurator session - faster approach"""
    imports = safe_import()
    if not imports['success']:
        return False, f"Import error: {imports['error']}", None
    
    try:
        from urllib.parse import quote_plus
        import sqlalchemy as sa
        from sqlalchemy import create_engine, inspect, text
        
        # Build connection string with proper URL encoding
        username = quote_plus(connection_details.get('username', ''))
        password = quote_plus(connection_details.get('password', ''))
        host = connection_details.get('host', 'localhost')
        port = connection_details.get('port', 5432)
        # Handle both 'database' and 'database_name' keys
        database = connection_details.get('database', connection_details.get('database_name', ''))
        
        connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
        
        # Create engine and connect
        engine = create_engine(connection_string, pool_timeout=30, pool_recycle=300)
        inspector = inspect(engine)
        
        # Enhanced schema discovery - support multiple schemas and auto-discovery
        target_schemas_param = connection_details.get('connection_params', {}).get('schema', '')
        
        # Determine which schemas to analyze
        target_schemas = []
        
        if target_schemas_param:
            # Support comma-separated schemas
            if ',' in target_schemas_param:
                target_schemas = [s.strip() for s in target_schemas_param.split(',') if s.strip()]
            else:
                target_schemas = [target_schemas_param.strip()]
        else:
            # Auto-discover all available schemas
            try:
                all_schemas = inspector.get_schema_names()
                # Filter out system schemas
                target_schemas = [s for s in all_schemas if s not in ['information_schema', 'pg_catalog', 'pg_toast', 'sys', 'mysql', 'performance_schema']]
                if not target_schemas:
                    # Fallback to default schema if no schemas found
                    target_schemas = ['public', 'staging_dashboard']
            except Exception as e:
                # Fallback to common schema names if auto-discovery fails
                target_schemas = ['public', 'staging_dashboard']
        
        tables_data = []
        schemas_found = []
        
        # Get tables from all target schemas
        for target_schema in target_schemas:
            try:
                table_names = inspector.get_table_names(schema=target_schema)
                if not table_names:
                    continue  # Skip empty schemas
                
                schemas_found.append(target_schema)
                
                for table_name in table_names[:50]:  # Limit to first 50 tables for performance
                    try:
                        # Get columns
                        columns = inspector.get_columns(table_name, schema=target_schema)
                        
                        # Get row count (with timeout)
                        row_count = None
                        try:
                            with engine.connect() as conn:
                                result = conn.execute(text(f"SELECT COUNT(*) FROM {target_schema}.{table_name}"))
                                row_count = result.scalar()
                        except:
                            row_count = "Unknown"
                        
                        # Format table data
                        table_data = {
                            'table_name': table_name,
                            'schema_name': target_schema,
                            'columns': [
                                {
                                    'column_name': col['name'],
                                    'data_type': str(col['type']),
                                    'nullable': col.get('nullable', True),
                                    'default': col.get('default')
                                }
                                for col in columns
                            ],
                            'row_count': row_count
                        }
                        
                        tables_data.append(table_data)
                        
                    except Exception as e:
                        # Skip tables we can't access
                        continue
                        
            except Exception as e:
                # Skip schemas we can't access
                continue
        
        # Build comprehensive result for all schemas
        if tables_data:
            schema_result = {
                'tables': tables_data,
                'schemas_analyzed': schemas_found,
                'schema_name': ', '.join(schemas_found) if len(schemas_found) > 1 else schemas_found[0] if schemas_found else 'None',
                'total_tables': len(tables_data),
                'total_schemas': len(schemas_found)
            }
            
            schema_summary = f"Found {len(tables_data)} tables across {len(schemas_found)} schema(s): {', '.join(schemas_found)}"
            return True, schema_summary, schema_result
        else:
            return False, f"No accessible tables found in any of the target schemas: {', '.join(target_schemas)}", None
            
    except Exception as e:
        return False, f"Direct schema discovery error: {str(e)}", None

# Removed get_database_schema function - using direct method only for better performance and reliability

def create_configuration_session(connection_id: str, user_id: str = "vaishakh_configurator") -> Tuple[bool, str, Optional[str]]:
    """Create a configuration session"""
    imports = safe_import()
    if not imports['success']:
        return False, f"Import error: {imports['error']}", None
    
    try:
        payload = {"connection_id": connection_id}
        
        with imports['httpx'].Client(timeout=30.0) as client:
            response = client.post(f"http://localhost:8000/configurator/sessions?user_id={user_id}", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return True, "Configuration session created", result['session_id']
            else:
                return False, f"API error: {response.status_code} - {response.text}", None
                
    except imports['httpx'].ConnectError:
        return False, "Cannot connect to API server. Make sure it's running on localhost:8000", None
    except Exception as e:
        return False, f"Session creation error: {str(e)}", None

def create_new_template(connection_id: str, template_data: Dict[str, Any]) -> Tuple[bool, str]:
    """Create a new context template with database configuration data directly in connection_context_templates table"""
    imports = safe_import()
    if not imports['success']:
        return False, f"Import error: {imports['error']}"
    
    logger = imports['logger']
    
    try:
        logger.info(f"🚀 Starting template creation for connection_id: {connection_id}")
        logger.info(f"📋 Template data keys: {list(template_data.keys())}")
        
        if not imports['db_available']:
            return False, f"Database not available: {imports['db_error']}"
        
        # Generate a unique template ID
        template_id = imports['uuid'].uuid4()
        logger.info(f"🆔 Generated template ID: {template_id}")
        
        # Create the template record directly in connection_context_templates table
        with imports['SessionLocal']() as session:
            new_template = imports['ConnectionContextTemplateModel'](
                id=template_id,
                connection_id=imports['uuid'].UUID(connection_id),
                template_name=template_data['template_name'],
                template_version=template_data.get('version', '1.0'),
                is_active=True,
                business_rules_template=template_data['business_rules'],
                schema_context_template=template_data['schema_context'],
                domain_specific_prompts=template_data.get('domain_prompts', ''),
                # Store selected columns and schema metadata in table_relationships and field_mappings
                table_relationships=template_data.get('schema_metadata', {}),
                field_mappings={col: col for col in template_data.get('selected_columns', [])},  # Simple column mapping
                common_patterns=[],
                user_corrections=[],
                failed_queries_log=[],
                success_patterns=[],
                created_by="playground_user",
                updated_by="playground_user",
                usage_count=0
            )
            
            session.add(new_template)
            session.commit()
            
            logger.info(f"✅ Template stored in connection_context_templates table")
            logger.info(f"📦 Template includes {len(template_data.get('selected_columns', []))} selected columns")
            logger.info(f"📊 Business rules: {len(template_data['business_rules'])} chars")
            logger.info(f"📊 Schema context: {len(template_data['schema_context'])} chars")
            
            return True, f"Template '{template_data['template_name']}' created successfully with ID: {template_id}"
                
    except KeyError as e:
        logger.error(f"🔑 Missing key in template_data: {str(e)}")
        logger.error(f"📋 Available keys: {list(template_data.keys())}")
        return False, f"Missing required field: {str(e)}"
    except Exception as e:
        logger.error(f"💥 Unexpected error in template creation: {str(e)}")
        logger.error(f"🔍 Error type: {type(e).__name__}")
        import traceback
        logger.error(f"📚 Full traceback: {traceback.format_exc()}")
        return False, f"Template creation error: {str(e)}"

# Main application layout using tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 Query Testing", "📋 Template Management", "💾 Database Config", "🔧 Setup & Debug", "📊 Analytics"])

with tab1:
    st.header("🎯 Query Testing")
    
    # Two-column layout for better organization
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📋 Template Selection")
        
        # Load templates button with status indicator
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
                    st.success(f"Loaded {len(templates)} templates")
        
        # Template selection with enhanced display
        if st.session_state.templates_loaded and st.session_state.templates:
            template_options = []
            for i, template in enumerate(st.session_state.templates):
                status = "[Active]" if template['is_active'] else "[Inactive]"
                enhanced = "[Enhanced]" if template['has_enhanced_content'] else "[Basic]"
                template_options.append(f"{status} {template['template_name']} v{template['version']} {enhanced}")
            
            selected_idx = st.selectbox(
                "Choose Template:",
                range(len(template_options)),
                format_func=lambda x: template_options[x],
                help="[Active] Currently active | [Inactive] Disabled | [Enhanced] Has rich context | [Basic] Standard template"
            )
            
            if selected_idx is not None:
                selected_template = st.session_state.templates[selected_idx]
                # Use the template's connection_id for query testing
                st.session_state.selected_connection = selected_template['connection_id']
                st.session_state.selected_template_name = selected_template['template_name']
                st.session_state.selected_template_id = selected_template['id']
                
                # Template info in a card with dark theme
                st.markdown("### 📊 Template Metrics")
                
                # Metrics in grid layout
                metric_col1, metric_col2 = st.columns(2)
                with metric_col1:
                    st.metric("Usage Count", selected_template['usage_count'])
                    st.metric("Business Rules", f"{selected_template['business_rules_size']} chars")
                with metric_col2:
                    st.metric("Success Rate", f"{selected_template['success_rate']:.1%}")
                    st.metric("Schema Context", f"{selected_template['schema_context_size']} chars")
                
                # Enhanced content indicator
                if selected_template['has_enhanced_content']:
                    st.markdown('<div class="success-card">✅ Enhanced template with comprehensive context</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="warning-card">⚠️ Basic template - consider adding enhanced context</div>', unsafe_allow_html=True)
                
                # Template details in expandable section
                with st.expander("🔍 Template Details"):
                    st.write(f"**Database Type:** {selected_template.get('database_type', 'postgresql')}")
                    st.write(f"**Domain:** {selected_template.get('domain_hint', 'financial')}")
                    st.write(f"**Created:** {selected_template['created_at'].strftime('%Y-%m-%d %H:%M') if selected_template['created_at'] else 'Unknown'}")
                    
                    if selected_template.get('business_rules_template'):
                        st.write("**Business Rules Preview:**")
                        st.code(selected_template['business_rules_template'][:200] + "..." if len(selected_template['business_rules_template']) > 200 else selected_template['business_rules_template'])
        
        elif st.session_state.templates_loaded:
            st.markdown('<div class="info-card">📝 No templates found. Create one in the Template Management tab.</div>', unsafe_allow_html=True)
    
    with col2:
        st.subheader("💬 Query Testing")
        
        # Database Connection Selector
        st.markdown("#### 🔗 Database Connection")
        
        # Load available connections button
        if st.button("🔄 Load Database Connections", help="Refresh list of available database connections"):
            with st.spinner("Loading connections..."):
                connections, error = get_available_connections()
                if error:
                    st.error(f"❌ Failed to load connections: {error}")
                    st.session_state.available_connections = []
                else:
                    st.session_state.available_connections = connections
                    st.success(f"✅ Loaded {len(connections)} database connections")
        
        # Initialize available connections if not set
        if 'available_connections' not in st.session_state:
            st.session_state.available_connections = []
        
        # Connection selector dropdown
        if st.session_state.available_connections:
            connection_options = [f"{conn['name']} ({conn['database_type']})" for conn in st.session_state.available_connections]
            selected_conn_idx = st.selectbox(
                "Select Database Connection",
                range(len(connection_options)),
                format_func=lambda x: connection_options[x],
                help="Choose the database connection to execute queries against",
                key="connection_selector"
            )
            
            if selected_conn_idx is not None:
                selected_connection = st.session_state.available_connections[selected_conn_idx]
                
                # Only override connection if no template is selected
                # Template's connection ID takes precedence
                if not st.session_state.get('selected_template_name'):
                    st.session_state.selected_connection = selected_connection['id']
                    # Show connection details
                    st.info(f"🔗 **Connected to:** {selected_connection['name']} ({selected_connection['database_type']})")
                else:
                    # Show that template connection takes precedence
                    st.info(f"📋 **Template Connection Active:** Using connection from selected template")
                    st.info(f"🔗 **Template Connection ID:** {st.session_state.selected_connection}")
        else:
            st.warning("⚠️ No database connections available. Please load connections first.")
            st.session_state.selected_connection = None
        
        st.markdown("---")
        
        if st.session_state.selected_connection:
            # Show connection status and template info if available
            if st.session_state.get('selected_template_name'):
                st.success(f"✅ Template selected: {st.session_state.selected_template_name}")
                
                # Automatically ensure business rules are populated for this template
                if st.session_state.get('selected_template_id'):
                    try:
                        # Check if business rules exist, if not create them automatically
                        response = httpx.get(f"{API_BASE_URL}/business-rules/connections/{st.session_state.selected_template_id}/business-context")
                        if response.status_code == 404:
                            # Auto-populate business rules silently in background
                            populate_business_rules_from_template(st.session_state.selected_template_id, st.session_state.selected_connection)
                    except Exception as e:
                        logger.warning(f"Auto-population check failed: {e}")
            
            # Query input with examples
            st.markdown("**Enter your natural language question:**")
            
            # Example questions
            example_questions = [
                "Show me total disbursements for this month",
                "What are the top 10 customers by loan amount?",
                "Find all overdue collections from last week",
                "Calculate average processing time for loan approvals"
            ]
            
            with st.expander("💡 Example Questions"):
                for i, example in enumerate(example_questions, 1):
                    if st.button(f"{i}. {example}", key=f"example_{i}"):
                        st.session_state.query_input = example
            
            # Query input - now enabled
            query = st.text_area(
                "Your Question:",
                value=st.session_state.get('query_input', ''),
                height=100,
                help="Ask questions in natural language about your data"
            )
            
            # Domain hint selection - now enabled
            domain_hint = st.selectbox(
                "Domain Context:",
                ["financial", "healthcare", "ecommerce", "general"],
                help="Select the business domain for better context understanding"
            )
            
            # Test query button - now enabled
            if st.button("🚀 Test Query", type="primary", disabled=not query.strip()):
                with st.spinner("Generating and executing query..."):
                    # Store the question for feedback system
                    st.session_state.last_question = query
                    
                    result = test_api_with_enhanced_validation(
                        st.session_state.selected_connection,
                        query,
                        domain_hint
                    )
                    st.session_state.last_test_result = result
            
            # Display results in enhanced grid layout
            if st.session_state.last_test_result:
                result = st.session_state.last_test_result
                
                st.markdown("---")
                st.subheader("📊 Query Results")
                
                if result['success']:
                    # Results grid layout
                    result_col1, result_col2 = st.columns([1, 1])
                    
                    with result_col1:
                        # Execution metrics
                        st.markdown("**⚡ Execution Metrics**")
                        metrics_container = st.container()
                        with metrics_container:
                            metric_row1_col1, metric_row1_col2 = st.columns(2)
                            with metric_row1_col1:
                                st.metric("Execution Time", f"{result['execution_time']:.0f}ms")
                            with metric_row1_col2:
                                st.metric("Rows Returned", result['row_count'])
                            
                            if result.get('confidence_score'):
                                st.metric("Confidence", f"{result['confidence_score']:.1%}")
                        
                        # SQL Query
                        if result.get('generated_sql'):
                            st.markdown("**🔍 Generated SQL**")
                            st.code(result['generated_sql'], language='sql')
                    
                    with result_col2:
                        # Status and error handling
                        if result['has_sql_error']:
                            st.markdown('<div class="error-card">', unsafe_allow_html=True)
                            st.markdown("**❌ Query Execution Failed**")
                            st.write(result['error_message'])
                            
                            if result.get('error_analysis'):
                                analysis = result['error_analysis']
                                st.markdown(f"**Error Type:** {analysis['type']}")
                                st.markdown(f"**Description:** {analysis['description']}")
                                st.markdown(f"**Suggestion:** {analysis['suggestion']}")
                                
                                if analysis.get('problematic_column'):
                                    st.markdown(f"**Problematic Column:** `{analysis['problematic_column']}`")
                                elif analysis.get('problematic_table'):
                                    st.markdown(f"**Problematic Table:** `{analysis['problematic_table']}`")
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            # Add feedback interface for failed queries
                            st.markdown("---")
                            add_query_feedback_interface(
                                result_data=result,
                                question=st.session_state.get('last_question', ''),
                                connection_id=st.session_state.selected_connection
                            )
                        else:
                            st.markdown('<div class="success-card">', unsafe_allow_html=True)
                            st.markdown("**✅ Query Executed Successfully**")
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            # Data preview
                            if result.get('query_results') and len(result['query_results']) > 0:
                                st.markdown("**📋 Data Preview**")
                                df = pd.DataFrame(result['query_results'])
                                st.dataframe(df.head(10), use_container_width=True)
                                
                                if len(result['query_results']) > 10:
                                    st.info(f"Showing first 10 rows of {len(result['query_results'])} total rows")
                            
                            # Add feedback interface for successful queries too
                            st.markdown("---")
                            add_query_feedback_interface(
                                result_data=result,
                                question=st.session_state.get('last_question', ''),
                                connection_id=st.session_state.selected_connection
                            )
                else:
                    st.markdown(f'<div class="error-card">❌ {result["error"]}</div>', unsafe_allow_html=True)
                    if result.get('suggestion'):
                        st.markdown(f'<div class="info-card">💡 **Suggestion:** {result["suggestion"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="warning-card">⚠️ Please select a template first to enable query testing</div>', unsafe_allow_html=True)

with tab2:
    st.header("📋 Template Management")
    
    # Template management tabs
    mgmt_tab1, mgmt_tab2 = st.tabs(["➕ Create New", "📝 Manage Existing"])
    
    with mgmt_tab1:
        st.subheader("➕ Create New Template")
        
        # Schema Analysis Loading (Outside Form)
        st.markdown("### 🔍 Schema Analysis Helper")
        auto_populate_col1, auto_populate_col2 = st.columns([3, 1])
        with auto_populate_col1:
            st.markdown("**Load schema analysis data to auto-populate template fields**")
        with auto_populate_col2:
            load_schema_connection_id = st.text_input(
                "Connection ID for Schema",
                placeholder="Enter connection UUID",
                help="Enter connection ID to load schema analysis",
                key="load_schema_conn_id"
            )
        
        load_col1, load_col2 = st.columns([1, 1])
        with load_col1:
            if st.button("🤖 Load Schema Analysis", help="Load schema analysis for this connection"):
                if load_schema_connection_id.strip():
                    with st.spinner("Loading schema analysis..."):
                        schema_data = get_schema_analysis_for_template(load_schema_connection_id.strip())
                        st.session_state.create_template_schema_data = schema_data
                        if schema_data.get('vector_context') or schema_data.get('tables_analysis') or schema_data.get('columns_analysis'):
                            st.success("✅ Schema analysis loaded!")
                        else:
                            st.warning("⚠️ No schema analysis found for this connection")
                else:
                    st.error("❌ Please enter a connection ID first")
        
        with load_col2:
            if hasattr(st.session_state, 'create_template_schema_data') and st.session_state.create_template_schema_data:
                if st.button("📋 Use Schema Analysis", help="Auto-populate schema context with loaded analysis"):
                    st.session_state.auto_populate_schema = format_schema_analysis_for_display(st.session_state.create_template_schema_data)
                    st.success("✅ Schema context will be auto-populated in form below")
                    st.rerun()
        
        # Display schema analysis if available
        if hasattr(st.session_state, 'create_template_schema_data') and st.session_state.create_template_schema_data:
            with st.expander("📊 Available Schema Analysis", expanded=False):
                schema_display = format_schema_analysis_for_display(st.session_state.create_template_schema_data)
                st.text_area(
                    "Schema Analysis Preview",
                    value=schema_display[:1000] + "..." if len(schema_display) > 1000 else schema_display,
                    height=200,
                    disabled=True,
                    help="Preview of available schema analysis data"
                )
        
        st.markdown("---")
        
        with st.form("create_template_form"):
            # Basic template information
            col1, col2 = st.columns(2)
            
            with col1:
                template_name = st.text_input(
                    "Template Name *",
                    placeholder="e.g., Financial Analysis Template",
                    help="Give your template a descriptive name"
                )
                
                version = st.text_input(
                    "Version *",
                    value="1.0",
                    help="Template version (e.g., 1.0, 1.1, 2.0)"
                )
                
                connection_id = st.text_input(
                    "Connection ID *",
                    value=load_schema_connection_id if 'load_schema_connection_id' in locals() else "",
                    placeholder="Enter connection UUID",
                    help="UUID of the database connection this template will use"
                )
            
            with col2:
                database_type = st.selectbox(
                    "Database Type",
                    ["postgresql", "mysql", "sqlite", "oracle", "sqlserver"],
                    help="Type of database this template targets"
                )
                
                domain_hint = st.selectbox(
                    "Domain Context",
                    ["financial", "healthcare", "ecommerce", "manufacturing", "education", "general"],
                    help="Business domain for better context understanding"
                )
            
            # Template content
            st.markdown("### Template Content")
            
            st.markdown('<div class="large-textarea">', unsafe_allow_html=True)
            business_rules = st.text_area(
                "Business Rules Template *",
                height=350,
                placeholder="""# Business Rules
- Use current tables over historical ones
- Apply proper date filtering for time-based queries
- Use SUM for amount aggregations
- Prefer specific table names over generic ones

## Table Preferences
- Disbursements: use fed_disbursement_details, disbursement_details
- Collections: use collection_details, loan_emi_mapping

## Date Handling
- Use disbursed_date for disbursement queries
- Use collection_due_date for collection queries""",
                help="Define business rules and logic for query generation"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="large-textarea">', unsafe_allow_html=True)
            schema_context = st.text_area(
                "Schema Context Template *",
                value=st.session_state.get('auto_populate_schema', ''),
                height=350,
                placeholder="""# Database Schema Context

## Primary Tables
- customers: customer information and demographics
- loans: loan details and terms
- disbursements: loan disbursement records
- collections: payment and collection data

## Key Relationships
- customer_id: links customers to loans
- loan_id: links loans to disbursements and collections
- disbursement_id: tracks disbursement records

## Important Columns
- amount fields: use DECIMAL/NUMERIC types
- date fields: use DATE or TIMESTAMP types
- status fields: use VARCHAR with specific values""",
                help="Describe the database schema and relationships"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="medium-textarea">', unsafe_allow_html=True)
            domain_prompts = st.text_area(
                "Domain-Specific Prompts",
                height=240,
                placeholder="""# Financial Domain Prompts
- Focus on accuracy for monetary calculations
- Apply regulatory compliance rules
- Use appropriate aggregation functions for financial metrics
- Consider time-based analysis for trends
- Handle currency formatting appropriately""",
                help="Domain-specific guidance for query generation"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Form submission
            submitted = st.form_submit_button("➕ Create Template", type="primary")
            
            if submitted:
                # Validation
                errors = []
                if not template_name.strip():
                    errors.append("Template name is required")
                if not version.strip():
                    errors.append("Version is required")
                if not connection_id.strip():
                    errors.append("Connection ID is required")
                if not business_rules.strip():
                    errors.append("Business rules template is required")
                if not schema_context.strip():
                    errors.append("Schema context template is required")
                
                # Validate UUID format
                if connection_id.strip():
                    try:
                        uuid.UUID(connection_id.strip())
                    except ValueError:
                        errors.append("Connection ID must be a valid UUID")
                
                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                else:
                    # Create template
                    template_data = {
                        'template_name': template_name.strip(),
                        'version': version.strip(),
                        'database_type': database_type,
                        'domain_hint': domain_hint,
                        'business_rules': business_rules.strip(),
                        'schema_context': schema_context.strip(),
                        'domain_prompts': domain_prompts.strip() if domain_prompts.strip() else None
                    }
                    
                    with st.spinner("Creating template..."):
                        success, message = create_new_template(connection_id.strip(), template_data)
                        if success:
                            st.success(f"✅ {message}")
                            st.info("🔄 Refresh the template list in the Query Testing tab to see your new template")
                            # Clear form by rerunning
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
    
    with mgmt_tab2:
        st.subheader("📝 Manage Existing Templates")
        
        # Load and display existing templates
        if st.button("🔄 Refresh Template List", help="Load latest templates from database"):
            templates, error = load_templates_safely()
            if error:
                st.error(f"❌ {error}")
            else:
                st.session_state.mgmt_templates = templates
                st.success(f"✅ Loaded {len(templates)} templates")
        
        if hasattr(st.session_state, 'mgmt_templates') and st.session_state.mgmt_templates:
            st.markdown(f"**Found {len(st.session_state.mgmt_templates)} templates:**")
            
            for i, template in enumerate(st.session_state.mgmt_templates):
                with st.expander(f"{template['template_name']} v{template['version']} {'(⭐ Enhanced)' if template['has_enhanced_content'] else '(📝 Basic)'}"):
                    # Template info
                    info_col1, info_col2, info_col3 = st.columns(3)
                    
                    with info_col1:
                        st.write(f"**Status:** {'🟢 Active' if template['is_active'] else '🔴 Inactive'}")
                        st.write(f"**Database:** {template.get('database_type', 'postgresql')}")
                        st.write(f"**Domain:** {template.get('domain_hint', 'financial')}")
                    
                    with info_col2:
                        st.write(f"**Usage Count:** {template['usage_count']}")
                        st.write(f"**Success Rate:** {template['success_rate']:.1%}")
                        st.write(f"**Created:** {template['created_at'].strftime('%Y-%m-%d') if template['created_at'] else 'Unknown'}")
                    
                    with info_col3:
                        st.write(f"**Business Rules:** {template['business_rules_size']} chars")
                        st.write(f"**Schema Context:** {template['schema_context_size']} chars")
                        st.write(f"**Domain Prompts:** {template['domain_prompts_size']} chars")
                    
                    # Template content preview
                    if template.get('business_rules_template'):
                        with st.expander("📜 Business Rules Preview"):
                            st.code(template['business_rules_template'][:500] + "..." if len(template['business_rules_template']) > 500 else template['business_rules_template'])
                    
                    if template.get('schema_context_template'):
                        with st.expander("📊 Schema Context Preview"):
                            st.code(template['schema_context_template'][:500] + "..." if len(template['schema_context_template']) > 500 else template['schema_context_template'])
                    
                    # Action buttons
                    action_col1, action_col2, action_col3 = st.columns(3)
                    
                    with action_col1:
                        if st.button(f"✏️ Edit", key=f"edit_{template['id']}"):
                            st.session_state.editing_template = template
                            st.rerun()
                    
                    with action_col2:
                        if st.button(f"📋 Copy", key=f"copy_{template['id']}"):
                            # Copy template data to create form
                            st.info("📋 Template data copied! Go to 'Create New' tab to create a copy.")
                    
                    with action_col3:
                        if st.button(f"🗑️ Delete", key=f"delete_{template['id']}", type="secondary"):
                            if st.session_state.get(f"confirm_delete_{template['id']}"):
                                with st.spinner("Deleting template..."):
                                    success, message = delete_template(template['id'])
                                    if success:
                                        st.success(f"✅ {message}")
                                        # Refresh the list
                                        templates, _ = load_templates_safely()
                                        st.session_state.mgmt_templates = templates
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {message}")
                            else:
                                st.session_state[f"confirm_delete_{template['id']}"] = True
                                st.warning("⚠️ Click Delete again to confirm")
                                st.rerun()
        
        elif hasattr(st.session_state, 'mgmt_templates'):
            st.markdown('<div class="info-card">📝 No templates found. Create your first template using the "Create New" tab above.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="info-card">🔄 Click "Refresh Template List" to load existing templates.</div>', unsafe_allow_html=True)
        
        # Edit template form (if editing)
        if hasattr(st.session_state, 'editing_template'):
            st.markdown("---")
            st.subheader(f"✏️ Edit Template: {st.session_state.editing_template['template_name']}")
            
            template = st.session_state.editing_template
            
            # Load schema analysis data for this template
            if st.button("🔄 Load Schema Analysis", help="Retrieve schema analysis and vector DB data for this template"):
                with st.spinner("Loading schema analysis from vector DB..."):
                    schema_data = get_schema_analysis_for_template(template['connection_id'])
                    st.session_state.template_schema_data = schema_data
                    if schema_data.get('vector_context') or schema_data.get('tables_analysis') or schema_data.get('columns_analysis'):
                        st.success("✅ Schema analysis loaded successfully!")
                    else:
                        st.warning("⚠️ No schema analysis found. Please run schema discovery first.")
            
            # Display schema analysis if available
            if hasattr(st.session_state, 'template_schema_data') and st.session_state.template_schema_data:
                with st.expander("📊 Schema Analysis & Vector DB Data", expanded=False):
                    schema_display = format_schema_analysis_for_display(st.session_state.template_schema_data)
                    st.text_area(
                        "Schema Analysis (Read-only)",
                        value=schema_display,
                        height=300,
                        disabled=True,
                        help="This shows the schema analysis and vector DB data for reference"
                    )
                    
                    # Show schema statistics
                    schema_stats_col1, schema_stats_col2, schema_stats_col3 = st.columns(3)
                    with schema_stats_col1:
                        tables_count = len(st.session_state.template_schema_data.get('tables_analysis', {}))
                        st.metric("Tables Analyzed", tables_count)
                    with schema_stats_col2:
                        columns_count = sum(len(cols) for cols in st.session_state.template_schema_data.get('columns_analysis', {}).values())
                        st.metric("Columns Analyzed", columns_count)
                    with schema_stats_col3:
                        vector_available = "Yes" if st.session_state.template_schema_data.get('vector_context') else "No"
                        st.metric("Vector DB Data", vector_available)
            
            with st.form("edit_template_form"):
                # Basic template information
                edit_col1, edit_col2 = st.columns(2)
                
                with edit_col1:
                    edit_template_name = st.text_input(
                        "Template Name *",
                        value=template['template_name'],
                        help="Give your template a descriptive name"
                    )
                    
                    edit_version = st.text_input(
                        "Version *",
                        value=template['version'],
                        help="Template version (e.g., 1.0, 1.1, 2.0)"
                    )
                
                with edit_col2:
                    edit_database_type = st.selectbox(
                        "Database Type",
                        ["postgresql", "mysql", "sqlite", "oracle", "sqlserver"],
                        index=["postgresql", "mysql", "sqlite", "oracle", "sqlserver"].index(template.get('database_type', 'postgresql')),
                        help="Type of database this template targets"
                    )
                    
                    edit_domain_hint = st.selectbox(
                        "Domain Context",
                        ["financial", "healthcare", "ecommerce", "manufacturing", "education", "general"],
                        index=["financial", "healthcare", "ecommerce", "manufacturing", "education", "general"].index(template.get('domain_hint', 'financial')),
                        help="Business domain for better context understanding"
                    )
                
                # Template content with enhanced pre-population
                st.markdown("### Template Content")
                
                # Auto-populate button
                if hasattr(st.session_state, 'template_schema_data') and st.session_state.template_schema_data:
                    if st.form_submit_button("🤖 Auto-Populate from Schema Analysis", help="Fill template fields with schema analysis data"):
                        # Auto-populate schema context with analysis data
                        schema_display = format_schema_analysis_for_display(st.session_state.template_schema_data)
                        template['schema_context_template'] = schema_display
                        st.rerun()
                
                st.markdown('<div class="large-textarea">', unsafe_allow_html=True)
                edit_business_rules = st.text_area(
                    "Business Rules Template *",
                    value=template.get('business_rules_template', ''),
                    height=350,
                    help="Define business rules and logic for query generation"
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="large-textarea">', unsafe_allow_html=True)
                edit_schema_context = st.text_area(
                    "Schema Context Template *",
                    value=template.get('schema_context_template', ''),
                    height=350,
                    help="Describe the database schema and relationships"
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="medium-textarea">', unsafe_allow_html=True)
                edit_domain_prompts = st.text_area(
                    "Domain-Specific Prompts",
                    value=template.get('domain_specific_prompts', ''),
                    height=240,
                    help="Domain-specific guidance for query generation"
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Form submission
                edit_col1, edit_col2 = st.columns(2)
                with edit_col1:
                    edit_submitted = st.form_submit_button("✅ Update Template", type="primary")
                with edit_col2:
                    cancel_edit = st.form_submit_button("❌ Cancel")
                
                if cancel_edit:
                    del st.session_state.editing_template
                    st.rerun()
                
                if edit_submitted:
                    # Validation
                    edit_errors = []
                    if not edit_template_name.strip():
                        edit_errors.append("Template name is required")
                    if not edit_version.strip():
                        edit_errors.append("Version is required")
                    if not edit_business_rules.strip():
                        edit_errors.append("Business rules template is required")
                    if not edit_schema_context.strip():
                        edit_errors.append("Schema context template is required")
                    
                    if edit_errors:
                        for error in edit_errors:
                            st.error(f"❌ {error}")
                    else:
                        # Update template
                        edit_template_data = {
                            'template_name': edit_template_name.strip(),
                            'version': edit_version.strip(),
                            'database_type': edit_database_type,
                            'domain_hint': edit_domain_hint,
                            'business_rules': edit_business_rules.strip(),
                            'schema_context': edit_schema_context.strip(),
                            'domain_prompts': edit_domain_prompts.strip() if edit_domain_prompts.strip() else None
                        }
                        
                        with st.spinner("Updating template..."):
                            success, message = update_template(template['id'], edit_template_data)
                            if success:
                                st.success(f"✅ {message}")
                                del st.session_state.editing_template
                                # Refresh the list
                                templates, _ = load_templates_safely()
                                st.session_state.mgmt_templates = templates
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")

with tab3:
    st.header("💾 Database Configuration")
    st.markdown("**Complete workflow: Connect → Discover Schema → Select Columns → Create Templates → Embed to Vector DB**")
    
    # Initialize session state for database configuration
    if 'db_config_step' not in st.session_state:
        st.session_state.db_config_step = 'connection'
    if 'db_connection_id' not in st.session_state:
        st.session_state.db_connection_id = None
    if 'db_schema_data' not in st.session_state:
        st.session_state.db_schema_data = None
    if 'selected_columns' not in st.session_state:
        st.session_state.selected_columns = {}
    if 'configuration_session_id' not in st.session_state:
        st.session_state.configuration_session_id = None
    
    # Edit Schema Discovery Feature
    st.markdown("### 🔄 Edit Schema Discovery")
    st.markdown("*Revisit and modify schema selections for existing database connections*")
    
    # Load existing connections for editing
    
    edit_col1, edit_col2 = st.columns([2, 1])
    
    with edit_col1:
        if st.button("🔄 Load Existing Connections", help="Load your existing database connections for schema editing"):
            with st.spinner("Loading connections..."):
                connections, error = get_available_connections()
                if error:
                    st.error(f"❌ Failed to load connections: {error}")
                    st.session_state.edit_available_connections = []
                else:
                    st.session_state.edit_available_connections = connections
                    st.success(f"✅ Loaded {len(connections)} database connections")
    
    with edit_col2:
        if st.button("➕ New Connection", help="Create a new database connection"):
            # Reset to new connection workflow
            st.session_state.db_config_step = 'connection'
            st.session_state.db_connection_id = None
            st.session_state.db_schema_data = None
            st.session_state.selected_columns = {}
            st.session_state.configuration_session_id = None
            if 'edit_available_connections' in st.session_state:
                del st.session_state.edit_available_connections
            st.rerun()
    
    # Show existing connections for editing
    if 'edit_available_connections' in st.session_state and st.session_state.edit_available_connections:
        st.markdown("**Select a connection to edit its schema discovery:**")
        
        for i, conn in enumerate(st.session_state.edit_available_connections):
            # Debug: Show connection keys for troubleshooting
            if st.checkbox(f"Debug connection {i}", key=f"debug_{i}"):
                st.write("**Available keys:**", list(conn.keys()))
                st.json(conn)
            
            # Use safe key access with fallbacks
            conn_name = conn.get('name', 'Unknown')
            conn_type = conn.get('database_type', 'Unknown')
            conn_host = conn.get('host', 'Unknown')
            conn_port = conn.get('port', 'Unknown')
            conn_db = conn.get('database', conn.get('database_name', 'Unknown'))
            
            with st.expander(f"🔗 {conn_name} ({conn_type}) - {conn_host}:{conn_port}/{conn_db}"):
                edit_conn_col1, edit_conn_col2, edit_conn_col3 = st.columns([2, 1, 1])
                
                with edit_conn_col1:
                    st.write(f"**Connection ID:** {conn.get('id', 'Unknown')}")
                    st.write(f"**Created:** {conn.get('created_at', 'Unknown')}")
                    st.write(f"**Status:** {'✅ Active' if conn.get('is_active', True) else '❌ Inactive'}")
                
                with edit_conn_col2:
                    if st.button(f"🔬 Edit Schema", key=f"edit_schema_{conn.get('id', i)}", help="Edit schema discovery for this connection"):
                        # Set up for schema editing with proper connection persistence
                        connection_id = conn.get('id')
                        st.session_state.db_connection_id = connection_id
                        st.session_state.connection_id = connection_id  # Also store as connection_id
                        st.session_state.db_connection_details = {
                            'host': conn.get('host', ''),
                            'port': conn.get('port', 5432),
                            'database': conn.get('database', conn.get('database_name', '')),
                            'database_name': conn.get('database', conn.get('database_name', '')),  # Store both keys
                            'username': conn.get('username', ''),
                            'password': conn.get('password', ''),  # May need to re-enter
                            'database_type': conn.get('database_type', 'postgresql'),
                            'ssl_enabled': conn.get('ssl_enabled', False),
                            'connection_params': conn.get('connection_params', {})
                        }
                        st.session_state.db_config_step = 'schema'
                        st.session_state.edit_mode = True
                        st.rerun()
                
                with edit_conn_col3:
                    if st.button(f"🗑️ Delete", key=f"delete_conn_{conn['id']}", help="Delete this connection"):
                        # Add confirmation logic here if needed
                        st.warning("⚠️ Delete functionality would go here")
    
    elif 'edit_available_connections' in st.session_state:
        st.info("📝 No existing connections found. Create a new connection below.")
    
    st.markdown("---")
    
    # Progress indicator
    steps = ['Connection', 'Schema Discovery', 'Column Selection', 'Template Creation', 'Vector Embedding']
    current_step_idx = steps.index(st.session_state.db_config_step.title()) if st.session_state.db_config_step.title() in steps else 0
    
    progress_cols = st.columns(len(steps))
    for i, step in enumerate(steps):
        with progress_cols[i]:
            if i < current_step_idx:
                st.markdown(f"✅ **{step}**")
            elif i == current_step_idx:
                st.markdown(f"🔄 **{step}**")
            else:
                st.markdown(f"⏸️ {step}")
    
    st.markdown("---")
    
    # Step 1: Database Connection
    if st.session_state.db_config_step == 'connection':
        st.subheader("🔗 Step 1: Database Connection Setup")
        
        with st.form("db_connection_form"):
            st.markdown("**Enter your database credentials:**")
            
            conn_col1, conn_col2 = st.columns(2)
            
            with conn_col1:
                connection_name = st.text_input(
                    "Connection Name *",
                    placeholder="e.g., Production Database",
                    help="Give your connection a descriptive name"
                )
                
                database_type = st.selectbox(
                    "Database Type *",
                    ["postgresql", "mysql", "sqlite", "oracle", "sqlserver"],
                    help="Select your database type"
                )
                
                host = st.text_input(
                    "Host *",
                    placeholder="localhost or IP address",
                    help="Database server hostname or IP"
                )
                
                port = st.number_input(
                    "Port *",
                    value=5432 if database_type == "postgresql" else 3306,
                    min_value=1,
                    max_value=65535,
                    help="Database server port"
                )
            
            with conn_col2:
                database_name = st.text_input(
                    "Database Name *",
                    placeholder="database_name",
                    help="Name of the database to connect to"
                )
                
                username = st.text_input(
                    "Username *",
                    placeholder="db_username",
                    help="Database username"
                )
                
                password = st.text_input(
                    "Password *",
                    type="password",
                    placeholder="db_password",
                    help="Database password"
                )
                
                ssl_enabled = st.checkbox(
                    "Enable SSL",
                    help="Use SSL connection for security"
                )
                
                schema_name = st.text_input(
                    "Schema (Optional)",
                    placeholder="e.g., staging_dashboard",
                    help="Specific schema to focus on (optional)"
                )
            
            # Form buttons
            form_col1, form_col2 = st.columns(2)
            with form_col1:
                test_connection = st.form_submit_button("🔍 Test Connection", type="secondary")
            with form_col2:
                create_connection = st.form_submit_button("✅ Create & Continue", type="primary")
            
            if test_connection:
                if all([connection_name, host, database_name, username, password]):
                    connection_details = {
                        'name': connection_name,
                        'database_type': database_type,
                        'host': host,
                        'port': int(port),
                        'database_name': database_name,
                        'username': username,
                        'password': password,
                        'ssl_enabled': ssl_enabled,
                        'connection_params': {'schema': schema_name} if schema_name else {}
                    }
                    
                    with st.spinner("Testing database connection..."):
                        success, message = test_database_connection(connection_details)
                        if success:
                            st.success(f"✅ {message}")
                        else:
                            st.error(f"❌ {message}")
                else:
                    st.error("❌ Please fill in all required fields")
            
            if create_connection:
                if all([connection_name, host, database_name, username, password]):
                    connection_details = {
                        'name': connection_name,
                        'database_type': database_type,
                        'host': host,
                        'port': int(port),
                        'database_name': database_name,
                        'username': username,
                        'password': password,
                        'ssl_enabled': ssl_enabled,
                        'connection_params': {'schema': schema_name} if schema_name else {}
                    }
                    
                    with st.spinner("Creating database connection..."):
                        success, message, connection_id = create_database_connection(connection_details)
                        if success:
                            st.success(f"✅ {message}")
                            # Store connection details in multiple session state keys for compatibility
                            st.session_state.db_connection_id = connection_id
                            st.session_state.connection_id = connection_id  # Also store as connection_id
                            st.session_state.db_connection_details = connection_details  # Store for direct access
                            st.session_state.db_config_step = 'schema'
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                else:
                    st.error("❌ Please fill in all required fields")
    
    # Step 2: Schema Discovery
    elif st.session_state.db_config_step == 'schema':
        st.subheader("Step 2: Schema Discovery")
        st.info(f"Connected to database (ID: {st.session_state.db_connection_id})")
        
        st.markdown("**Direct schema analysis** - Fast and reliable connection to your database.")
        
        if st.button("Discover Database Schema", type="primary"):
            # Use direct schema discovery only
            if 'db_connection_details' not in st.session_state:
                st.error("Connection details not found. Please go back and create the connection again.")
            else:
                with st.spinner("Analyzing database schema... This should take just a few seconds."):
                    success, message, schema_data = get_database_schema_direct(st.session_state.db_connection_details)
                    if success:
                        st.success(f"Schema discovered: {message}")
                        st.session_state.db_schema_data = schema_data
                        # Ensure connection details persist to next step
                        if 'db_connection_id' in st.session_state:
                            st.session_state.connection_id = st.session_state.db_connection_id
                        st.session_state.db_config_step = 'columns'
                        st.rerun()
                    else:
                        st.error(f"Schema discovery failed: {message}")
        
        # Show previous schema if available
        if st.session_state.db_schema_data:
            st.markdown("### 📊 Previous Schema Analysis")
            schema_data = st.session_state.db_schema_data
            
            if 'tables' in schema_data:
                st.write(f"**Found {len(schema_data['tables'])} tables**")
                
                # Show table summary
                table_summary = []
                for table in schema_data['tables'][:10]:  # Show first 10 tables
                    table_summary.append({
                        'Table': table.get('table_name', 'Unknown'),
                        'Schema': table.get('schema_name', 'public'),
                        'Columns': len(table.get('columns', [])),
                        'Row Count': table.get('row_count', 'Unknown')
                    })
                
                if table_summary:
                    df = pd.DataFrame(table_summary)
                    st.dataframe(df, use_container_width=True)
                
                if len(schema_data['tables']) > 10:
                    st.info(f"Showing first 10 tables. Total: {len(schema_data['tables'])} tables found.")
            
            if st.button("➡️ Continue to Column Selection"):
                st.session_state.db_config_step = 'columns'
                st.rerun()
    
    # Step 3: Advanced Column & Table Analysis
    elif st.session_state.db_config_step == 'columns':
        st.subheader("Step 3: Intelligent Schema Analysis")
        st.markdown("**AI-powered analysis of tables and columns with editable insights:**")
        
        # Initialize session state for advanced analysis
        if 'table_analyses' not in st.session_state:
            st.session_state.table_analyses = {}
        if 'column_analyses' not in st.session_state:
            st.session_state.column_analyses = {}
        if 'selected_table_for_analysis' not in st.session_state:
            st.session_state.selected_table_for_analysis = None
        if 'selected_tables_for_storage' not in st.session_state:
            st.session_state.selected_tables_for_storage = set()
        
        if st.session_state.db_schema_data and 'tables' in st.session_state.db_schema_data:
            schema_data = st.session_state.db_schema_data
            
            # Advanced Analysis Interface
            st.markdown("### 🔬 AI-Powered Schema Intelligence")
            st.markdown("*Analyze tables and columns with AI insights, then select which to include in your template*")
            
            # Show current selection status
            analyzed_tables = len(st.session_state.table_analyses)
            selected_for_storage = len(st.session_state.selected_tables_for_storage)
            analyzed_columns = len(st.session_state.column_analyses)
            
            status_col1, status_col2, status_col3 = st.columns(3)
            with status_col1:
                st.metric("Tables Analyzed", analyzed_tables)
            with status_col2:
                st.metric("Tables Selected", selected_for_storage)
            with status_col3:
                st.metric("Columns Analyzed", analyzed_columns)
            
            # Two-column layout for analysis
            analysis_col1, analysis_col2 = st.columns([1, 1])
            
            with analysis_col1:
                st.markdown("**Table Selection & Analysis**")
                
                # Table selection controls
                tables = schema_data['tables']
                table_names = [f"{t.get('schema_name', 'public')}.{t.get('table_name', 'unknown')}" for t in tables]
                
                # Select All Tables functionality
                col_select_all, col_clear_all = st.columns(2)
                with col_select_all:
                    if st.button("📋 Select All Tables", help="Select all tables for template creation"):
                        for table_name in table_names:
                            st.session_state.selected_tables_for_storage.add(table_name)
                        st.rerun()
                
                with col_clear_all:
                    if st.button("🗑️ Clear All Tables", help="Clear all selected tables"):
                        st.session_state.selected_tables_for_storage.clear()
                        st.rerun()
                
                # Show selected tables for storage
                if st.session_state.selected_tables_for_storage:
                    st.markdown("**📋 Tables Selected for Template:**")
                    for table_key in st.session_state.selected_tables_for_storage:
                        st.write(f"✓ {table_key}")
                    
                    # Comprehensive One-Stop Analysis Button
                    st.markdown("---")
                    st.markdown("**🚀 One-Stop Solution**")
                    
                    if st.button("🎯 Generate Comprehensive Database Template", 
                                type="primary", 
                                help="Analyze all selected tables, generate business & schema descriptions, create unified template, and embed in vector DB"):
                        
                        if st.session_state.get('selected_tables_for_storage') and len(st.session_state.selected_tables_for_storage) > 0:
                            with st.spinner("🔄 Generating comprehensive database template... This may take 2-3 minutes."):
                                try:
                                    # Import required modules
                                    from app.services.advanced_schema_analyzer import create_schema_analyzer
                                    from app.models.database.schema_analysis_models import TableAnalysisModel
                                    from app.core.database import SessionLocal
                                    import json
                                    from datetime import datetime
                                    
                                    logger.info("Starting template generation from database analysis data")
                                    
                                    # Initialize template content sections
                                    business_rules_content = []
                                    schema_context_content = []
                                    domain_specific_content = []
                                    
                                    # Get database connection details
                                    connection_id = st.session_state.get('connection_id')
                                    database_name = st.session_state.db_connection_details.get('database_name', 'Unknown')
                                    schemas_analyzed = list(set([table_key.split('.')[0] for table_key in st.session_state.selected_tables_for_storage]))
                                    
                                    logger.info(f"Generating template for {len(st.session_state.selected_tables_for_storage)} tables from database: {database_name}")
                                    
                                    # Generate domain-specific prompts (financial domain focus)
                                    domain_specific_content.append(f"""
# Domain-Specific Prompts for Financial Services

## Financial Domain Context
This database contains financial services data with focus on loan management, disbursements, and customer lifecycle management.

## Query Guidelines for Financial Data
- Always consider regulatory compliance requirements
- Use appropriate date filtering for financial reporting periods
- Handle monetary amounts with proper precision (use ROUND function for PostgreSQL)
- Consider loan lifecycle stages when querying disbursement vs collection data
- Apply proper data governance rules for sensitive financial information

## Business Process Context
- **Loan Origination**: Customer onboarding, application processing, approval workflows
- **Disbursement Management**: Fund release, payment processing, transaction tracking
- **Collection Operations**: Payment collection, overdue management, recovery processes
- **Customer Lifecycle**: Account management, relationship tracking, service delivery

## Query Best Practices
- Use indexed columns for joins and filtering
- Filter by date ranges for performance optimization
- Aggregate monetary amounts carefully with proper rounding
- Consider data quality and completeness in financial calculations
""")
                                    
                                    # Generate business rules and schema context from database
                                    with SessionLocal() as db_session:
                                        for table_key in st.session_state.selected_tables_for_storage:
                                            schema_name, table_name = table_key.split('.', 1)
                                            
                                            # Get latest analysis for this table from database
                                            db_analysis = db_session.query(TableAnalysisModel).filter_by(
                                                connection_id=connection_id,
                                                schema_name=schema_name,
                                                table_name=table_name
                                            ).order_by(TableAnalysisModel.analyzed_at.desc()).first()
                                            
                                            if db_analysis:
                                                logger.info(f"Processing database analysis for table: {table_key}")
                                                
                                                # Extract analysis data
                                                primary_purpose = db_analysis.primary_purpose or 'Not specified'
                                                business_description = db_analysis.ai_business_description or 'No description available'
                                                key_columns = db_analysis.key_columns or []
                                                business_processes = db_analysis.business_processes or []
                                                primary_keys = db_analysis.primary_keys or []
                                                foreign_keys = db_analysis.foreign_keys or []
                                                columns_analysis = db_analysis.columns_analysis or []
                                                
                                                # Generate business rules section
                                                business_rules_content.append(f"""
## Table: {table_name} ({schema_name} schema)

### Business Context
**Primary Purpose**: {primary_purpose}
**Business Description**: {business_description}
**Row Count**: {db_analysis.row_count:,} rows
**Analysis Confidence**: {db_analysis.analysis_confidence:.1%}

### Key Business Information
**Key Columns**: {', '.join(key_columns) if key_columns else 'None identified'}
**Business Processes**: {', '.join(business_processes) if business_processes else 'None identified'}
**Data Category**: {db_analysis.data_category or 'Not specified'}

### Data Governance
**Primary Keys**: {', '.join(primary_keys) if primary_keys else 'None identified'}
**Foreign Keys**: {len(foreign_keys)} relationships identified
**Data Quality Score**: {db_analysis.analysis_confidence:.1%}

### Column Analysis
""")
                                                                                        # Add detailed column analysis
                                                if columns_analysis:
                                                    for col_data in columns_analysis:
                                                        col_name = col_data.get('column_name', 'Unknown')
                                                        data_type = col_data.get('data_type', 'Unknown')
                                                        business_desc = col_data.get('business_description', 'No description')
                                                        is_primary_key = col_data.get('is_primary_key', False)
                                                        foreign_key_target = col_data.get('foreign_key_target', None)
                                                        enum_values = col_data.get('enum_values', [])
                                                        
                                                        business_rules_content.append(f"""
**{col_name}** ({data_type}):
- Purpose: {business_desc}
- Type: {'Primary Key' if is_primary_key else f'Foreign Key → {foreign_key_target}' if foreign_key_target else 'Data Column'}
- Categorical Values: {len(enum_values)} options available
""")
                                                
                                                # Generate schema context section
                                                schema_context_content.append(f"""
### Table: {table_name} ({schema_name})

**Technical Specifications**:
- Row Count: {db_analysis.row_count:,}
- Column Count: {db_analysis.column_count}
- Table Type: {db_analysis.table_type or 'Standard'}
- Storage Size: {db_analysis.size_bytes or 'Unknown'} bytes

**Relationships**:
- Primary Keys: {', '.join(primary_keys) if primary_keys else 'None'}
- Foreign Keys: {len(foreign_keys)} relationships
- Parent Tables: {', '.join(db_analysis.parent_tables or [])}
- Child Tables: {', '.join(db_analysis.child_tables or [])}

**Query Optimization**:
- Indexed Columns: Primary keys and foreign keys
- Join Performance: {'Optimized' if primary_keys else 'Consider adding indexes'}
- Query Pattern: {'OLTP' if db_analysis.row_count < 1000000 else 'OLAP'} optimized
- Query Complexity: {'Low' if db_analysis.row_count < 100000 else 'High'}
""")
                                            else:
                                                logger.warning(f"No database analysis found for {table_key}")
                                                business_rules_content.append(f"""
## Table: {table_name} ({schema_name} schema)
**Status**: Analysis not found in database - please re-analyze this table
""")
                                                schema_context_content.append(f"""
### Table: {table_name} ({schema_name})
**Status**: Analysis not found in database - please re-analyze this table
""")
                                    
                                    # Combine all sections
                                    unified_business_rules = '\n'.join(business_rules_content)
                                    unified_schema_context = '\n'.join(schema_context_content)
                                    unified_domain_prompts = '\n'.join(domain_specific_content)
                                
                                    # Store in session state with organized template categories
                                    st.session_state.comprehensive_template = {
                                        'business_rules': unified_business_rules,
                                        'schema_context': unified_schema_context,
                                        'domain_prompts': unified_domain_prompts,
                                        'tables_analyzed': len(st.session_state.selected_tables_for_storage),
                                        'database_name': database_name,
                                        'schemas': schemas_analyzed,
                                        'generated_at': datetime.now(datetime.timezone.utc).isoformat(),
                                        'version': '3.0-production',
                                        'embedding_optimized': True,
                                        'query_generation_ready': True
                                    }
                                    
                                    logger.info(f"Template generation completed with {len(business_rules_content)} business rules sections, {len(schema_context_content)} schema sections, and {len(domain_specific_content)} domain sections")
                                    
                                    # Mark template generation as complete
                                    st.session_state.template_generation_complete = True
                                    
                                    # Show success message
                                    st.success(f"Template generation completed successfully! Generated {len(business_rules_content)} business rules sections, {len(schema_context_content)} schema sections, and {len(domain_specific_content)} domain sections.")
                                    
                                    logger.info("Template generation completed successfully")
                            
                                except Exception as e:
                                    logger.error(f"Error during template generation: {str(e)}")
                                    st.error(f"Template generation failed: {str(e)}")
                                    st.session_state.template_generation_complete = False
                        
                        else:
                            st.error("No tables selected for template generation")
                            logger.error("Template generation attempted with no selected tables")
                    
                    else:
                        st.warning("Please complete database connection and table selection first")
                        logger.warning("Template generation attempted without proper setup")
                    
                    # Display Generated Template if Available
                    if 'comprehensive_template' in st.session_state:
                        st.markdown("---")
                        st.markdown("## Generated Template")
                        
                        template_data = st.session_state.comprehensive_template
                        
                        # Template preview tabs
                        tab1, tab2, tab3 = st.tabs(["Business Rules", "Schema Context", "Domain Prompts"])
                        
                        with tab1:
                            st.text_area(
                                "Business Rules:",
                                value=template_data.get('business_rules', 'No business rules generated'),
                                height=300,
                                disabled=True
                            )
                        
                        with tab2:
                            st.text_area(
                                "Schema Context:",
                                value=template_data.get('schema_context', 'No schema context generated'),
                                height=300,
                                disabled=True
                            )
                        
                        with tab3:
                            st.text_area(
                                "Domain Prompts:",
                                value=template_data.get('domain_prompts', 'No domain prompts generated'),
                                height=300,
                                disabled=True
                            )
                    
                    st.markdown("---")
                
                # Table selection dropdown with current selection shown
                current_selection = None
                if hasattr(st.session_state, 'selected_table_for_analysis') and st.session_state.selected_table_for_analysis:
                    current_selection = st.session_state.selected_table_for_analysis.get('table_key')
                
                # Set default index based on current selection
                default_index = 0
                if current_selection and current_selection in table_names:
                    default_index = table_names.index(current_selection) + 1
                
                selected_table_name = st.selectbox(
                    "Select Table for Analysis:",
                    ["-- Select a table --"] + table_names,
                    index=default_index,
                    help="Choose a table to analyze with AI"
                )
                
                if selected_table_name and selected_table_name != "-- Select a table --":
                    # Parse table name
                    schema_name, table_name = selected_table_name.split('.', 1)
                    table_key = f"{schema_name}.{table_name}"
                    
                    # Store selected table
                    st.session_state.selected_table_for_analysis = {
                        'schema_name': schema_name,
                        'table_name': table_name,
                        'table_key': table_key
                    }
                    
                    # Cache status display
                    if 'db_connection_id' in st.session_state or 'connection_id' in st.session_state:
                        connection_id = st.session_state.get('connection_id') or st.session_state.get('db_connection_id')
                        if connection_id:
                            try:
                                from app.services.table_analysis_cache import table_analysis_cache
                                cache_stats = table_analysis_cache.get_cache_stats(connection_id)
                                if 'error' not in cache_stats:
                                    st.info(f"📊 **Cache Status**: {cache_stats['valid_cached']} valid, {cache_stats['expired_cached']} expired, {cache_stats['total_cached']} total cached analyses")
                            except Exception as e:
                                st.warning(f"Cache status unavailable: {e}")
                    
                    # On-demand table analysis button with cache integration
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        analyze_button = st.button(f"🔬 Analyze Table: {table_name}", type="primary")
                    with col2:
                        force_refresh = st.button("🔄 Force Refresh", help="Skip cache and force new analysis")
                    
                    if analyze_button or force_refresh:
                        # Check cache first (unless force refresh)
                        cached_analysis = None
                        connection_id = st.session_state.get('connection_id') or st.session_state.get('db_connection_id')
                        
                        if not force_refresh and connection_id:
                            try:
                                from app.services.table_analysis_cache import table_analysis_cache
                                cached_analysis = table_analysis_cache.get_cached_analysis(
                                    connection_id, schema_name, table_name
                                )
                                if cached_analysis:
                                    st.success(f"✅ Loaded cached analysis for {table_name} (saves 1-2 minutes!)")
                            except Exception as e:
                                st.warning(f"Cache lookup failed: {e}")
                        
                        if cached_analysis:
                            # Use cached analysis
                            st.session_state.table_analyses[table_key] = {
                                'business_description': cached_analysis.business_description,
                                'primary_purpose': cached_analysis.primary_purpose,
                                'data_category': cached_analysis.data_category,
                                'parent_tables': cached_analysis.parent_tables or [],
                                'child_tables': cached_analysis.child_tables or [],
                                'key_columns': cached_analysis.key_columns or [],
                                'business_processes': cached_analysis.business_processes or [],
                                'typical_queries': cached_analysis.typical_queries or [],
                                'join_patterns': cached_analysis.join_patterns or [],
                                'columns': cached_analysis.columns or [],
                                'row_count': cached_analysis.row_count,
                                'confidence_score': cached_analysis.confidence_score,
                                'analysis_source': 'cache',
                                'user_notes': getattr(cached_analysis, 'user_notes', ''),
                                'business_rules': getattr(cached_analysis, 'business_rules', ''),
                                'usage_context': getattr(cached_analysis, 'usage_context', ''),
                                'analyzed_at': cached_analysis.analyzed_at.isoformat() if hasattr(cached_analysis, 'analyzed_at') and cached_analysis.analyzed_at else None
                            }
                            st.rerun()
                        else:
                            # Perform new analysis
                            analysis_start_time = time.time()
                            with st.spinner(f"AI is analyzing table {table_name}... This may take 1-2 minutes."):
                                # Import and use the advanced analyzer
                                try:
                                    from app.services.advanced_schema_analyzer import create_schema_analyzer
                                    import asyncio
                                    import time
                                    
                                    analyzer = create_schema_analyzer()
                                    
                                    # Run async analysis in sync context
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                
                                    analysis = loop.run_until_complete(
                                        analyzer.analyze_table_on_demand(
                                            st.session_state.db_connection_details,
                                            table_name,
                                        schema_name
                                    )
                                )
                                
                                    loop.close()
                                    
                                    analysis_duration_ms = (time.time() - analysis_start_time) * 1000
                                    
                                    if analysis:
                                        # Store analysis in session state
                                        st.session_state.table_analyses[table_key] = {
                                            'business_description': analysis.business_description,
                                            'primary_purpose': analysis.primary_purpose,
                                            'data_category': analysis.data_category,
                                            'parent_tables': analysis.parent_tables or [],
                                            'child_tables': analysis.child_tables or [],
                                            'key_columns': analysis.key_columns or [],
                                            'business_processes': analysis.business_processes or [],
                                            'typical_queries': analysis.typical_queries or [],
                                            'join_patterns': analysis.join_patterns or [],
                                            'columns': analysis.columns or [],
                                            'row_count': analysis.row_count,
                                            'confidence_score': analysis.confidence_score,
                                            'analysis_source': 'fresh',
                                            'analysis_duration_ms': analysis_duration_ms,
                                            'user_notes': analysis.user_notes or '',
                                            'business_rules': analysis.business_rules or '',
                                            'usage_context': analysis.usage_context or '',
                                            'analyzed_at': analysis.analyzed_at.isoformat() if analysis.analyzed_at else None
                                        }
                                        
                                        # Ensure sample_data is initialized if missing
                                        if not hasattr(analysis, 'sample_data') or analysis.sample_data is None:
                                            analysis.sample_data = []
                                        
                                        # Save to database for persistence
                                        if connection_id:
                                            try:
                                                from app.services.table_analysis_cache import table_analysis_cache
                                                
                                                # Get table metadata for schema hash
                                                table_metadata = {
                                                    'table_name': table_name,
                                                    'schema_name': schema_name,
                                                    'columns': [
                                                        {
                                                            'name': col.column_name,
                                                            'type': col.data_type,
                                                            'nullable': col.is_nullable,
                                                            'primary_key': False  # Default
                                                        }
                                                        for col in (analysis.columns or [])
                                                    ]
                                                }
                                                
                                                # Save to database
                                                save_success = table_analysis_cache.save_analysis(
                                                    connection_id, analysis, table_metadata, analysis_duration_ms
                                                )
                                                
                                                if save_success:
                                                    st.success(f"✅ Analysis completed for {table_name} and saved to database! (took {analysis_duration_ms:.0f}ms)")
                                                else:
                                                    st.warning(f"⚠️ Analysis completed for {table_name} but database save failed! (took {analysis_duration_ms:.0f}ms)")
                                                    
                                            except Exception as cache_error:
                                                st.error(f"❌ Database save error for {table_name}: {str(cache_error)}")
                                                st.success(f"✅ Analysis completed for {table_name} (in memory only) - took {analysis_duration_ms:.0f}ms")
                                        else:
                                            st.warning(f"⚠️ Analysis completed for {table_name} but no connection_id for database save!")
                                        
                                        st.rerun()
                                    else:
                                        st.error("❌ Analysis failed - no results returned")
                                        
                                except Exception as e:
                                    st.error(f"❌ Analysis failed: {str(e)}")
                                    import traceback
                                    st.error(f"Error details: {traceback.format_exc()}")
                    
                    # Table selection checkbox for storage
                    table_selected_for_storage = st.checkbox(
                        f"Include {table_name} in template",
                        value=table_key in st.session_state.selected_tables_for_storage,
                        help="Select this table to include in your template creation",
                        key=f"table_storage_{table_key}"
                    )
                    
                    # Update selected tables set
                    if table_selected_for_storage:
                        st.session_state.selected_tables_for_storage.add(table_key)
                    else:
                        st.session_state.selected_tables_for_storage.discard(table_key)
                    
                    # Show existing analysis if available
                    if table_key in st.session_state.table_analyses:
                        analysis = st.session_state.table_analyses[table_key]
                        
                        st.markdown("**📈 Table Analysis Results**")
                        
                        # Editable description - Always expanded with full text display
                        with st.expander("📝 Business Description (LLM-Optimized for Query Generation)", expanded=True):
                            # Show full description with proper formatting
                            st.markdown("**AI-Generated Description (Optimized for LLM Query Generation):**")
                            edited_description = st.text_area(
                                "Description for Analysis",
                                value=analysis['business_description'],
                                height=250,  # Increased height to show full text
                                help="This description is optimized for LLM query generation with detailed enum values and column context",
                                key=f"table_desc_{table_key}"
                            )
                            
                            # Show column count and enum information
                            if 'columns' in analysis and analysis['columns']:
                                col_count = len(analysis['columns'])
                                # Handle both dict and ColumnAnalysis object formats
                                enum_cols = []
                                for col in analysis['columns']:
                                    if hasattr(col, 'enum_values'):  # ColumnAnalysis object
                                        if col.enum_values:
                                            enum_cols.append(col)
                                    elif isinstance(col, dict) and col.get('enum_values_explicit'):  # Dict format
                                        enum_cols.append(col)
                                analysis_source = analysis.get('analysis_source', 'unknown')
                                duration_info = ""
                                if 'analysis_duration_ms' in analysis:
                                    duration_info = f" | Analysis time: {analysis['analysis_duration_ms']:.0f}ms"
                                cache_indicator = "🔄 Fresh" if analysis_source == 'fresh' else "💾 Cached"
                                st.info(f"📊 **Analysis Summary:** {col_count} columns analyzed | {len(enum_cols)} enum columns detected | {cache_indicator}{duration_info}")
                                
                                # Show all enum columns summary
                                if enum_cols:
                                    st.markdown("**🎯 Enum Columns for Query Generation:**")
                                    for col in enum_cols:  # Show ALL enum columns
                                        # Handle both ColumnAnalysis objects and dict formats
                                        if hasattr(col, 'enum_values'):  # ColumnAnalysis object
                                            column_name = col.column_name
                                            enum_values = col.enum_values or []
                                            sample_values = col.sample_values or []
                                        else:  # Dict format
                                            column_name = col.get('column_name', 'Unknown')
                                            enum_values = col.get('enum_values_explicit', [])
                                            sample_values = col.get('distinct_values_sample', [])
                                        
                                        if enum_values:
                                            st.markdown(f"- **{column_name}**: {', '.join(enum_values[:8])}{'...' if len(enum_values) > 8 else ''}")
                                        elif sample_values:
                                            # Show categorical columns with distinct values
                                            st.markdown(f"- **{column_name}** (categorical): {', '.join(sample_values[:5])}{'...' if len(sample_values) > 5 else ''}")
                            
                            if edited_description != analysis['business_description']:
                                st.session_state.table_analyses[table_key]['business_description'] = edited_description
                        
                        # Show analysis details
                        st.write(f"**Purpose:** {analysis['primary_purpose']}")
                        st.write(f"**Category:** {analysis['data_category']}")
                        
                        if analysis['parent_tables']:
                            st.write(f"**References:** {', '.join(analysis['parent_tables'])}")
                        if analysis['child_tables']:
                            st.write(f"**Referenced by:** {', '.join(analysis['child_tables'])}")
                        
                        # User editable fields
                        with st.expander("📝 Add Your Insights"):
                            user_notes = st.text_area(
                                "Your Notes:",
                                value=analysis.get('user_notes', ''),
                                placeholder="Add your own insights about this table...",
                                key=f"table_notes_{table_key}"
                            )
                            
                            business_rules = st.text_area(
                                "Business Rules:",
                                value=analysis.get('business_rules', ''),
                                placeholder="e.g., 'Always filter by active status', 'Use for financial reporting'...",
                                key=f"table_rules_{table_key}"
                            )
                            
                            usage_context = st.text_area(
                                "Usage Context:",
                                value=analysis.get('usage_context', ''),
                                placeholder="e.g., 'Used in daily reports', 'Join with users table for analytics'...",
                                key=f"table_usage_{table_key}"
                            )
                            
                            # Update analysis with user input
                            st.session_state.table_analyses[table_key].update({
                                'user_notes': user_notes,
                                'business_rules': business_rules,
                                'usage_context': usage_context
                            })
            
            with analysis_col2:
                st.markdown("**📋 Column Analysis & Selection**")
                
                # Show columns for selected table
                if (st.session_state.selected_table_for_analysis and 
                    st.session_state.selected_table_for_analysis['table_key'] in st.session_state.table_analyses):
                    
                    selected_table = st.session_state.selected_table_for_analysis
                    table_key = selected_table['table_key']
                    
                    # Find the table data
                    table_data = None
                    for table in tables:
                        if (table.get('table_name') == selected_table['table_name'] and 
                            table.get('schema_name', 'public') == selected_table['schema_name']):
                            table_data = table
                            break
                    
                    if table_data and 'columns' in table_data:
                        columns = table_data['columns']
                        
                        st.write(f"**Analyzing columns in: {selected_table['table_name']}**")
                        
                        # Select All Columns functionality
                        col_select_all_cols, col_clear_all_cols = st.columns(2)
                        with col_select_all_cols:
                            if st.button("📋 Select All Columns", key=f"select_all_cols_{table_key}", help="Select all columns for template creation"):
                                for col in columns:
                                    col_name = col.get('column_name', 'unknown')
                                    col_key = f"{table_key}.{col_name}"
                                    st.session_state.selected_columns[col_key] = True
                                st.rerun()
                        
                        with col_clear_all_cols:
                            if st.button("🗑️ Clear All Columns", key=f"clear_all_cols_{table_key}", help="Clear all selected columns"):
                                for col in columns:
                                    col_name = col.get('column_name', 'unknown')
                                    col_key = f"{table_key}.{col_name}"
                                    st.session_state.selected_columns[col_key] = False
                                st.rerun()
                        
                        st.markdown("---")
                        
                        # Column selection with analysis
                        for i, col in enumerate(columns[:10]):  # Limit to first 10 columns
                            col_name = col.get('column_name', 'unknown')
                            col_type = col.get('data_type', 'unknown')
                            col_key = f"{table_key}.{col_name}"
                            
                            with st.expander(f"📄 {col_name} ({col_type})", expanded=False):
                                # Column selection checkbox
                                col_selected = st.checkbox(
                                    f"Include {col_name} in templates",
                                    value=st.session_state.selected_columns.get(col_key, False),
                                    key=f"col_select_{col_key}"
                                )
                                st.session_state.selected_columns[col_key] = col_selected
                                
                                # On-demand column analysis
                                if st.button(f"🔬 Analyze Column", key=f"analyze_{col_key}"):
                                    with st.spinner(f"Analyzing {col_name}..."):
                                        try:
                                            from app.services.advanced_schema_analyzer import create_schema_analyzer
                                            import asyncio
                                            
                                            analyzer = create_schema_analyzer()
                                            
                                            # Run async analysis
                                            loop = asyncio.new_event_loop()
                                            asyncio.set_event_loop(loop)
                                            
                                            col_analysis = loop.run_until_complete(
                                                analyzer.analyze_column_on_demand(
                                                    st.session_state.db_connection_details,
                                                    selected_table['table_name'],
                                                    col_name,
                                                    selected_table['schema_name']
                                                )
                                            )
                                            
                                            loop.close()
                                            
                                            # Store column analysis
                                            st.session_state.column_analyses[col_key] = {
                                                'business_description': col_analysis.business_description,
                                                'category': col_analysis.category,
                                                'sample_values': col_analysis.sample_values or [],
                                                'distinct_count': col_analysis.distinct_count,
                                                'enum_values': col_analysis.enum_values or [],
                                                'user_notes': '',
                                                'business_rules': '',
                                                'confidence_score': col_analysis.confidence_score
                                            }
                                            
                                            st.success(f"✓ Column analysis complete!")
                                            st.rerun()
                                            
                                        except Exception as e:
                                            st.error(f"✗ Column analysis failed: {str(e)}")
                                
                                # Show existing column analysis
                                if col_key in st.session_state.column_analyses:
                                    col_analysis = st.session_state.column_analyses[col_key]
                                    
                                    # AI-generated insights
                                    st.write(f"**AI Category:** {col_analysis['category']}")
                                    
                                    # Editable description
                                    edited_col_desc = st.text_area(
                                        "Description:",
                                        value=col_analysis['business_description'],
                                        height=60,
                                        key=f"col_desc_{col_key}"
                                    )
                                    st.session_state.column_analyses[col_key]['business_description'] = edited_col_desc
                                    
                                    # Sample values
                                    if col_analysis['sample_values']:
                                        st.write(f"**Sample Values:** {', '.join(col_analysis['sample_values'][:5])}")
                                    
                                    # Enum detection
                                    if col_analysis['enum_values'] and len(col_analysis['enum_values']) <= 10:
                                        st.write(f"**Possible Enum:** {', '.join(col_analysis['enum_values'])}")
                                        
                                        # Ask for confirmation
                                        is_enum = st.checkbox(
                                            "Is this an enum/category column?",
                                            key=f"enum_confirm_{col_key}"
                                        )
                                    
                                    # Distinct count info
                                    if col_analysis['distinct_count'] is not None:
                                        st.write(f"**Distinct Values:** {col_analysis['distinct_count']}")
                                    
                                    # User input for additional context
                                    user_col_notes = st.text_area(
                                        "Your Notes:",
                                        value=col_analysis.get('user_notes', ''),
                                        placeholder="e.g., 'This column is used for...', 'Always non-null in practice'...",
                                        height=50,
                                        key=f"col_notes_{col_key}"
                                    )
                                    st.session_state.column_analyses[col_key]['user_notes'] = user_col_notes
                
                else:
                    st.info("↑ Select and analyze a table first to see its columns")
            
            # Summary and continue button
            st.markdown("---")
            selected_count = sum(1 for v in st.session_state.selected_columns.values() if v)
            analyzed_tables = len(st.session_state.table_analyses)
            analyzed_columns = len(st.session_state.column_analyses)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Selected Columns", selected_count)
            with col2:
                st.metric("Analyzed Tables", analyzed_tables)
            with col3:
                st.metric("Analyzed Columns", analyzed_columns)
            
            if selected_count > 0:
                if st.button("Continue to Enum Mapping Discovery", type="primary"):
                    st.session_state.db_config_step = 'enum_mapping'
                    st.rerun()
            else:
                st.warning("Please select at least one column to continue")

        else:
            st.error("No schema data available. Please go back to Schema Discovery.")
    
    # Step 4: Automated Enum Mapping (NEW)
    elif st.session_state.db_config_step == 'enum_mapping':
        st.subheader("Step 4: Automated Enum Mapping Discovery")
        st.markdown("**AI will automatically discover enum columns and generate natural language mappings:**")
        
        # Show selected tables and columns summary
        selected_columns = {k: v for k, v in st.session_state.selected_columns.items() if v}
        selected_tables = list(st.session_state.selected_tables_for_storage)
        
        st.info(f"🔍 Analyzing {len(selected_tables)} selected tables with {len(selected_columns)} selected columns for enum patterns")
        
        # Debug information
        with st.expander("🔧 Debug Information", expanded=False):
            st.write("**Session State Debug:**")
            st.write(f"- Selected tables: {selected_tables}")
            st.write(f"- Connection ID: {st.session_state.get('connection_id', 'NOT SET')}")
            st.write(f"- Selected tables for storage: {st.session_state.get('selected_tables_for_storage', 'NOT SET')}")
            st.write(f"- Selected columns count: {len(selected_columns)}")
            st.write(f"- Enum mapping status: {st.session_state.get('enum_mapping_status', 'NOT SET')}")
        
        # Initialize enum mapping state
        if 'enum_mapping_results' not in st.session_state:
            st.session_state.enum_mapping_results = None
        if 'enum_mapping_status' not in st.session_state:
            st.session_state.enum_mapping_status = 'ready'
        
        # Show selected tables
        if selected_tables:
            with st.expander("📋 Selected Tables for Enum Analysis", expanded=True):
                for i, table in enumerate(selected_tables, 1):
                    st.write(f"{i}. `{table}`")
        
        # Enum mapping controls
        enum_col1, enum_col2, enum_col3 = st.columns([2, 1, 1])
        
        with enum_col1:
            if st.button("🤖 Generate Enum Mappings", type="primary", disabled=st.session_state.enum_mapping_status == 'running'):
                # Improved validation with detailed error messages
                connection_id = st.session_state.get('connection_id') or st.session_state.get('db_connection_id')
                connection_details = st.session_state.get('db_connection_details')
                
                if not connection_id:
                    st.error("❌ No database connection found. Please go back to Schema Discovery and connect to your database.")
                    st.info(f"🔍 Debug: Available session keys: {list(st.session_state.keys())}")
                elif not connection_details:
                    st.error("❌ No database connection details found. Please go back to Schema Discovery and connect to your database.")
                    st.info(f"🔍 Debug: Connection ID found but details missing: {connection_id}")
                elif not selected_tables:
                    st.error("❌ No tables selected. Please go back to Table Analysis and select at least one table.")
                elif len(selected_tables) == 0:
                    st.error("❌ Selected tables list is empty. Please go back to Table Analysis and select tables.")
                else:
                    st.success(f"✅ Validation passed: {len(selected_tables)} tables selected, connection ID: {connection_id[:8] if len(connection_id) > 8 else connection_id}...")
                    st.info(f"🔗 Connection details available: {bool(connection_details)}")
                    with st.spinner("🔍 AI is analyzing your schema for enum patterns..."):
                        try:
                            # Import the enum mapping generator
                            from app.services.automated_enum_mapping_generator import generate_enum_mappings_for_connection
                            from app.agents.configurator.database_persistence import ConfiguratorDatabase
                            
                            st.session_state.enum_mapping_status = 'running'
                            
                            # Get connection details - use session state first, fallback to database
                            import asyncio
                            
                            if connection_details:
                                # Use existing connection details from session state
                                st.info("🔗 Using connection details from session state")
                            else:
                                # Fallback to database lookup
                                st.info("🔄 Loading connection details from database...")
                                configurator_db = ConfiguratorDatabase()
                                db_connection = asyncio.run(configurator_db.get_database_connection(connection_id))
                                
                                if db_connection:
                                    # Convert database connection to dictionary format
                                    connection_details = {
                                        "database_type": db_connection.database_type,
                                        "host": db_connection.host,
                                        "port": db_connection.port,
                                        "database_name": db_connection.database_name,
                                        "username": db_connection.username,
                                        "password": db_connection.password,
                                        "ssl_enabled": db_connection.ssl_enabled,
                                        "connection_params": db_connection.connection_params or {}
                                    }
                                    # Store in session state for future use
                                    st.session_state.db_connection_details = connection_details
                                else:
                                    st.error("❌ Could not load connection details from database")
                                    st.session_state.enum_mapping_status = 'error'
                                    st.stop()
                            
                            # Ensure we have connection details at this point
                            if connection_details:
                                
                                # Generate enum mappings for selected tables only
                                result = asyncio.run(generate_enum_mappings_for_connection(
                                    connection_id=st.session_state.connection_id,
                                    connection_details=connection_details,
                                    target_schema="staging_dashboard",  # You can make this configurable
                                    target_tables=selected_tables
                                ))
                                
                                st.session_state.enum_mapping_results = result
                                st.session_state.enum_mapping_status = 'completed'
                                st.rerun()
                            else:
                                st.error("❌ Could not retrieve database connection details")
                                st.session_state.enum_mapping_status = 'error'
                                
                        except Exception as e:
                            st.error(f"❌ Error generating enum mappings: {str(e)}")
                            st.session_state.enum_mapping_status = 'error'
        
        with enum_col2:
            if st.button("⏭️ Skip Enum Mapping"):
                st.session_state.db_config_step = 'templates'
                st.rerun()
        
        with enum_col3:
            if st.button("🔄 Reset"):
                st.session_state.enum_mapping_results = None
                st.session_state.enum_mapping_status = 'ready'
                st.rerun()
        
        # Show enum mapping results
        if st.session_state.enum_mapping_results:
            result = st.session_state.enum_mapping_results
            
            if result.get('success'):
                st.success(f"✅ Successfully analyzed {result['enum_columns_found']} enum columns and generated {result['mapping_rules_generated']} mapping rules!")
                
                # Show discovered enum columns
                if result.get('enum_columns_details'):
                    with st.expander("🔤 Discovered Enum Columns", expanded=True):
                        for col_detail in result['enum_columns_details']:
                            st.markdown(f"""
                            **`{col_detail['table']}.{col_detail['column']}`**
                            - Enum values: {col_detail['enum_count']}
                            - Confidence: {col_detail['confidence']:.2f}
                            """)
                
                # Show preview of generated mappings
                if result.get('template_content'):
                    with st.expander("📝 Generated Enum Mapping Rules Preview", expanded=False):
                        st.code(result['template_content'][:2000] + "..." if len(result['template_content']) > 2000 else result['template_content'], language="text")
                
                # Apply mappings option
                apply_col1, apply_col2 = st.columns([1, 1])
                with apply_col1:
                    if st.button("✅ Apply Enum Mappings", type="primary"):
                        try:
                            # Apply mappings to business rules template
                            template_file_path = "/Users/vaishakh/Code/supervisory-agent/templates/enhanced_business_rules_template.txt"
                            
                            with open(template_file_path, 'r') as f:
                                current_content = f.read()
                            
                            # Append new enum mappings
                            updated_content = current_content + result['template_file_update']
                            
                            with open(template_file_path, 'w') as f:
                                f.write(updated_content)
                            
                            st.success("✅ Enum mappings successfully applied to business rules template!")
                            st.info("🎯 Your natural language queries will now automatically map to correct enum values")
                            
                            # Auto-advance to next step
                            st.session_state.db_config_step = 'templates'
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Error applying enum mappings: {str(e)}")
                
                with apply_col2:
                    if st.button("➡️ Continue Without Applying"):
                        st.session_state.db_config_step = 'templates'
                        st.rerun()
            else:
                st.error(f"❌ Enum mapping generation failed: {result.get('error', 'Unknown error')}")
        
        elif st.session_state.enum_mapping_status == 'running':
            st.info("🔄 Generating enum mappings... This may take a few moments.")
        
        # Navigation
        nav_col1, nav_col2 = st.columns([1, 1])
        with nav_col1:
            if st.button("⬅️ Back to Column Selection"):
                st.session_state.db_config_step = 'column_selection'
                st.rerun()
        with nav_col2:
            if st.button("➡️ Continue to Templates"):
                st.session_state.db_config_step = 'templates'
                st.rerun()

    # Step 5: Template Creation
    elif st.session_state.db_config_step == 'templates':
        st.subheader("Step 4: LLM-Guided Template Creation")
        st.markdown("**The LLM will help you create comprehensive templates based on your selected schema:**")
        
        # Show selected columns summary
        selected_columns = {k: v for k, v in st.session_state.selected_columns.items() if v}
        st.info(f"Working with {len(selected_columns)} selected columns")
        
        # Template creation form with LLM guidance
        with st.form("template_creation_form"):
            st.markdown("### LLM-Assisted Template Generation")
            
            # Get database name for better template naming
            db_name = "Unknown"
            if hasattr(st.session_state, 'db_schema_data') and st.session_state.db_schema_data:
                db_name = st.session_state.db_schema_data.get('database_name', 'Unknown')
            
            # Basic template info in symmetric grid
            template_col1, template_col2 = st.columns(2)
            with template_col1:
                st.markdown("**Template Information**")
                template_name = st.text_input(
                    "Template Name *",
                    value=f"{db_name} Template {datetime.now().strftime('%Y%m%d_%H%M')}",
                    help="Descriptive name for your template"
                )
                
                domain_context = st.selectbox(
                    "Business Domain *",
                    ["financial", "healthcare", "ecommerce", "manufacturing", "education", "general"],
                    help="Select your business domain for better context"
                )
            
            with template_col2:
                template_version = st.text_input(
                    "Version *",
                    value="1.0",
                    help="Template version"
                )
                
                database_type = st.selectbox(
                    "Database Type",
                    ["postgresql", "mysql", "sqlite", "oracle", "sqlserver"],
                    help="Your database type"
                )
            
            # LLM-guided content in symmetric layout
            st.markdown("### Template Content")
            st.info("The following templates are auto-generated based on your schema. You can customize them as needed.")
            
            content_col1, content_col2 = st.columns(2)
            
            with content_col1:
                st.markdown("**Business Rules**")
                # Generate detailed business rules from actual table analysis
                business_rules_value = ""
                
                if 'comprehensive_template' in st.session_state and st.session_state.comprehensive_template:
                    business_rules_value = st.session_state.comprehensive_template['business_rules']
                else:
                    # Generate business rules from database analysis
                    from app.models.database.schema_analysis_models import TableAnalysisModel
                    from app.core.database import SessionLocal
                    import logging
                    
                    # Set up logging for debugging
                    logging.basicConfig(level=logging.INFO)
                    logger = logging.getLogger(__name__)
                    
                    try:
                        logger.info("Starting business rules template generation")
                        with SessionLocal() as db_session:
                            connection_id = st.session_state.get('connection_id')
                            logger.info(f"Using connection_id: {connection_id}")
                            
                            if connection_id:
                                # Get all analyzed tables for this connection
                                logger.info(f"Querying TableAnalysisModel for connection_id: {connection_id}")
                                analyzed_tables = db_session.query(TableAnalysisModel).filter_by(
                                    connection_id=connection_id
                                ).order_by(TableAnalysisModel.analyzed_at.desc()).all()
                                
                                logger.info(f"Found {len(analyzed_tables)} analyzed tables")
                                
                                if analyzed_tables:
                                    business_rules_parts = []
                                    business_rules_parts.append("# Financial Domain Business Rules\n")
                                    
                                    for i, analysis in enumerate(analyzed_tables):
                                        table_name = analysis.table_name
                                        schema_name = analysis.schema_name
                                        logger.info(f"Processing table {i+1}/{len(analyzed_tables)}: {schema_name}.{table_name}")
                                        
                                        # Extract business context
                                        primary_purpose = analysis.primary_purpose or 'Data storage and management'
                                        business_description = analysis.ai_business_description or 'No specific business description available'
                                        key_columns = analysis.key_columns or []
                                        business_processes = analysis.business_processes or []
                                        columns_analysis = analysis.columns_analysis or []
                                        
                                        logger.info(f"Table {table_name}: {len(columns_analysis)} columns analyzed, confidence: {analysis.analysis_confidence:.1%}")
                                        
                                        business_rules_parts.append(f"""
## Table: {table_name} ({schema_name} schema)

**Business Purpose**: {primary_purpose}

**Description**: {business_description}

**Key Business Information**:
- Row Count: {analysis.row_count:,} records
- Business Processes: {', '.join(business_processes) if business_processes else 'General data operations'}
- Data Category: {analysis.data_category or 'Operational data'}
- Analysis Confidence: {analysis.analysis_confidence:.1%}

**Column Analysis & Business Rules**:""")
                                        
                                        # Add detailed column analysis with enum values
                                        if columns_analysis:
                                            logger.info(f"Processing {len(columns_analysis)} columns for table {table_name}")
                                            for col_idx, col_data in enumerate(columns_analysis):
                                                col_name = col_data.get('column_name', 'Unknown')
                                                data_type = col_data.get('data_type', 'Unknown')
                                                business_desc = col_data.get('business_description', 'No description')
                                                enum_values = col_data.get('enum_values', [])
                                                is_primary_key = col_data.get('is_primary_key', False)
                                                is_foreign_key = col_data.get('is_foreign_key', False)
                                                
                                                if enum_values:
                                                    logger.info(f"Column {col_name}: Found {len(enum_values)} enum values: {enum_values[:5]}{'...' if len(enum_values) > 5 else ''}")
                                                
                                                business_rules_parts.append(f"""
- **{col_name}** ({data_type}): {business_desc}""")
                                                
                                                if enum_values:
                                                    enum_str = ', '.join([f"'{val}'" for val in enum_values[:10]])
                                                    if len(enum_values) > 10:
                                                        enum_str += f" (and {len(enum_values) - 10} more)"
                                                    business_rules_parts.append(f"  - Enum Values: [{enum_str}]")
                                                
                                                if is_primary_key:
                                                    business_rules_parts.append(f"  - Primary Key: Use for unique identification and joins")
                                                elif is_foreign_key:
                                                    business_rules_parts.append(f"  - Foreign Key: Use for table relationships")
                                        
                                        # Add query guidelines
                                        business_rules_parts.append(f"""
**Query Guidelines for {table_name}**:
- Use indexed columns ({', '.join(analysis.primary_keys or ['id'])}) for optimal performance
- Apply appropriate date filtering on timestamp columns (created_at, updated_at)
- Consider data quality when aggregating monetary amounts
- Join with related tables using primary/foreign key relationships
- Filter by status/type columns for business logic compliance

**Common Query Patterns**:
- Status-based filtering: WHERE status = 'ACTIVE'
- Date range queries: WHERE created_at BETWEEN '2024-01-01' AND '2024-12-31'
- Geographic filtering: WHERE state = 'Maharashtra' AND locality = 'Pune'
- Lifecycle stage queries: WHERE level IN ('APPROVED', 'DISBURSED')

---""")
                                    
                                    logger.info(f"Generated business rules template with {len(business_rules_parts)} sections")
                                    business_rules_value = '\n'.join(business_rules_parts)
                                else:
                                    logger.warning("No analyzed tables found for connection")
                                    business_rules_value = "No table analysis available. Please analyze tables first to generate detailed business rules."
                            else:
                                logger.error("No connection_id found in session state")
                                business_rules_value = "No database connection found. Please connect to a database first."
                    except Exception as e:
                        logger.error(f"Error generating business rules: {str(e)}", exc_info=True)
                        business_rules_value = f"Error generating business rules: {str(e)}"
                
                st.markdown('<div class="large-textarea">', unsafe_allow_html=True)
                business_rules = st.text_area(
                    "Business Rules Template *",
                    value=business_rules_value,
                    height=350,
                    help="Business rules for query generation",
                    key="business_rules_input"
                )
                st.markdown('</div>', unsafe_allow_html=True)
            
            with content_col2:
                st.markdown("**Schema Context**")
                # Generate detailed schema context from actual table analysis
                schema_context_value = ""
                
                if 'comprehensive_template' in st.session_state and st.session_state.comprehensive_template:
                    schema_context_value = st.session_state.comprehensive_template['schema_context']
                else:
                    # Generate schema context from database analysis
                    try:
                        logger.info("Starting schema context template generation")
                        with SessionLocal() as db_session:
                            connection_id = st.session_state.get('connection_id')
                            logger.info(f"Using connection_id for schema context: {connection_id}")
                            
                            if connection_id:
                                # Get all analyzed tables for this connection
                                logger.info(f"Querying TableAnalysisModel for schema context, connection_id: {connection_id}")
                                analyzed_tables = db_session.query(TableAnalysisModel).filter_by(
                                    connection_id=connection_id
                                ).order_by(TableAnalysisModel.analyzed_at.desc()).all()
                                
                                logger.info(f"Found {len(analyzed_tables)} tables for schema context generation")
                                
                                if analyzed_tables:
                                    schema_context_parts = []
                                    schema_context_parts.append("# Database Schema Context\n")
                                    
                                    for i, analysis in enumerate(analyzed_tables):
                                        table_name = analysis.table_name
                                        schema_name = analysis.schema_name
                                        logger.info(f"Processing schema context for table {i+1}/{len(analyzed_tables)}: {schema_name}.{table_name}")
                                        
                                        # Extract technical specifications
                                        primary_keys = analysis.primary_keys or []
                                        foreign_keys = analysis.foreign_keys or []
                                        columns_analysis = analysis.columns_analysis or []
                                        
                                        logger.info(f"Schema context - Table {table_name}: {len(primary_keys)} PKs, {len(foreign_keys)} FKs, {len(columns_analysis)} columns")
                                        
                                        schema_context_parts.append(f"""
## Table: {table_name} ({schema_name})

**Technical Specifications**:
- Row Count: {analysis.row_count:,}
- Column Count: {analysis.column_count}
- Table Type: {analysis.table_type or 'Standard'}
- Storage Size: {analysis.size_bytes or 'Unknown'} bytes

**Primary Keys**: {', '.join(primary_keys) if primary_keys else 'None identified'}
**Foreign Keys**: {len(foreign_keys)} relationships identified

**Column Schema Details**:""")
                                        
                                        # Add detailed column schema information
                                        if columns_analysis:
                                            for col_data in columns_analysis:
                                                col_name = col_data.get('column_name', 'Unknown')
                                                data_type = col_data.get('data_type', 'Unknown')
                                                is_nullable = col_data.get('is_nullable', True)
                                                is_primary_key = col_data.get('is_primary_key', False)
                                                is_foreign_key = col_data.get('is_foreign_key', False)
                                                max_length = col_data.get('max_length')
                                                default_value = col_data.get('default_value')
                                                
                                                key_indicator = ""
                                                if is_primary_key:
                                                    key_indicator = " [PK]"
                                                elif is_foreign_key:
                                                    key_indicator = " [FK]"
                                                
                                                nullable_indicator = "(NOT NULL)" if not is_nullable else "(nullable)"
                                                
                                                schema_context_parts.append(f"""
- **{col_name}**: {data_type}{key_indicator} {nullable_indicator}""")
                                                
                                                if max_length:
                                                    schema_context_parts.append(f"  - Max Length: {max_length}")
                                                if default_value:
                                                    schema_context_parts.append(f"  - Default: {default_value}")
                                        
                                        # Add relationship information
                                        if foreign_keys:
                                            schema_context_parts.append(f"""
**Relationships**:""")
                                            for fk in foreign_keys:
                                                if isinstance(fk, dict):
                                                    column = fk.get('column', 'unknown')
                                                    referenced_table = fk.get('referenced_table', 'unknown')
                                                    schema_context_parts.append(f"- {column} → {referenced_table}")
                                        
                                        # Add query optimization notes
                                        schema_context_parts.append(f"""
**Query Optimization**:
- Indexed Columns: Primary keys and foreign keys
- Join Performance: {'Optimized' if primary_keys else 'Consider adding indexes'}
- Query Pattern: {'OLTP' if analysis.row_count < 1000000 else 'OLAP'} optimized
- Best Practices: Use indexed columns for WHERE clauses and JOINs

**Data Quality Notes**:
- Analysis Confidence: {analysis.analysis_confidence:.1%}
- Data Completeness: Review nullable columns for completeness
- Referential Integrity: Validate foreign key relationships

---""")
                                    
                                    logger.info(f"Generated schema context template with {len(schema_context_parts)} sections")
                                    schema_context_value = '\n'.join(schema_context_parts)
                                else:
                                    logger.warning("No analyzed tables found for schema context generation")
                                    schema_context_value = "No table analysis available. Please analyze tables first to generate detailed schema context."
                            else:
                                logger.error("No connection_id found in session state for schema context")
                                schema_context_value = "No database connection found. Please connect to a database first."
                    except Exception as e:
                        logger.error(f"Error generating schema context: {str(e)}", exc_info=True)
                        schema_context_value = f"Error generating schema context: {str(e)}"
                
                st.markdown('<div class="large-textarea">', unsafe_allow_html=True)
                schema_context = st.text_area(
                    "Schema Context Template *",
                    value=schema_context_value,
                    height=350,
                    help="Schema context for query generation",
                    key="schema_context_input"
                )
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Domain-Specific Prompts (full width)
            st.markdown("**Domain-Specific Prompts**")
            domain_prompts_text = f"""Domain-Specific Prompts for {domain_context}:

- Focus on {domain_context}-specific metrics and KPIs
- Apply industry best practices for data analysis
- Consider regulatory and compliance requirements
- Use appropriate aggregation methods for {domain_context} data
- Handle {domain_context}-specific date ranges and time periods"""
            
            st.markdown('<div class="medium-textarea">', unsafe_allow_html=True)
            domain_prompts = st.text_area(
                "Domain-Specific Prompts",
                value=domain_prompts_text,
                height=200,
                help="Domain-specific guidance for query generation"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Submit button
            create_template_btn = st.form_submit_button("Create Template & Embed to Vector DB", type="primary")
            
            if create_template_btn:
                if all([template_name, business_rules, schema_context]):
                    # Create template with selected columns metadata
                    template_data = {
                        'template_name': template_name.strip(),
                        'version': template_version.strip(),
                        'database_type': database_type,
                        'domain_hint': domain_context,
                        'business_rules': business_rules.strip(),
                        'schema_context': schema_context.strip(),
                        'domain_prompts': domain_prompts.strip() if domain_prompts.strip() else None,
                        'selected_columns': selected_columns,
                        'schema_metadata': st.session_state.db_schema_data
                    }
                    
                    with st.spinner("Creating template and embedding to vector database..."):
                        # Create template in database
                        success, message = create_new_template(st.session_state.db_connection_id, template_data)
                        if success:
                            st.success(f"Template created successfully: {message}")
                            st.session_state.db_config_step = 'embedding'
                            st.rerun()
                        else:
                            st.error(f"Error creating template: {message}")
                else:
                    st.error("Please fill in all required template fields")
    
    # Step 5: Configuration Complete
    elif st.session_state.db_config_step == 'embedding':
        st.subheader("Step 5: Configuration Complete!")
        
        st.markdown('<div class="success-card">', unsafe_allow_html=True)
        st.markdown("""
        **Database Configuration Completed Successfully!**
        
        Your configuration includes:
        - Database connection established
        - Schema analyzed and columns selected
        - Templates created with LLM guidance
        - Template stored in SQL database
        - Ready for query testing
        
        **Note:** Vector embedding occurs automatically during the configurator workflow when schema analysis is performed.
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Summary information
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Configuration Summary")
            st.write(f"**Connection ID:** {st.session_state.db_connection_id}")
            selected_count = sum(1 for v in st.session_state.selected_columns.values() if v)
            st.write(f"**Selected Columns:** {selected_count}")
            st.write(f"**Templates Created:** 1")
        
        with col2:
            st.markdown("### Next Steps")
            st.write("1. Go to **Query Testing** tab")
            st.write("2. Load your new template")
            st.write("3. Test natural language queries")
            st.write("4. Validate and refine as needed")
        
        # Action buttons
        action_col1, action_col2, action_col3 = st.columns(3)
        with action_col1:
            if st.button("Go to Query Testing", type="primary"):
                # Switch to query testing tab (this would need JavaScript or page refresh)
                st.info("Please click on the 'Query Testing' tab above to start testing your queries!")
        
        with action_col2:
            if st.button("Start New Configuration"):
                # Reset all session state
                st.session_state.db_config_step = 'connection'
                st.session_state.db_connection_id = None
                st.session_state.db_schema_data = None
                st.session_state.selected_columns = {}
                st.session_state.configuration_session_id = None
                st.rerun()
        
        with action_col3:
            if st.button("📋 Manage Templates"):
                st.info("🔄 Please click on the 'Template Management' tab above to manage your templates!")
    
    # Navigation buttons (always visible)
    st.markdown("---")
    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
    
    with nav_col1:
        if st.session_state.db_config_step != 'connection':
            if st.button("⬅️ Previous Step"):
                steps_order = ['connection', 'schema', 'columns', 'templates', 'embedding']
                current_idx = steps_order.index(st.session_state.db_config_step)
                if current_idx > 0:
                    st.session_state.db_config_step = steps_order[current_idx - 1]
                    st.rerun()
    
    with nav_col3:
        if st.button("🔄 Reset Configuration"):
            st.session_state.db_config_step = 'connection'
            st.session_state.db_connection_id = None
            st.session_state.db_schema_data = None
            st.session_state.selected_columns = {}
            st.session_state.configuration_session_id = None
            st.rerun()

with tab4:
    st.header("🔧 Setup & Debug")
    
    # System status overview
    st.subheader("📊 System Status Overview")
    
    # Status check buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh All Status", help="Check all system components"):
            st.session_state.force_status_refresh = True
    
    with col2:
        if st.button("🛠️ Create Missing Tables", help="Create any missing database tables"):
            with st.spinner("Creating tables..."):
                success, message = create_missing_tables()
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
    
    with col3:
        if st.button("🔥 Start Phoenix Tracing", help="Setup Phoenix for LLM observability"):
            with st.spinner("Setting up Phoenix..."):
                result = setup_phoenix_tracing()
                if result['status'] == 'started':
                    st.success(f"✅ {result['message']}")
                    st.info(f"🌐 Phoenix UI: {result['url']}")
                    st.session_state.phoenix_enabled = True
                elif result['status'] == 'running':
                    st.info(f"🔄 {result['message']}")
                    st.info(f"🌐 Phoenix UI: {result['url']}")
                    st.session_state.phoenix_enabled = True
                else:
                    st.error(f"❌ {result['message']}")
    
    st.markdown("---")
    
    # Detailed status checks
    status_col1, status_col2 = st.columns(2)
    
    with status_col1:
        # Import Status
        with st.expander("📦 Import Status", expanded=True):
            imports = safe_import()
            if imports['success']:
                st.markdown('<div class="success-card">✅ All imports successful</div>', unsafe_allow_html=True)
                st.write("**Available modules:**")
                st.write("- Database connection")
                st.write("- Template models")
                st.write("- Business rules")
                st.write("- Query generator")
                st.write("- Vector storage")
                st.write("- HTTP client")
            else:
                st.markdown(f'<div class="error-card">❌ Import error: {imports["error"]}</div>', unsafe_allow_html=True)
                with st.expander("🔍 Error Details"):
                    st.code(imports['traceback'])
                st.markdown('<div class="info-card">💡 **Tip:** Activate your virtual environment: `source venv/bin/activate`</div>', unsafe_allow_html=True)
        
        # Database Connection
        with st.expander("💾 Database Connection", expanded=True):
            if st.button("🔍 Test Database Connection", key="db_test"):
                with st.spinner("Testing database connection..."):
                    db_status = check_database_connection()
                    st.session_state.db_status = db_status
            
            if hasattr(st.session_state, 'db_status'):
                db_status = st.session_state.db_status
                if db_status['status'] == 'connected':
                    st.markdown(f'<div class="success-card">✅ {db_status["message"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="error-card">❌ {db_status["message"]}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="info-card">💡 **Tip:** Check your database configuration in settings</div>', unsafe_allow_html=True)
    
    with status_col2:
        # API Server Status
        with st.expander("🌐 API Server Status", expanded=True):
            if st.button("🔍 Test API Server", key="api_test"):
                with st.spinner("Testing API server..."):
                    api_status = check_api_server_status()
                    st.session_state.api_status = api_status
            
            if hasattr(st.session_state, 'api_status'):
                api_status = st.session_state.api_status
                if api_status['status'] == 'running':
                    st.markdown(f'<div class="success-card">✅ {api_status["message"]}</div>', unsafe_allow_html=True)
                    if api_status.get('details'):
                        st.write("**Server details:**")
                        st.json(api_status['details'])
                elif api_status['status'] == 'offline':
                    st.markdown(f'<div class="warning-card">⚠️ {api_status["message"]}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="info-card">💡 **Start server:** `uvicorn app.main:app --reload`</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="error-card">❌ {api_status["message"]}</div>', unsafe_allow_html=True)
        
        # Phoenix Tracing Status
        with st.expander("🔥 Phoenix Tracing", expanded=True):
            if st.session_state.get('phoenix_enabled'):
                st.markdown('<div class="success-card">✅ Phoenix tracing is enabled</div>', unsafe_allow_html=True)
                st.markdown('🌐 **Phoenix UI:** [http://localhost:6006](http://localhost:6006)')
                st.write("**Features enabled:**")
                st.write("- LLM call tracing")
                st.write("- Query generation monitoring")
                st.write("- Performance analytics")
            else:
                st.markdown('<div class="info-card">📊 Phoenix tracing not started</div>', unsafe_allow_html=True)
                st.write("Click 'Start Phoenix Tracing' above to enable LLM observability")
    
    # Environment Information
    st.markdown("---")
    st.subheader("🌍 Environment Information")
    
    env_col1, env_col2 = st.columns(2)
    
    with env_col1:
        st.write("**Python Environment:**")
        st.code(f"Python: {sys.version}")
        st.write("**Key Dependencies:**")
        try:
            import streamlit as st_version
            st.write(f"- Streamlit: {st_version.__version__}")
        except:
            st.write("- Streamlit: Unknown")
        
        try:
            import pandas as pd_version
            st.write(f"- Pandas: {pd_version.__version__}")
        except:
            st.write("- Pandas: Unknown")
    
    with env_col2:
        st.write("**Application Settings:**")
        st.write(f"- Working Directory: {os.getcwd()}")
        st.write(f"- Playground Path: {Path(__file__).name}")
        st.write("**Session State:**")
        st.write(f"- Templates Loaded: {st.session_state.get('templates_loaded', False)}")
        st.write(f"- Selected Connection: {'Yes' if st.session_state.get('selected_connection') else 'No'}")
        st.write(f"- Phoenix Enabled: {st.session_state.get('phoenix_enabled', False)}")

with tab4:
    st.header("📊 Analytics")
    st.info("🚧 Analytics dashboard will be added in the next increment")
    
    # Placeholder for analytics
    st.subheader("Template Performance")
    st.write("Template usage statistics and performance metrics will be implemented here")
    
    st.subheader("Query Success Rates")
    st.write("Query execution success rates and error analysis will be implemented here")
    
    st.subheader("System Metrics")
    st.write("System performance and health metrics will be implemented here")

with tab5:
    st.header("📊 Analytics")
    st.markdown("**System analytics, template usage statistics, and query performance metrics**")
    
    # Analytics overview
    analytics_col1, analytics_col2, analytics_col3, analytics_col4 = st.columns(4)
    
    with analytics_col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Templates", "--", help="Total number of context templates")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with analytics_col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Active Connections", "--", help="Number of active database connections")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with analytics_col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Queries Today", "--", help="Number of queries executed today")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with analytics_col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Success Rate", "--", help="Query success rate percentage")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Placeholder sections for future analytics
    tab_analytics1, tab_analytics2, tab_analytics3 = st.tabs(["📈 Usage Trends", "🎯 Query Performance", "🔧 System Health"])
    
    with tab_analytics1:
        st.markdown("### 📈 Template Usage Trends")
        st.info("📊 Coming Soon: Template usage over time, most popular templates, and usage patterns")
        
        # Placeholder chart
        st.markdown("**Template Usage Over Time (Last 30 Days)**")
        import pandas as pd
        st.line_chart(pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=30),
            'queries': [10, 15, 8, 22, 18, 25, 30, 12, 28, 35, 20, 15, 40, 32, 25, 18, 45, 38, 22, 50, 42, 35, 28, 55, 48, 40, 33, 60, 52, 45]
        }).set_index('date'))
    
    with tab_analytics2:
        st.markdown("### 🎯 Query Performance Analytics")
        st.info("⚡ Coming Soon: Query execution times, success rates, error analysis, and optimization suggestions")
        
        # Placeholder metrics
        perf_col1, perf_col2 = st.columns(2)
        with perf_col1:
            st.markdown("**Average Query Time**")
            st.bar_chart(pd.DataFrame({
                'Template': ['Template A', 'Template B', 'Template C', 'Template D'],
                'Avg Time (ms)': [150, 230, 180, 320]
            }).set_index('Template'))
        
        with perf_col2:
            st.markdown("**Success Rate by Template**")
            st.bar_chart(pd.DataFrame({
                'Template': ['Template A', 'Template B', 'Template C', 'Template D'],
                'Success Rate (%)': [95, 87, 92, 78]
            }).set_index('Template'))
    
    with tab_analytics3:
        st.markdown("### 🔧 System Health Monitoring")
        st.info("💚 Coming Soon: Database connection health, API response times, vector DB performance, and system alerts")
        
        # Placeholder system health
        health_col1, health_col2 = st.columns(2)
        with health_col1:
            st.markdown("**System Components Status**")
            components = [
                {"Component": "Database", "Status": "🟢 Healthy", "Response Time": "15ms"},
                {"Component": "API Server", "Status": "🟢 Healthy", "Response Time": "25ms"},
                {"Component": "Vector DB", "Status": "🟡 Warning", "Response Time": "150ms"},
                {"Component": "Phoenix Tracing", "Status": "🟢 Healthy", "Response Time": "10ms"}
            ]
            df_health = pd.DataFrame(components)
            st.dataframe(df_health, use_container_width=True)
        
        with health_col2:
            st.markdown("**Resource Usage**")
            st.progress(0.65, "CPU Usage: 65%")
            st.progress(0.45, "Memory Usage: 45%")
            st.progress(0.30, "Disk Usage: 30%")
            st.progress(0.80, "Network I/O: 80%")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; margin-top: 2rem;">
    <p>🎯 MiFiX.AI Configurator v1.0 </p>
    <p>Next: Implementing query testing functionality</p>
</div>
""", unsafe_allow_html=True)
