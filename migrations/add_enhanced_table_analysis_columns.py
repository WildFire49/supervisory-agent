"""
Database migration to add enhanced table analysis columns
Run this to add the new columns for comprehensive AI-powered table analysis
"""

from sqlalchemy import text
from app.core.database import SessionLocal, engine
import logging

logger = logging.getLogger(__name__)

def migrate_table_analysis_model():
    """Add enhanced columns to table_analysis_results table"""
    
    # SQL statements to add new columns
    migration_sql = [
        # Enhanced AI-powered analysis results
        "ALTER TABLE table_analysis_results ADD COLUMN IF NOT EXISTS ai_business_description TEXT;",
        "ALTER TABLE table_analysis_results ADD COLUMN IF NOT EXISTS primary_purpose VARCHAR(500);",
        "ALTER TABLE table_analysis_results ADD COLUMN IF NOT EXISTS data_category VARCHAR(100);",
        "ALTER TABLE table_analysis_results ADD COLUMN IF NOT EXISTS parent_tables JSON DEFAULT '[]';",
        "ALTER TABLE table_analysis_results ADD COLUMN IF NOT EXISTS child_tables JSON DEFAULT '[]';",
        "ALTER TABLE table_analysis_results ADD COLUMN IF NOT EXISTS key_columns JSON DEFAULT '[]';",
        "ALTER TABLE table_analysis_results ADD COLUMN IF NOT EXISTS business_processes JSON DEFAULT '[]';",
        "ALTER TABLE table_analysis_results ADD COLUMN IF NOT EXISTS typical_queries JSON DEFAULT '[]';",
        "ALTER TABLE table_analysis_results ADD COLUMN IF NOT EXISTS join_patterns JSON DEFAULT '[]';",
        
        # Column-level analysis (comprehensive)
        "ALTER TABLE table_analysis_results ADD COLUMN IF NOT EXISTS columns_analysis JSON DEFAULT '[]';",
        "ALTER TABLE table_analysis_results ADD COLUMN IF NOT EXISTS enum_columns JSON DEFAULT '[]';",
        "ALTER TABLE table_analysis_results ADD COLUMN IF NOT EXISTS sample_data JSON DEFAULT '[]';",
        
        # Analysis versioning and caching
        "ALTER TABLE table_analysis_results ADD COLUMN IF NOT EXISTS analysis_version VARCHAR(50) DEFAULT '1.0';",
        "ALTER TABLE table_analysis_results ADD COLUMN IF NOT EXISTS connection_id UUID;",
        "ALTER TABLE table_analysis_results ADD COLUMN IF NOT EXISTS schema_hash VARCHAR(255);",
        "ALTER TABLE table_analysis_results ADD COLUMN IF NOT EXISTS analysis_duration_ms FLOAT;",
        
        # Add index on connection_id for performance
        "CREATE INDEX IF NOT EXISTS idx_table_analysis_connection_id ON table_analysis_results(connection_id);",
        "CREATE INDEX IF NOT EXISTS idx_table_analysis_schema_table ON table_analysis_results(schema_name, table_name);",
    ]
    
    try:
        with SessionLocal() as session:
            logger.info("🚀 Starting table_analysis_results migration...")
            
            for i, sql in enumerate(migration_sql, 1):
                try:
                    session.execute(text(sql))
                    logger.info(f"✅ Migration step {i}/{len(migration_sql)}: {sql[:50]}...")
                except Exception as e:
                    logger.warning(f"⚠️ Migration step {i} failed (may already exist): {e}")
            
            session.commit()
            logger.info("✅ Migration completed successfully!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

def verify_migration():
    """Verify that all new columns exist"""
    verification_sql = """
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'table_analysis_results' 
    AND column_name IN (
        'ai_business_description', 'primary_purpose', 'data_category',
        'parent_tables', 'child_tables', 'key_columns', 'business_processes',
        'typical_queries', 'join_patterns', 'columns_analysis', 'enum_columns',
        'sample_data', 'analysis_version', 'connection_id', 'schema_hash',
        'analysis_duration_ms'
    )
    ORDER BY column_name;
    """
    
    try:
        with SessionLocal() as session:
            result = session.execute(text(verification_sql))
            columns = [row[0] for row in result.fetchall()]
            
            expected_columns = [
                'ai_business_description', 'analysis_duration_ms', 'analysis_version',
                'business_processes', 'child_tables', 'columns_analysis', 'connection_id',
                'data_category', 'enum_columns', 'join_patterns', 'key_columns',
                'parent_tables', 'primary_purpose', 'sample_data', 'schema_hash',
                'typical_queries'
            ]
            
            missing_columns = set(expected_columns) - set(columns)
            
            if missing_columns:
                logger.warning(f"⚠️ Missing columns: {missing_columns}")
                return False
            else:
                logger.info(f"✅ All {len(columns)} enhanced columns verified!")
                return True
                
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Running table analysis enhancement migration...")
    
    # Run migration
    if migrate_table_analysis_model():
        print("✅ Migration completed!")
        
        # Verify migration
        if verify_migration():
            print("✅ Migration verified successfully!")
        else:
            print("⚠️ Migration verification failed - some columns may be missing")
    else:
        print("❌ Migration failed!")
