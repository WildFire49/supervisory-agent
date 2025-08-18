#!/usr/bin/env python3
"""
Script to embed database schema into ChromaDB for vector search.
This will create the necessary collection and enable full vector DB retry.
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.agents.configurator.vector_storage import SchemaVectorStore
from app.agents.configurator.database_persistence import ConfiguratorDatabase
from app.agents.configurator.database_utils import DatabaseConnector, SchemaAnalyzer
from app.core.config import settings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def embed_schema_for_connection(connection_id: str):
    """Embed schema metadata into ChromaDB for a specific connection."""
    
    logger.info(f"🚀 Starting schema embedding for connection: {connection_id}")
    
    # Initialize services
    db_persistence = ConfiguratorDatabase()
    vector_storage = SchemaVectorStore()
    db_connector = DatabaseConnector()
    schema_analyzer = SchemaAnalyzer()
    
    try:
        # 1. Get connection details
        logger.info("📊 Fetching connection details...")
        connection = await db_persistence.get_connection(connection_id)
        if not connection:
            logger.error(f"❌ Connection not found: {connection_id}")
            return False
        
        logger.info(f"✅ Found connection: {connection.get('name', 'Unknown')}")
        
        # 2. Connect to database and analyze schema
        logger.info("🔍 Analyzing database schema...")
        schema_info = await db_utils.analyze_schema(
            connection['db_type'],
            connection['connection_string']
        )
        
        if not schema_info:
            logger.error("❌ Failed to analyze schema")
            return False
        
        logger.info(f"✅ Schema analysis complete:")
        logger.info(f"   - Tables: {len(schema_info.get('tables', []))}")
        logger.info(f"   - Views: {len(schema_info.get('views', []))}")
        logger.info(f"   - Relationships: {len(schema_info.get('relationships', []))}")
        
        # 3. Store schema metadata in vector DB
        logger.info("💾 Embedding schema into ChromaDB...")
        
        # Create collection name based on connection_id
        collection_name = f"schema_{connection_id.replace('-', '_')}"
        
        # Store schema information
        success = await vector_storage.store_schema_info(
            connection_id=connection_id,
            schema_info=schema_info
        )
        
        if success:
            logger.info(f"✅ Schema successfully embedded into collection: {collection_name}")
            
            # 4. Test vector search to verify
            logger.info("🧪 Testing vector search...")
            test_results = await vector_storage.search_schema(
                connection_id=connection_id,
                query="loan amount disbursement",
                top_k=5
            )
            
            if test_results:
                logger.info(f"✅ Vector search working! Found {len(test_results)} relevant tables/columns")
                for i, result in enumerate(test_results[:3], 1):
                    logger.info(f"   {i}. {result.get('metadata', {}).get('table_name', 'Unknown')}")
            else:
                logger.warning("⚠️ Vector search returned no results")
        else:
            logger.error("❌ Failed to embed schema into ChromaDB")
            return False
        
        # 5. Store schema analysis in database for persistence
        logger.info("📝 Persisting schema analysis to database...")
        await db_persistence.store_schema_analysis(
            connection_id=connection_id,
            schema_info=schema_info
        )
        
        logger.info("🎉 Schema embedding complete and ready for vector DB retry!")
        return True
        
    except Exception as e:
        logger.error(f"💥 Error embedding schema: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        await db_persistence.close()


async def main():
    """Main function to run schema embedding."""
    
    # Get the connection ID from the playground
    # This is the connection that was showing the error
    connection_id = "26c6b353-35b3-4125-9697-617b3b9c0146"
    
    logger.info("=" * 60)
    logger.info("SCHEMA EMBEDDING TO CHROMADB")
    logger.info("=" * 60)
    
    success = await embed_schema_for_connection(connection_id)
    
    if success:
        logger.info("\n✅ SUCCESS! Schema is now embedded in ChromaDB")
        logger.info("The vector DB retry and type casting fixes will now work automatically!")
    else:
        logger.error("\n❌ FAILED! Please check the logs above for errors")
    
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
