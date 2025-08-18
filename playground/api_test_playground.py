#!/usr/bin/env python3
"""
API Testing Playground for Context Template System
Simple script to test the context template API endpoints
"""

import requests
import json
import uuid
from datetime import datetime
from typing import Dict, Any

class ContextTemplateAPITester:
    """API testing client for context template system"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.connection_id = None
        self.template_id = None
    
    def test_server_health(self) -> bool:
        """Test if the server is running"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ Server is running")
                return True
            else:
                print(f"❌ Server health check failed: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to server. Make sure it's running at http://localhost:8000")
            return False
    
    def create_test_connection(self) -> str:
        """Create a test connection ID"""
        self.connection_id = str(uuid.uuid4())
        print(f"🔗 Created test connection ID: {self.connection_id}")
        return self.connection_id
    
    def test_create_template(self) -> bool:
        """Test creating a context template"""
        print("\n📝 Testing template creation...")
        
        if not self.connection_id:
            self.create_test_connection()
        
        payload = {
            "connection_id": self.connection_id,
            "template_name": "Test Financial Template",
            "database_type": "postgresql",
            "domain_hint": "financial",
            "business_rules_template": """
# Test Business Rules
- Use current tables over historical ones
- Apply proper date filtering
- Use SUM for amount aggregations
            """,
            "schema_context_template": """
# Test Schema Context
- Primary tables: loans, customers, transactions
- Key relationships: customer_id, loan_id
- Date fields: created_date, updated_date
            """,
            "domain_specific_prompts": """
# Financial Domain Prompts
- Focus on accuracy for monetary calculations
- Apply regulatory compliance rules
- Use appropriate aggregation functions
            """
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/context-templates/",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                self.template_id = result.get("template_id")
                print(f"✅ Template created successfully: {self.template_id}")
                return True
            else:
                print(f"❌ Template creation failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating template: {str(e)}")
            return False
    
    def test_get_template(self) -> bool:
        """Test retrieving a template"""
        print("\n🔍 Testing template retrieval...")
        
        if not self.connection_id:
            print("❌ No connection ID available")
            return False
        
        try:
            response = self.session.get(
                f"{self.base_url}/context-templates/{self.connection_id}"
            )
            
            if response.status_code == 200:
                template = response.json()
                print("✅ Template retrieved successfully")
                print(f"   Name: {template.get('template_name')}")
                print(f"   Version: {template.get('version')}")
                print(f"   Domain: {template.get('domain_hint')}")
                return True
            else:
                print(f"❌ Template retrieval failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error retrieving template: {str(e)}")
            return False
    
    def test_update_template(self) -> bool:
        """Test updating a template"""
        print("\n✏️ Testing template update...")
        
        if not self.template_id:
            print("❌ No template ID available")
            return False
        
        payload = {
            "template_id": self.template_id,
            "updates": {
                "business_rules_template": "Updated business rules content",
                "updated_by": "api_tester"
            }
        }
        
        try:
            response = self.session.put(
                f"{self.base_url}/context-templates/{self.template_id}",
                json=payload
            )
            
            if response.status_code == 200:
                print("✅ Template updated successfully")
                return True
            else:
                print(f"❌ Template update failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error updating template: {str(e)}")
            return False
    
    def test_enhanced_context(self) -> bool:
        """Test getting enhanced context"""
        print("\n🎯 Testing enhanced context generation...")
        
        if not self.connection_id:
            print("❌ No connection ID available")
            return False
        
        payload = {
            "connection_id": self.connection_id,
            "natural_language_question": "How much was disbursed today?",
            "domain_hint": "financial"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/context-templates/enhanced-context",
                json=payload
            )
            
            if response.status_code == 200:
                context = response.json()
                print("✅ Enhanced context generated successfully")
                print(f"   Schema Context Length: {len(context.get('schema_context', ''))}")
                print(f"   Business Rules Length: {len(context.get('business_rules', ''))}")
                print(f"   Query Intent: {context.get('query_intent', {})}")
                return True
            else:
                print(f"❌ Enhanced context generation failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error generating enhanced context: {str(e)}")
            return False
    
    def test_query_correction(self) -> bool:
        """Test logging a query correction"""
        print("\n📝 Testing query correction logging...")
        
        if not self.connection_id or not self.template_id:
            print("❌ Missing connection ID or template ID")
            return False
        
        payload = {
            "connection_id": self.connection_id,
            "template_id": self.template_id,
            "natural_language_question": "How much was disbursed today?",
            "generated_sql_original": "SELECT * FROM disbursements;",
            "user_feedback": "Query should sum amounts and filter by date",
            "correction_type": "missing_aggregation_and_filter",
            "corrected_sql": "SELECT SUM(amount) FROM disbursements WHERE date = CURRENT_DATE;",
            "additional_context": "Always use SUM for amount totals"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/context-templates/corrections",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Query correction logged: {result.get('correction_id')}")
                return True
            else:
                print(f"❌ Query correction logging failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error logging query correction: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all API tests"""
        print("="*60)
        print("🧪 CONTEXT TEMPLATE API TESTING")
        print("="*60)
        
        results = {}
        
        # Test server health
        results['server_health'] = self.test_server_health()
        if not results['server_health']:
            print("\n❌ Server is not running. Please start the server first:")
            print("   cd /Users/vaishakh/Code/supervisory-agent")
            print("   python -m uvicorn app.main:app --reload")
            return results
        
        # Run tests in sequence
        results['create_template'] = self.test_create_template()
        results['get_template'] = self.test_get_template()
        results['update_template'] = self.test_update_template()
        results['enhanced_context'] = self.test_enhanced_context()
        results['query_correction'] = self.test_query_correction()
        
        # Print summary
        print("\n" + "="*60)
        print("📊 TEST RESULTS SUMMARY")
        print("="*60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title():<25} {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Context Template API is working correctly.")
        else:
            print(f"⚠️ {total - passed} tests failed. Please check the errors above.")
        
        return results

def main():
    """Main entry point"""
    tester = ContextTemplateAPITester()
    results = tester.run_all_tests()
    
    if all(results.values()):
        print("\n🚀 API is ready for use!")
        print("\nNext steps:")
        print("1. Launch the Streamlit playground: python playground/launch_playground.py")
        print("2. Start Phoenix tracing for LLM observability")
        print("3. Test with real database connections")
    else:
        print("\n🔧 Please fix the failing tests before proceeding.")

if __name__ == "__main__":
    main()
