#!/usr/bin/env python3
"""
Inspect actual database schema to find correct column names
This will help us fix the schema mismatch in the enhanced context templates
"""

import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

import asyncio
import logging
from sqlalchemy import create_engine, text, inspect
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inspect_database_schema():
    """Inspect the actual database schema to find correct column names"""
    try:
        # Create database connection
        engine = create_engine(settings.DATABASE_URL)
        
        print("🔍 INSPECTING ACTUAL DATABASE SCHEMA")
        print("="*70)
        
        # Get table inspector
        inspector = inspect(engine)
        
        # Tables we're interested in
        tables_to_inspect = [
            'loan_emi_mapping',
            'collection_details', 
            'collection_user',
            'employee'
        ]
        
        schema_info = {}
        
        for table_name in tables_to_inspect:
            print(f"\n📋 TABLE: staging_dashboard.{table_name}")
            print("-" * 50)
            
            try:
                # Get columns for this table
                columns = inspector.get_columns(table_name, schema='staging_dashboard')
                
                if not columns:
                    print(f"   ❌ Table not found or no columns")
                    continue
                
                table_columns = []
                for column in columns:
                    col_info = {
                        'name': column['name'],
                        'type': str(column['type']),
                        'nullable': column['nullable'],
                        'primary_key': column.get('primary_key', False)
                    }
                    table_columns.append(col_info)
                    
                    # Print column info
                    pk_marker = " (PK)" if col_info['primary_key'] else ""
                    nullable_marker = " (NULL)" if col_info['nullable'] else " (NOT NULL)"
                    print(f"   📝 {col_info['name']}: {col_info['type']}{pk_marker}{nullable_marker}")
                
                schema_info[table_name] = table_columns
                
                # Get foreign keys
                try:
                    foreign_keys = inspector.get_foreign_keys(table_name, schema='staging_dashboard')
                    if foreign_keys:
                        print(f"   🔗 FOREIGN KEYS:")
                        for fk in foreign_keys:
                            print(f"      {fk['constrained_columns']} -> {fk['referred_schema']}.{fk['referred_table']}.{fk['referred_columns']}")
                except:
                    print(f"   🔗 No foreign keys found")
                
            except Exception as e:
                print(f"   ❌ Error inspecting table {table_name}: {e}")
                continue
        
        # Now let's analyze the relationships we need
        print(f"\n🔍 ANALYZING RELATIONSHIPS FOR COLLECTION QUERIES")
        print("="*70)
        
        if 'loan_emi_mapping' in schema_info:
            lem_columns = [col['name'] for col in schema_info['loan_emi_mapping']]
            print(f"📋 loan_emi_mapping columns: {lem_columns}")
            
            # Look for potential relationship columns
            relationship_columns = [col for col in lem_columns if 'id' in col.lower() or 'ref' in col.lower()]
            print(f"🔗 Potential relationship columns: {relationship_columns}")
            
            # Check for collection-related columns
            collection_columns = [col for col in lem_columns if 'collection' in col.lower()]
            print(f"📊 Collection-related columns: {collection_columns}")
        
        # Generate corrected SQL template
        print(f"\n💡 SUGGESTED SCHEMA CORRECTIONS")
        print("="*70)
        
        if 'loan_emi_mapping' in schema_info:
            lem_cols = [col['name'] for col in schema_info['loan_emi_mapping']]
            
            # Try to find the correct relationship column
            possible_collection_refs = [
                col for col in lem_cols 
                if any(keyword in col.lower() for keyword in ['collection', 'detail', 'ref', 'fk'])
            ]
            
            if possible_collection_refs:
                print(f"✅ Found possible collection reference columns:")
                for col in possible_collection_refs:
                    print(f"   - {col}")
                
                # Suggest corrected SQL
                suggested_col = possible_collection_refs[0]
                print(f"\n📝 SUGGESTED SQL CORRECTION:")
                print(f"   Instead of: lem.collection_details_id")
                print(f"   Try using: lem.{suggested_col}")
                
                corrected_sql = f"""
SELECT 
  e.employee_name AS field_officer,
  e.employee_code,
  ROUND((SUM(lem.emi_collected) / NULLIF(SUM(lem.emi_amount), 0) * 100)::numeric, 2) AS collection_percentage
FROM staging_dashboard.loan_emi_mapping lem
JOIN staging_dashboard.collection_details cd ON cd.source_id = lem.{suggested_col}
JOIN staging_dashboard.collection_user cu ON cu.source_id = cd.field_officer_id
JOIN staging_dashboard.employee e ON e.source_id = cu.employee_id
WHERE lem.collection_due_date >= DATE_TRUNC('month', CURRENT_DATE)
  AND lem.collection_due_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
GROUP BY e.employee_name, e.employee_code
ORDER BY collection_percentage DESC
LIMIT 1;
"""
                print(corrected_sql)
            else:
                print(f"❌ No obvious collection reference columns found")
                print(f"   Available columns: {lem_cols}")
        
        return schema_info
        
    except Exception as e:
        print(f"❌ Error inspecting database: {e}")
        import traceback
        traceback.print_exc()
        return {}

if __name__ == "__main__":
    schema_info = inspect_database_schema()
    
    if schema_info:
        print(f"\n✅ Schema inspection completed successfully!")
        print(f"📊 Found {len(schema_info)} tables with schema information")
    else:
        print(f"❌ Schema inspection failed")
