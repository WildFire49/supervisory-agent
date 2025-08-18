#!/usr/bin/env python3
"""
Simple test to verify the direct type casting fix works
"""

import re

# Test the exact error message and SQL from the API response
error_message = "(psycopg2.errors.UndefinedFunction) function sum(text) does not exist"
original_sql = """-- Query to calculate total disbursements for the current month
SELECT 
    SUM(loan_amount) AS total_disbursements
FROM 
    staging_dashboard.fed_disbursement_details
WHERE 
    disbursement_date >= DATE_TRUNC('month', CURRENT_DATE)
    AND disbursement_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
    AND disbursement_status = 'success';"""

print("🧪 Testing Direct Type Casting Fix")
print("=" * 50)

# Test 1: Error detection
print("1. Error Detection:")
has_sum_text_error = "function sum(text) does not exist" in error_message.lower()
print(f"   SUM(text) error detected: {has_sum_text_error}")

# Test 2: SQL pattern replacement
print("\n2. SQL Pattern Replacement:")
print(f"   Original SQL: {original_sql[:100]}...")

fixed_sql = re.sub(r'SUM\s*\(([^)]+)\)', r'SUM(\1::numeric)', original_sql, flags=re.IGNORECASE)
sql_changed = fixed_sql != original_sql

print(f"   SQL changed: {sql_changed}")
if sql_changed:
    print(f"   Fixed SQL: {fixed_sql[:100]}...")
    
    # Show the specific change
    original_line = [line for line in original_sql.split('\n') if 'SUM(' in line][0].strip()
    fixed_line = [line for line in fixed_sql.split('\n') if 'SUM(' in line][0].strip()
    
    print(f"\n   Specific change:")
    print(f"   Before: {original_line}")
    print(f"   After:  {fixed_line}")

# Test 3: Complete fix logic
print("\n3. Complete Fix Logic:")
should_apply_fix = has_sum_text_error and sql_changed
print(f"   Should apply fix: {should_apply_fix}")

if should_apply_fix:
    print("✅ Direct type casting fix should work!")
    print("\nFixed SQL:")
    print(fixed_sql)
else:
    print("❌ Direct type casting fix will not work!")
