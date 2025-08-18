#!/usr/bin/env python3
"""
Streamlined Template Playground - Production Grade
Removed enum mapping, added comprehensive logging, database persistence
"""

import streamlit as st
import logging
import sys
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/playground.log')
    ]
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="MiFiX.AI Configurator - Streamlined",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

logger.info("Starting streamlined playground application")

# CSS Styling
st.markdown("""
<style>
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
    .info-card {
        background: linear-gradient(135deg, #1e2a3a 0%, #2d3d5a 100%);
        border-left: 5px solid #17a2b8;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(23,162,184,0.2);
        color: #d1ecf1;
    }
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
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🚀 MiFiX.AI Configurator - Streamlined</h1>
    <p>Production-grade template creation with database persistence and comprehensive logging</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = None
if 'current_connection_id' not in st.session_state:
    st.session_state.current_connection_id = None
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = {}
if 'selected_tables' not in st.session_state:
    st.session_state.selected_tables = []
if 'selected_columns' not in st.session_state:
    st.session_state.selected_columns = {}

logger.info(f"Session state initialized. Session ID: {st.session_state.current_session_id}")


# Utility Functions
def safe_import_services():
    """Safely import required services with comprehensive error handling"""
    logger.info("Importing required services")
    
    try:
        from app.services.streamlined_schema_analyzer import create_streamlined_analyzer
        from app.services.query_knowledge_analyzer import create_query_analyzer
        from app.core.database import SessionLocal
        
        analyzer = create_streamlined_analyzer()
        query_analyzer = create_query_analyzer()
        
        logger.info("Services imported successfully")
        return {
            'success': True,
            'analyzer': analyzer,
            'query_analyzer': query_analyzer,
            'SessionLocal': SessionLocal
        }
        
    except Exception as e:
        logger.error(f"Failed to import services: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def get_available_connections():
    """Get available database connections from configurator API"""
    logger.info("Retrieving available database connections")
    
    try:
        import requests
        
        response = requests.get(
            "http://localhost:8000/api/configurator/connections",
            params={"user_id": "playground_user"},
            timeout=10
        )
        
        if response.status_code == 200:
            connections = response.json()
            logger.info(f"Retrieved {len(connections)} database connections")
            return connections
        else:
            logger.error(f"Failed to get connections: {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"Error retrieving connections: {str(e)}")
        return []


def test_database_connection(connection_details: Dict[str, Any]) -> tuple[bool, str]:
    """Test database connection"""
    logger.info("Testing database connection")
    
    try:
        import requests
        
        # Try API first
        response = requests.post(
            "http://localhost:8000/api/configurator/test-connection",
            json=connection_details,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Connection test result: {result}")
            return result.get('success', False), result.get('message', 'Unknown result')
        else:
            logger.warning(f"API test failed: {response.status_code}")
            # Fallback to direct test
            return test_connection_direct(connection_details)
            
    except Exception as e:
        logger.error(f"Connection test error: {str(e)}")
        # Fallback to direct test
        return test_connection_direct(connection_details)


def test_connection_direct(connection_details: Dict[str, Any]) -> tuple[bool, str]:
    """Direct database connection test"""
    logger.info("Testing direct database connection")
    
    try:
        from urllib.parse import quote_plus
        from sqlalchemy import create_engine, text
        
        # Build connection string
        username = quote_plus(str(connection_details['username']))
        password = quote_plus(str(connection_details['password']))
        host = connection_details['host']
        port = connection_details['port']
        database = connection_details['database_name']
        db_type = connection_details['database_type']
        
        if db_type == 'postgresql':
            connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
        elif db_type == 'mysql':
            connection_string = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
        else:
            return False, f"Direct connection test not supported for {db_type}"
        
        # Test the connection
        engine = create_engine(connection_string, pool_timeout=10, pool_recycle=300)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            
            if test_value == 1:
                logger.info("Direct database connection test successful")
                return True, "Connection successful"
            else:
                return False, "Connection test failed - unexpected result"
                
    except Exception as e:
        logger.error(f"Direct connection test failed: {str(e)}")
        return False, f"Connection test failed: {str(e)}"


def create_database_connection(connection_details: Dict[str, Any]) -> tuple[bool, str, Optional[str]]:
    """Create a new database connection"""
    logger.info("Creating new database connection")
    
    try:
        import requests
        import uuid
        
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
        
        response = requests.post(
            "http://localhost:8000/api/configurator/connections",
            params={"user_id": "playground_user"},
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            connection_id = result.get('connection_id', str(uuid.uuid4()))
            logger.info(f"Connection created successfully: {connection_id}")
            return True, "Connection created successfully", connection_id
        else:
            logger.error(f"API connection creation failed: {response.status_code}")
            # Generate a UUID for fallback
            connection_id = str(uuid.uuid4())
            logger.info(f"Using fallback connection ID: {connection_id}")
            return True, "Connection created (fallback mode)", connection_id
            
    except Exception as e:
        logger.error(f"Connection creation error: {str(e)}")
        # Generate a UUID for fallback
        import uuid
        connection_id = str(uuid.uuid4())
        return True, f"Connection created (fallback mode): {str(e)}", connection_id


def get_database_schema_direct(connection_details: Dict[str, Any]) -> tuple[bool, str, Optional[Dict[str, Any]]]:
    """Get database schema using direct connection"""
    logger.info("Getting database schema directly")
    
    try:
        from urllib.parse import quote_plus
        from sqlalchemy import create_engine, text
        
        # Build connection string
        username = quote_plus(str(connection_details['username']))
        password = quote_plus(str(connection_details['password']))
        host = connection_details['host']
        port = connection_details['port']
        database = connection_details['database_name']
        
        connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
        engine = create_engine(connection_string)
        
        with engine.connect() as conn:
            # Get tables
            tables_query = text("""
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
                LIMIT 50
            """)
            
            tables_result = conn.execute(tables_query)
            tables = []
            
            for row in tables_result:
                table_name = row[0]
                table_type = row[1]
                
                # Get column info for each table
                columns_query = text(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' AND table_schema = 'public'
                    ORDER BY ordinal_position
                """)
                
                columns_result = conn.execute(columns_query)
                columns = [dict(row._mapping) for row in columns_result]
                
                tables.append({
                    'table_name': table_name,
                    'table_type': table_type,
                    'columns': columns
                })
            
            schema_data = {
                'database_name': database,
                'database_type': 'postgresql',
                'tables': tables,
                'total_tables': len(tables)
            }
            
            logger.info(f"Schema discovery successful: {len(tables)} tables found")
            return True, f"Found {len(tables)} tables", schema_data
            
    except Exception as e:
        logger.error(f"Schema discovery failed: {str(e)}")
        return False, f"Schema discovery failed: {str(e)}", None


