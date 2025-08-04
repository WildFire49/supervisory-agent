from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import traceback
import json
from app.models.schemas import (
    ChatRequest, ChatResponse, ConversationCreateRequest, ConversationCreateResponse,
    ConversationListResponse, ChatHistoryResponse, ConversationInfo, ChatMessageResponse
)
from app.agents.supervisor import agent_executor
from app.core.database import (
    get_or_create_conversation,
    add_message_to_conversation,
    get_conversation_history,
    get_conversations_for_user,
    SenderType,
    SessionLocal
)

app = FastAPI(
    title="Supervisory Agent API",
    description="An API for a supervisory agent that can handle dynamic workflows.",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint that receives user requests and routes them to the supervisory agent.
    """
    if not request.user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    try:
        # 1. Get or create the conversation object
        conversation = get_or_create_conversation(request.user_id, request.conversation_id)
        actual_conversation_id = str(conversation.id)

        # 2. Save the user's message to the history
        add_message_to_conversation(conversation.id, SenderType.USER, request.message)

        # 3. Fetch recent chat history (use the actual UUID, not the request conversation_id)
        chat_history = get_conversation_history(actual_conversation_id)
        print(f"DEBUG MAIN: Loaded {len(chat_history)} messages from database")
        for i, msg in enumerate(chat_history):
            print(f"DEBUG MAIN: History[{i}]: {msg.sender_type.value} - {msg.content[:50]}...")

        # 4. Prepare agent input, loading state from the conversation
        agent_input = {
            "user_id": request.user_id,
            "conversation_id": request.conversation_id,
            "user_query": request.message,
            "chat_history": chat_history,
            # Load previous state if it exists
            "bank_name": conversation.state.get('bank_name') if conversation.state else None,
            "product_name": conversation.state.get('product_name') if conversation.state else None,
        }

        # 5. Asynchronously invoke the agent
        print(f"DEBUG MAIN: Passing {len(agent_input.get('chat_history', []))} messages to agent")
        response_data = await agent_executor.ainvoke(agent_input)

        # 6. Save the AI's response to the history
        ai_response_content = json.dumps(response_data.get('response'))
        add_message_to_conversation(conversation.id, SenderType.AI, ai_response_content)

        # 7. Update and save the conversation state
        # We only persist the fields that should be remembered across turns.
        final_state = {
            'bank_name': response_data.get('bank_name'),
            'product_name': response_data.get('product_name'),
            'current_step_id': response_data.get('current_step_id')
        }
        conversation.state = final_state
        # The get_or_create_conversation function returns a detached object,
        # so we need a proper session to merge and commit the change.
        db = SessionLocal()
        try:
            db.merge(conversation)
            db.commit()
        finally:
            db.close()

        print(f"--- FINAL RESPONSE ---\n{json.dumps(response_data.get('response'), indent=2)}\n----------------------")
        return ChatResponse(
            response=response_data.get('response'),
            conversation_id=actual_conversation_id
        )

    except Exception as e:
        print("--- AGENT EXCEPTION ---")
        traceback.print_exc()
        print("-----------------------")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/conversations", response_model=ConversationCreateResponse)
async def create_conversation(request: ConversationCreateRequest):
    """
    Create a new conversation with a backend-generated UUID.
    Frontend should use this UUID for all subsequent chat requests.
    """
    if not request.user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    
    try:
        # Create a new conversation - pass None as conversation_id to generate new UUID
        conversation = get_or_create_conversation(request.user_id, None)
        
        print(f"Created new conversation: {conversation.id} for user: {request.user_id}")
        
        return ConversationCreateResponse(
            conversation_id=str(conversation.id),
            user_id=request.user_id,
            created_at=conversation.created_at
        )
    except Exception as e:
        print("--- CONVERSATION CREATION EXCEPTION ---")
        traceback.print_exc()
        print("-----------------------")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}/conversations", response_model=ConversationListResponse)
async def list_user_conversations(user_id: str):
    """
    Retrieve all conversations for a specific user, ordered by most recent.
    """
    try:
        conversations = get_conversations_for_user(user_id)
        response_data = [
            ConversationInfo(
                id=str(conv.id),
                user_id=conv.user_id,
                created_at=conv.created_at,
                updated_at=conv.updated_at
            ) for conv in conversations
        ]
        return ConversationListResponse(conversations=response_data)
    except Exception as e:
        print("--- CONVERSATION LISTING EXCEPTION ---")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversations/{conversation_id}/history", response_model=ChatHistoryResponse)
async def get_history(conversation_id: str):
    """
    Retrieve the chat history for a specific conversation.
    """
    try:
        history = get_conversation_history(conversation_id, limit=1000)  # Fetch a large number of messages
        response_data = [
            ChatMessageResponse(
                sender_type=msg.sender_type.value,
                content=msg.content,
                created_at=msg.created_at
            ) for msg in history
        ]
        return ChatHistoryResponse(history=response_data)
    except Exception as e:
        print("--- HISTORY FETCHING EXCEPTION ---")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}
