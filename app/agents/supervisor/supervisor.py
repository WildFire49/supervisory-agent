import json
from logging import Logger
from typing import TypedDict, List, NotRequired
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain, create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
import chromadb
from langgraph.graph import StateGraph, END

from app.core.config import settings
from app.core.database import (
    get_workflow_details, update_workflow_action_schema, ChatMessage,
    create_customer, get_customer_by_id, search_customers,
    create_workflow_session, get_active_workflow_session, update_workflow_session,
    get_workflow_sequence_preview, create_modified_workflow, get_workflow_modification_history,
    store_pending_workflow_modification, get_pending_workflow_modification, clear_pending_workflow_modification
)
from app.clients.external_services import ExternalServicesClient
from .mcp_client import MCPClient
from .prompts import SUPERVISOR_ROUTER_PROMPT, WORKFLOW_MODIFICATION_PROMPT
from ..configurator.configurator_graph import create_configurator_graph
from ..configurator.models import DatabaseConnection, DatabaseType
from ..configurator.database_persistence import configurator_db

# Define the state for our graph
class AgentState(TypedDict):
    user_id: str
    conversation_id: str
    user_query: str
    chat_history: NotRequired[list[ChatMessage]]
    bank_name: NotRequired[str]
    product_name: NotRequired[str]
    current_step_id: NotRequired[str]
    response: NotRequired[dict]
    route_decision: str
    mcp_tool_json: NotRequired[dict]
    question_for_dashboard: NotRequired[str]
    credit_metadata: NotRequired[dict]
    rule_data: NotRequired[dict]
    mcp_tool_name: NotRequired[str]
    mcp_tool_params: NotRequired[dict]

# Initialize components
llm = ChatOpenAI(model=settings.LLM_MODEL_NAME, temperature=0, api_key=settings.OPENAI_API_KEY)
mcp_client = MCPClient()
external_services_client = ExternalServicesClient()

# Fetch available MCP tools at startup
print("Fetching available MCP tools...")
mcp_tools_data = mcp_client.get_available_tools()
mcp_tools = mcp_tools_data.get('tools', [])
print(f"Available MCP tools: {[tool.get('name', 'unknown') for tool in mcp_tools]}")

# --- Graph Nodes ---

def router_node(state: AgentState):
    print("---INTENT ROUTER---")
    user_query = state.get('user_query', '')
    user_id = state.get('user_id')
    
    # Extract workflow context from the message if present
    # This allows frontend to pass current workflow state for context-aware progression
    import json
    import re
    
    workflow_context = {}
    
    # Try to extract JSON payload from the message for workflow context
    # Use a simple approach: find the first { and match to the corresponding }
    print(f"ROUTER: Starting JSON extraction from user_query: '{user_query}'")
    start_idx = user_query.find('{')
    print(f"ROUTER: Found opening brace at index: {start_idx}")
    if start_idx != -1:
        # Count braces to find the matching closing brace
        brace_count = 0
        end_idx = start_idx
        for i, char in enumerate(user_query[start_idx:], start_idx):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i
                    break
        
        if brace_count == 0:  # Found matching closing brace
            json_str = user_query[start_idx:end_idx + 1]
            print(f"Extracted JSON string: {json_str}")
            
            # Create a mock match object for compatibility
            class MockMatch:
                def __init__(self, text):
                    self._text = text
                def group(self):
                    return self._text
            
            json_match = MockMatch(json_str)
        else:
            json_match = None
    else:
        json_match = None
    
    if json_match:
        try:
            json_str = json_match.group()
            print(f"Processing JSON payload: {json_str}")
            context_json = json.loads(json_str)
            
            # Extract workflow context for regular workflow execution
            workflow_context = {
                'current_action_id': context_json.get('current_action_id'),
                'session_id': context_json.get('session_id'),
                'customer_id': context_json.get('customer_id'),
                'form_data': context_json.get('form_data', {})
            }
            print(f"Extracted workflow context: {workflow_context}")
            
            # Check for workflow modification action BEFORE cleaning the user query
            action = context_json.get('action')
            print(f"ROUTER DEBUG: Action extracted: '{action}'")
            
            # Route workflow modification requests directly (using the same parsed JSON)
            if action == 'modify_workflow':
                bank = context_json.get('bank', '')
                product = context_json.get('product', '')
                request = context_json.get('request', '')
                print(f"🔥 ROUTER: WORKFLOW MODIFICATION DETECTED! 🔥")
                print(f"📋 ROUTER: Full context_json = {context_json}")
                print(f"🏦 ROUTER: Extracted bank = '{bank}'")
                print(f"📦 ROUTER: Extracted product = '{product}'")
                print(f"📝 ROUTER: Extracted request = '{request}'")
                print(f"⚙️  ROUTER: Setting state values...")
                state['route_decision'] = 'workflow_modification'
                state['bank_name'] = bank
                state['product_name'] = product
                state['modification_request'] = request
                print(f"✅ ROUTER: State set - bank_name='{state.get('bank_name')}', product_name='{state.get('product_name')}', modification_request='{state.get('modification_request')}'")
                print(f"🔍 ROUTER: Final state keys before return: {list(state.keys())}")
                print(f"🔍 ROUTER: Final state content before return: {dict(state)}")
                print(f"🚀 ROUTER: Returning state to workflow_modification node")
                
                # Verify the modification_request is actually in the state
                if 'modification_request' not in state:
                    print(f"❌ ROUTER: CRITICAL ERROR - modification_request not in state!")
                    state['modification_request'] = request  # Force set it again
                    print(f"🔧 ROUTER: Force set modification_request = '{request}'")
                
                return state
            
            # Clean the user query by removing the JSON payload for regular processing
            user_query = user_query.replace(json_str, '').strip()
            state['user_query'] = user_query
            print(f"Cleaned user query: '{user_query}'")
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse workflow context JSON: {e}")
            print(f"Problematic JSON string: {json_str}")
    else:
        print("No JSON payload found in user query")
        print(f"User query was: {user_query}")
    
    # Store workflow context in state for workflow execution node
    state['workflow_context'] = workflow_context
    print(f"ROUTER: Stored workflow context in state: {workflow_context}")
    print(f"ROUTER: State keys after storing context: {list(state.keys())}")
    
    # Also check for confirmation/cancellation in plain text (without JSON)
    if user_query.lower().strip() in ['confirm', 'yes', 'apply']:
        print(f"ROUTER: Detected plain text confirmation, routing to workflow_modification")
        state['route_decision'] = 'workflow_modification'
        state['confirmation_action'] = 'confirm'
        return state
        
    elif user_query.lower().strip() in ['cancel', 'no', 'abort']:
        print(f"ROUTER: Detected plain text cancellation, routing to workflow_modification")
        state['route_decision'] = 'workflow_modification'
        state['confirmation_action'] = 'cancel'
        return state
    
    # Get chat history for context
    chat_history = state.get('chat_history', [])
    print(f"DEBUG: Raw chat history length: {len(chat_history)}")
    
    # Format history for the prompt
    formatted_history = ""
    for msg in chat_history[-5:]:  # Last 5 messages for context
        # Handle both ChatMessage objects and dictionary formats
        if hasattr(msg, 'sender_type'):
            # ChatMessage object
            role = msg.sender_type.value if hasattr(msg.sender_type, 'value') else str(msg.sender_type)
            content = msg.content
        else:
            # Dictionary format (fallback)
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
        formatted_history += f"{role}: {content}\n"
    
    print(f"DEBUG: Formatted history for prompt:\n{formatted_history}")
    print("--- END HISTORY ---")

    # Dynamically create the list of tools for the prompt
    base_tools = (
        "- `credit_analysis`: Use to analyze a customer's credit based on their metadata.\n"
        "- `rule_saver`: Use to update or add new credit rules.\n"
        "- `workflow_modification`: Modifies an existing workflow based on user instructions.\n"
        "- `workflow_execution`: Executes a predefined workflow step-by-step.\n"
        "- `dashboard_agent`: Use for any questions about statistics, reports, collections, disbursements, or performance of Field Officers or CECs.\n"
        "- `configurator`: Use to configure database connections and set up retrieval agents for RAG-based SQL query generation.\n"
        "- `general_qa`: Answers general questions using a knowledge base."
    )
    
    # Add MCP tools dynamically
    mcp_tool_descriptions = ""
    for tool in mcp_tools:
        tool_name = tool.get('name', 'unknown')
        tool_desc = tool.get('description', f'MCP tool: {tool_name}')
        mcp_tool_descriptions += f"- `{tool_name}`: {tool_desc}\n"
    
    tool_descriptions = base_tools
    if mcp_tool_descriptions:
        tool_descriptions += "\n" + mcp_tool_descriptions.rstrip()

    prompt = SUPERVISOR_ROUTER_PROMPT.format(
        user_query=state['user_query'],
        chat_history=formatted_history,
        tools=tool_descriptions
    )
    
    response = llm.invoke(prompt)
    print(f"--- LLM RAW RESPONSE ---\n{response.content}\n------------------------")
    
    try:
        # Clean the response to handle markdown code blocks
        cleaned_content = response.content.strip().replace("```json", "").replace("```", "").strip()
        parsed_output = json.loads(cleaned_content)

        # Decide the route
        route = parsed_output.get('route', 'general_qa')
        state['route_decision'] = route
        print(f"Routing decision: {route}")

        # Update state intelligently. Only overwrite an existing state value if the LLM
        # provides a new, non-null value. This prevents wiping context on subsequent turns.
        new_bank = parsed_output.get('bank')
        if new_bank and new_bank.lower() not in ['null', 'none']:
            state['bank_name'] = new_bank

        new_product = parsed_output.get('product')
        if new_product and new_product.lower() not in ['null', 'none']:
            state['product_name'] = new_product
        
        if route == 'mcp_tool_call':
            tool_params = parsed_output.get('tool_parameters', {})
            # Dynamically find the tool name based on the parameters provided by the LLM.
            # This is a simple heuristic: find the first tool that has all the parameters from the LLM.
            matched_tool_name = None
            for tool in mcp_tools:
                tool_props = tool.get('parameters', {}).get('properties', {})
                if tool_props and all(param in tool_props for param in tool_params.keys()):
                    matched_tool_name = tool['name']
                    break

            if matched_tool_name:
                state['mcp_tool_json'] = {
                    "tool_name": matched_tool_name,
                    "parameters": tool_params
                }
            else:
                # If we can't find a matching tool, it's an error state.
                # For now, we'll just pass the raw JSON and let the next node handle it.
                state['mcp_tool_json'] = parsed_output.get('mcp_tool_json', {})
        elif route == 'dashboard_agent':
            state['question_for_dashboard'] = parsed_output.get('question')
        elif route == 'credit_analysis':
            state['credit_metadata'] = parsed_output.get('credit_metadata')
        elif route == 'rule_saver':
            state['rule_data'] = parsed_output.get('rule_data')
        elif route == 'configurator':
            # Handle configurator routing - extract any configuration parameters
            state['configurator_action'] = parsed_output.get('action', 'setup')
            state['configurator_data'] = parsed_output.get('data', {})
        elif route in [tool.get('name') for tool in mcp_tools]:
            # This handles direct tool calls when the route itself is the tool name
            state['mcp_tool_name'] = route
            state['mcp_tool_params'] = parsed_output.get('tool_parameters', {})

    except json.JSONDecodeError:
        print("Error: LLM returned invalid JSON for routing. Defaulting to General QA.")
        state['route_decision'] = 'general_qa'
        
    return state