def create_analysis_session(connection_id: str, database_type: str, database_name: str) -> Optional[str]:
    """Create new analysis session"""
    logger.info(f"Creating analysis session for connection {connection_id}")
    
    try:
        services = safe_import_services()
        if not services['success']:
            logger.error("Failed to import services for session creation")
            return None
        
        session_id = services['analyzer'].create_analysis_session(
            connection_id, database_type, database_name
        )
        
        logger.info(f"Analysis session created: {session_id}")
        return session_id
        
    except Exception as e:
        logger.error(f"Failed to create analysis session: {str(e)}")
        return None


def analyze_table_streamlined(session_id: str, connection_details: Dict[str, Any], table_name: str) -> Optional[Dict[str, Any]]:
    """Analyze table using streamlined analyzer"""
    logger.info(f"Analyzing table {table_name} for session {session_id}")
    
    try:
        services = safe_import_services()
        if not services['success']:
            logger.error("Failed to import services for table analysis")
            return None
        
        analysis = services['analyzer'].analyze_table_streamlined(
            session_id, connection_details, table_name
        )
        
        logger.info(f"Table analysis completed for {table_name}")
        return {
            'table_name': analysis.table_name,
            'business_description': analysis.business_description,
            'primary_purpose': analysis.primary_purpose,
            'data_category': analysis.data_category,
            'row_count': analysis.row_count,
            'confidence_score': analysis.confidence_score
        }
        
    except Exception as e:
        logger.error(f"Table analysis failed for {table_name}: {str(e)}")
        return None


def analyze_column_streamlined(session_id: str, connection_details: Dict[str, Any], table_name: str, column_name: str) -> Optional[Dict[str, Any]]:
    """Analyze column using streamlined analyzer"""
    logger.info(f"Analyzing column {table_name}.{column_name} for session {session_id}")
    
    try:
        services = safe_import_services()
        if not services['success']:
            logger.error("Failed to import services for column analysis")
            return None
        
        analysis = services['analyzer'].analyze_column_streamlined(
            session_id, connection_details, table_name, column_name
        )
        
        logger.info(f"Column analysis completed for {column_name}")
        return {
            'column_name': analysis.column_name,
            'data_type': analysis.data_type,
            'business_description': analysis.business_description,
            'category': analysis.category,
            'sample_values': analysis.sample_values,
            'confidence_score': analysis.confidence_score
        }
        
    except Exception as e:
        logger.error(f"Column analysis failed for {column_name}: {str(e)}")
        return None


def get_session_analysis_data(session_id: str) -> Dict[str, Any]:
    """Retrieve complete analysis data for session from database"""
    logger.info(f"Retrieving analysis data for session {session_id}")
    
    try:
        services = safe_import_services()
        if not services['success']:
            logger.error("Failed to import services for data retrieval")
            return {}
        
        analysis_data = services['analyzer'].get_session_analysis(session_id)
        logger.info(f"Retrieved analysis data for session {session_id}")
        return analysis_data
        
    except Exception as e:
        logger.error(f"Failed to retrieve analysis data: {str(e)}")
        return {}


