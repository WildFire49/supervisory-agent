import enum
import uuid
from datetime import datetime, timedelta

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
class Customer(Base):
    __tablename__ = "customers"
    id = Column(String, primary_key=True, index=True)  # Custom customer ID like CI-SH-FED-2a7c963330c9
    name = Column(String, nullable=False)
    mobile_number = Column(String, nullable=True, index=True)
    email = Column(String, nullable=True)
    bank_name = Column(String, nullable=False)
    product_type = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False)  # active, inactive, suspended
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to workflow sessions
    workflow_sessions = relationship("WorkflowSession", back_populates="customer")

class WorkflowSession(Base):
    __tablename__ = "workflow_sessions"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False, index=True)
    bank_name = Column(String, nullable=False)
    product_type = Column(String, nullable=False)
    current_action_id = Column(String, nullable=False)  # Current step in workflow
    session_data = Column(JSON, nullable=True, default=lambda: {})  # Store form data, progress, etc.
    flow_type = Column(String, nullable=False)  # onboarding, collections, etc.
    status = Column(String, default="active", nullable=False)  # active, completed, abandoned
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="workflow_sessions")

class Workflow(Base):
    __tablename__ = "workflows"
    id = Column(Integer, primary_key=True, index=True)
    bank_name = Column(String, nullable=False)
    product_type = Column(String, nullable=False)
    action_schema = Column(JSON, nullable=False)
    ui_schema = Column(JSON, nullable=False)
    api_schema = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)  # Version number for tracking changes
    deleted_at = Column(DateTime, nullable=True)  # Soft delete for versioning
    modified_by = Column(String, nullable=True)  # Who made the modification
    modification_reason = Column(Text, nullable=True)  # Why the modification was made
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Allow multiple versions, but only one active version per bank/product
    __table_args__ = (
        UniqueConstraint('bank_name', 'product_type', 'deleted_at', name='_bank_product_version_uc'),
    )

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    state = Column(JSON, nullable=True, default=lambda: {})

    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")
    pending_modifications = relationship("PendingWorkflowModification", back_populates="conversation", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(PG_UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    sender_type = Column(SQLAlchemyEnum(SenderType), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")

class PendingWorkflowModification(Base):
    __tablename__ = "pending_workflow_modifications"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(PG_UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    user_id = Column(String, nullable=False)
    bank_name = Column(String, nullable=False)  # Changed from 'bank' to match Workflow model
    product_type = Column(String, nullable=False)  # Changed from 'product' to match Workflow model
    modification_data = Column(JSON, nullable=False)  # Store the complete pending modification
    created_at = Column(DateTime, default=datetime.utcnow)
    # Removed expires_at column to fix database schema issues
    
    conversation = relationship("Conversation", back_populates="pending_modifications")


# --- Database Functions ---
def create_tables():
    Base.metadata.create_all(bind=engine)

# Customer Management Functions
def generate_customer_id(bank_name: str) -> str:
    """Generate a unique customer ID based on bank name"""
    import secrets
    
    # Bank prefix mapping
    bank_prefixes = {
        "federal": "CI-SH-FED-",
        "federalbank": "CI-SH-FED-",
        "federal_bank": "CI-SH-FED-",
        "dhanlaxmi": "CI-SH-DLXB-",
        "dhanlaxmibank": "CI-SH-DLXB-",
        "dhanlaxmi_bank": "CI-SH-DLXB-",
        "default": "CI-SH-GEN-"
    }
    
    prefix = bank_prefixes.get(bank_name.lower(), bank_prefixes["default"])
    unique_id = secrets.token_hex(6)  # 12 character hex string
    return f"{prefix}{unique_id}"

def create_customer(name: str, bank_name: str, mobile_number: str = None, email: str = None, product_type: str = None) -> Customer:
    """Create a new customer record"""
    db = SessionLocal()
    try:
        customer_id = generate_customer_id(bank_name)
        
        # Ensure unique customer ID
        while db.query(Customer).filter(Customer.id == customer_id).first():
            customer_id = generate_customer_id(bank_name)
        
        customer = Customer(
            id=customer_id,
            name=name,
            mobile_number=mobile_number,
            email=email,
            bank_name=bank_name,
            product_type=product_type
        )
        
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer
    finally:
        db.close()

def get_customer_by_id(customer_id: str) -> Customer:
    """Get customer by ID"""
    db = SessionLocal()
    try:
        return db.query(Customer).filter(Customer.id == customer_id).first()
    finally:
        db.close()

def get_customer_by_mobile(mobile_number: str) -> Customer:
    """Get customer by mobile number"""
    db = SessionLocal()
    try:
        return db.query(Customer).filter(Customer.mobile_number == mobile_number).first()
    finally:
        db.close()

def search_customers(name: str = None, mobile_number: str = None, bank_name: str = None) -> list[Customer]:
    """Search customers by various criteria"""
    db = SessionLocal()
    try:
        query = db.query(Customer)
        
        if name:
            query = query.filter(Customer.name.ilike(f"%{name}%"))
        if mobile_number:
            query = query.filter(Customer.mobile_number == mobile_number)
        if bank_name:
            query = query.filter(Customer.bank_name.ilike(f"%{bank_name}%"))
        
        return query.all()
    finally:
        db.close()

# Workflow Session Management Functions
def create_workflow_session(customer_id: str, bank_name: str, product_type: str, flow_type: str, current_action_id: str = "welcome") -> WorkflowSession:
    """Create a new workflow session for a customer"""
    db = SessionLocal()
    try:
        # Check if there's an active session for this customer and product
        existing_session = db.query(WorkflowSession).filter(
            WorkflowSession.customer_id == customer_id,
            WorkflowSession.bank_name == bank_name,
            WorkflowSession.product_type == product_type,
            WorkflowSession.status == "active"
        ).first()
        
        if existing_session:
            return existing_session
        
        session = WorkflowSession(
            customer_id=customer_id,
            bank_name=bank_name,
            product_type=product_type,
            current_action_id=current_action_id,
            flow_type=flow_type,
            session_data={"started_at": datetime.utcnow().isoformat()}
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    finally:
        db.close()

def get_workflow_session(session_id: str) -> WorkflowSession:
    """Get workflow session by ID"""
    db = SessionLocal()
    try:
        return db.query(WorkflowSession).filter(WorkflowSession.id == session_id).first()
    finally:
        db.close()

def get_active_workflow_session(customer_id: str, bank_name: str, product_type: str) -> WorkflowSession:
    """Get active workflow session for customer and product"""
    db = SessionLocal()
    try:
        return db.query(WorkflowSession).filter(
            WorkflowSession.customer_id == customer_id,
            WorkflowSession.bank_name == bank_name,
            WorkflowSession.product_type == product_type,
            WorkflowSession.status == "active"
        ).first()
    finally:
        db.close()

def update_workflow_session(session_id: str, current_action_id: str = None, session_data: dict = None, status: str = None) -> WorkflowSession:
    """Update workflow session state"""
    db = SessionLocal()
    try:
        session = db.query(WorkflowSession).filter(WorkflowSession.id == session_id).first()
        if not session:
            return None
        
        if current_action_id:
            session.current_action_id = current_action_id
        
        if session_data:
            # Merge with existing session data
            existing_data = session.session_data or {}
            existing_data.update(session_data)
            session.session_data = existing_data
        
        if status:
            session.status = status
            if status == "completed":
                session.completed_at = datetime.utcnow()
        
        session.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(session)
        return session
    finally:
        db.close()

def get_workflow_details(bank: str, product: str):
    """Get workflow details for a specific bank and product (active version only)"""
    db = SessionLocal()
    try:
        workflow = db.query(Workflow).filter(
            Workflow.bank_name == bank,
            Workflow.product_type == product,
            Workflow.is_active == True,
            Workflow.deleted_at.is_(None)  # Only get non-deleted workflows
        ).first()
        
        if workflow:
            return {
                'action_schema': workflow.action_schema,
                'ui_schema': workflow.ui_schema,
                'api_schema': workflow.api_schema,
                'version': workflow.version,
                'id': workflow.id
            }
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

# Workflow Modification Functions
def get_workflow_sequence_preview(bank: str, product: str):
    """Get current workflow sequence in plain English for preview"""
    workflow_details = get_workflow_details(bank, product)
    if not workflow_details:
        return None
    
    action_schema = workflow_details['action_schema']
    sequence = []
    
    # Start from the first action (usually welcome or kcc-welcome)
    current_action = None
    for action in action_schema:
        if action['id'] in ['welcome', 'kcc-welcome']:
            current_action = action
            break
    
    if not current_action:
        current_action = action_schema[0]  # Fallback to first action
    
    visited = set()
    while current_action and current_action['id'] not in visited:
        visited.add(current_action['id'])
        sequence.append({
            'step': len(sequence) + 1,
            'action_id': current_action['id'],
            'stage_name': current_action.get('stage_name', current_action['id']),
            'description': current_action.get('desc_for_llm', '')
        })
        
        # Find next action
        next_action_id = current_action.get('next_success_action_id')
        if next_action_id:
            current_action = next((a for a in action_schema if a['id'] == next_action_id), None)
        else:
            break
    
    return {
        'bank': bank,
        'product': product,
        'version': workflow_details['version'],
        'sequence': sequence
    }

def create_modified_workflow(bank: str, product: str, new_action_schema: list, 
                           modified_by: str, modification_reason: str):
    """Create a new version of workflow with modifications"""
    db = SessionLocal()
    try:
        # Get current active workflow
        current_workflow = db.query(Workflow).filter(
            Workflow.bank_name == bank,
            Workflow.product_type == product,
            Workflow.is_active == True,
            Workflow.deleted_at.is_(None)
        ).first()
        
        if not current_workflow:
            return {'success': False, 'error': f'No active workflow found for {bank} {product}'}
        
        # Soft delete current workflow
        current_workflow.deleted_at = datetime.utcnow()
        current_workflow.is_active = False
        
        # Create new workflow version
        new_workflow = Workflow(
            bank_name=bank,
            product_type=product,
            action_schema=new_action_schema,
            ui_schema=current_workflow.ui_schema,  # Keep same UI schema
            api_schema=current_workflow.api_schema,  # Keep same API schema
            is_active=True,
            version=current_workflow.version + 1,
            modified_by=modified_by,
            modification_reason=modification_reason
        )
        
        db.add(new_workflow)
        db.commit()
        
        return {
            'success': True,
            'new_version': new_workflow.version,
            'workflow_id': new_workflow.id,
            'message': f'Successfully created workflow version {new_workflow.version} for {bank} {product}'
        }
        
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()

def get_workflow_modification_history(bank: str, product: str):
    """Get modification history for a workflow"""
    db = SessionLocal()
    try:
        workflows = db.query(Workflow).filter(
            Workflow.bank_name == bank,
            Workflow.product_type == product
        ).order_by(Workflow.version.desc()).all()
        
        history = []
        for workflow in workflows:
            history.append({
                'version': workflow.version,
                'is_active': workflow.is_active and workflow.deleted_at is None,
                'created_at': workflow.created_at.isoformat(),
                'modified_by': workflow.modified_by,
                'modification_reason': workflow.modification_reason,
                'deleted_at': workflow.deleted_at.isoformat() if workflow.deleted_at else None
            })
        
        return history
    finally:
        db.close()

# Pending Workflow Modification Functions
def store_pending_workflow_modification(conversation_id: str, user_id: str, bank_name: str, product_type: str, modification_data: dict) -> bool:
    """Store a pending workflow modification in the database"""
    import uuid
    db = SessionLocal()
    try:
        # Convert conversation_id string to UUID
        conversation_uuid = uuid.UUID(conversation_id) if isinstance(conversation_id, str) else conversation_id
        
        # Clear any existing pending modifications for this conversation/user
        db.query(PendingWorkflowModification).filter(
            PendingWorkflowModification.conversation_id == conversation_uuid,
            PendingWorkflowModification.user_id == user_id
        ).delete()
        
        # Create new pending modification
        pending_mod = PendingWorkflowModification(
            conversation_id=conversation_uuid,
            user_id=user_id,
            bank_name=bank_name,
            product_type=product_type,
            modification_data=modification_data
        )
        
        db.add(pending_mod)
        db.commit()
        print(f"✅ Stored pending workflow modification for conversation {conversation_id}")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error storing pending modification: {e}")
        return False
    finally:
        db.close()

def get_pending_workflow_modification(conversation_id: str, user_id: str) -> dict:
    """Retrieve a pending workflow modification from the database"""
    import uuid
    db = SessionLocal()
    try:
        # Convert conversation_id string to UUID
        conversation_uuid = uuid.UUID(conversation_id) if isinstance(conversation_id, str) else conversation_id
        
        # Skip expired cleanup for now since expires_at column may not exist
        # TODO: Add proper database migration for expires_at column
        
        # Get the pending modification
        pending_mod = db.query(PendingWorkflowModification).filter(
            PendingWorkflowModification.conversation_id == conversation_uuid,
            PendingWorkflowModification.user_id == user_id
        ).first()
        
        if pending_mod:
            print(f"✅ Found pending workflow modification for conversation {conversation_id}")
            # Return complete record structure including database columns
            return {
                'id': str(pending_mod.id),
                'conversation_id': str(pending_mod.conversation_id),
                'user_id': pending_mod.user_id,
                'bank_name': pending_mod.bank_name,
                'product_type': pending_mod.product_type,
                'modification_data': pending_mod.modification_data,
                'created_at': pending_mod.created_at.isoformat() if pending_mod.created_at else None
            }
        else:
            print(f"❌ No pending workflow modification found for conversation {conversation_id}")
            return None
            
    except Exception as e:
        print(f"❌ Error retrieving pending modification: {e}")
        return None
    finally:
        db.close()

def clear_pending_workflow_modification(conversation_id: str, user_id: str) -> bool:
    """Clear a pending workflow modification from the database"""
    import uuid
    db = SessionLocal()
    try:
        # Convert conversation_id string to UUID
        conversation_uuid = uuid.UUID(conversation_id) if isinstance(conversation_id, str) else conversation_id
        
        deleted_count = db.query(PendingWorkflowModification).filter(
            PendingWorkflowModification.conversation_id == conversation_uuid,
            PendingWorkflowModification.user_id == user_id
        ).delete()
        
        db.commit()
        print(f"✅ Cleared {deleted_count} pending workflow modification(s) for conversation {conversation_id}")
        return deleted_count > 0
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error clearing pending modification: {e}")
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
