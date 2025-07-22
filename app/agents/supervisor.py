import json
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
from app.core.database import get_workflow_details, update_workflow_action_schema, ChatMessage
from .mcp_client import MCPClient
from .prompts import SUPERVISOR_ROUTER_PROMPT, WORKFLOW_MODIFICATION_PROMPT

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

# Fetch available MCP tools at startup
print("Fetching available MCP tools...")
mcp_tools_data = mcp_client.get_available_tools()
mcp_tools = mcp_tools_data.get('tools', [])
print(f"Available MCP tools: {[tool.get('name', 'unknown') for tool in mcp_tools]}")

# --- Graph Nodes ---

def router_node(state: AgentState):
    """Determines the next step based on the user query."""
    print("---INTENT ROUTER--- ")
    
    # Format chat history for the prompt
    history = state.get('chat_history', [])
    print(f"DEBUG: Raw chat history length: {len(history)}")
    for i, msg in enumerate(history):
        print(f"DEBUG: History[{i}]: {msg.sender_type.value.upper()}: {msg.content[:100]}...")
    
    formatted_history = "\n".join([
        f"{msg.sender_type.value.upper()}: {msg.content}" for msg in history
    ])
    print(f"DEBUG: Formatted history for prompt:\n{formatted_history}\n--- END HISTORY ---")

    # Dynamically create the list of tools for the prompt
    base_tools = (
        "- `credit_analysis`: Use to analyze a customer's credit based on their metadata.\n"
        "- `rule_saver`: Use to update or add new credit rules.\n"
        "- `workflow_modification`: Modifies an existing workflow based on user instructions.\n"
        "- `workflow_execution`: Executes a predefined workflow step-by-step.\n"
        "- `dashboard_agent`: Use for any questions about statistics, reports, collections, disbursements, or performance of Field Officers or CECs.\n"
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
             state['mcp_tool_json'] = parsed_output.get('mcp_tool_json')
        elif route == 'dashboard_agent':
            state['question_for_dashboard'] = parsed_output.get('question')
        elif route == 'credit_analysis':
            state['credit_metadata'] = parsed_output.get('credit_metadata')
        elif route == 'rule_saver':
            state['rule_data'] = parsed_output.get('rule_data')
        elif route in [tool.get('name') for tool in mcp_tools]:
            # Handle MCP tool calls
            state['mcp_tool_name'] = route
            state['mcp_tool_params'] = parsed_output.get('tool_parameters', {})

    except json.JSONDecodeError:
        print("Error: LLM returned invalid JSON for routing. Defaulting to General QA.")
        state['route_decision'] = 'general_qa'
        
    return state

def workflow_execution_node(state: AgentState):
    print("---WORKFLOW EXECUTION---")
    bank = state.get('bank_name')
    product = state.get('product_name')
    
    if not bank or not product:
        state['response'] = {"error": "I need to know which bank and product you're asking about."}
        return state

    workflow = get_workflow_details(bank, product)
    if not workflow:
        state['response'] = {"error": f"I couldn't find a workflow for {bank} {product}."}
        return state

    action_schema = workflow['action_schema']
    ui_schema = workflow['ui_schema']
    
    step_id_to_show = state.get('current_step_id') or action_schema[0]['id']
    
    current_action = next((item for item in action_schema if item["id"] == step_id_to_show), None)
    
    if not current_action:
        state['response'] = {"error": f"Step '{step_id_to_show}' not found in the workflow."}
        return state

    ui_id = current_action.get('ui_id')
    ui_component = next((item for item in ui_schema if item["id"] == ui_id), None)

    state['response'] = {
        "status": "success",
        "current_action": current_action,
        "ui_component": ui_component
    }
    state['current_step_id'] = step_id_to_show
    return state

def mcp_tool_node(state: AgentState):
    print("---MCP TOOL CALL--- ")
    tool_call = state.get('mcp_tool_json')
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
        state['response'] = {"error": "Missing question for Dashboard Agent."}
        return state
    
    print(f"Dashboard agent question: {question}")
    response = mcp_client.call_dashboard_agent(question)
    state['response'] = response
    return state

def credit_analysis_node(state: AgentState):
    print("---CREDIT ANALYSIS--- ")
    metadata = state.get('credit_metadata')
    if not metadata:
        state['response'] = {"error": "Missing metadata for credit analysis."}
        return state
    
    response = mcp_client.call_credit_analysis(metadata)
    state['response'] = response
    return state

def rule_saver_node(state: AgentState):
    print("---RULE SAVER--- ")
    rule_data = state.get('rule_data')
    if not rule_data:
        state['response'] = {"error": "Missing rule data for rule saver."}
        return state
    
    response = mcp_client.call_rule_saver(rule_data)
    state['response'] = response
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

def workflow_modification_node(state: AgentState):
    print("---WORKFLOW MODIFICATION---")
    bank = state.get('bank_name')
    product = state.get('product_name')
    user_request = state['user_query']

    if not bank or not product:
        state['response'] = {"error": "Please specify which bank and product workflow you want to change."}
        return state

    workflow = get_workflow_details(bank, product)
    if not workflow:
        state['response'] = {"error": f"Cannot modify a workflow that does not exist for {bank} {product}."}
        return state

    prompt = WORKFLOW_MODIFICATION_PROMPT.format(
        current_schema=json.dumps(workflow['action_schema'], indent=2),
        user_request=user_request
    )
    
    response = llm.invoke(prompt)
    
    cleaned_json_str = response.content.strip().replace("```json", "").replace("```", "").strip()

    try:
        new_action_schema = json.loads(cleaned_json_str)
        update_workflow_action_schema(bank, product, new_action_schema)
        
        summary_prompt = f"Summarize the following change in a single sentence: The user asked to '{user_request}' and the workflow was updated."
        summary = llm.invoke(summary_prompt).content

        state['response'] = {
            "status": "success",
            "message": f"Workflow for {bank} {product} has been updated. {summary}",
            "new_action_schema": new_action_schema
        }
    except json.JSONDecodeError:
        state['response'] = {"error": "The LLM failed to generate a valid JSON for the new workflow. Please try rephrasing your request."}
    
    return state

def get_retriever():
    """Initializes a ChromaDB retriever for RAG."""
    client = chromadb.HttpClient(host='3.6.132.24', port=8000)
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

    # Compile the graph
    return workflow.compile()

# Create the agent executor by calling the factory function
agent_executor = create_graph()
