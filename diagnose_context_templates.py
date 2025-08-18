#!/usr/bin/env python3
"""
Diagnostic script to check context template system status
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

async def diagnose_context_templates():
    """Diagnose the current state of context templates"""
    print("🔍 CONTEXT TEMPLATE SYSTEM DIAGNOSIS")
    print("="*60)
    
    # Check database tables
    print("1. Checking database tables...")
    try:
        with SessionLocal() as session:
            # Check if context template tables exist and have data
            template_count = session.query(ConnectionContextTemplateModel).count()
            print(f"   📊 Total context templates in database: {template_count}")
            
            if template_count > 0:
                templates = session.query(ConnectionContextTemplateModel).all()
                for template in templates:
                    print(f"   📋 Template ID: {template.id}")
                    print(f"      Connection ID: {template.connection_id}")
                    print(f"      Template Name: {template.template_name}")
                    print(f"      Is Active: {template.is_active}")
                    print(f"      Created: {template.created_at}")
                    print(f"      Business Rules Length: {len(template.business_rules_template or '') if template.business_rules_template else 0}")
                    print(f"      Schema Context Length: {len(template.schema_context_template or '') if template.schema_context_template else 0}")
                    print()
            else:
                print("   ⚠️  No context templates found in database!")
                
    except Exception as e:
        print(f"   ❌ Error checking database: {str(e)}")
        return False
    
    # Check template files
    print("2. Checking template files...")
    templates_dir = Path("templates")
    if templates_dir.exists():
        template_files = list(templates_dir.glob("*.txt"))
        print(f"   📁 Template files found: {len(template_files)}")
        for file in template_files:
            print(f"      📄 {file.name}")
    else:
        print("   ⚠️  Templates directory not found!")
    
    # Check enhanced templates
    enhanced_files = [
        "templates/enhanced_business_rules_template.txt",
        "templates/enhanced_schema_context_template.txt", 
        "templates/domain_specific_prompts_financial.txt"
    ]
    
    print("3. Checking enhanced template files...")
    for file_path in enhanced_files:
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            print(f"   ✅ {Path(file_path).name} ({size} bytes)")
        else:
            print(f"   ❌ {Path(file_path).name} - NOT FOUND")
    
    # Test context template service
    print("4. Testing context template service...")
    try:
        # Try to get enhanced context for a test connection
        test_connection_id = "test-connection-123"
        context = await context_template_service.get_enhanced_context_for_query(
            connection_id=test_connection_id,
            natural_language_question="How much was collected today?",
            domain_hint="financial"
        )
        
        if context:
            print("   ✅ Context template service working")
            print(f"   📊 Context keys: {list(context.keys())}")
        else:
            print("   ⚠️  Context template service returned None")
            
    except Exception as e:
        print(f"   ❌ Error testing context service: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Check if we have any retrieval configurations
    print("5. Checking retrieval configurations...")
    try:
        from app.models.database.retrieval_models import RetrievalConfigurationModel
        with SessionLocal() as session:
            config_count = session.query(RetrievalConfigurationModel).count()
            print(f"   📊 Total retrieval configurations: {config_count}")
            
            if config_count > 0:
                configs = session.query(RetrievalConfigurationModel).all()
                for config in configs:
                    print(f"   🔗 Connection ID: {config.connection_id}")
                    print(f"      Database Type: {config.database_type}")
                    print(f"      Status: {config.status}")
                    print()
    except Exception as e:
        print(f"   ⚠️  Could not check retrieval configurations: {str(e)}")
    
    print("="*60)
    print("📋 DIAGNOSIS SUMMARY")
    print("="*60)
    
    return True

async def create_test_template():
    """Create a test context template using the enhanced templates"""
    print("\n🛠️  CREATING TEST CONTEXT TEMPLATE")
    print("="*60)
    
    try:
        # Load the enhanced templates we created
        business_rules = Path("templates/enhanced_business_rules_template.txt").read_text()
        schema_context = Path("templates/enhanced_schema_context_template.txt").read_text()
        domain_prompts = Path("templates/domain_specific_prompts_financial.txt").read_text()
        
        # Create a test template using create_default_template
        template_id = await context_template_service.create_default_template(
            connection_id="test-financial-connection",
            database_type="postgresql",
            domain_hint="financial"
        )
        
        # Now update it with our enhanced templates
        await context_template_service.update_template(
            template_id=template_id,
            updates={
                "business_rules_template": business_rules,
                "schema_context_template": schema_context,
                "domain_specific_prompts": domain_prompts,
                "template_name": "Enhanced Financial Template"
            },
            updated_by="system"
        )
        
        print(f"✅ Created test template with ID: {template_id}")
        
        # Test the enhanced context
        context = await context_template_service.get_enhanced_context_for_query(
            connection_id="test-financial-connection",
            natural_language_question="How much EMI was collected today?",
            domain_hint="financial"
        )
        
        if context:
            print("✅ Enhanced context generated successfully!")
            print(f"📊 Context includes: {list(context.keys())}")
            
            # Show a sample of the business rules
            if 'business_rules' in context:
                rules_preview = context['business_rules'][:200] + "..." if len(context['business_rules']) > 200 else context['business_rules']
                print(f"📋 Business Rules Preview: {rules_preview}")
                
        else:
            print("❌ Failed to generate enhanced context")
            
        return template_id
        
    except Exception as e:
        print(f"❌ Error creating test template: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Main diagnostic function"""
    print("🔥 CONTEXT TEMPLATE SYSTEM DIAGNOSTICS")
    print("="*60)
    
    # Run diagnosis
    await diagnose_context_templates()
    
    # Ask user if they want to create a test template
    print("\n🤔 Would you like to create a test context template?")
    print("This will use the enhanced templates we created earlier.")
    
    # For now, let's automatically create it to test
    template_id = await create_test_template()
    
    if template_id:
        print(f"\n🎉 SUCCESS! Test template created with ID: {template_id}")
        print("\n📋 Next Steps:")
        print("1. Use this connection ID in your playground: 'test-financial-connection'")
        print("2. Test queries like: 'How much EMI was collected today?'")
        print("3. Check Phoenix tracing at http://localhost:6006")
        print("4. The system should now use enhanced context instead of generic fallback")
    else:
        print("\n❌ Failed to create test template. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())