def workflow_execution_node(state: AgentState):
    print("---WORKFLOW EXECUTION---")
    user_query = state.get('user_query', '')
    
    # Import all necessary database functions at the top
    from app.core.database import (
        SessionLocal, WorkflowSession, get_workflow_details, 
        create_customer, create_workflow_session, generate_customer_id,
        update_workflow_session, get_active_workflow_session
    )
    
    # Extract workflow context from state (passed from frontend payload)
    print(f"EXECUTION: State keys received: {list(state.keys())}")
    workflow_context = state.get('workflow_context', {})
    print(f"EXECUTION: Raw workflow_context from state: {workflow_context}")
    
    # Fallback: Extract workflow context directly if not present in state
    if not workflow_context or not workflow_context.get('current_action_id'):
        print("EXECUTION: Workflow context missing, extracting from user_query directly")
        print(f"EXECUTION: user_query for JSON extraction: '{user_query}'")
        print(f"EXECUTION: user_query length: {len(user_query)}")
        import json
        
        # Use the same JSON extraction logic as the router
        start_idx = user_query.find('{')
        print(f"EXECUTION: Found opening brace at index: {start_idx}")
        if start_idx != -1:
            brace_count = 0
            end_idx = start_idx
            for i, char in enumerate(user_query[start_idx:], start_idx):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i
                        break
            
            if brace_count == 0:
                json_str = user_query[start_idx:end_idx + 1]
                print(f"EXECUTION: Extracted JSON string: {json_str}")
                try:
                    context_json = json.loads(json_str)
                    workflow_context = {
                        'current_action_id': context_json.get('current_action_id'),
                        'session_id': context_json.get('session_id'),
                        'customer_id': context_json.get('customer_id'),
                        'form_data': context_json.get('form_data', {})
                    }
                    print(f"EXECUTION: Extracted workflow context: {workflow_context}")
                    # Clean the user query
                    user_query = user_query.replace(json_str, '').strip()
                    print(f"EXECUTION: Cleaned user query: '{user_query}'")
                except json.JSONDecodeError as e:
                    print(f"EXECUTION: Failed to parse JSON: {e}")
    current_action_id = workflow_context.get('current_action_id')
    session_id = workflow_context.get('session_id')
    customer_id = workflow_context.get('customer_id')
    form_data = workflow_context.get('form_data', {})
    
    print(f"Workflow context final: {workflow_context}")
    
    # MODULAR WORKFLOW PROGRESSION SYSTEM
    # This system uses context from the payload to determine workflow progression
    # without hardcoded conditional logic - it's completely data-driven
    
    def get_workflow_progression(context, user_query, db_session):
        """Modular function to determine workflow progression based on context"""
        
        print(f"\n=== WORKFLOW PROGRESSION DEBUG ===")
        print(f"Context: {context}")
        print(f"User query: '{user_query}'")
        print(f"Context has current_action_id: {context.get('current_action_id') is not None}")
        print(f"Context has session_id: {context.get('session_id') is not None}")
        
        # If we have workflow context from frontend, use it for progression
        if context.get('current_action_id') and context.get('session_id'):
            print("Using context-based progression")
            return handle_context_based_progression(context, user_query, db_session)
        
        # Handle direct step requests (e.g., "mobile verification", "action_id:welcome")
        direct_step = extract_direct_step_request(user_query)
        print(f"Direct step extracted: {direct_step}")
        if direct_step:
            print(f"Using direct step request for: {direct_step}")
            return handle_direct_step_request(direct_step, db_session)
        
        # Handle new onboarding requests
        if is_onboarding_request(user_query):
            bank = state.get('bank_name') or state.get('bank')
            product = state.get('product_name') or state.get('product')
            return handle_new_onboarding(bank, product, db_session)
        
        # Handle continuation requests without context
        if is_continuation_request(user_query):
            return handle_continuation_without_context(user_query, db_session)
        
        return None
    
    def handle_context_based_progression(context, user_query, db_session):
        """Handle workflow progression when we have frontend context"""
        session_id = context['session_id']
        current_action_id = context['current_action_id']
        form_data = context.get('form_data', {})
        
        print(f"Context-based progression: {current_action_id} -> next")
        print(f"Looking for session: {session_id}")
        
        # Convert session_id to UUID if it's a string
        from uuid import UUID
        try:
            if isinstance(session_id, str):
                session_uuid = UUID(session_id)
            else:
                session_uuid = session_id
        except ValueError:
            return {'error': f'Invalid session ID format: {session_id}'}
        
        # Get the workflow session from database
        session = db_session.query(WorkflowSession).filter(
            WorkflowSession.id == session_uuid
        ).first()
        
        if not session:
            print(f"Session not found in database: {session_uuid}")
            # Try to find any active session for this customer as fallback
            customer_id = context.get('customer_id')
            if customer_id:
                session = db_session.query(WorkflowSession).filter(
                    WorkflowSession.customer_id == customer_id,
                    WorkflowSession.status == 'active'
                ).order_by(WorkflowSession.started_at.desc()).first()
                
            if not session:
                return {'error': f'Session {session_id} not found and no active session for customer'}
        
        # Get workflow details for this session
        bank_name_mapping = {
            "federal bank": "federal", "federalbank": "federal", 
            "dhanlaxmi bank": "dhanlaxmi", "dhanlaxmibank": "dhanlaxmi"
        }
        
        db_bank_name = bank_name_mapping.get(session.bank_name.lower(), 
                                            bank_name_mapping.get(session.bank_name.lower().replace(" ", ""), 
                                                                 session.bank_name.lower()))
        
        workflow_details = get_workflow_details(db_bank_name, session.product_type)
        if not workflow_details:
            print(f"No workflow found for bank='{db_bank_name}', product='{session.product_type}'")
            print(f"Session details: bank_name='{session.bank_name}', product_type='{session.product_type}'")
            return {'error': f'Workflow configuration not found for bank={db_bank_name}, product={session.product_type}'}
        
        action_schema = workflow_details.get('action_schema', [])
        ui_schema = workflow_details.get('ui_schema', {})
        
        # Debug: Print workflow details
        print(f"Looking for action '{current_action_id}' in workflow for bank='{db_bank_name}', product='{session.product_type}'")
        print(f"Workflow details found: {workflow_details is not None}")
        print(f"Action schema length: {len(action_schema)}")
        print(f"Available actions: {[a['id'] for a in action_schema]}")
        
        # Find current action in schema
        current_action = next((a for a in action_schema if a['id'] == current_action_id), None)
        if not current_action:
            return {'error': f'Action {current_action_id} not found in workflow schema. Available actions: {[a["id"] for a in action_schema]}. Bank: {db_bank_name}, Product: {session.product_type}'}
        
        # Determine next action based on current action's configuration
        next_action_id = current_action.get('next_success_action_id')
        if not next_action_id:
            return {
                'status': 'workflow_complete',
                'message': 'Workflow completed successfully!',
                'customer_id': session.customer_id,
                'session_id': str(session.id),
                'form_data_received': form_data
            }
        
        # Find next action in schema
        next_action = next((a for a in action_schema if a['id'] == next_action_id), None)
        if not next_action:
            return {'error': f'Next action {next_action_id} not found in workflow schema'}
        
        # Update session to next action
        update_workflow_session(str(session.id), current_action_id=next_action_id)
        
        # Get UI for next action
        next_ui = ui_schema.get(next_action_id, {})
        
        return {
            'status': 'workflow_continue',
            'customer_id': session.customer_id,
            'session_id': str(session.id),
            'message': f'Progressed from {current_action["stage_name"]} to {next_action["stage_name"]}',
            'success': True,
            'current_action': {
                'action_id': next_action['id'],
                'stage_name': next_action['stage_name'],
                'action_type': next_action['action_type'],
                'priority': next_action['priority'],
                'is_mandatory': next_action['is_mandatory'],
                'flow_type': next_action['flow_type'],
                'description': next_action.get('desc_for_llm', '')
            },
            'ui_schema': {
                'id': next_ui.get('id', f'ui_{next_action_id}_001'),
                'session_id': str(session.id),
                'screen_id': next_ui.get('screen_id', f'{next_action_id}_screen'),
                'ui_components': next_ui.get('ui_components', [])
            },
            'navigation': {
                'next_success_action_id': next_action.get('next_success_action_id'),
                'next_err_action_id': next_action.get('next_err_action_id'),
                'can_skip': next_action.get('can_skip', False)
            },
            'session_data': {
                'session_id': str(session.id),
                'customer_id': session.customer_id,
                'flow_type': next_action['flow_type'],
                'current_step': next_action['priority'],
                'total_steps': len(action_schema),
                'bank_name': session.bank_name,
                'product_type': session.product_type
            },
            'form_data_received': form_data
        }
        
        # Find next action
        next_action = next((a for a in action_schema if a['id'] == next_action_id), None)
        if not next_action:
            return {'error': f'Next action {next_action_id} not found in workflow schema'}
        
        # Update session with form data and next action
        session_data_update = {}
        if form_data:
            current_session_data = session.session_data or {}
            current_session_data.update(form_data)
            session_data_update['session_data'] = current_session_data
            print(f"Storing form data: {form_data}")
        
        # Update session to next action
        update_workflow_session(
            str(session.id), 
            current_action_id=next_action_id,
            **session_data_update
        )
        
        # Get UI for next action
        next_ui = ui_schema.get(next_action_id, {})
        
        return {
            'status': 'workflow_continue',
            'customer_id': session.customer_id,
            'session_id': str(session.id),
            'message': f'Progressed from {current_action["stage_name"]} to {next_action["stage_name"]}',
            'success': True,
            'current_action': {
                'action_id': next_action['id'],
                'stage_name': next_action['stage_name'],
                'action_type': next_action['action_type'],
                'priority': next_action['priority'],
                'is_mandatory': next_action['is_mandatory'],
                'flow_type': next_action['flow_type'],
                'description': next_action.get('desc_for_llm', '')
            },
            'ui_schema': {
                'id': next_ui.get('id', f'ui_{next_action_id}_001'),
                'session_id': str(session.id),
                'screen_id': next_ui.get('screen_id', f'{next_action_id}_screen'),
                'ui_components': next_ui.get('ui_components', [])
            },
            'navigation': {
                'next_success_action_id': next_action.get('next_success_action_id'),
                'next_err_action_id': next_action.get('next_err_action_id'),
                'can_skip': next_action.get('can_skip', False)
            },
            'session_data': {
                'session_id': str(session.id),
                'customer_id': session.customer_id,
                'flow_type': next_action['flow_type'],
                'current_step': next_action['priority'],
                'total_steps': len(action_schema),
                'bank_name': session.bank_name,
                'product_type': session.product_type
            },
            'form_data_received': form_data if form_data else None
        }
    
    # Helper functions for different request types
    def extract_direct_step_request(query):
        """Extract direct step request from user query"""
        workflow_step_keywords = {
            'mobile verification': 'mobile-verification',
            'video consent': 'video-consent',
            'flow selection': 'flow-selection',
            'welcome': 'welcome',
            'otp verification': 'otp-verification'
        }
        
        if 'action_id:' in query.lower():
            return query.lower().split('action_id:')[1].strip()
        
        for keyword, step_id in workflow_step_keywords.items():
            if keyword in query.lower():
                return step_id
        return None
    
    def is_onboarding_request(query):
        """Check if query is a new onboarding request"""
        onboarding_keywords = ['onboard', 'customer', 'new customer', 'start onboarding']
        return any(keyword in query.lower() for keyword in onboarding_keywords)
    
    def is_continuation_request(query):
        """Check if query is a continuation request"""
        continuation_keywords = ['what next', 'next', 'continue', 'proceed']
        return any(keyword in query.lower() for keyword in continuation_keywords)
    
    def handle_direct_step_request(step_id, db_session):
        """Handle direct workflow step requests"""
        # Get the most recent active workflow session
        recent_session = db_session.query(WorkflowSession).filter(
            WorkflowSession.status == 'active'
        ).order_by(WorkflowSession.started_at.desc()).first()
        
        if not recent_session:
            # Create a new session for Federal Bank JLG (default)
            customer = create_customer('New Customer', 'federal', product_type='jlg')
            
            recent_session = create_workflow_session(
                customer_id=customer.id,
                bank_name='federal bank',
                product_type='jlg',
                flow_type='onboarding',
                current_action_id=step_id
            )
        else:
            # Update existing session to the requested step
            update_workflow_session(str(recent_session.id), current_action_id=step_id)
        
        # Get workflow details and return UI for the requested step
        bank_name_mapping = {
            "federal bank": "federal", "federalbank": "federal", 
            "dhanlaxmi bank": "dhanlaxmi", "dhanlaxmibank": "dhanlaxmi"
        }
        
        db_bank_name = bank_name_mapping.get(recent_session.bank_name.lower(), 'federal')
        workflow_details = get_workflow_details(db_bank_name, recent_session.product_type)
        
        if not workflow_details:
            return {'error': 'Workflow configuration not found'}
        
        action_schema = workflow_details.get('action_schema', [])
        ui_schema = workflow_details.get('ui_schema', {})
        
        requested_action = next((a for a in action_schema if a['id'] == step_id), None)
        if not requested_action:
            return {'error': f'Step {step_id} not found in workflow'}
        
        step_ui = ui_schema.get(step_id, {})
        
        return {
            'status': 'workflow_step_loaded',
            'customer_id': recent_session.customer_id,
            'session_id': str(recent_session.id),
            'message': f'Loaded {requested_action["stage_name"]} step',
            'success': True,
            'current_action': {
                'action_id': requested_action['id'],
                'stage_name': requested_action['stage_name'],
                'action_type': requested_action['action_type'],
                'priority': requested_action['priority'],
                'is_mandatory': requested_action['is_mandatory'],
                'flow_type': requested_action['flow_type'],
                'description': requested_action.get('desc_for_llm', '')
            },
            'ui_schema': {
                'id': step_ui.get('id', f'ui_{step_id}_001'),
                'session_id': str(recent_session.id),
                'screen_id': step_ui.get('screen_id', f'{step_id}_screen'),
                'ui_components': step_ui.get('ui_components', [])
            },
            'navigation': {
                'next_success_action_id': requested_action.get('next_success_action_id'),
                'next_err_action_id': requested_action.get('next_err_action_id'),
                'can_skip': requested_action.get('can_skip', False)
            },
            'session_data': {
                'session_id': str(recent_session.id),
                'customer_id': recent_session.customer_id,
                'flow_type': requested_action['flow_type'],
                'current_step': requested_action['priority'],
                'total_steps': len(action_schema),
                'bank_name': recent_session.bank_name,
                'product_type': recent_session.product_type
            }
        }
    
    def handle_new_onboarding(bank, product, db_session):
        """Handle new customer onboarding requests"""
        if not bank or not product:
            return {
                'status': 'info_needed',
                'message': 'Please specify the bank and product for onboarding (e.g., "federal bank jlg")',
                'required_info': ['bank_name', 'product_type']
            }
        
        # Normalize bank and product names
        bank_name_mapping = {
            "federal bank": "federal", "federalbank": "federal", 
            "dhanlaxmi bank": "dhanlaxmi", "dhanlaxmibank": "dhanlaxmi"
        }
        
        normalized_bank = bank_name_mapping.get(bank.lower(), bank.lower())
        normalized_product = product.lower()
        
        # Create customer (customer ID is generated internally)
        customer = create_customer('New Customer', normalized_bank, product_type=normalized_product)
        
        # Get workflow details first to determine the starting action
        workflow_details = get_workflow_details(normalized_bank, normalized_product)
        if not workflow_details:
            return {'error': f'Workflow not found for {bank} {product}'}
        
        action_schema = workflow_details.get('action_schema', [])
        ui_schema = workflow_details.get('ui_schema', {})
        
        # Find the first action (lowest priority) as the starting point
        if not action_schema:
            return {'error': 'No actions found in workflow schema'}
        
        # Sort by priority to get the first step
        sorted_actions = sorted(action_schema, key=lambda x: x.get('priority', 999))
        first_action = sorted_actions[0]
        starting_action_id = first_action['id']
        
        print(f"Starting KCC workflow with action: {starting_action_id}")
        
        # Create workflow session with the correct starting action
        session = create_workflow_session(
            customer_id=customer.id,
            bank_name=bank,
            product_type=normalized_product,
            flow_type='onboarding',
            current_action_id=starting_action_id
        )
        
        # Get UI for the starting action
        starting_ui = ui_schema.get(starting_action_id, {})
        
        return {
            'status': 'workflow_started',
            'customer_id': customer.id,
            'session_id': str(session.id),
            'message': f'Started {normalized_product.upper()} workflow for new customer {customer.id}',
            'success': True,
            'current_action': {
                'action_id': first_action['id'],
                'stage_name': first_action['stage_name'],
                'action_type': first_action['action_type'],
                'priority': first_action['priority'],
                'is_mandatory': first_action['is_mandatory'],
                'flow_type': first_action['flow_type'],
                'description': first_action.get('desc_for_llm', '')
            },
            'ui_schema': {
                'id': starting_ui.get('id', f'ui_{starting_action_id}_001'),
                'session_id': str(session.id),
                'screen_id': starting_ui.get('screen_id', f'{starting_action_id}_screen'),
                'ui_components': starting_ui.get('ui_components', [])
            },
            'navigation': {
                'next_success_action_id': first_action.get('next_success_action_id'),
                'next_err_action_id': first_action.get('next_err_action_id'),
                'can_skip': first_action.get('can_skip', False)
            },
            'session_data': {
                'session_id': str(session.id),
                'customer_id': customer.id,
                'flow_type': first_action['flow_type'],
                'current_step': first_action['priority'],
                'total_steps': len(action_schema),
                'bank_name': bank,
                'product_type': normalized_product
            }
        }
    
    def handle_continuation_without_context(user_query, db_session):
        """Handle continuation requests when no workflow context is provided"""
        recent_session = db_session.query(WorkflowSession).filter(
            WorkflowSession.status == 'active'
        ).order_by(WorkflowSession.started_at.desc()).first()
        
        if not recent_session:
            return {
                'status': 'no_active_session',
                'message': 'No active workflow session found. Please start a new onboarding workflow.',
                'suggestion': 'Try: "I want to onboard a customer for federal bank jlg"'
            }
        
        # Use the existing session context to continue
        context = {
            'current_action_id': recent_session.current_action_id,
            'session_id': str(recent_session.id),
            'customer_id': recent_session.customer_id,
            'form_data': {}
        }
        
        return handle_context_based_progression(context, user_query, db_session)
    
    # Execute the modular workflow progression
    db = SessionLocal()
    try:
        result = get_workflow_progression(workflow_context, user_query, db)
        if result:
            state['response'] = result
            return state
    finally:
        db.close()
    
    # Define bank name mapping for database lookup (used throughout the function)
    bank_name_mapping = {
        "federal bank": "federal",
        "federalbank": "federal", 
        "dhanlaxmi bank": "dhanlaxmi",
        "dhanlaxmibank": "dhanlaxmi"
    }
    
    # Check if user wants to onboard a customer
    # Also check if we have bank and product info from router (indicates onboarding context)
    has_onboarding_keywords = any(keyword in user_query.lower() for keyword in ['onboard', 'customer', 'new customer', 'start onboarding'])
    has_bank_product_info = bool(state.get('bank') or state.get('bank_name')) and bool(state.get('product') or state.get('product_name'))
    
    if has_onboarding_keywords or has_bank_product_info:
        # Get bank and product from router state
        bank = state.get('bank_name') or state.get('bank')  # Handle both key formats
        product = state.get('product_name') or state.get('product')  # Handle both key formats
        
        # Get the correct bank name for database lookup
        db_bank_name = None
        if bank:
            bank_key = bank.lower().replace(" ", "")
            db_bank_name = bank_name_mapping.get(bank.lower(), bank_name_mapping.get(bank_key, bank_key))
        
        if not bank:
            state['response'] = {
                "status": "info_needed",
                "message": "Which bank would you like to onboard the customer for?",
                "options": ["Federal Bank", "Dhanlaxmi Bank"],
                "next_step": "bank_selection"
            }
            return state
            
        if not product:
            state['response'] = {
                "status": "info_needed", 
                "message": "Which product would you like to onboard the customer for?",
                "options": ["Personal Loan", "Credit Card", "Home Loan"],
                "next_step": "product_selection"
            }
            return state
        
        # Check if this is for an existing customer
        if 'existing' in user_query or 'customer id' in user_query:
            state['response'] = {
                "status": "info_needed",
                "message": "Please provide the Customer ID and Customer Name for the existing customer.",
                "fields": [
                    {"name": "customer_id", "type": "text", "placeholder": "e.g., CI-SH-FED-2a7c963330c9"},
                    {"name": "customer_name", "type": "text", "placeholder": "Customer Name"}
                ],
                "next_step": "existing_customer_verification"
            }
            return state
        
        # For new customer onboarding, create customer and start workflow
        try:
            # Generate new customer ID and create customer record
            # Process bank name for proper prefix mapping
            processed_bank_name = bank.lower().replace(" ", "")
            customer = create_customer(
                name="New Customer",  # Will be updated during onboarding
                bank_name=processed_bank_name,
                product_type=product.lower().replace(" ", "_")
            )
            
            # Create workflow session
            session = create_workflow_session(
                customer_id=customer.id,
                bank_name=bank.lower().replace(" ", ""),
                product_type=product.lower().replace(" ", "_"),
                flow_type="onboarding",
                current_action_id="welcome"
            )
            
            # Get workflow schema from database
            workflow_details = get_workflow_details(db_bank_name, product.lower().replace(" ", "_"))
            
            # Generate session data
            session_data = {
                "session_id": str(session.id),
                "customer_id": customer.id,
                "bank_name": bank,
                "product_type": product,
                "flow_type": "onboarding"
            }
            
            # Generate workflow response using database-stored schemas
            if not workflow_details:
                # If no workflow found in DB, create a default response
                print(f"No workflow found for {db_bank_name} {product}, using default")
                workflow_response = {
                    "success": True,
                    "current_action": {"action_id": "welcome", "stage_name": "Welcome Screen"},
                    "ui_schema": {"screen_id": "default_screen", "ui_components": []},
                    "session_data": session_data
                }
            else:
                # Use database workflow with complete UI schema
                print(f"Using database workflow for {db_bank_name} {product}")
                
                # Get action details from database schema
                action_schema = workflow_details.get('action_schema', [])
                ui_schema = workflow_details.get('ui_schema', {})
                
                # Find welcome action in schema
                current_action = next((item for item in action_schema if item["id"] == "welcome"), None)
                
                if current_action:
                    # Get UI components for welcome action from database
                    ui_components = ui_schema.get("welcome", {})
                    
                    # Build response with database data
                    workflow_response = {
                        "success": True,
                        "current_action": {
                            "action_id": current_action["id"],
                            "stage_name": current_action["stage_name"],
                            "action_type": current_action["action_type"],
                            "priority": current_action["priority"],
                            "is_mandatory": current_action["is_mandatory"],
                            "flow_type": current_action["flow_type"],
                            "description": current_action.get("desc_for_llm", "")
                        },
                        "ui_schema": {
                            "id": ui_components.get("id", "ui_welcome_001"),
                            "session_id": session_data.get("session_id"),
                            "screen_id": ui_components.get("screen_id", "welcome_screen"),
                            "ui_components": ui_components.get("ui_components", [])
                        },
                        "navigation": {
                            "next_success_action_id": current_action.get("next_success_action_id"),
                            "next_err_action_id": current_action.get("next_err_action_id"),
                            "can_skip": current_action.get("can_skip", False)
                        },
                        "session_data": {
                            "session_id": session_data.get("session_id"),
                            "customer_id": session_data.get("customer_id"),
                            "flow_type": current_action["flow_type"],
                            "current_step": current_action["priority"],
                            "total_steps": len(action_schema),
                            **session_data
                        }
                    }
                else:
                    # Fallback if welcome action not found
                    workflow_response = {
                        "success": True,
                        "current_action": {"action_id": "welcome", "stage_name": "Welcome Screen"},
                        "ui_schema": {"screen_id": "default_screen", "ui_components": []},
                        "session_data": session_data
                    }
            
            state['response'] = {
                "status": "workflow_started",
                "customer_id": customer.id,
                "session_id": str(session.id),
                "message": f"Started onboarding workflow for new customer {customer.id}",
                **workflow_response
            }
            
        except Exception as e:
            print(f"Error creating customer/session: {e}")
            state['response'] = {
                "status": "error",
                "message": f"Failed to start onboarding workflow: {str(e)}"
            }
            
        return state
    
    # Handle direct workflow step requests (e.g., "I need to do mobile verification" or "action_id:mobile-verification")
    workflow_step_keywords = {
        'mobile verification': 'mobile-verification',
        'mobile verify': 'mobile-verification', 
        'verify mobile': 'mobile-verification',
        'video consent': 'video-consent',
        'consent': 'video-consent',
        'flow selection': 'flow-selection',
        'select flow': 'flow-selection',
        'welcome': 'welcome',
        'otp verification': 'otp-verification',
        'verify otp': 'otp-verification'
    }
    
    # Check for direct step requests
    requested_step = None
    
    # First check for action_id format (e.g., "action_id:mobile-verification")
    if 'action_id:' in user_query.lower():
        action_id_part = user_query.lower().split('action_id:')[1].strip()
        requested_step = action_id_part
        print(f"Direct action_id request: {requested_step}")
    else:
        # Check for keyword-based requests
        for keyword, step_id in workflow_step_keywords.items():
            if keyword in user_query.lower():
                requested_step = step_id
                break
    
    if requested_step:
        print(f"Direct workflow step requested: {requested_step}")
        
        # Find or create a workflow session for this step
        from app.core.database import SessionLocal, WorkflowSession, get_workflow_details
        db = SessionLocal()
        try:
            # Look for existing active session first
            recent_session = db.query(WorkflowSession).filter(
                WorkflowSession.status == 'active'
            ).order_by(WorkflowSession.started_at.desc()).first()
            
            if not recent_session:
                # Create a new session for Federal Bank JLG (default)
                customer_id = generate_customer_id('federal')
                customer = create_customer(customer_id, 'New Customer', bank_name='federal', product_type='jlg')
                
                session = create_workflow_session(
                    customer_id=customer_id,
                    bank_name='federalbank',
                    product_type='jlg',
                    current_action_id=requested_step,
                    flow_type='onboarding'
                )
                recent_session = session
                print(f"Created new session for step {requested_step}")
            else:
                # Update existing session to requested step
                from app.core.database import update_workflow_session
                update_workflow_session(str(recent_session.id), current_action_id=requested_step)
                recent_session.current_action_id = requested_step
                print(f"Updated existing session to step {requested_step}")
            
            # Get workflow details and return UI for requested step
            bank_name_mapping = {
                "federal bank": "federal",
                "federalbank": "federal", 
                "dhanlaxmi bank": "dhanlaxmi",
                "dhanlaxmibank": "dhanlaxmi"
            }
            
            db_bank_name = bank_name_mapping.get(recent_session.bank_name.lower(), 
                                                bank_name_mapping.get(recent_session.bank_name.lower().replace(" ", ""), 
                                                                     recent_session.bank_name.lower()))
            
            workflow_details = get_workflow_details(db_bank_name, recent_session.product_type)
            
            if workflow_details:
                action_schema = workflow_details.get('action_schema', [])
                ui_schema = workflow_details.get('ui_schema', {})
                
                # Find the requested action
                requested_action = next((item for item in action_schema if item["id"] == requested_step), None)
                
                if requested_action:
                    # Get UI components for the requested step
                    step_ui = ui_schema.get(requested_step, {})
                    
                    workflow_response = {
                        "success": True,
                        "current_action": {
                            "action_id": requested_action["id"],
                            "stage_name": requested_action["stage_name"],
                            "action_type": requested_action["action_type"],
                            "priority": requested_action["priority"],
                            "is_mandatory": requested_action["is_mandatory"],
                            "flow_type": requested_action["flow_type"],
                            "description": requested_action.get("desc_for_llm", "")
                        },
                        "ui_schema": {
                            "id": step_ui.get("id", f"ui_{requested_step}_001"),
                            "session_id": str(recent_session.id),
                            "screen_id": step_ui.get("screen_id", f"{requested_step}_screen"),
                            "ui_components": step_ui.get("ui_components", [])
                        },
                        "navigation": {
                            "next_success_action_id": requested_action.get("next_success_action_id"),
                            "next_err_action_id": requested_action.get("next_err_action_id"),
                            "can_skip": requested_action.get("can_skip", False)
                        },
                        "session_data": {
                            "session_id": str(recent_session.id),
                            "customer_id": recent_session.customer_id,
                            "flow_type": requested_action["flow_type"],
                            "current_step": requested_action["priority"],
                            "total_steps": len(action_schema),
                            "bank_name": recent_session.bank_name,
                            "product_type": recent_session.product_type
                        }
                    }
                    
                    state['response'] = {
                        "status": "workflow_step_loaded",
                        "customer_id": recent_session.customer_id,
                        "session_id": str(recent_session.id),
                        "message": f"Loaded {requested_action['stage_name']} step",
                        **workflow_response
                    }
                    return state
                else:
                    state['response'] = {
                        "status": "error",
                        "message": f"Workflow step '{requested_step}' not found in schema"
                    }
                    return state
            else:
                state['response'] = {
                    "status": "error",
                    "message": "Workflow configuration not found"
                }
                return state
                
        finally:
            db.close()
    
    # Handle form data submission with workflow progression
    # Check if this is a form submission with data (e.g., "continue with mobile number 9876543210")
    form_data = {}
    if 'continue with' in user_query.lower():
        # Extract form data from the message
        query_parts = user_query.lower().split('continue with')
        if len(query_parts) > 1:
            data_part = query_parts[1].strip()
            
            # Parse different types of form data
            if 'mobile number' in data_part:
                mobile_match = data_part.replace('mobile number', '').strip()
                form_data['mobile_number'] = mobile_match
            elif 'otp' in data_part:
                otp_match = data_part.replace('otp', '').strip()
                form_data['otp'] = otp_match
            elif 'name' in data_part:
                name_match = data_part.replace('name', '').strip()
                form_data['customer_name'] = name_match
    
    # Handle workflow continuation ("what next", button clicks, form submissions, etc.)
    # Check if this is a workflow continuation request
    is_continuation = any(keyword in user_query.lower() for keyword in ['what next', 'next', 'continue', 'proceed'])
    has_form_data = bool(form_data)
    
    if is_continuation or has_form_data:
        # Look for existing workflow session from conversation history or state
        # Try to extract customer info from conversation context
        conversation_id = state.get('conversation_id')
        
        # Get the most recent workflow session for this user
        # This is a simplified approach - in production you'd want more robust session management
        db = SessionLocal()
        try:
            # Find the most recent active workflow session
            recent_session = db.query(WorkflowSession).filter(
                WorkflowSession.status == 'active'
            ).order_by(WorkflowSession.started_at.desc()).first()
            
            if recent_session:
                print(f"Found recent workflow session: {recent_session.id}")
                
                # Get workflow details from database
                # Apply bank name mapping to ensure consistency
                bank_name_mapping = {
                    "federal bank": "federal",
                    "federalbank": "federal", 
                    "dhanlaxmi bank": "dhanlaxmi",
                    "dhanlaxmibank": "dhanlaxmi"
                }
                
                # Normalize bank name for database lookup
                db_bank_name = bank_name_mapping.get(recent_session.bank_name.lower(), 
                                                    bank_name_mapping.get(recent_session.bank_name.lower().replace(" ", ""), 
                                                                         recent_session.bank_name.lower()))
                
                workflow_details = get_workflow_details(db_bank_name, recent_session.product_type)
                
                if workflow_details:
                    action_schema = workflow_details.get('action_schema', [])
                    ui_schema = workflow_details.get('ui_schema', {})
                    
                    # Find current action
                    current_action = next((item for item in action_schema if item["id"] == recent_session.current_action_id), None)
                    
                    if current_action and current_action.get('next_success_action_id'):
                        # Move to next action
                        next_action_id = current_action['next_success_action_id']
                        next_action = next((item for item in action_schema if item["id"] == next_action_id), None)
                        
                        if next_action:
                            # Update session to next action and store form data if present
                            # Prepare session data update
                            session_data_update = {}
                            if has_form_data:
                                # Store form data in session
                                current_session_data = recent_session.session_data or {}
                                current_session_data.update(form_data)
                                session_data_update['session_data'] = current_session_data
                                print(f"Storing form data: {form_data}")
                            
                            # Update session with next action and form data
                            update_workflow_session(
                                str(recent_session.id), 
                                current_action_id=next_action_id,
                                **session_data_update
                            )
                            
                            # Get UI components for next action
                            ui_components = ui_schema.get(next_action_id, {})
                            
                            # Build response for next step
                            # Prepare standardized workflow response
                            workflow_response = {
                                "success": True,
                                "current_action": {
                                    "action_id": next_action["id"],
                                    "stage_name": next_action["stage_name"],
                                    "action_type": next_action["action_type"],
                                    "priority": next_action["priority"],
                                    "is_mandatory": next_action["is_mandatory"],
                                    "flow_type": next_action["flow_type"],
                                    "description": next_action.get("desc_for_llm", "")
                                },
                                "ui_schema": {
                                    "id": ui_components.get("id", f"ui_{next_action_id}_001"),
                                    "session_id": str(recent_session.id),
                                    "screen_id": ui_components.get("screen_id", f"{next_action_id}_screen"),
                                    "ui_components": ui_components.get("ui_components", [])
                                },
                                "navigation": {
                                    "next_success_action_id": next_action.get("next_success_action_id"),
                                    "next_err_action_id": next_action.get("next_err_action_id"),
                                    "can_skip": next_action.get("can_skip", False)
                                },
                                "session_data": {
                                    "session_id": str(recent_session.id),
                                    "customer_id": recent_session.customer_id,
                                    "flow_type": next_action["flow_type"],
                                    "current_step": next_action["priority"],
                                    "total_steps": len(action_schema),
                                    "bank_name": recent_session.bank_name,
                                    "product_type": recent_session.product_type
                                },
                                "form_data_received": form_data if has_form_data else None,
                                "frontend_guidance": {
                                    "payload_structure": {
                                        "simple_continue": {
                                            "user_id": "your_user_id",
                                            "message": "continue",
                                            "conversation_id": "your_conversation_id"
                                        },
                                        "with_form_data": {
                                            "user_id": "your_user_id",
                                            "message": f"continue with {list(form_data.keys())[0] if form_data else 'field_name'} field_value",
                                            "conversation_id": "your_conversation_id"
                                        },
                                        "direct_action": {
                                            "user_id": "your_user_id",
                                            "message": f"action_id:{next_action['id']}",
                                            "conversation_id": "your_conversation_id"
                                        }
                                    }
                                }
                            }
                            
                            state['response'] = {
                                "status": "workflow_continue",
                                "customer_id": recent_session.customer_id,
                                "session_id": str(recent_session.id),
                                "message": f"Proceeding to {next_action['stage_name']}",
                                **workflow_response
                            }
                            return state
                        else:
                            state['response'] = {
                                "status": "workflow_complete",
                                "message": "Workflow completed successfully!"
                            }
                            return state
                    else:
                        state['response'] = {
                            "status": "workflow_complete",
                            "message": "Workflow completed successfully!"
                        }
                        return state
                else:
                    state['response'] = {
                        "status": "error",
                        "message": "Workflow configuration not found"
                    }
                    return state
            else:
                state['response'] = {
                    "status": "info_needed",
                    "message": "No active workflow session found. Please start a new onboarding process."
                }
                return state
        finally:
            db.close()
    
    # Handle existing workflow continuation (legacy logic)
    current_step_id = state.get('current_step_id', 'welcome')
    customer_id = state.get('customer_id')
    
    if customer_id:
        # Get active workflow session
        bank = state.get('bank_name', 'federal')
        product = state.get('product_name', 'personal_loan')
        
        session = get_active_workflow_session(customer_id, bank, product)
        if session:
            session_data = {
                "session_id": str(session.id),
                "customer_id": customer_id,
                "bank_name": bank,
                "product_type": product,
                "current_action_id": session.current_action_id
            }
            
            try:
                # Get workflow schema from database
                bank_name_mapping = {
                    "federal bank": "federal",
                    "federalbank": "federal", 
                    "dhanlaxmi bank": "dhanlaxmi",
                    "dhanlaxmibank": "dhanlaxmi"
                }
                db_bank_name = bank_name_mapping.get(bank.lower(), bank.lower().replace(" ", ""))
                workflow_details = get_workflow_details(db_bank_name, product.lower().replace(" ", "_"))
                
                if not workflow_details:
                    # If no workflow found in DB, create a default response
                    workflow_response = {
                        "success": True,
                        "current_action": {"action_id": session.current_action_id, "stage_name": "Current Step"},
                        "ui_schema": {"screen_id": "default_screen", "ui_components": []},
                        "session_data": session_data
                    }
                else:
                    # Use database workflow with complete UI schema
                    action_schema = workflow_details.get('action_schema', [])
                    ui_schema = workflow_details.get('ui_schema', {})
                    
                    # Find current action in schema
                    current_action = next((item for item in action_schema if item["id"] == session.current_action_id), None)
                    
                    if current_action:
                        # Get UI components for current action from database
                        ui_components = ui_schema.get(session.current_action_id, {})
                        
                        # Build response with database data
                        workflow_response = {
                            "success": True,
                            "current_action": {
                                "action_id": current_action["id"],
                                "stage_name": current_action["stage_name"],
                                "action_type": current_action["action_type"],
                                "priority": current_action["priority"],
                                "is_mandatory": current_action["is_mandatory"],
                                "flow_type": current_action["flow_type"],
                                "description": current_action.get("desc_for_llm", "")
                            },
                            "ui_schema": {
                                "id": ui_components.get("id", f"ui_{session.current_action_id}_001"),
                                "session_id": session_data.get("session_id"),
                                "screen_id": ui_components.get("screen_id", f"{session.current_action_id}_screen"),
                                "ui_components": ui_components.get("ui_components", [])
                            },
                            "navigation": {
                                "next_success_action_id": current_action.get("next_success_action_id"),
                                "next_err_action_id": current_action.get("next_err_action_id"),
                                "can_skip": current_action.get("can_skip", False)
                            },
                            "session_data": {
                                "session_id": session_data.get("session_id"),
                                "customer_id": session_data.get("customer_id"),
                                "flow_type": current_action["flow_type"],
                                "current_step": current_action["priority"],
                                "total_steps": len(action_schema),
                                **session_data
                            }
                        }
                    else:
                        # Fallback if current action not found
                        workflow_response = {
                            "success": True,
                            "current_action": {"action_id": session.current_action_id, "stage_name": "Current Step"},
                            "ui_schema": {"screen_id": "default_screen", "ui_components": []},
                            "session_data": session_data
                        }
                
                state['response'] = {
                    "status": "workflow_continue",
                    "customer_id": customer_id,
                    "session_id": str(session.id),
                    **workflow_response
                }
            except Exception as e:
                print(f"Error in workflow continuation: {e}")
                state['response'] = {
                    "status": "error",
                    "message": f"Failed to get workflow response: {str(e)}"
                }
        else:
            state['response'] = {
                "status": "error",
                "message": "No active workflow session found for this customer"
            }
    else:
        # Default fallback
        state['response'] = {
            "status": "info_needed",
            "message": "Please specify what you'd like to do. You can say 'I want to onboard a new customer' to start the onboarding process."
        }
    
    return state

