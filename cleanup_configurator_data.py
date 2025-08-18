#!/usr/bin/env python3
"""
Cleanup script to clear all configurator data from PostgreSQL and ChromaDB.
This allows for a fresh start with clean data.
"""
import asyncio
import logging
from sqlalchemy import text
from app.core.config import settings
from app.agents.configurator.database_persistence import configurator_db
from app.agents.configurator.vector_storage import SchemaVectorStore
import chromadb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def cleanup_postgresql_data():
    """Clear all configurator data from PostgreSQL."""
    try:
        logger.info("🧹 Cleaning up PostgreSQL configurator data...")
        
        # Clear all tables in reverse dependency order
        tables_to_clear = [
            "retrieval_test_queries",
            "retrieval_user_schema_inputs", 
            "retrieval_database_schemas",
            "retrieval_configuration_sessions",
            "retrieval_configurations",
            "retrieval_database_connections"
        ]
        
        with configurator_db.get_session() as session:
            for table in tables_to_clear:
                try:
                    result = session.execute(text(f"DELETE FROM {table}"))
                    session.commit()
                    logger.info(f"  ✓ Cleared {result.rowcount} rows from {table}")
                except Exception as e:
                    logger.warning(f"  ⚠️ Could not clear {table}: {e}")
                    session.rollback()
        
        logger.info("✅ PostgreSQL cleanup completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error cleaning PostgreSQL data: {e}")
        return False

async def cleanup_chromadb_data():
    """Clear all configurator collections from ChromaDB."""
    try:
        logger.info("🧹 Cleaning up ChromaDB collections...")
        
        # Connect to ChromaDB
        try:
            client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT
            )
            logger.info(f"  📡 Connected to remote ChromaDB at {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")
        except Exception as e:
            logger.warning(f"  ⚠️ Could not connect to remote ChromaDB: {e}")
            return False
        
        # List all collections
        collections = client.list_collections()
        logger.info(f"  📋 Found {len(collections)} collections")
        
        # Delete schema collections (those starting with 'schema_')
        deleted_count = 0
        for collection in collections:
            if collection.name.startswith('schema_'):
                try:
                    client.delete_collection(collection.name)
                    logger.info(f"  ✓ Deleted collection: {collection.name}")
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"  ⚠️ Could not delete {collection.name}: {e}")
        
        logger.info(f"✅ ChromaDB cleanup completed! Deleted {deleted_count} schema collections")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error cleaning ChromaDB data: {e}")
        return False

async def main():
    """Main cleanup function."""
    logger.info("🚀 Starting configurator data cleanup...")
    logger.info("=" * 60)
    
    # Cleanup PostgreSQL
    pg_success = await cleanup_postgresql_data()
    
    # Cleanup ChromaDB
    chroma_success = await cleanup_chromadb_data()
    
    logger.info("=" * 60)
    if pg_success and chroma_success:
        logger.info("🎉 Complete cleanup successful!")
        logger.info("📋 Ready for fresh configuration workflow:")
        logger.info("   1. Create new database connection")
        logger.info("   2. Start new configuration session") 
        logger.info("   3. Run configuration workflow")
        logger.info("   4. Generate test queries")
    else:
        logger.warning("⚠️ Partial cleanup completed. Check logs for details.")

if __name__ == "__main__":
    asyncio.run(main())
