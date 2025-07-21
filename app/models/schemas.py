from pydantic import BaseModel, Field
from typing import Any, Optional

class ChatRequest(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    conversation_id: str = Field(..., description="The unique identifier for the conversation.")
    message: str = Field(..., description="The message from the user.")
    bank_name: Optional[str] = Field(None, description="The name of the bank, e.g., KVB, Federal.")
    product_name: Optional[str] = Field(None, description="The name of the product, e.g., JLG, individual_loan.")

class ChatResponse(BaseModel):
    response: Any = Field(..., description="The response from the agent, could be a UI schema or a text message.")
