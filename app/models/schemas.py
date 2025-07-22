from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime

class ChatRequest(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    conversation_id: Optional[str] = Field(None, description="The unique identifier for the conversation. If not provided, a new conversation will be created.")
    message: str = Field(..., description="The message from the user.")
    bank_name: Optional[str] = Field(None, description="The name of the bank, e.g., KVB, Federal.")
    product_name: Optional[str] = Field(None, description="The name of the product, e.g., JLG, individual_loan.")

class ChatResponse(BaseModel):
    response: Any = Field(..., description="The response from the agent, could be a UI schema or a text message.")
    conversation_id: str = Field(..., description="The conversation UUID for this chat session.")

class ConversationCreateRequest(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")

class ConversationCreateResponse(BaseModel):
    conversation_id: str = Field(..., description="The backend-generated UUID for the conversation.")
    user_id: str = Field(..., description="The unique identifier for the user.")
    created_at: datetime = Field(..., description="When the conversation was created.")


class ConversationInfo(BaseModel):
    id: str = Field(..., description="The unique identifier for the conversation.")
    user_id: str = Field(..., description="The unique identifier for the user.")
    created_at: datetime = Field(..., description="The timestamp when the conversation was created.")
    updated_at: datetime = Field(..., description="The timestamp when the conversation was last updated.")

class ConversationListResponse(BaseModel):
    conversations: list[ConversationInfo] = Field(..., description="A list of conversations for the user.")

class ChatMessageResponse(BaseModel):
    sender_type: str = Field(..., description="The sender of the message, either 'user' or 'ai'.")
    content: str = Field(..., description="The content of the message.")
    created_at: datetime = Field(..., description="The timestamp when the message was created.")

class ChatHistoryResponse(BaseModel):
    history: list[ChatMessageResponse] = Field(..., description="A list of messages in the conversation.")