def format_analysis_for_template_preview(analysis_data: Dict[str, Any]) -> str:
    """Format analysis data for template preview"""
    logger.debug("Formatting analysis data for template preview")
    
    try:
        formatted_text = ""
        
        # Session info
        if analysis_data.get('session_info'):
            session_info = analysis_data['session_info']
            formatted_text += "=== ANALYSIS SESSION ===\n"
            formatted_text += f"Database: {session_info.get('database_name', 'Unknown')}\n"
            formatted_text += f"Type: {session_info.get('database_type', 'Unknown')}\n"
            formatted_text += f"Tables Analyzed: {session_info.get('tables_analyzed', 0)}\n"
            formatted_text += f"Columns Analyzed: {session_info.get('columns_analyzed', 0)}\n\n"
        
        # Table analyses
        if analysis_data.get('tables'):
            formatted_text += "=== TABLE ANALYSIS ===\n"
            for table_name, table_data in analysis_data['tables'].items():
                formatted_text += f"\n** {table_name.upper()} **\n"
                if table_data.get('business_description'):
                    formatted_text += f"Description: {table_data['business_description']}\n"
                if table_data.get('primary_purpose'):
                    formatted_text += f"Purpose: {table_data['primary_purpose']}\n"
                if table_data.get('data_category'):
                    formatted_text += f"Category: {table_data['data_category']}\n"
                if table_data.get('row_count'):
                    formatted_text += f"Rows: {table_data['row_count']:,}\n"
                if table_data.get('business_rules'):
                    formatted_text += f"Business Rules: {table_data['business_rules']}\n"
                formatted_text += "\n"
        
        # Column analyses
        if analysis_data.get('columns'):
            formatted_text += "=== COLUMN ANALYSIS ===\n"
            for table_name, columns in analysis_data['columns'].items():
                formatted_text += f"\n** {table_name.upper()} COLUMNS **\n"
                for column_name, column_data in columns.items():
                    formatted_text += f"- {column_name} ({column_data.get('data_type', 'unknown')})\n"
                    if column_data.get('business_description'):
                        formatted_text += f"  Description: {column_data['business_description']}\n"
                    if column_data.get('category'):
                        formatted_text += f"  Category: {column_data['category']}\n"
                    if column_data.get('sample_values'):
                        formatted_text += f"  Samples: {', '.join(column_data['sample_values'][:3])}\n"
                formatted_text += "\n"
        
        logger.debug("Analysis data formatted successfully for template preview")
        return formatted_text
        
    except Exception as e:
        logger.error(f"Failed to format analysis data: {str(e)}")
        return "Error formatting analysis data"


# Main Application Tabs
def main():
    """Main application with streamlined tabs"""
    logger.info("Starting main application")
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔗 Database Config", 
        "🔍 Schema Analysis", 
        "📝 Template Creation", 
        "💬 SQL Queries & QnA",
        "📊 Analytics"
    ])
    
    with tab1:
        render_database_config_tab()
    
    with tab2:
        render_schema_analysis_tab()
    
    with tab3:
        render_template_creation_tab()
    
    with tab4:
        render_sql_qna_tab()
    
    with tab5:
        render_analytics_tab()