def mcp_tool_node(state: AgentState):
    print("---MCP TOOL CALL--- ")
    tool_call = state.get('mcp_tool_json')
    print(state,'STATEEE')
    if not tool_call:
        state['response'] = {"error": "Missing tool call JSON for MCP."}
        return state
    
    response = mcp_client.call_tool(json.dumps(tool_call))
    state['response'] = response
    return state

def dashboard_agent_node(state: AgentState):
    print("---DASHBOARD AGENT--- ")
    question = state.get('question_for_dashboard')
    if not question:
        state['response'] = {"error": "No question provided for the dashboard agent."}
        return state

    result = external_services_client.call_dashboard_agent(question)
    state['response'] = result
    return state

def credit_analysis_node(state: AgentState):
    print("---CREDIT ANALYSIS--- ")
    metadata = state.get('credit_metadata')
    if not metadata:
        state['response'] = {"error": "No metadata provided for credit analysis."}
        return state
    result = external_services_client.call_credit_analysis(metadata)
    state['response'] = result
    return state

def rule_saver_node(state: AgentState):
    print("---RULE SAVER--- ")
    rule_data = state.get('rule_data')
    if not rule_data:
        state['response'] = {"error": "No rule data provided to save."}
        return state

    result = external_services_client.call_rule_saver(rule_data)
    state['response'] = result
    return state

