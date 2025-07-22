import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    create_engine, Column, Integer, String, JSON, DateTime, 
    Enum as SQLAlchemyEnum, Text, ForeignKey, Boolean, UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.exc import NoResultFound

from .config import settings

DATABASE_URL = settings.DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- Enums ---
class SenderType(enum.Enum):
    USER = "user"
    AI = "ai"

# --- Models ---
class Workflow(Base):
    __tablename__ = "workflows"
    id = Column(Integer, primary_key=True, index=True)
    bank_name = Column(String, nullable=False)
    product_type = Column(String, nullable=False)
    action_schema = Column(JSON, nullable=False)
    ui_schema = Column(JSON, nullable=False)
    api_schema = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint('bank_name', 'product_type', name='_bank_product_uc'),)

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    state = Column(JSON, nullable=True, default=lambda: {})

    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(PG_UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    sender_type = Column(SQLAlchemyEnum(SenderType), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


# --- Database Functions ---
def create_tables():
    Base.metadata.create_all(bind=engine)

def get_workflow_details(bank: str, product: str):
    db = SessionLocal()
    try:
        workflow = db.query(Workflow).filter(
            func.lower(Workflow.bank_name) == func.lower(bank),
            func.lower(Workflow.product_type) == func.lower(product),
            Workflow.is_active == True
        ).one()
        return {
            "action_schema": workflow.action_schema,
            "ui_schema": workflow.ui_schema,
            "api_schema": workflow.api_schema
        }
    except NoResultFound:
        return None
    finally:
        db.close()

def update_workflow_action_schema(bank: str, product: str, new_action_schema: dict):
    db = SessionLocal()
    try:
        workflow = db.query(Workflow).filter(
            Workflow.bank_name == bank,
            Workflow.product_type == product
        ).one()
        workflow.action_schema = new_action_schema
        db.commit()
        return True
    except NoResultFound:
        return False
    finally:
        db.close()

def get_or_create_conversation(user_id: str, conversation_id_str: str = None) -> Conversation:
    session = SessionLocal()
    try:
        if conversation_id_str is None:
            # Create a new conversation with backend-generated UUID
            print(f"Creating new conversation for user: {user_id}")
            conversation = Conversation(user_id=user_id)
        else:
            try:
                # Try to treat it as a UUID
                conversation_id = uuid.UUID(conversation_id_str)
                conversation = session.query(Conversation).filter_by(id=conversation_id).first()
                if conversation:
                    print(f"Found existing conversation by UUID: {conversation_id}")
                    return conversation
                # If not found, create one with the client-provided UUID
                print(f"Creating conversation with provided UUID: {conversation_id}")
                conversation = Conversation(id=conversation_id, user_id=user_id)
            except ValueError:
                # If not a valid UUID, create a new conversation (ignore the invalid string)
                print(f"Invalid UUID '{conversation_id_str}', creating new conversation for user: {user_id}")
                conversation = Conversation(user_id=user_id)

        session.add(conversation)
        session.commit()
        session.refresh(conversation)
        print(f"Successfully created/retrieved conversation: {conversation.id}")
        return conversation
    finally:
        session.close()

def add_message_to_conversation(conversation_id: uuid.UUID, sender: SenderType, content: str):
    db = SessionLocal()
    try:
        message = ChatMessage(
            conversation_id=conversation_id,
            sender_type=sender,
            content=content
        )
        db.add(message)
        db.commit()
    finally:
        db.close()

def get_conversations_for_user(user_id: str) -> list[Conversation]:
    """Get all conversations for a specific user."""
    db = SessionLocal()
    try:
        conversations = (
            db.query(Conversation)
            .filter(func.lower(Conversation.user_id) == func.lower(user_id))
            .order_by(Conversation.updated_at.desc())
            .all()
        )
        return conversations
    finally:
        db.close()

def get_conversation_history(conversation_id_str: str, limit: int = 10) -> list[ChatMessage]:
    """Get chat history for a conversation. conversation_id_str must be a valid UUID."""
    db = SessionLocal()
    try:
        print(f"DEBUG DB: Looking for conversation_id: {conversation_id_str}")
        conversation_id = uuid.UUID(conversation_id_str)
        print(f"DEBUG DB: Converted to UUID: {conversation_id}")
        
        history = (
            db.query(ChatMessage)
            .filter(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all()
        )
        print(f"DEBUG DB: Found {len(history)} messages in database")
        return list(reversed(history))  # Return in chronological order
    except ValueError as e:
        print(f"DEBUG DB: Invalid UUID format: {conversation_id_str} - {e}")
        return []
    except Exception as e:
        print(f"DEBUG DB: Error getting conversation history: {e}")
        return []
    finally:
        db.close()
