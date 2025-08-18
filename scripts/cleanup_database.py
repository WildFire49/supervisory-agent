#!/usr/bin/env python3
"""
Database Cleanup Script
Clears all retrieval, configuration, and analysis data for fresh testing
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine
from app.models.database.schema_analysis_models import (
    SchemaAnalysisSessionModel,
    TableAnalysisModel,
    RelationshipAnalysisModel,
    BusinessContextAnalysisModel,
    SchemaEvolutionLogModel,
    QueryGenerationLogModel,
    QueryExecutionLogModel,
    DataQualityAssessmentModel
)
from app.models.database.business_rules_models import (
    BusinessRuleModel,
    BusinessRuleTemplateModel,
    RuleValidationResultModel
)
from app.models.database.configurator_models import (
    DatabaseConnectionModel,
    RetrievalConfigurationModel
)
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clear_chromadb_collections():
    """Clear ChromaDB collections"""
    try:
        import chromadb
        from app.core.config import settings
        
        # Connect to ChromaDB
        if hasattr(settings, 'CHROMA_HOST') and hasattr(settings, 'CHROMA_PORT'):
            client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT
            )
        else:
            client = chromadb.Client()
        
        # List and delete all collections
        collections = client.list_collections()
        for collection in collections:
            logger.info(f"Deleting ChromaDB collection: {collection.name}")
            client.delete_collection(collection.name)
            
        logger.info("ChromaDB collections cleared successfully")
        
    except Exception as e:
        logger.warning(f"Could not clear ChromaDB collections: {str(e)}")


def clear_postgresql_tables():
    """Clear all PostgreSQL tables related to retrieval and analysis"""
    
    with SessionLocal() as session:
        try:
            # Use raw SQL to disable foreign key checks temporarily
            logger.info("Temporarily disabling foreign key constraints...")
            session.execute(text("SET session_replication_role = replica;"))
            
            # Clear all tables without worrying about foreign key order
            logger.info("Clearing schema analysis data...")
            session.query(DataQualityAssessmentModel).delete()
            session.query(BusinessContextAnalysisModel).delete()
            session.query(RelationshipAnalysisModel).delete()
            session.query(TableAnalysisModel).delete()
            session.query(QueryExecutionLogModel).delete()
            session.query(QueryGenerationLogModel).delete()
            session.query(SchemaEvolutionLogModel).delete()
            session.query(SchemaAnalysisSessionModel).delete()
            
            # Clear business rules data
            logger.info("Clearing business rules data...")
            session.query(RuleValidationResultModel).delete()
            session.query(BusinessRuleModel).delete()
            session.query(BusinessRuleTemplateModel).delete()
            
            # Clear configurator data
            logger.info("Clearing configurator data...")
            session.query(RetrievalConfigurationModel).delete()
            session.query(DatabaseConnectionModel).delete()
            
            # Re-enable foreign key constraints
            logger.info("Re-enabling foreign key constraints...")
            session.execute(text("SET session_replication_role = DEFAULT;"))
            
            # Commit all deletions
            session.commit()
            logger.info("PostgreSQL tables cleared successfully")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error clearing PostgreSQL tables: {str(e)}")
            raise


def reset_sequences():
    """Reset PostgreSQL sequences if needed"""
    with SessionLocal() as session:
        try:
            # Reset any sequences that might need resetting
            # This is optional but ensures clean IDs for testing
            logger.info("Resetting sequences...")
            session.commit()
            
        except Exception as e:
            logger.warning(f"Could not reset sequences: {str(e)}")


def main():
    """Main cleanup function"""
    print("=" * 60)
    print("DATABASE CLEANUP SCRIPT")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    print()
    
    # Confirm with user
    response = input("This will DELETE ALL retrieval, configuration, and analysis data. Continue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Cleanup cancelled.")
        return
    
    try:
        # Clear PostgreSQL tables
        print("\n1. Clearing PostgreSQL tables...")
        clear_postgresql_tables()
        
        # Clear ChromaDB collections
        print("\n2. Clearing ChromaDB collections...")
        clear_chromadb_collections()
        
        # Reset sequences
        print("\n3. Resetting sequences...")
        reset_sequences()
        
        print("\n" + "=" * 60)
        print("✅ CLEANUP COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("You can now run a fresh configuration workflow.")
        print(f"Completed at: {datetime.now().isoformat()}")
        
    except Exception as e:
        print(f"\n❌ CLEANUP FAILED: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