def configurator_node(state: AgentState):
    print("---CONFIGURATOR--- ")
    user_id = state.get('user_id')
    action = state.get('configurator_action', 'setup')
    data = state.get('configurator_data', {})
    
    if not user_id:
        state['response'] = {"error": "User ID is required for configurator operations."}
        return state
    
    try:
        # Create configurator graph instance
        configurator_graph = create_configurator_graph()
        
        # Create initial configurator state
        configurator_state = {
            'user_id': user_id,
            'session_id': data.get('session_id', str(uuid.uuid4())),
            'current_step': 'connection_setup',
            'database_connection': None,
            'connection_test_result': None,
            'database_schema': None,
            'user_input': None,
            'test_queries': None,
            'vector_storage_result': None,
            'configuration_complete': False,
            'error_message': None,
            'response': {},
            'messages': []
        }
        
        # Handle different configurator actions
        if action == 'setup' and data.get('connection_details'):
            # Create database connection from provided details
            connection_details = data['connection_details']
            db_connection = DatabaseConnection(
                id=str(uuid.uuid4()),
                name=connection_details.get('connection_name', 'New Connection'),
                database_type=DatabaseType(connection_details.get('database_type')),
                host=connection_details.get('host'),
                port=int(connection_details.get('port')),
                database_name=connection_details.get('database_name'),
                username=connection_details.get('username'),
                password=connection_details.get('password'),
                ssl_enabled=connection_details.get('ssl_enabled', False)
            )
            configurator_state['database_connection'] = db_connection
        
        elif action == 'user_input' and data.get('user_schema_input'):
            # Handle user schema input
            from .configurator.models import UserSchemaInput
            user_input = UserSchemaInput(
                connection_id=data.get('connection_id', ''),
                **data['user_schema_input']
            )
            configurator_state['user_input'] = user_input
        
        # Run configurator graph (this will be async in production)
        import asyncio
        result = asyncio.run(configurator_graph.run_configuration(configurator_state))
        
        state['response'] = {
            "status": "success" if result.get('configuration_complete') else "in_progress",
            "session_id": result.get('session_id'),
            "current_step": result.get('current_step'),
            "data": result.get('response', {}),
            "error": result.get('error_message')
        }
        
    except Exception as e:
        print(f"Error in configurator node: {str(e)}")
        state['response'] = {
            "status": "error",
            "error": f"Configurator error: {str(e)}"
        }
    
    return state

