#!/usr/bin/env python3
"""
Create missing business_rules table and related tables
"""

import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

import logging
from app.core.database import engine, Base
from app.models.database.business_rules_models import (
    BusinessRuleModel, 
    BusinessRuleTemplateModel, 
    RuleValidationLogModel, 
    RuleExtractionLogModel
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_business_rules_tables():
    """Create all business rules related tables"""
    try:
        logger.info("Creating business rules tables...")
        
        # Create all tables defined in the models
        Base.metadata.create_all(bind=engine, tables=[
            BusinessRuleModel.__table__,
            BusinessRuleTemplateModel.__table__,
            RuleValidationLogModel.__table__,
            RuleExtractionLogModel.__table__
        ])
        
        logger.info("✅ Business rules tables created successfully!")
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        required_tables = [
            'business_rules',
            'business_rule_templates', 
            'rule_validation_logs',
            'rule_extraction_logs'
        ]
        
        for table in required_tables:
            if table in existing_tables:
                logger.info(f"✅ Table '{table}' exists")
            else:
                logger.error(f"❌ Table '{table}' not found")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating business rules tables: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_business_rules_tables()
    if success:
        print("🎉 Business rules tables created successfully!")
    else:
        print("❌ Failed to create business rules tables")
        sys.exit(1)
