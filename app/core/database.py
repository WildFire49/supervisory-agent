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

def get_or_create_conversation(user_id: str, conversation_id_str: str) -> Conversation:
    session = SessionLocal()
    try:
        conversation_id = uuid.UUID(conversation_id_str)
        conversation = session.query(Conversation).filter_by(id=conversation_id).first()
        if conversation:
            return conversation
        # If not found, create one with the client-provided UUID
        conversation = Conversation(id=conversation_id, user_id=user_id)
    except ValueError:
        # If conversation_id_str is not a valid UUID, create a new one and let the DB generate the ID
        conversation = Conversation(user_id=user_id)

    try:
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
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

def get_conversation_history(conversation_id_str: str, limit: int = 10) -> list[ChatMessage]:
    db = SessionLocal()
    try:
        conversation_id = uuid.UUID(conversation_id_str)
        history = (
            db.query(ChatMessage)
            .filter(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all()
        )
        return list(reversed(history))  # Return in chronological order
    except (NoResultFound, ValueError):
        return []
    finally:
        db.close()