def mcp_tool_direct_node(state: AgentState):
    print("---MCP TOOL DIRECT--- ")
    tool_name = state.get('mcp_tool_name')
    tool_params = state.get('mcp_tool_params', {})
    
    if not tool_name:
        state['response'] = {"error": "Missing MCP tool name."}
        return state
    
    print(f"Calling MCP tool: {tool_name} with params: {tool_params}")
    response = mcp_client.call_mcp_tool(tool_name, tool_params)
    state['response'] = response
    return state

def handle_workflow_confirmation(state: AgentState, user_id: str, confirm: bool):
    """Handle workflow modification confirmation or cancellation"""
    print(f"---WORKFLOW CONFIRMATION--- Confirm: {confirm}")
    
    # Get pending modification from conversation state in database
    conversation_id = state.get('conversation_id')
    if not conversation_id:
        state['response'] = {"error": "No active conversation found for confirmation"}
        return state
    
    # Retrieve pending modification from dedicated database table
    pending_modification = get_pending_workflow_modification(conversation_id, user_id)
    print(f"CONFIRMATION DEBUG: Pending modification found: {pending_modification is not None}")
    if pending_modification:
        print(f"CONFIRMATION DEBUG: Pending modification keys: {list(pending_modification.keys())}")
    else:
        print(f"CONFIRMATION DEBUG: No pending modification found for conversation {conversation_id}")
    
    if not pending_modification:
        state['response'] = {
            "error": "No pending workflow modification found. Please start a new modification request.",
            "suggestion": "Try: 'I want to change federal bank kcc workflow where aadhar verification comes before otp verification'"
        }
        return state
    
    if not confirm:
        # User cancelled the modification
        state['response'] = {
            "status": "cancelled",
            "message": "Workflow modification has been cancelled. No changes were made."
        }
        # Clear pending modification from database
        clear_pending_workflow_modification(conversation_id, user_id)
        return state
    
    # User confirmed - apply the modification
    try:
        bank = pending_modification['bank']
        product = pending_modification['product']
        new_schema = pending_modification['new_schema']
        modification_request = pending_modification['modification_request']
        
        result = create_modified_workflow(
            bank=bank,
            product=product,
            new_action_schema=new_schema,
            modified_by=user_id,
            modification_reason=modification_request['description']
        )
        
        if result['success']:
            # Get the new workflow preview
            new_preview = get_workflow_sequence_preview(bank, product)
            
            state['response'] = {
                "status": "success",
                "message": f"✅ Workflow modification applied successfully!\n\n{result['message']}",
                "modification_applied": {
                    "bank": bank,
                    "product": product,
                    "old_version": pending_modification['current_workflow']['version'],
                    "new_version": result['new_version'],
                    "change_description": modification_request['description']
                },
                "new_workflow_sequence": new_preview['sequence'] if new_preview else [],
                "success_message": f"The {bank} {product} workflow has been updated to version {result['new_version']}. All future workflow sessions will use the new sequence."
            }
        else:
            state['response'] = {
                "status": "error",
                "message": f"Failed to apply workflow modification: {result['error']}"
            }
        
        # Clear pending modification from database
        clear_pending_workflow_modification(conversation_id, user_id)
        
    except Exception as e:
        state['response'] = {
            "status": "error",
            "message": f"Error applying workflow modification: {str(e)}"
        }
        # Clear pending modification from database on error too
        clear_pending_workflow_modification(conversation_id, user_id)
    
    return state

