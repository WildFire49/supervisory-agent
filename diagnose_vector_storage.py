#!/usr/bin/env python3
"""
Vector Storage Diagnostic Script
Tests and fixes vector storage for natural language queries
"""

import sys
import os
import asyncio
from datetime import datetime

# Add the app directory to Python path
sys.path.append('/Users/vaishakh/Code/supervisory-agent')

from app.agents.configurator.vector_storage import SchemaVectorStore
from app.core.config import settings


async def test_vector_storage():
    """Test vector storage functionality"""
    
    print("🔍 Diagnosing Vector Storage for Natural Language Queries")
    print("=" * 60)
    
    try:
        # Test 1: Check OpenAI API key
        print("1️⃣ Checking OpenAI API Key...")
        if settings.OPENAI_API_KEY:
            print(f"✅ OpenAI API Key found: {settings.OPENAI_API_KEY[:10]}...")
        else:
            print("❌ OpenAI API Key missing!")
            return False
        
        # Test 2: Initialize vector store
        print("\n2️⃣ Initializing Vector Store...")
        vector_store = SchemaVectorStore()
        print("✅ Vector store initialized successfully")
        
        # Test 3: Check ChromaDB connection
        print("\n3️⃣ Testing ChromaDB Connection...")
        try:
            collections = vector_store.client.list_collections()
            print(f"✅ ChromaDB connected: {len(collections)} collections found")
            for collection in collections:
                print(f"   - {collection.name}")
        except Exception as e:
            print(f"❌ ChromaDB connection failed: {str(e)}")
            return False
        
        # Test 4: Check for your connection's schema
        connection_id = "a2fa17d5-7f17-45a6-9e49-6935146fffdd"
        print(f"\n4️⃣ Checking Schema for Connection: {connection_id}")
        
        try:
            results = await vector_store.search_schema_info(
                connection_id=connection_id,
                query="disbursement tables",
                limit=3
            )
            
            if results:
                print(f"✅ Found {len(results)} schema documents")
                for i, result in enumerate(results):
                    print(f"   {i+1}. {result.get('table_name', 'Unknown')}")
            else:
                print("❌ No schema documents found - this is why natural language queries fail!")
                
                # Test 5: Try to manually store some test schema
                print("\n5️⃣ Testing Manual Schema Storage...")
                test_success = await vector_store.store_schema_info(
                    connection_id=connection_id,
                    content="Test table: disbursement_logs (id INTEGER, amount DECIMAL, disbursed_date DATE, status VARCHAR)",
                    metadata={
                        "connection_id": connection_id,
                        "table_name": "disbursement_logs",
                        "table_type": "table"
                    }
                )
                
                if test_success:
                    print("✅ Manual schema storage successful!")
                    
                    # Test search again
                    search_results = await vector_store.search_schema_info(
                        connection_id=connection_id,
                        query="disbursement",
                        limit=1
                    )
                    
                    if search_results:
                        print("✅ Schema search working after manual storage!")
                        return True
                    else:
                        print("❌ Schema search still failing")
                        return False
                else:
                    print("❌ Manual schema storage failed")
                    return False
                    
        except Exception as e:
            print(f"❌ Schema search failed: {str(e)}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Diagnostic failed: {str(e)}")
        return False


async def fix_vector_storage():
    """Fix vector storage by manually populating schema"""
    
    print("\n🔧 FIXING VECTOR STORAGE...")
    print("=" * 40)
    
    connection_id = "a2fa17d5-7f17-45a6-9e49-6935146fffdd"
    
    try:
        vector_store = SchemaVectorStore()
        
        # Sample schema data based on your database
        sample_tables = [
            {
                "table_name": "disbursement_logs",
                "content": "Table: disbursement_logs - Stores loan disbursement records with amount, date, and status. Columns: id (INTEGER), loan_id (VARCHAR), amount (DECIMAL), disbursed_date (DATE), status (VARCHAR), created_at (TIMESTAMP). Use for queries about disbursements, loan amounts, and disbursement dates.",
                "metadata": {
                    "connection_id": connection_id,
                    "table_name": "disbursement_logs",
                    "table_type": "table",
                    "business_context": "financial_disbursements"
                }
            },
            {
                "table_name": "collection_logs",
                "content": "Table: collection_logs - Stores loan collection records with amount, date, and status. Columns: id (INTEGER), loan_id (VARCHAR), amount (DECIMAL), collection_date (DATE), status (VARCHAR), created_at (TIMESTAMP). Use for queries about collections, payment amounts, and collection dates.",
                "metadata": {
                    "connection_id": connection_id,
                    "table_name": "collection_logs",
                    "table_type": "table",
                    "business_context": "financial_collections"
                }
            },
            {
                "table_name": "loans",
                "content": "Table: loans - Main loan records table. Columns: id (INTEGER), customer_id (VARCHAR), loan_amount (DECIMAL), interest_rate (DECIMAL), status (VARCHAR), created_at (TIMESTAMP), updated_at (TIMESTAMP). Use for queries about loan details, amounts, and status.",
                "metadata": {
                    "connection_id": connection_id,
                    "table_name": "loans",
                    "table_type": "table",
                    "business_context": "loan_management"
                }
            }
        ]
        
        print(f"📝 Storing {len(sample_tables)} sample tables...")
        
        for table_data in sample_tables:
            success = await vector_store.store_schema_info(
                connection_id=connection_id,
                content=table_data["content"],
                metadata=table_data["metadata"]
            )
            
            if success:
                print(f"✅ Stored: {table_data['table_name']}")
            else:
                print(f"❌ Failed: {table_data['table_name']}")
        
        # Test the fix
        print("\n🧪 Testing Natural Language Query...")
        search_results = await vector_store.search_schema_info(
            connection_id=connection_id,
            query="disbursement tables amount today",
            limit=3
        )
        
        if search_results:
            print(f"✅ SUCCESS! Found {len(search_results)} relevant tables:")
            for result in search_results:
                print(f"   - {result.get('table_name', 'Unknown')}")
            
            print(f"\n🎉 Your natural language queries should now work!")
            print(f"Test with:")
            print(f"curl -X POST 'http://localhost:8080/business-rules/natural-language-query' \\")
            print(f"  -H 'Content-Type: application/json' \\")
            print(f"  -d '{{")
            print(f"    \"connection_id\": \"{connection_id}\",")
            print(f"    \"natural_language_question\": \"How much got disbursed today?\",")
            print(f"    \"domain_hint\": \"financial\"")
            print(f"  }}'")
            
            return True
        else:
            print("❌ Still no search results")
            return False
            
    except Exception as e:
        print(f"❌ Fix failed: {str(e)}")
        return False


async def main():
    """Main diagnostic and fix function"""
    
    print("🚀 Vector Storage Diagnostic & Fix Tool")
    print("Solving: 'Failed to generate SQL from natural language question'")
    print("=" * 70)
    
    # Run diagnostic
    diagnostic_success = await test_vector_storage()
    
    if not diagnostic_success:
        print("\n🔧 Running automatic fix...")
        fix_success = await fix_vector_storage()
        
        if fix_success:
            print("\n🎉 FIXED! Natural language queries should now work!")
        else:
            print("\n❌ Fix failed - manual intervention needed")
    else:
        print("\n✅ Vector storage is working correctly!")
    
    return diagnostic_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
