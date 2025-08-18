#!/usr/bin/env python3
"""
Initialize the configurator database schemas.
This script creates all the necessary tables for the retrieval agent configurator.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.agents.configurator.database_persistence import Base, ConfiguratorDatabase
from app.core.config import settings
from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_configurator_database():
    """Initialize the configurator database with all required tables."""
    try:
        logger.info("Initializing configurator database...")
        logger.info(f"Database URL: {settings.DATABASE_URL}")
        
        # Create engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Created configurator database tables:")
        
        # List created tables
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'retrieval_%'
                ORDER BY table_name
            """))
            
            tables = result.fetchall()
            for table in tables:
                logger.info(f"  ✓ {table[0]}")
        
        logger.info("Configurator database initialization completed successfully!")
        
        # Initialize configurator database instance to ensure it works
        configurator_db = ConfiguratorDatabase()
        logger.info("ConfiguratorDatabase instance created successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"Error initializing configurator database: {str(e)}")
        return False

if __name__ == "__main__":
    success = init_configurator_database()
    if success:
        print("\n🎉 Configurator database initialized successfully!")
        print("\nCreated tables:")
        print("  • retrieval_database_connections")
        print("  • retrieval_database_schemas") 
        print("  • retrieval_user_schema_inputs")
        print("  • retrieval_configuration_sessions")
        print("  • retrieval_test_queries")
        print("  • retrieval_configurations")
        print("\nYou can now use the configurator API endpoints!")
    else:
        print("\n❌ Failed to initialize configurator database")
        sys.exit(1)