def workflow_modification_node(state: AgentState):
    """Production-grade workflow modification system with modular design"""
    print("=== WORKFLOW MODIFICATION SYSTEM ===")
    
    try:
        # Extract core parameters
        user_query = state.get('user_query', '')
        user_id = state.get('user_id')
        conversation_id = state.get('conversation_id')
        
        print(f"📋 Processing request for user: {user_id}, conversation: {conversation_id}")
        
        # Handle confirmation/cancellation flow
        if _is_confirmation_message(user_query):
            return _handle_confirmation_flow(state, user_id, conversation_id, confirm=True)
        elif _is_cancellation_message(user_query):
            return _handle_confirmation_flow(state, user_id, conversation_id, confirm=False)
        
        # Extract modification parameters
        params = _extract_modification_parameters(state, user_query)
        if not params['valid']:
            return _create_error_response(params['error'], params.get('details'))
        
        bank, product, modification_request = params['bank'], params['product'], params['request']
        print(f"🎯 Parameters: bank='{bank}', product='{product}', request='{modification_request}'")
        
        # Get current workflow
        workflow_data = _get_workflow_data(bank, product)
        if not workflow_data['valid']:
            return _create_error_response(workflow_data['error'])
        
        # Parse modification request
        modification_plan = _parse_modification_request(modification_request, workflow_data['schema'])
        if not modification_plan['valid']:
            return _create_error_response(modification_plan['error'], {
                "current_sequence": workflow_data['preview'],
                "available_actions": [f"{a['id']} ({a.get('stage_name', '')})" for a in workflow_data['schema']]
            })
        
        # Create modified workflow
        new_workflow = _create_modified_workflow(workflow_data['schema'], modification_plan)
        if not new_workflow['valid']:
            return _create_error_response(new_workflow['error'])
        
        # Generate previews
        current_preview = workflow_data['preview']
        new_preview = _generate_workflow_preview(new_workflow['schema'], bank, product)
        
        # Store pending modification
        _store_pending_modification(conversation_id, user_id, bank, product, {
            "modification_request": modification_request,
            "modification_plan": modification_plan,
            "new_schema": new_workflow['schema']
        })
        
        # Return confirmation prompt with previews
        return _create_confirmation_response(
            modification_request, current_preview, new_preview, bank, product
        )
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR in workflow_modification_node: {e}")
        import traceback
        print(f"📋 Full traceback: {traceback.format_exc()}")
        return _create_error_response(f"System error: {e}")


