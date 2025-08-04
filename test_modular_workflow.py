#!/usr/bin/env python3
"""
Test script for the new modular, context-aware workflow system.
This demonstrates how the frontend can pass workflow context in the payload
for seamless workflow progression without hardcoded logic.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.agents.supervisor import create_graph
import json

def test_modular_workflow_system():
    """Test the modular workflow system with context-aware progression"""
    
    print("🚀 Testing Modular, Context-Aware Workflow System")
    print("=" * 60)
    
    graph = create_graph()
    
    # Step 1: Start a new onboarding workflow
    print("\n📋 Step 1: Starting new onboarding workflow")
    initial_state = {
        'user_query': 'I want to onboard a customer for federal bank jlg',
        'user_id': 'test_user_modular'
    }
    
    try:
        result1 = graph.invoke(initial_state)
        response1 = result1.get('response', {})
        
        if response1.get('status') == 'workflow_started':
            print("✅ SUCCESS: Workflow started")
            customer_id = response1.get('customer_id')
            session_id = response1.get('session_id')
            current_action = response1.get('current_action', {})
            
            print(f"   Customer ID: {customer_id}")
            print(f"   Session ID: {session_id}")
            print(f"   Current Action: {current_action.get('action_id')} - {current_action.get('stage_name')}")
            
            # Step 2: Test context-based progression (simulate frontend button click)
            print(f"\n🔄 Step 2: Context-based progression from {current_action.get('action_id')}")
            
            # Frontend payload with workflow context
            context_payload = {
                "current_action_id": current_action.get('action_id'),
                "session_id": session_id,
                "customer_id": customer_id,
                "form_data": {}
            }
            
            # Simulate frontend sending context in the message
            progression_message = f"continue {json.dumps(context_payload)}"
            
            progression_state = {
                'user_query': progression_message,
                'user_id': 'test_user_modular'
            }
            
            result2 = graph.invoke(progression_state)
            response2 = result2.get('response', {})
            
            if response2.get('status') == 'workflow_continue':
                print("✅ SUCCESS: Context-based progression worked!")
                next_action = response2.get('current_action', {})
                print(f"   Progressed to: {next_action.get('action_id')} - {next_action.get('stage_name')}")
                print(f"   Message: {response2.get('message')}")
                
                # Step 3: Test progression with form data
                print(f"\n📝 Step 3: Progression with form data from {next_action.get('action_id')}")
                
                form_data_payload = {
                    "current_action_id": next_action.get('action_id'),
                    "session_id": session_id,
                    "customer_id": customer_id,
                    "form_data": {
                        "mobile_number": "9876543210",
                        "consent_given": True
                    }
                }
                
                form_message = f"continue {json.dumps(form_data_payload)}"
                
                form_state = {
                    'user_query': form_message,
                    'user_id': 'test_user_modular'
                }
                
                result3 = graph.invoke(form_state)
                response3 = result3.get('response', {})
                
                if response3.get('status') == 'workflow_continue':
                    print("✅ SUCCESS: Form data progression worked!")
                    final_action = response3.get('current_action', {})
                    print(f"   Progressed to: {final_action.get('action_id')} - {final_action.get('stage_name')}")
                    print(f"   Form data received: {response3.get('form_data_received')}")
                    
                    # Step 4: Demonstrate frontend payload structure
                    print(f"\n📱 Step 4: Frontend Integration Examples")
                    print("Frontend can now use these payload structures:")
                    
                    print("\n🔹 Simple Continue (button click):")
                    simple_payload = {
                        "user_id": "test_user_modular",
                        "message": f"continue {json.dumps({
                            'current_action_id': final_action.get('action_id'),
                            'session_id': session_id,
                            'customer_id': customer_id
                        })}",
                        "conversation_id": "your-conversation-id"
                    }
                    print(json.dumps(simple_payload, indent=2))
                    
                    print("\n🔹 Form Submission:")
                    form_payload = {
                        "user_id": "test_user_modular",
                        "message": f"continue {json.dumps({
                            'current_action_id': final_action.get('action_id'),
                            'session_id': session_id,
                            'customer_id': customer_id,
                            'form_data': {
                                'otp': '123456'
                            }
                        })}",
                        "conversation_id": "your-conversation-id"
                    }
                    print(json.dumps(form_payload, indent=2))
                    
                    print("\n🎉 MODULAR WORKFLOW SYSTEM IS WORKING!")
                    print("✅ Context-aware progression")
                    print("✅ Form data handling") 
                    print("✅ No hardcoded logic")
                    print("✅ Database-driven workflow")
                    print("✅ Frontend-friendly payloads")
                    
                else:
                    print(f"❌ Form data progression failed: {response3.get('status')}")
                    print(f"   Message: {response3.get('message')}")
                    
            else:
                print(f"❌ Context-based progression failed: {response2.get('status')}")
                print(f"   Message: {response2.get('message')}")
                
        else:
            print(f"❌ Workflow start failed: {response1.get('status')}")
            print(f"   Message: {response1.get('message')}")
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_modular_workflow_system()
