#!/usr/bin/env python3
"""
Direct script to embed database schema into ChromaDB.
Uses the existing vector storage implementation directly.
"""

import asyncio
import os
import sys
from pathlib import Path
import logging
from datetime import datetime
import chromadb
from chromadb.config import Settings
import uuid

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import psycopg2
from sqlalchemy import create_engine, inspect, text
from openai import OpenAI

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
CONNECTION_ID = "26c6b353-35b3-4125-9697-617b3b9c0146"
CONNECTION_STRING = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/supervisory_agent")
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def get_chroma_client():
    """Get ChromaDB client."""
    return chromadb.HttpClient(
        host=CHROMA_HOST,
        port=CHROMA_PORT,
        settings=Settings(anonymized_telemetry=False)
    )


def get_openai_embeddings(texts):
    """Generate embeddings using OpenAI."""
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    embeddings = []
    for text in texts:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        embeddings.append(response.data[0].embedding)
    
    return embeddings


async def analyze_database_schema():
    """Analyze the database schema."""
    logger.info("🔍 Analyzing database schema...")
    
    engine = create_engine(CONNECTION_STRING)
    inspector = inspect(engine)
    
    schema_info = {
        'tables': [],
        'views': [],
        'relationships': []
    }
    
    # Get all schemas
    schemas = inspector.get_schema_names()
    logger.info(f"   Found schemas: {schemas}")
    
    # Focus on staging_dashboard schema
    target_schemas = ['staging_dashboard', 'public']
    
    for schema_name in target_schemas:
        if schema_name not in schemas:
            continue
            
        # Get tables
        tables = inspector.get_table_names(schema=schema_name)
        logger.info(f"   Schema '{schema_name}' has {len(tables)} tables")
        
        for table_name in tables[:50]:  # Limit to first 50 tables for testing
            columns = inspector.get_columns(table_name, schema=schema_name)
            
            # Get row count
            try:
                with engine.connect() as conn:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {schema_name}.{table_name} LIMIT 1"))
                    row_count = result.scalar()
            except:
                row_count = 0
            
            table_info = {
                'table_name': table_name,
                'schema_name': schema_name,
                'full_name': f"{schema_name}.{table_name}",
                'columns': [
                    {
                        'column_name': col['name'],
                        'data_type': str(col['type']),
                        'nullable': col.get('nullable', True)
                    }
                    for col in columns
                ],
                'row_count': row_count,
                'business_context': determine_business_context(table_name)
            }
            
            schema_info['tables'].append(table_info)
    
    logger.info(f"✅ Schema analysis complete: {len(schema_info['tables'])} tables")
    return schema_info


def determine_business_context(table_name):
    """Determine business context from table name."""
    contexts = {
        'disbursement': 'Loan Disbursement',
        'collection': 'Loan Collection',
        'customer': 'Customer Management',
        'loan': 'Loan Management',
        'payment': 'Payment Processing',
        'transaction': 'Transaction Management',
        'account': 'Account Management',
        'product': 'Product Management'
    }
    
    table_lower = table_name.lower()
    for key, context in contexts.items():
        if key in table_lower:
            return context
    
    return 'General Business'


async def embed_schema_to_chromadb(schema_info):
    """Embed schema information into ChromaDB."""
    logger.info("💾 Embedding schema into ChromaDB...")
    
    # Get ChromaDB client
    client = get_chroma_client()
    
    # Create collection name
    collection_name = f"schema_{CONNECTION_ID.replace('-', '_')}"
    
    # Delete existing collection if it exists
    try:
        client.delete_collection(collection_name)
        logger.info(f"   Deleted existing collection: {collection_name}")
    except:
        pass
    
    # Create new collection with cosine similarity for text embeddings
    # Cosine is better than L2 (default) for semantic text search
    collection = client.create_collection(
        name=collection_name,
        metadata={
            "description": "Database schema information",
            "hnsw:space": "cosine"  # Use cosine distance instead of L2
        }
    )
    logger.info(f"   Created collection: {collection_name}")
    
    # Prepare documents for embedding
    documents = []
    metadatas = []
    ids = []
    
    # Add table-level documents
    for table in schema_info['tables']:
        # Table document
        table_doc = f"Table: {table['full_name']}\n"
        table_doc += f"Business Context: {table['business_context']}\n"
        table_doc += f"Columns: {', '.join([col['column_name'] for col in table['columns']])}\n"
        table_doc += f"Row Count: {table['row_count']}"
        
        documents.append(table_doc)
        metadatas.append({
            'type': 'table',
            'table_name': table['full_name'],
            'schema_name': table['schema_name'],
            'business_context': table['business_context'],
            'row_count': str(table['row_count'])
        })
        ids.append(f"table_{table['schema_name']}_{table['table_name']}")
        
        # Add column-level documents
        for col in table['columns']:
            col_doc = f"Column: {table['full_name']}.{col['column_name']}\n"
            col_doc += f"Table: {table['full_name']}\n"
            col_doc += f"Data Type: {col['data_type']}\n"
            col_doc += f"Business Context: {table['business_context']}"
            
            documents.append(col_doc)
            metadatas.append({
                'type': 'column',
                'table_name': table['full_name'],
                'column_name': col['column_name'],
                'data_type': col['data_type'],
                'business_context': table['business_context']
            })
            ids.append(f"col_{table['schema_name']}_{table['table_name']}_{col['column_name']}")
    
    logger.info(f"   Prepared {len(documents)} documents for embedding")
    
    # Generate embeddings
    logger.info("   Generating embeddings...")
    embeddings = get_openai_embeddings(documents)
    
    # Add to collection
    logger.info("   Adding documents to ChromaDB...")
    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )
    
    logger.info(f"✅ Successfully embedded {len(documents)} documents into ChromaDB")
    return collection_name


async def test_vector_search(collection_name):
    """Test vector search to verify embedding."""
    logger.info("🧪 Testing vector search...")
    
    client = get_chroma_client()
    collection = client.get_collection(collection_name)
    
    test_queries = [
        "loan amount disbursement",
        "collection due date",
        "total disbursements",
        "customer details"
    ]
    
    for query in test_queries:
        # Generate embedding for query
        query_embedding = get_openai_embeddings([query])[0]
        
        # Search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )
        
        logger.info(f"\n   Query: '{query}'")
        if results['metadatas'] and results['metadatas'][0]:
            for i, metadata in enumerate(results['metadatas'][0], 1):
                if metadata.get('type') == 'column':
                    logger.info(f"      {i}. {metadata.get('table_name')}.{metadata.get('column_name')}")
                else:
                    logger.info(f"      {i}. {metadata.get('table_name')}")
        else:
            logger.warning(f"      No results found")


async def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("DIRECT SCHEMA EMBEDDING TO CHROMADB")
    logger.info("=" * 60)
    
    try:
        # 1. Analyze database schema
        schema_info = await analyze_database_schema()
        
        # 2. Embed into ChromaDB
        collection_name = await embed_schema_to_chromadb(schema_info)
        
        # 3. Test vector search
        await test_vector_search(collection_name)
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ SUCCESS! Schema is now embedded in ChromaDB")
        logger.info("The vector DB retry and type casting fixes will now work!")
        logger.info("\nNext steps:")
        logger.info("1. Go back to the playground")
        logger.info("2. Try the query again: 'total disbursements for current month'")
        logger.info("3. The system should now automatically fix type casting errors")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