def _is_confirmation_message(user_query: str) -> bool:
    """Check if message is a confirmation"""
    confirmation_words = ['confirm', 'yes', 'apply', 'proceed', 'ok']
    return user_query.lower().strip() in confirmation_words


def _is_cancellation_message(user_query: str) -> bool:
    """Check if message is a cancellation"""
    cancellation_words = ['cancel', 'no', 'abort', 'stop', 'nevermind']
    return user_query.lower().strip() in cancellation_words


def _extract_modification_parameters(state: AgentState, user_query: str) -> dict:
    """Extract bank, product, and modification request from state or user query"""
    try:
        # Try to get from state first
        bank = state.get('bank_name', '').strip()
        product = state.get('product_name', '').strip()
        modification_request = state.get('modification_request', '').strip()
        
        # If missing, extract from user_query JSON
        if not modification_request and user_query:
            import json
            start_idx = user_query.find('{')
            if start_idx != -1:
                end_idx = _find_matching_brace(user_query, start_idx)
                if end_idx != -1:
                    json_str = user_query[start_idx:end_idx + 1]
                    try:
                        context_json = json.loads(json_str)
                        bank = bank or context_json.get('bank', '').strip()
                        product = product or context_json.get('product', '').strip()
                        modification_request = context_json.get('request', '').strip()
                    except json.JSONDecodeError:
                        pass
        
        if not all([bank, product, modification_request]):
            return {
                'valid': False,
                'error': 'Missing required parameters for workflow modification',
                'details': {
                    'received': {
                        'bank': bank,
                        'product': product,
                        'modification_request': modification_request
                    }
                }
            }
        
        return {
            'valid': True,
            'bank': bank,
            'product': product,
            'request': modification_request
        }
        
    except Exception as e:
        return {
            'valid': False,
            'error': f'Failed to extract parameters: {e}'
        }


def _find_matching_brace(text: str, start_idx: int) -> int:
    """Find the matching closing brace for JSON extraction"""
    brace_count = 0
    for i, char in enumerate(text[start_idx:], start_idx):
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                return i
    return -1


def _get_workflow_data(bank: str, product: str) -> dict:
    """Get workflow data and preview"""
    try:
        # Get workflow details
        workflow = get_workflow_details(bank, product)
        if not workflow:
            return {
                'valid': False,
                'error': f'No workflow found for {bank} {product}'
            }
        
        # Parse action schema
        action_schema = workflow['action_schema']
        if isinstance(action_schema, str):
            import json
            action_schema = json.loads(action_schema)
        
        # Get current preview
        current_preview = get_workflow_sequence_preview(bank, product)
        if not current_preview:
            return {
                'valid': False,
                'error': f'Could not generate preview for {bank} {product} workflow'
            }
        
        return {
            'valid': True,
            'workflow': workflow,
            'schema': action_schema,
            'preview': current_preview
        }
        
    except Exception as e:
        return {
            'valid': False,
            'error': f'Failed to get workflow data: {e}'
        }


def _parse_modification_request(request: str, schema: list) -> dict:
    """Parse natural language modification request"""
    try:
        request_lower = request.lower().strip()
        
        # Parse "move X before/after Y" pattern
        if 'move' in request_lower and ('before' in request_lower or 'after' in request_lower):
            if 'before' in request_lower:
                direction = 'before'
                parts = request_lower.split('before')
            else:
                direction = 'after'
                parts = request_lower.split('after')
            
            if len(parts) == 2:
                source_name = parts[0].replace('move', '').strip()
                target_name = parts[1].strip()
                
                # Find actual action IDs
                source_id = _find_action_by_name(schema, source_name)
                target_id = _find_action_by_name(schema, target_name)
                
                if source_id and target_id:
                    return {
                        'valid': True,
                        'type': 'reorder',
                        'source_action_id': source_id,
                        'target_action_id': target_id,
                        'direction': direction
                    }
                else:
                    return {
                        'valid': False,
                        'error': f'Could not find actions: source="{source_name}" -> "{source_id}", target="{target_name}" -> "{target_id}"'
                    }
        
        return {
            'valid': False,
            'error': f'Could not parse modification request: "{request}". Expected format: "move [action] before/after [action]"'
        }
        
    except Exception as e:
        return {
            'valid': False,
            'error': f'Failed to parse modification request: {e}'
        }


def _find_action_by_name(schema: list, action_name: str) -> str:
    """Find action ID by name using fuzzy matching"""
    action_name_lower = action_name.lower()
    
    # Try exact match first
    for action in schema:
        if action['id'].lower() == action_name_lower:
            return action['id']
    
    # Try partial match in stage_name or id
    for action in schema:
        stage_name = action.get('stage_name', '').lower()
        if action_name_lower in stage_name or action_name_lower in action['id'].lower():
            return action['id']
    
    return None


def _create_modified_workflow(schema: list, modification_plan: dict) -> dict:
    """Create modified workflow based on modification plan"""
    try:
        if modification_plan['type'] == 'reorder':
            new_schema = _reorder_workflow_actions(
                schema,
                modification_plan['source_action_id'],
                modification_plan['target_action_id'],
                modification_plan['direction']
            )
            return {
                'valid': True,
                'schema': new_schema
            }
        else:
            return {
                'valid': False,
                'error': f'Unsupported modification type: {modification_plan["type"]}'
            }
            
    except Exception as e:
        return {
            'valid': False,
            'error': f'Failed to create modified workflow: {e}'
        }


def _reorder_workflow_actions(schema: list, source_id: str, target_id: str, direction: str) -> list:
    """Reorder workflow actions by moving source before/after target"""
    new_schema = schema.copy()
    
    # Find and remove source action
    source_action = None
    for i, action in enumerate(new_schema):
        if action['id'] == source_id:
            source_action = new_schema.pop(i)
            break
    
    if not source_action:
        raise ValueError(f'Source action "{source_id}" not found')
    
    # Find target position and insert
    for i, action in enumerate(new_schema):
        if action['id'] == target_id:
            if direction == 'before':
                new_schema.insert(i, source_action)
            else:  # after
                new_schema.insert(i + 1, source_action)
            break
    else:
        raise ValueError(f'Target action "{target_id}" not found')
    
    # Update next_success_action_id and priority
    for i, action in enumerate(new_schema):
        if i < len(new_schema) - 1:
            action['next_success_action_id'] = new_schema[i + 1]['id']
        else:
            action['next_success_action_id'] = None
        action['priority'] = i + 1
    
    return new_schema


def _generate_workflow_preview(schema: list, bank: str, product: str) -> list:
    """Generate workflow preview from schema"""
    preview = []
    for i, action in enumerate(schema):
        preview.append({
            "step": i + 1,
            "action_id": action['id'],
            "stage_name": action.get('stage_name', action['id']),
            "description": action.get('description', action.get('desc_for_llm', ''))
        })
    return preview


