#!/usr/bin/env python3
"""
Update existing dashboard_template with enhanced context templates
"""

import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

import asyncio
import logging
from app.core.database import SessionLocal
from app.models.database.context_template_models import ConnectionContextTemplateModel
from app.services.context_template_service import context_template_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def update_dashboard_template():
    """Update the existing dashboard_template with enhanced context"""
    print("🔄 UPDATING DASHBOARD TEMPLATE")
    print("="*60)
    
    try:
        # Load the enhanced templates we created
        print("1. Loading enhanced templates...")
        business_rules = Path("templates/enhanced_business_rules_template.txt").read_text()
        schema_context = Path("templates/enhanced_schema_context_template.txt").read_text()
        domain_prompts = Path("templates/domain_specific_prompts_financial.txt").read_text()
        
        print(f"   ✅ Business Rules: {len(business_rules)} characters")
        print(f"   ✅ Schema Context: {len(schema_context)} characters")
        print(f"   ✅ Domain Prompts: {len(domain_prompts)} characters")
        
        # Find the dashboard_template
        print("2. Finding dashboard_template...")
        with SessionLocal() as session:
            template = session.query(ConnectionContextTemplateModel).filter(
                ConnectionContextTemplateModel.template_name == "dashboard_template"
            ).first()
            
            if not template:
                print("   ❌ dashboard_template not found!")
                return False
                
            print(f"   ✅ Found template ID: {template.id}")
            print(f"   📋 Connection ID: {template.connection_id}")
            print(f"   📊 Current business rules length: {len(template.business_rules_template or '')}")
            print(f"   📊 Current schema context length: {len(template.schema_context_template or '')}")
        
        # Update the template with enhanced content
        print("3. Updating template with enhanced content...")
        await context_template_service.update_template(
            template_id=str(template.id),
            updates={
                "business_rules_template": business_rules,
                "schema_context_template": schema_context,
                "domain_specific_prompts": domain_prompts,
                "template_name": "Enhanced Dashboard Template"
            },
            updated_by="system"
        )
        
        print("   ✅ Template updated successfully!")
        
        # Test the enhanced context
        print("4. Testing enhanced context generation...")
        context = await context_template_service.get_enhanced_context_for_query(
            connection_id=str(template.connection_id),
            natural_language_question="How much EMI was collected today?",
            domain_hint="financial"
        )
        
        if context:
            print("   ✅ Enhanced context generated successfully!")
            print(f"   📊 Context includes: {list(context.keys())}")
            
            # Show preview of business rules being used
            if 'business_rules' in context and context['business_rules']:
                rules_preview = context['business_rules'][:300] + "..." if len(context['business_rules']) > 300 else context['business_rules']
                print(f"   📋 Business Rules Preview:")
                print(f"      {rules_preview}")
                
            # Show preview of schema context
            if 'schema_context' in context and context['schema_context']:
                schema_preview = context['schema_context'][:300] + "..." if len(context['schema_context']) > 300 else context['schema_context']
                print(f"   🗄️  Schema Context Preview:")
                print(f"      {schema_preview}")
                
        else:
            print("   ❌ Failed to generate enhanced context")
            return False
            
        # Test with different questions
        print("5. Testing with different query types...")
        test_questions = [
            "How much was disbursed today?",
            "Which field officer has the highest collection percentage for this month?",
            "Show me overdue customers",
            "What's the total outstanding amount?"
        ]
        
        for question in test_questions:
            print(f"   🔍 Testing: '{question}'")
            context = await context_template_service.get_enhanced_context_for_query(
                connection_id=str(template.connection_id),
                natural_language_question=question,
                domain_hint="financial"
            )
            
            if context:
                # Check if context is being customized based on question
                intent = context.get('query_intent', {})
                print(f"      📊 Query Type: {intent.get('query_type', 'unknown')}")
                print(f"      🎯 Entities: {intent.get('entities', [])}")
                print(f"      📅 Time Context: {intent.get('time_context', 'unknown')}")
            else:
                print(f"      ❌ No context generated")
        
        print("\n🎉 SUCCESS! Dashboard template updated with enhanced context")
        print(f"📋 Connection ID to use: {template.connection_id}")
        
        return str(template.connection_id)
        
    except Exception as e:
        print(f"❌ Error updating template: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function"""
    print("🔥 ENHANCED CONTEXT TEMPLATE UPDATE")
    print("="*60)
    
    connection_id = await update_dashboard_template()
    
    if connection_id:
        print("\n📋 NEXT STEPS:")
        print("="*60)
        print(f"1. Use this connection ID in your queries: {connection_id}")
        print("2. Test in your playground or API:")
        print("   - 'How much EMI was collected today?'")
        print("   - 'Which field officer has the highest collection percentage?'")
        print("3. Check Phoenix tracing at http://localhost:6006")
        print("4. The system should now generate different, context-aware SQL for each question")
        print("\n🚀 The enhanced context template system is now active!")
    else:
        print("\n❌ Failed to update template. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())