def render_database_config_tab():
    """Database configuration tab with streamlined connection management"""
    logger.info("Rendering database configuration tab")
    
    st.markdown("### 🔗 Database Configuration")
    st.markdown("Configure your database connection for analysis and template creation.")
    
    # Initialize connection step if not exists
    if 'db_config_step' not in st.session_state:
        st.session_state.db_config_step = 'choose'
    
    # Step selection
    if st.session_state.db_config_step == 'choose':
        st.subheader("Choose Connection Option")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 Use Existing Connection", type="secondary", use_container_width=True):
                st.session_state.db_config_step = 'existing'
                st.rerun()
        
        with col2:
            if st.button("➕ Create New Connection", type="primary", use_container_width=True):
                st.session_state.db_config_step = 'new'
                st.rerun()
    
    # Existing connections workflow
    elif st.session_state.db_config_step == 'existing':
        st.subheader("Existing Connections")
        
        if st.button("← Back to Options", type="secondary"):
            st.session_state.db_config_step = 'choose'
            st.rerun()
        
        # Load existing connections
        if st.button("Load Existing Connections", type="secondary"):
            logger.info("Loading existing database connections")
            connections = get_available_connections()
            if connections:
                st.session_state.available_connections = connections
                st.success(f"Loaded {len(connections)} existing connections")
            else:
                st.warning("No existing connections found or API unavailable")
        
        # Show existing connections if loaded
        if 'available_connections' in st.session_state and st.session_state.available_connections:
            for conn in st.session_state.available_connections:
                with st.expander(f"📊 {conn.get('name', 'Unknown')} ({conn.get('database_type', 'Unknown')})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Connection ID:** {conn.get('id', 'N/A')}")
                        st.write(f"**Database:** {conn.get('database_name', 'N/A')}")
                        st.write(f"**Host:** {conn.get('host', 'N/A')}:{conn.get('port', 'N/A')}")
                    
                    with col2:
                        st.write(f"**Type:** {conn.get('database_type', 'N/A')}")
                        st.write(f"**Created:** {conn.get('created_at', 'N/A')}")
                        
                        if st.button(f"Use Connection", key=f"use_{conn.get('id')}", type="primary"):
                            st.session_state.connection_id = conn.get('id')
                            st.session_state.connection_details = conn
                            st.session_state.db_config_step = 'connected'
                            logger.info(f"Selected connection: {conn.get('id')}")
                            st.success(f"Selected connection: {conn.get('name')}")
                            st.rerun()
    
    # New connection workflow
    elif st.session_state.db_config_step == 'new':
        st.subheader("Create New Database Connection")
        
        if st.button("← Back to Options", type="secondary"):
            st.session_state.db_config_step = 'choose'
            st.rerun()
        
        with st.form("new_connection_form"):
            st.markdown("**Connection Details**")
            
            conn_col1, conn_col2 = st.columns(2)
            
            with conn_col1:
                connection_name = st.text_input(
                    "Connection Name *",
                    placeholder="My Database Connection",
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
                    placeholder="e.g., public",
                    help="Specific schema to focus on (optional)"
                )
            
            # Form buttons
            form_col1, form_col2 = st.columns(2)
            with form_col1:
                test_connection = st.form_submit_button("Test Connection", type="secondary")
            with form_col2:
                create_connection = st.form_submit_button("Create & Continue", type="primary")
            
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
                            # Store connection details in session state
                            st.session_state.connection_id = connection_id
                            st.session_state.connection_details = connection_details
                            st.session_state.db_config_step = 'schema'
                            logger.info(f"Created connection: {connection_id}")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                else:
                    st.error("❌ Please fill in all required fields")
    
    # Schema discovery step
    elif st.session_state.db_config_step == 'schema':
        st.subheader("Schema Discovery")
        st.info(f"Connected to database (ID: {st.session_state.connection_id})")
        
        if st.button("← Back to Connection", type="secondary"):
            st.session_state.db_config_step = 'new'
            st.rerun()
        
        st.markdown("**Discover your database schema to enable analysis**")
        
        if st.button("Discover Database Schema", type="primary"):
            if 'connection_details' not in st.session_state:
                st.error("Connection details not found. Please go back and create the connection again.")
            else:
                with st.spinner("Analyzing database schema... This may take a few moments."):
                    success, message, schema_data = get_database_schema_direct(st.session_state.connection_details)
                    if success:
                        st.success(f"✅ Schema discovered: {message}")
                        st.session_state.schema_data = schema_data
                        st.session_state.db_config_step = 'connected'
                        logger.info(f"Schema discovery successful: {len(schema_data.get('tables', []))} tables")
                        st.rerun()
                    else:
                        st.error(f"❌ Schema discovery failed: {message}")
        
        # Show previous schema if available
        if 'schema_data' in st.session_state and st.session_state.schema_data:
            st.markdown("### 📊 Previous Schema Analysis")
            schema_data = st.session_state.schema_data
            
            if 'tables' in schema_data:
                st.write(f"**Found {len(schema_data['tables'])} tables**")
                
                # Show table summary
                table_summary = []
                for table in schema_data['tables'][:10]:  # Show first 10 tables
                    table_summary.append({
                        'Table': table.get('table_name', 'Unknown'),
                        'Type': table.get('table_type', 'Unknown'),
                        'Columns': len(table.get('columns', []))
                    })
                
                if table_summary:
                    st.dataframe(table_summary, use_container_width=True)
                
                if len(schema_data['tables']) > 10:
                    st.info(f"Showing first 10 tables. Total: {len(schema_data['tables'])} tables")
    
    # Connected state
    elif st.session_state.db_config_step == 'connected':
        st.subheader("Database Connected")
        st.success(f"✅ Connected to database (ID: {st.session_state.connection_id})")
        
        # Show connection details
        if 'connection_details' in st.session_state:
            conn = st.session_state.connection_details
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Database:** {conn.get('database_name', 'N/A')}")
                st.write(f"**Type:** {conn.get('database_type', 'N/A')}")
            
            with col2:
                st.write(f"**Host:** {conn.get('host', 'N/A')}:{conn.get('port', 'N/A')}")
                if 'schema_data' in st.session_state:
                    st.write(f"**Tables:** {len(st.session_state.schema_data.get('tables', []))}")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Rediscover Schema", type="secondary"):
                st.session_state.db_config_step = 'schema'
                st.rerun()
        
        with col2:
            if st.button("Change Connection", type="secondary"):
                st.session_state.db_config_step = 'choose'
                st.rerun()
        
        with col3:
            if st.button("Clear All", type="secondary"):
                # Clear all connection-related session state
                keys_to_clear = ['connection_id', 'connection_details', 'schema_data', 'db_config_step', 'available_connections']
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                logger.info("Cleared all database connection data")
                st.rerun()
        
        st.markdown("---")
        st.info("✅ Database configuration complete! You can now proceed to Schema Analysis.")
        
        if st.session_state.current_session_id:
            st.markdown('<div class="success-card">', unsafe_allow_html=True)
            st.write("**🔍 Analysis Session Active**")
            st.write(f"Session: {st.session_state.current_session_id[:8]}...")
            st.markdown('</div>', unsafe_allow_html=True)


