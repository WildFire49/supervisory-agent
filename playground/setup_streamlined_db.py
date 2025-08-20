#!/usr/bin/env python3
"""
Database Setup Script for Streamlined Playground
Creates all necessary tables for the new analysis system
"""

import sys
import logging
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """Create all database tables for the streamlined playground"""
    logger.info("Setting up database tables for streamlined playground")
    
    try:
        from app.core.database import engine, Base
        from app.models.database.playground_analysis_models import (
            PlaygroundAnalysisSession,
            PlaygroundTableAnalysis,
            PlaygroundColumnAnalysis,
            PlaygroundQueryAnalysis,
            PlaygroundKnowledgeBase
        )
        
        logger.info("Creating all tables...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Database tables created successfully!")
        
        # Verify tables exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        expected_tables = [
            'playground_analysis_sessions',
            'playground_table_analysis',
            'playground_column_analysis',
            'playground_query_analysis',
            'playground_knowledge_base'
        ]
        
        created_tables = [table for table in expected_tables if table in tables]
        logger.info(f"Created tables: {created_tables}")
        
        if len(created_tables) == len(expected_tables):
            logger.info("✅ All required tables created successfully!")
            return True
        else:
            missing_tables = set(expected_tables) - set(created_tables)
            logger.error(f"❌ Missing tables: {missing_tables}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database setup failed: {str(e)}")
        return False

def test_database_connection():
    """Test database connection and basic operations"""
    logger.info("Testing database connection")
    
    try:
        from app.core.database import SessionLocal
        from app.models.database.playground_analysis_models import PlaygroundAnalysisSession
        import uuid
        
        with SessionLocal() as session:
            # Test creating a session
            test_session = PlaygroundAnalysisSession(
                session_id=str(uuid.uuid4()),
                connection_id=str(uuid.uuid4()),
                database_type="postgresql",
                database_name="test_db",
                status="started"
            )
            
            session.add(test_session)
            session.commit()
            
            # Test querying
            result = session.query(PlaygroundAnalysisSession).filter(
                PlaygroundAnalysisSession.session_id == test_session.session_id
            ).first()
            
            if result:
                logger.info("✅ Database connection test successful!")
                
                # Clean up test data
                session.delete(result)
                session.commit()
                
                return True
            else:
                logger.error("❌ Database query test failed")
                return False
                
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Starting streamlined playground database setup")
    
    # Setup database
    if setup_database():
        logger.info("✅ Database setup completed")
        
        # Test connection
        if test_database_connection():
            logger.info("✅ Database testing completed")
            logger.info("🎉 Streamlined playground is ready to use!")
        else:
            logger.error("❌ Database testing failed")
            sys.exit(1)
    else:
        logger.error("❌ Database setup failed")
        sys.exit(1)
