from fastapi import FastAPI, HTTPException
import traceback
import json
from app.models.schemas import ChatRequest, ChatResponse
from app.agents.supervisor import agent_executor
from app.core.database import (
    get_or_create_conversation,
    add_message_to_conversation,
    get_conversation_history,
    SenderType,
    SessionLocal
)

app = FastAPI(
    title="Supervisory Agent API",
    description="An API for a supervisory agent that can handle dynamic workflows.",
    version="1.0.0",
)

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint that receives user requests and routes them to the supervisory agent.
    """
    if not request.user_id or not request.conversation_id:
        raise HTTPException(status_code=400, detail="user_id and conversation_id are required")

    try:
        # 1. Get or create the conversation object
        conversation = get_or_create_conversation(request.user_id, request.conversation_id)

        # 2. Save the user's message to the history
        add_message_to_conversation(conversation.id, SenderType.USER, request.message)

        # 3. Fetch recent chat history
        chat_history = get_conversation_history(request.conversation_id)

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
        return ChatResponse(response=response_data.get('response'))

    except Exception as e:
        print("--- AGENT EXCEPTION ---")
        traceback.print_exc()
        print("-----------------------")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}