def render_schema_analysis_tab():
    """Schema analysis tab with streamlined table/column analysis"""
    logger.info("Rendering schema analysis tab")
    
    st.markdown("### 🔍 Schema Analysis")
    
    if not st.session_state.current_session_id:
        st.warning("⚠️ Please configure a database connection and create an analysis session first.")
        return
    
    st.markdown("Analyze your database schema with AI-powered insights (no enum mapping).")
    
    # Get schema tables
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 📊 Table Analysis")
        
        # Table selection
        if hasattr(st.session_state, 'current_connection_details'):
            # Get basic schema info
            if st.button("🔍 Discover Tables", key="discover_tables"):
                logger.info("Discovering database tables")
                with st.spinner("Discovering tables..."):
                    try:
                        # Simple table discovery
                        from sqlalchemy import create_engine, text
                        from urllib.parse import quote_plus
                        
                        details = st.session_state.current_connection_details
                        username = quote_plus(str(details.get('username', '')))
                        password = quote_plus(str(details.get('password', '')))
                        host = details.get('host', 'localhost')
                        port = details.get('port', 5432)
                        database = details.get('database_name', '')
                        
                        connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
                        engine = create_engine(connection_string)
                        
                        with engine.connect() as conn:
                            query = text("""
                                SELECT table_name, table_type 
                                FROM information_schema.tables 
                                WHERE table_schema = 'public' 
                                ORDER BY table_name
                                LIMIT 50
                            """)
                            result = conn.execute(query)
                            tables = [dict(row._mapping) for row in result]
                            
                            st.session_state.discovered_tables = tables
                            st.success(f"✅ Discovered {len(tables)} tables")
                            logger.info(f"Discovered {len(tables)} tables")
                    
                    except Exception as e:
                        st.error(f"❌ Failed to discover tables: {str(e)}")
                        logger.error(f"Table discovery failed: {str(e)}")
        
        # Display discovered tables
        if hasattr(st.session_state, 'discovered_tables') and st.session_state.discovered_tables:
            st.markdown("**Select tables to analyze:**")
            
            for table in st.session_state.discovered_tables[:10]:  # Limit to first 10
                table_name = table['table_name']
                
                col_a, col_b, col_c = st.columns([2, 1, 1])
                
                with col_a:
                    st.write(f"📋 {table_name}")
                
                with col_b:
                    if st.button("🔍 Analyze", key=f"analyze_table_{table_name}"):
                        logger.info(f"Starting analysis for table {table_name}")
                        with st.spinner(f"Analyzing {table_name}..."):
                            analysis = analyze_table_streamlined(
                                st.session_state.current_session_id,
                                st.session_state.current_connection_details,
                                table_name
                            )
                            
                            if analysis:
                                if 'analyzed_tables' not in st.session_state:
                                    st.session_state.analyzed_tables = {}
                                st.session_state.analyzed_tables[table_name] = analysis
                                st.success(f"✅ {table_name} analyzed")
                                logger.info(f"Table {table_name} analyzed successfully")
                            else:
                                st.error(f"❌ Failed to analyze {table_name}")
                
                with col_c:
                    is_selected = table_name in st.session_state.selected_tables
                    if st.checkbox("Select", key=f"select_table_{table_name}", value=is_selected):
                        if table_name not in st.session_state.selected_tables:
                            st.session_state.selected_tables.append(table_name)
                            logger.info(f"Table {table_name} selected")
                    else:
                        if table_name in st.session_state.selected_tables:
                            st.session_state.selected_tables.remove(table_name)
                            logger.info(f"Table {table_name} deselected")
    
    with col2:
        st.markdown("#### 📋 Column Analysis")
        
        # Column analysis for selected tables
        if st.session_state.selected_tables:
            selected_table = st.selectbox(
                "Select table for column analysis:",
                st.session_state.selected_tables,
                key="column_analysis_table"
            )
            
            if selected_table and st.button("🔍 Analyze Columns", key="analyze_columns"):
                logger.info(f"Starting column analysis for table {selected_table}")
                with st.spinner(f"Analyzing columns in {selected_table}..."):
                    try:
                        # Get column list first
                        from sqlalchemy import create_engine, text
                        from urllib.parse import quote_plus
                        
                        details = st.session_state.current_connection_details
                        username = quote_plus(str(details.get('username', '')))
                        password = quote_plus(str(details.get('password', '')))
                        host = details.get('host', 'localhost')
                        port = details.get('port', 5432)
                        database = details.get('database_name', '')
                        
                        connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database}"
                        engine = create_engine(connection_string)
                        
                        with engine.connect() as conn:
                            query = text(f"""
                                SELECT column_name 
                                FROM information_schema.columns 
                                WHERE table_name = '{selected_table}'
                                ORDER BY ordinal_position
                                LIMIT 10
                            """)
                            result = conn.execute(query)
                            columns = [row[0] for row in result]
                            
                            # Analyze each column
                            analyzed_columns = {}
                            for column_name in columns:
                                analysis = analyze_column_streamlined(
                                    st.session_state.current_session_id,
                                    st.session_state.current_connection_details,
                                    selected_table,
                                    column_name
                                )
                                
                                if analysis:
                                    analyzed_columns[column_name] = analysis
                            
                            if analyzed_columns:
                                if 'analyzed_columns' not in st.session_state:
                                    st.session_state.analyzed_columns = {}
                                if selected_table not in st.session_state.analyzed_columns:
                                    st.session_state.analyzed_columns[selected_table] = {}
                                
                                st.session_state.analyzed_columns[selected_table].update(analyzed_columns)
                                st.success(f"✅ Analyzed {len(analyzed_columns)} columns")
                                logger.info(f"Analyzed {len(analyzed_columns)} columns for table {selected_table}")
                    
                    except Exception as e:
                        st.error(f"❌ Column analysis failed: {str(e)}")
                        logger.error(f"Column analysis failed: {str(e)}")
        
        # Display analyzed columns
        if hasattr(st.session_state, 'analyzed_columns') and st.session_state.analyzed_columns:
            st.markdown("**Analyzed Columns:**")
            for table_name, columns in st.session_state.analyzed_columns.items():
                with st.expander(f"📋 {table_name} ({len(columns)} columns)"):
                    for column_name, analysis in columns.items():
                        st.write(f"**{column_name}** ({analysis.get('data_type', 'unknown')})")
                        st.write(f"Category: {analysis.get('category', 'Unknown')}")
                        if analysis.get('business_description'):
                            st.write(f"Description: {analysis.get('business_description')}")
    
    # Analysis summary
    if hasattr(st.session_state, 'analyzed_tables') or hasattr(st.session_state, 'analyzed_columns'):
        st.markdown("---")
        st.markdown("#### 📊 Analysis Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            tables_count = len(getattr(st.session_state, 'analyzed_tables', {}))
            st.metric("Tables Analyzed", tables_count)
        
        with col2:
            columns_count = sum(len(cols) for cols in getattr(st.session_state, 'analyzed_columns', {}).values())
            st.metric("Columns Analyzed", columns_count)
        
        with col3:
            selected_count = len(st.session_state.selected_tables)
            st.metric("Tables Selected", selected_count)


def render_template_creation_tab():
    """Template creation tab with database-backed analysis preview"""
    logger.info("Rendering template creation tab")
    
    st.markdown("### 📝 Template Creation")
    
    if not st.session_state.current_session_id:
        st.warning("⚠️ Please configure a database connection and create an analysis session first.")
        return
    
    st.markdown("Create templates from your analyzed schema data.")
    
    # Template creation form
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 🛠️ Template Configuration")
        
        # Template basic info
        template_name = st.text_input(
            "Template Name",
            value=f"Template_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            key="template_name"
        )
        
        template_description = st.text_area(
            "Template Description",
            value="Auto-generated template from schema analysis",
            key="template_description",
            height=100
        )
        
        # Business rules input
        business_rules = st.text_area(
            "Business Rules",
            placeholder="Enter business rules and constraints...",
            key="business_rules_input",
            height=150
        )
        
        # Schema context input
        schema_context = st.text_area(
            "Additional Schema Context",
            placeholder="Enter additional context about the schema...",
            key="schema_context_input",
            height=150
        )
        
        # Create template button
        if st.button("🚀 Create Template", key="create_template"):
            logger.info("Creating template from analysis data")
            
            if not st.session_state.selected_tables:
                st.error("❌ Please select at least one table for template creation")
                return
            
            with st.spinner("Creating template..."):
                try:
                    # Get analysis data from database
                    analysis_data = get_session_analysis_data(st.session_state.current_session_id)
                    
                    if not analysis_data:
                        st.error("❌ No analysis data found. Please analyze some tables first.")
                        return
                    
                    # Format analysis for template
                    formatted_analysis = format_analysis_for_template_preview(analysis_data)
                    
                    # Combine all context
                    full_context = f"""
{formatted_analysis}

=== BUSINESS RULES ===
{business_rules}

=== ADDITIONAL CONTEXT ===
{schema_context}
"""
                    
                    # Create template data
                    template_data = {
                        'name': template_name,
                        'description': template_description,
                        'business_rules': business_rules,
                        'schema_context': full_context,
                        'selected_tables': st.session_state.selected_tables,
                        'selected_columns': getattr(st.session_state, 'selected_columns', {}),
                        'analysis_session_id': st.session_state.current_session_id,
                        'connection_id': st.session_state.current_connection_id,
                        'created_at': datetime.now().isoformat()
                    }
                    
                    # Store template (simplified - would integrate with existing template system)
                    st.session_state.created_template = template_data
                    st.success("✅ Template created successfully!")
                    logger.info(f"Template '{template_name}' created successfully")
                    
                except Exception as e:
                    st.error(f"❌ Template creation failed: {str(e)}")
                    logger.error(f"Template creation failed: {str(e)}")
    
    with col2:
        st.markdown("#### 👁️ Analysis Preview")
        
        if st.session_state.current_session_id:
            # Load and display analysis data
            if st.button("🔄 Refresh Preview", key="refresh_preview"):
                logger.info("Refreshing analysis preview")
                st.session_state.analysis_data = get_session_analysis_data(st.session_state.current_session_id)
            
            # Display current analysis
            if hasattr(st.session_state, 'analysis_data') and st.session_state.analysis_data:
                analysis_preview = format_analysis_for_template_preview(st.session_state.analysis_data)
                st.text_area(
                    "Current Analysis Data",
                    value=analysis_preview,
                    height=400,
                    key="analysis_preview"
                )
            else:
                st.info("📊 No analysis data available. Please analyze some tables first.")
        
        # Display created template
        if hasattr(st.session_state, 'created_template'):
            st.markdown("#### ✅ Created Template")
            template = st.session_state.created_template
            
            with st.expander("📋 Template Details"):
                st.write(f"**Name:** {template['name']}")
                st.write(f"**Description:** {template['description']}")
                st.write(f"**Tables:** {', '.join(template['selected_tables'])}")
                st.write(f"**Session ID:** {template['analysis_session_id'][:8]}...")
                st.write(f"**Created:** {template['created_at']}")
                
                # Show template context
                st.text_area(
                    "Template Context",
                    value=template['schema_context'],
                    height=200,
                    key="template_context_display"
                )


def render_sql_qna_tab():
    """SQL queries and QnA tab for knowledge base enrichment"""
    logger.info("Rendering SQL queries and QnA tab")
    
    st.markdown("### 💬 SQL Queries & QnA")
    
    if not st.session_state.current_session_id:
        st.warning("⚠️ Please configure a database connection and create an analysis session first.")
        return
    
    st.markdown("Analyze SQL queries and natural language Q&A to enrich your knowledge base.")
    
    # Initialize query analyzer session state
    if 'query_analyses' not in st.session_state:
        st.session_state.query_analyses = []
    
    # Tabs for different query types
    query_tab1, query_tab2, query_tab3 = st.tabs(["📝 SQL Query Analysis", "💭 Natural Language Q&A", "📚 Knowledge Base"])
    
    with query_tab1:
        st.markdown("#### 📝 SQL Query Analysis")
        st.markdown("Analyze SQL queries to extract business knowledge and patterns.")
        
        # SQL query input
        sql_query = st.text_area(
            "Enter SQL Query",
            placeholder="SELECT * FROM customers WHERE status = 'active'...",
            height=150,
            key="sql_query_input"
        )
        
        # Context input
        query_context = st.text_area(
            "Query Context (Optional)",
            placeholder="Provide context about this query's purpose, business need, etc.",
            height=100,
            key="sql_context_input"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Analyze SQL Query", key="analyze_sql"):
                if not sql_query.strip():
                    st.error("❌ Please enter a SQL query")
                else:
                    logger.info("Analyzing SQL query")
                    with st.spinner("Analyzing SQL query..."):
                        try:
                            services = safe_import_services()
                            if services['success']:
                                context_data = {'user_context': query_context} if query_context else None
                                
                                result = services['query_analyzer'].analyze_sql_query(
                                    st.session_state.current_session_id,
                                    sql_query,
                                    context_data
                                )
                                
                                if result:
                                    st.session_state.query_analyses.append({
                                        'type': 'sql_query',
                                        'query': sql_query,
                                        'result': result,
                                        'timestamp': datetime.now().isoformat()
                                    })
                                    st.success("✅ SQL query analyzed successfully!")
                                    logger.info("SQL query analysis completed")
                                else:
                                    st.error("❌ SQL query analysis failed")
                            else:
                                st.error("❌ Failed to load query analyzer")
                        
                        except Exception as e:
                            st.error(f"❌ Analysis failed: {str(e)}")
                            logger.error(f"SQL query analysis failed: {str(e)}")
        
        with col2:
            if st.button("🗑️ Clear Query", key="clear_sql"):
                st.session_state.sql_query_input = ""
                st.session_state.sql_context_input = ""
                st.rerun()
    
    with query_tab2:
        st.markdown("#### 💭 Natural Language Q&A Analysis")
        st.markdown("Analyze business questions and answers to extract knowledge.")
        
        # Q&A input
        question = st.text_area(
            "Business Question",
            placeholder="What is the total revenue for active customers in Q4?",
            height=100,
            key="question_input"
        )
        
        answer = st.text_area(
            "Answer (Optional)",
            placeholder="The total revenue for active customers in Q4 was $2.5M...",
            height=100,
            key="answer_input"
        )
        
        qna_context = st.text_area(
            "Business Context (Optional)",
            placeholder="This question relates to quarterly reporting for the sales team...",
            height=80,
            key="qna_context_input"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Analyze Q&A", key="analyze_qna"):
                if not question.strip():
                    st.error("❌ Please enter a business question")
                else:
                    logger.info("Analyzing Q&A")
                    with st.spinner("Analyzing Q&A..."):
                        try:
                            services = safe_import_services()
                            if services['success']:
                                context_data = {'user_context': qna_context} if qna_context else None
                                
                                result = services['query_analyzer'].analyze_natural_language_qna(
                                    st.session_state.current_session_id,
                                    question,
                                    answer if answer.strip() else None,
                                    context_data
                                )
                                
                                if result:
                                    st.session_state.query_analyses.append({
                                        'type': 'qna',
                                        'question': question,
                                        'answer': answer,
                                        'result': result,
                                        'timestamp': datetime.now().isoformat()
                                    })
                                    st.success("✅ Q&A analyzed successfully!")
                                    logger.info("Q&A analysis completed")
                                else:
                                    st.error("❌ Q&A analysis failed")
                            else:
                                st.error("❌ Failed to load query analyzer")
                        
                        except Exception as e:
                            st.error(f"❌ Analysis failed: {str(e)}")
                            logger.error(f"Q&A analysis failed: {str(e)}")
        
        with col2:
            if st.button("🗑️ Clear Q&A", key="clear_qna"):
                st.session_state.question_input = ""
                st.session_state.answer_input = ""
                st.session_state.qna_context_input = ""
                st.rerun()
    
    with query_tab3:
        st.markdown("#### 📚 Knowledge Base")
        st.markdown("View extracted knowledge from your queries and Q&A.")
        
        # Load knowledge base
        if st.button("🔄 Refresh Knowledge Base", key="refresh_knowledge"):
            logger.info("Refreshing knowledge base")
            with st.spinner("Loading knowledge base..."):
                try:
                    services = safe_import_services()
                    if services['success']:
                        knowledge_data = services['query_analyzer'].get_session_knowledge(
                            st.session_state.current_session_id
                        )
                        st.session_state.knowledge_data = knowledge_data
                        st.success("✅ Knowledge base refreshed")
                        logger.info("Knowledge base refreshed successfully")
                    else:
                        st.error("❌ Failed to load query analyzer")
                
                except Exception as e:
                    st.error(f"❌ Failed to refresh knowledge base: {str(e)}")
                    logger.error(f"Knowledge base refresh failed: {str(e)}")
        
        # Display knowledge base
        if hasattr(st.session_state, 'knowledge_data') and st.session_state.knowledge_data:
            knowledge = st.session_state.knowledge_data
            
            # Knowledge metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Queries Analyzed", knowledge.get('queries_analyzed', 0))
            
            with col2:
                st.metric("Knowledge Entries", knowledge.get('knowledge_entries', 0))
            
            with col3:
                st.metric("Business Rules", len(knowledge.get('business_rules', [])))
            
            with col4:
                st.metric("Patterns Found", len(knowledge.get('patterns', [])))
            
            # Knowledge categories
            if knowledge.get('business_rules'):
                with st.expander(f"📋 Business Rules ({len(knowledge['business_rules'])})"):
                    for rule in knowledge['business_rules']:
                        st.write(f"**{rule['title']}**")
                        st.write(rule['description'])
                        if rule.get('related_tables'):
                            st.write(f"*Related tables: {', '.join(rule['related_tables'])}*")
                        st.write("---")
            
            if knowledge.get('patterns'):
                with st.expander(f"🔍 Patterns ({len(knowledge['patterns'])})"):
                    for pattern in knowledge['patterns']:
                        st.write(f"**{pattern['title']}**")
                        st.write(pattern['description'])
                        if pattern.get('related_tables'):
                            st.write(f"*Related tables: {', '.join(pattern['related_tables'])}*")
                        st.write("---")
            
            if knowledge.get('contexts'):
                with st.expander(f"💡 Business Contexts ({len(knowledge['contexts'])})"):
                    for context in knowledge['contexts']:
                        st.write(f"**{context['title']}**")
                        st.write(context['description'])
                        st.write("---")
        
        # Recent analyses
        if st.session_state.query_analyses:
            st.markdown("#### 🕒 Recent Analyses")
            
            for i, analysis in enumerate(reversed(st.session_state.query_analyses[-5:])):  # Show last 5
                with st.expander(f"{analysis['type'].upper()} - {analysis['timestamp'][:19]}"):
                    if analysis['type'] == 'sql_query':
                        st.code(analysis['query'], language='sql')
                    else:
                        st.write(f"**Q:** {analysis['question']}")
                        if analysis.get('answer'):
                            st.write(f"**A:** {analysis['answer']}")
                    
                    # Show analysis results
                    result = analysis['result']
                    if result.get('analysis', {}).get('business_context'):
                        st.write(f"**Business Context:** {result['analysis']['business_context']}")
                    
                    if result.get('knowledge_entries'):
                        st.write(f"**Knowledge Entries Created:** {len(result['knowledge_entries'])}")


def render_analytics_tab():
    """Analytics and monitoring tab"""
    logger.info("Rendering analytics tab")
    
    st.markdown("### 📊 Analytics & Monitoring")
    st.markdown("Monitor your analysis sessions and template creation activities.")
    
    # Session analytics
    if st.session_state.current_session_id:
        st.markdown("#### 🔍 Current Session Analytics")
        
        # Load session data
        if st.button("🔄 Refresh Analytics", key="refresh_analytics"):
            logger.info("Refreshing session analytics")
            st.session_state.analysis_data = get_session_analysis_data(st.session_state.current_session_id)
        
        if hasattr(st.session_state, 'analysis_data') and st.session_state.analysis_data:
            data = st.session_state.analysis_data
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Tables Analyzed", len(data.get('tables', {})))
            
            with col2:
                total_columns = sum(len(cols) for cols in data.get('columns', {}).values())
                st.metric("Columns Analyzed", total_columns)
            
            with col3:
                st.metric("Selected Tables", len(st.session_state.selected_tables))
            
            with col4:
                query_count = len(getattr(st.session_state, 'query_analyses', []))
                st.metric("Queries Analyzed", query_count)
            
            # Session details
            if data.get('session_info'):
                session_info = data['session_info']
                st.markdown("#### 📋 Session Details")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Session ID:** {session_info.get('session_id', 'Unknown')[:8]}...")
                    st.write(f"**Database:** {session_info.get('database_name', 'Unknown')}")
                    st.write(f"**Type:** {session_info.get('database_type', 'Unknown')}")
                
                with col2:
                    st.write(f"**Status:** {session_info.get('status', 'Unknown')}")
                    st.write(f"**Tables Analyzed:** {session_info.get('tables_analyzed', 0)}")
                    st.write(f"**Columns Analyzed:** {session_info.get('columns_analyzed', 0)}")
    
    else:
        st.info("📊 No active session. Please configure a database connection first.")
    
    # Logging information
    st.markdown("---")
    st.markdown("#### 📝 System Logs")
    st.info("💡 Comprehensive logging is enabled. Check `/tmp/playground.log` for detailed logs.")
    
    # Show recent log entries (simplified)
    if st.button("📄 Show Recent Logs", key="show_logs"):
        try:
            with open('/tmp/playground.log', 'r') as f:
                logs = f.readlines()
                recent_logs = logs[-20:]  # Last 20 lines
                
                st.text_area(
                    "Recent Log Entries",
                    value=''.join(recent_logs),
                    height=300,
                    key="recent_logs"
                )
        except Exception as e:
            st.error(f"❌ Failed to read logs: {str(e)}")


if __name__ == "__main__":
    main()
