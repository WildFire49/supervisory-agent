#!/usr/bin/env python3
"""
Simple script to embed database schema into ChromaDB using existing API endpoints.
This will create the necessary collection and enable full vector DB retry.
"""

import asyncio
import os
import sys
from pathlib import Path
import logging
import uuid
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.agents.configurator.vector_storage import SchemaVectorStore
from app.agents.configurator.database_persistence import ConfiguratorDatabase
from app.services.schema_analysis_service import SchemaAnalysisService
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def embed_schema_for_connection(connection_id: str):
    """Embed schema metadata into ChromaDB for a specific connection."""
    
    logger.info(f"🚀 Starting schema embedding for connection: {connection_id}")
    
    try:
        # Initialize services
        db_persistence = ConfiguratorDatabase()
        vector_storage = SchemaVectorStore()
        schema_service = SchemaAnalysisService()
        
        # 1. Get connection details
        logger.info("📊 Fetching connection details...")
        connection = await db_persistence.get_connection(connection_id)
        if not connection:
            logger.error(f"❌ Connection not found: {connection_id}")
            return False
        
        logger.info(f"✅ Found connection: {connection.get('name', 'Unknown')}")
        
        # 2. Get stored schema analysis from database
        logger.info("🔍 Fetching stored schema analysis...")
        schema_analysis = await schema_service.get_schema_analysis(connection_id)
        
        if not schema_analysis or not schema_analysis.get('tables'):
            logger.error("❌ No schema analysis found in database. Please run configuration workflow first.")
            return False
        
        logger.info(f"✅ Found schema analysis:")
        logger.info(f"   - Tables: {len(schema_analysis.get('tables', []))}")
        logger.info(f"   - Business contexts identified: {len(set(t.get('business_context', '') for t in schema_analysis.get('tables', [])))}")
        
        # 3. Prepare schema info for vector storage
        logger.info("💾 Preparing schema for ChromaDB embedding...")
        
        # Convert schema analysis to format expected by vector storage
        schema_info = {
            'tables': [],
            'views': [],
            'relationships': schema_analysis.get('relationships', [])
        }
        
        # Process tables
        for table in schema_analysis.get('tables', []):
            table_info = {
                'table_name': table.get('table_name'),
                'schema_name': table.get('schema_name'),
                'columns': table.get('columns', []),
                'row_count': table.get('row_count'),
                'business_context': table.get('business_context'),
                'table_type': table.get('table_type', 'table')
            }
            
            if table.get('table_type') == 'view':
                schema_info['views'].append(table_info)
            else:
                schema_info['tables'].append(table_info)
        
        logger.info(f"   - Prepared {len(schema_info['tables'])} tables")
        logger.info(f"   - Prepared {len(schema_info['views'])} views")
        
        # 4. Store schema in vector DB
        logger.info("🚀 Embedding schema into ChromaDB...")
        
        # Store the schema
        success = await vector_storage.store_schema_info(
            connection_id=connection_id,
            schema_info=schema_info
        )
        
        if not success:
            logger.error("❌ Failed to store schema in ChromaDB")
            return False
        
        logger.info(f"✅ Schema successfully embedded into ChromaDB!")
        
        # 5. Test vector search
        logger.info("🧪 Testing vector search...")
        test_queries = [
            "loan amount disbursement",
            "collection due date",
            "customer details",
            "total disbursements"
        ]
        
        for query in test_queries:
            results = await vector_storage.search_schema(
                connection_id=connection_id,
                query=query,
                top_k=3
            )
            
            if results:
                logger.info(f"   ✅ Query '{query}' found {len(results)} results")
                for i, result in enumerate(results[:2], 1):
                    metadata = result.get('metadata', {})
                    table_name = metadata.get('table_name', 'Unknown')
                    column_name = metadata.get('column_name', '')
                    if column_name:
                        logger.info(f"      {i}. {table_name}.{column_name}")
                    else:
                        logger.info(f"      {i}. {table_name}")
            else:
                logger.warning(f"   ⚠️ Query '{query}' returned no results")
        
        logger.info("🎉 Schema embedding complete and ready for vector DB retry!")
        return True
        
    except Exception as e:
        logger.error(f"💥 Error embedding schema: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


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
        logger.info("\nNext steps:")
        logger.info("1. Go back to the playground")
        logger.info("2. Try the same query again")
        logger.info("3. The system should now automatically fix type casting errors")
    else:
        logger.error("\n❌ FAILED! Please check the logs above for errors")
        logger.error("\nTroubleshooting:")
        logger.error("1. Ensure the database configuration workflow was completed")
        logger.error("2. Check that schema analysis is stored in the database")
        logger.error("3. Verify ChromaDB is running and accessible")
    
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
