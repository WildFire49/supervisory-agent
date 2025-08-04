#!/usr/bin/env python3
"""
Database migration script to add versioning support to workflows table
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine, SessionLocal

def migrate_workflow_versioning():
    """Add versioning columns to workflows table"""
    db = SessionLocal()
    try:
        print("Starting workflow versioning migration...")
        
        # Add new columns to workflows table
        migrations = [
            "ALTER TABLE workflows ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1 NOT NULL;",
            "ALTER TABLE workflows ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;",
            "ALTER TABLE workflows ADD COLUMN IF NOT EXISTS modified_by VARCHAR NULL;",
            "ALTER TABLE workflows ADD COLUMN IF NOT EXISTS modification_reason TEXT NULL;",
        ]
        
        for migration in migrations:
            print(f"Executing: {migration}")
            db.execute(text(migration))
        
        # Update existing workflows to have version 1
        print("Setting version 1 for existing workflows...")
        db.execute(text("UPDATE workflows SET version = 1 WHERE version IS NULL;"))
        
        # Drop old unique constraint and add new one
        print("Updating unique constraints...")
        try:
            db.execute(text("ALTER TABLE workflows DROP CONSTRAINT IF EXISTS _bank_product_uc;"))
        except Exception as e:
            print(f"Note: Could not drop old constraint (may not exist): {e}")
        
        try:
            db.execute(text("ALTER TABLE workflows ADD CONSTRAINT _bank_product_version_uc UNIQUE (bank_name, product_type, deleted_at);"))
        except Exception as e:
            print(f"Note: Could not add new constraint (may already exist): {e}")
        
        db.commit()
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_workflow_versioning()
