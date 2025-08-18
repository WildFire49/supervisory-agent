#!/usr/bin/env python3
"""
Test script to verify and fix the automatic type casting for SUM(text) errors
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.configurator.query_executor import QueryExecutor
from app.agents.configurator.business_rules_persistence import BusinessRulesDatabase
from app.agents.configurator.rule_enhanced_query_generator import RuleEnhancedQueryGenerator
from app.models.business_rules import TestQuery
import uuid
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_type_casting_fix():
    """Test the automatic type casting fix for SUM(text) errors"""
    
    try:
        # Initialize components
        rules_db = BusinessRulesDatabase()
        rule_enhanced_generator = RuleEnhancedQueryGenerator(
            llm=None,  # We'll test the manual fix directly
            vector_store=None,
            rules_db=rules_db
        )
        
        query_executor = QueryExecutor(rules_db, rule_enhanced_generator)
        
        # Test the manual type casting fix directly
        logger.info("🧪 Testing manual type casting fix...")
        
        # Create a test query with SUM(text) that should fail
        test_query = TestQuery(
            query_id=str(uuid.uuid4()),
            connection_id="26c6b353-35b3-4125-9697-617b3b9c0146",
            sql_query="""
            SELECT 
                SUM(loan_amount) AS total_disbursements
            FROM 
                staging_dashboard.fed_disbursement_details
            WHERE 
                disbursement_date >= DATE_TRUNC('month', CURRENT_DATE)
                AND disbursement_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
                AND disbursement_status = 'success'
            """,
            description="Test query for type casting fix",
            expected_result_type="rows",
            business_context="Test query"
        )
        
        # Test the manual type casting fix
        fixed_query = await query_executor._manual_type_casting_fix(
            connection_id="26c6b353-35b3-4125-9697-617b3b9c0146",
            natural_language_question="What is the total disbursement amount for this month?",
            domain_hint="financial"
        )
        
        if fixed_query:
            logger.info("✅ Manual type casting fix generated SQL:")
            logger.info(f"   Original: {test_query.sql_query.strip()}")
            logger.info(f"   Fixed:    {fixed_query.sql_query.strip()}")
            
            # Check if the fix was applied
            if "::numeric" in fixed_query.sql_query:
                logger.info("✅ Type casting was successfully applied!")
                return True
            else:
                logger.error("❌ Type casting was NOT applied!")
                return False
        else:
            logger.error("❌ Manual type casting fix returned None")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing type casting fix: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_error_detection():
    """Test the error detection logic"""
    
    try:
        rules_db = BusinessRulesDatabase()
        rule_enhanced_generator = RuleEnhancedQueryGenerator(
            llm=None,
            vector_store=None,
            rules_db=rules_db
        )
        
        query_executor = QueryExecutor(rules_db, rule_enhanced_generator)
        
        # Test error message from the actual failure
        error_message = """(psycopg2.errors.UndefinedFunction) function sum(text) does not exist
LINE 3:     SUM(loan_amount) AS total_disbursements
            ^
HINT:  No function matches the given name and argument types. You might need to add explicit type casts."""
        
        logger.info("🔍 Testing error detection...")
        
        is_schema_error = query_executor._is_schema_mismatch_error(error_message)
        is_type_error = query_executor._is_data_type_error(error_message)
        
        logger.info(f"   Schema error detected: {is_schema_error}")
        logger.info(f"   Type error detected: {is_type_error}")
        
        if is_type_error:
            logger.info("✅ Error detection is working correctly!")
            return True
        else:
            logger.error("❌ Error detection is NOT working!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing error detection: {str(e)}")
        return False

async def main():
    """Main test function"""
    logger.info("🚀 Starting type casting fix tests...")
    
    # Test 1: Error detection
    logger.info("\n" + "="*50)
    logger.info("TEST 1: Error Detection")
    logger.info("="*50)
    
    error_detection_works = await test_error_detection()
    
    # Test 2: Type casting fix
    logger.info("\n" + "="*50)
    logger.info("TEST 2: Manual Type Casting Fix")
    logger.info("="*50)
    
    type_casting_works = await test_type_casting_fix()
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("TEST SUMMARY")
    logger.info("="*50)
    
    logger.info(f"Error Detection: {'✅ PASS' if error_detection_works else '❌ FAIL'}")
    logger.info(f"Type Casting Fix: {'✅ PASS' if type_casting_works else '❌ FAIL'}")
    
    if error_detection_works and type_casting_works:
        logger.info("🎉 All tests PASSED! The type casting fix should work.")
    else:
        logger.info("💥 Some tests FAILED! Need to debug further.")
    
    return error_detection_works and type_casting_works

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