def _store_pending_modification(conversation_id: str, user_id: str, bank_name: str, product_type: str, data: dict) -> bool:
    """Store the pending workflow modification in the database"""
    try:
        success = store_pending_workflow_modification(
            conversation_id=conversation_id,
            user_id=user_id,
            bank_name=bank_name,
            product_type=product_type,
            modification_data=data
        )
        
        if success:
            print(f"✅ STORE_PENDING: Successfully stored pending modification for {bank_name} {product_type}")
        else:
            print(f"❌ STORE_PENDING: Failed to store pending modification for {bank_name} {product_type}")
        
        return success
        
    except Exception as e:
        print(f"❌ Error storing pending modification: {e}")
        return False


def _handle_confirmation_flow(state: AgentState, user_id: str, conversation_id: str, confirm: bool):
    """Handle confirmation or cancellation of workflow modification"""
    try:
        # Get pending modification
        pending = get_pending_workflow_modification(conversation_id, user_id)
        if not pending:
            return _create_error_response("No pending workflow modification found to confirm or cancel.")
        
        if confirm:
            # Apply the modification
            success = _apply_workflow_modification(pending)
            if success:
                # Clear pending modification
                clear_pending_workflow_modification(conversation_id, user_id)
                return {
                    'response': {
                        "message": f"✅ Successfully applied workflow modification for {pending['bank']} {pending['product']}!",
                        "modification_applied": pending['modification_data']['modification_request'],
                        "status": "completed"
                    }
                }
            else:
                return _create_error_response("Failed to apply workflow modification to database.")
        else:
            # Cancel the modification
            clear_pending_workflow_modification(conversation_id, user_id)
            return {
                'response': {
                    "message": "❌ Workflow modification cancelled.",
                    "status": "cancelled"
                }
            }
            
    except Exception as e:
        return _create_error_response(f"Error handling confirmation: {e}")


def _apply_workflow_modification(pending_modification: dict) -> bool:
    """Apply the pending workflow modification to the database"""
    try:
        # Debug: Print the structure of pending_modification
        print(f"🔍 APPLY_MODIFICATION: Pending modification structure: {pending_modification}")
        print(f"🔍 APPLY_MODIFICATION: Keys available: {list(pending_modification.keys())}")
        
        # Access bank_name and product_type from the database record structure
        # The database stores bank_name/product_type as separate columns, not in modification_data
        bank_name = pending_modification.get('bank_name')
        product_type = pending_modification.get('product_type')
        user_id = pending_modification.get('user_id')
        modification_data = pending_modification.get('modification_data', {})
        
        new_schema = modification_data.get('new_schema')
        modification_request = modification_data.get('modification_request')
        
        print(f"🔍 APPLY_MODIFICATION: Extracted - bank_name='{bank_name}', product_type='{product_type}', user_id='{user_id}'")
        print(f"🔍 APPLY_MODIFICATION: Schema length: {len(new_schema) if new_schema else 'None'}")
        print(f"🔍 APPLY_MODIFICATION: Request: '{modification_request}'")
        
        if not all([bank_name, product_type, new_schema, modification_request, user_id]):
            print(f"❌ APPLY_MODIFICATION: Missing required data - bank_name={bank_name}, product_type={product_type}, schema={bool(new_schema)}, request={bool(modification_request)}, user={user_id}")
            return False
        
        # Create new workflow version
        success = create_modified_workflow(
            bank=bank_name,
            product=product_type,
            new_action_schema=new_schema,
            modification_reason=modification_request,
            modified_by=user_id
        )
        
        print(f"🔍 APPLY_MODIFICATION: create_modified_workflow returned: {success}")
        return success
        
    except Exception as e:
        import traceback
        print(f"❌ Error applying workflow modification: {e}")
        print(f"📋 Full traceback: {traceback.format_exc()}")
        return False


def _create_confirmation_response(request: str, current_preview: list, new_preview: list, bank: str, product: str) -> dict:
    """Create confirmation response with before/after previews"""
    return {
        'response': {
            "message": f"🔄 Workflow Modification Preview for {bank.upper()} {product.upper()}",
            "modification_request": request,
            "current_sequence": current_preview,
            "proposed_sequence": new_preview,
            "confirmation_prompt": "\n✅ Reply 'confirm' to apply this modification\n❌ Reply 'cancel' to abort",
            "bank": bank,
            "product": product,
            "status": "pending_confirmation"
        }
    }


def _create_error_response(error_message: str, details: dict = None) -> dict:
    """Create standardized error response"""
    response = {
        'response': {
            "error": error_message,
            "status": "error"
        }
    }
    
    if details:
        response['response'].update(details)
    
    return response

# Old duplicate function removed - using _reorder_workflow_actions instead

def generate_workflow_preview_from_schema(action_schema, bank, product):
    """Generate workflow preview from action schema"""
    sequence = []
    for i, action in enumerate(action_schema):
        sequence.append({
            'step': i + 1,
            'action_id': action['id'],
            'stage_name': action.get('stage_name', action['id']),
            'description': action.get('desc_for_llm', '')
        })
    
    return {
        'bank': bank,
        'product': product,
        'sequence': sequence
    }

def confirm_workflow_modification(bank, product, new_schema, modification_request, user_id):
    """Apply the confirmed workflow modification to database"""
    try:
        result = create_modified_workflow(
            bank=bank,
            product=product,
            new_action_schema=new_schema,
            modified_by=user_id,
            modification_reason=modification_request['description']
        )
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}
    
    return state

def get_retriever():
    """Initializes a ChromaDB retriever for RAG."""
    client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
    embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
    vector_store = Chroma(
        client=client,
        collection_name="jlg_docs",
        embedding_function=embeddings,
    )
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    return retriever

retriever = get_retriever()

def general_qa_node(state: AgentState):
    print("---GENERAL QA (RAG)--- ")
    question = state['user_query']
    db_chat_history = state.get('chat_history', [])
    print(f"Answering question: {question}")

    # 1. Create a history-aware retriever
    contextualize_q_system_prompt = ("""
    Given a chat history and the latest user question which might reference context in the chat history, 
    formulate a standalone question which can be understood without the chat history. 
    Do NOT answer the question, just reformulate it if needed and otherwise return it as is.
    """
    )
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    # 2. Create a chain to answer the question
    qa_system_prompt = ("""
    You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. 
    If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
    Also, consider the chat history to provide a conversational answer.

    <context>
    {context}
    </context>
    """
    )
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    # 3. Create the final conversational retrieval chain
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    # 4. Format the chat history from our DB format to the LangChain Message format
    chat_history_messages = []
    for msg in db_chat_history:
        if msg.sender_type == 'USER':
            chat_history_messages.append(HumanMessage(content=msg.content))
        else:
            chat_history_messages.append(AIMessage(content=msg.content))

    # 5. Invoke the chain
    response = rag_chain.invoke({"input": question, "chat_history": chat_history_messages})
    
    response_text = response.get("answer", "I couldn't find an answer.")
    
    state['response'] = {"type": "text", "content": response_text}
    return state

# --- Graph Definition ---

def create_graph():
    """Creates the agent graph."""
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("workflow_executor", workflow_execution_node)
    workflow.add_node("workflow_modifier", workflow_modification_node)
    workflow.add_node("general_qa", general_qa_node)
    workflow.add_node("mcp_tool_caller", mcp_tool_node)
    workflow.add_node("dashboard_agent", dashboard_agent_node)
    workflow.add_node("credit_analyzer", credit_analysis_node)
    workflow.add_node("rule_updater", rule_saver_node)
    workflow.add_node("mcp_tool_direct", mcp_tool_direct_node)
    workflow.add_node("configurator", configurator_node)

    # Set entry point
    workflow.set_entry_point("router")

    # Define conditional logic for routing
    def decide_next_node(state: AgentState) -> str:
        """Directs the graph based on the router's decision."""
        print(f"---DECIDING NEXT NODE---")
        decision = state.get('route_decision', 'general_qa')
        print(f"Route: {decision}")

        if decision == 'workflow_modification':
            return 'workflow_modifier'
        elif decision == 'mcp_tool_call':
            return 'mcp_tool_caller'
        elif decision == 'dashboard_agent':
            return 'dashboard_agent'
        elif decision == 'credit_analysis':
            return 'credit_analyzer'
        elif decision == 'rule_saver':
            return 'rule_updater'
        elif decision == 'workflow_execution':
            return 'workflow_executor'
        elif decision == 'configurator':
            return 'configurator'
        elif decision in [tool.get('name') for tool in mcp_tools]:
            return 'mcp_tool_direct'
        else:
            return 'general_qa'

    workflow.add_conditional_edges(
        "router",
        decide_next_node,
        {
            "workflow_executor": "workflow_executor",
            "workflow_modifier": "workflow_modifier",
            "mcp_tool_caller": "mcp_tool_caller",
            "dashboard_agent": "dashboard_agent",
            "credit_analyzer": "credit_analyzer",
            "rule_updater": "rule_updater",
            "mcp_tool_direct": "mcp_tool_direct",
            "configurator": "configurator",
            "general_qa": "general_qa",
        }
    )

    # Define edges to the end state
    workflow.add_edge("workflow_executor", END)
    workflow.add_edge("workflow_modifier", END)
    workflow.add_edge("general_qa", END)
    workflow.add_edge("mcp_tool_caller", END)
    workflow.add_edge("dashboard_agent", END)
    workflow.add_edge("credit_analyzer", END)
    workflow.add_edge("rule_updater", END)
    workflow.add_edge("mcp_tool_direct", END)
    workflow.add_edge("configurator", END)

    # Compile the graph
    return workflow.compile()

# Create the agent executor by calling the factory function
agent_executor = create_graph()
