"""
Business Rules Models for Template System
Stores domain-specific business rules extracted from schema analysis
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
import uuid


class RuleCategory(str, Enum):
    """Categories of business rules"""
    TABLE_USAGE = "table_usage"           # Which tables to use/avoid for specific contexts
    DATE_FILTERING = "date_filtering"     # Date field usage rules
    JOIN_PATTERNS = "join_patterns"       # Required JOIN patterns
    DATA_PRECISION = "data_precision"     # Precision and formatting rules
    VALIDATION = "validation"             # Data validation rules
    LIFECYCLE = "lifecycle"               # Lifecycle stage rules
    CONTEXT_SEPARATION = "context_separation"  # Context-specific table separation


class RuleSeverity(str, Enum):
    """Severity levels for rule enforcement"""
    CRITICAL = "critical"     # Must be enforced, query fails if violated
    WARNING = "warning"       # Should be enforced, but not blocking
    SUGGESTION = "suggestion" # Optional best practice


class BusinessRule(BaseModel):
    """Individual business rule definition"""
    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    connection_id: str
    category: RuleCategory
    severity: RuleSeverity
    title: str
    description: str
    
    # Rule conditions and patterns
    trigger_patterns: List[str] = Field(default_factory=list)  # Keywords that trigger this rule
    table_patterns: List[str] = Field(default_factory=list)    # Table name patterns
    column_patterns: List[str] = Field(default_factory=list)   # Column name patterns
    
    # Rule actions
    allowed_tables: List[str] = Field(default_factory=list)    # Tables allowed for this context
    forbidden_tables: List[str] = Field(default_factory=list)  # Tables forbidden for this context
    required_joins: List[Dict[str, str]] = Field(default_factory=list)  # Required JOIN patterns
    date_field_mappings: Dict[str, str] = Field(default_factory=dict)   # Context -> date field mapping
    
    # SQL transformation rules
    sql_transformations: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.8)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Examples and validation
    positive_examples: List[str] = Field(default_factory=list)  # Good SQL examples
    negative_examples: List[str] = Field(default_factory=list)  # Bad SQL examples
    
    class Config:
        use_enum_values = True


class BusinessRuleTemplate(BaseModel):
    """Template for generating business rules for similar schemas"""
    template_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    domain: str  # e.g., "financial", "healthcare", "e-commerce"
    
    # Template patterns for rule extraction
    extraction_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Default rules that apply to this domain
    default_rules: List[BusinessRule] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class RuleValidationResult(BaseModel):
    """Result of validating a query against business rules"""
    is_valid: bool
    violated_rules: List[BusinessRule] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    corrected_sql: Optional[str] = None


class RuleExtractionRequest(BaseModel):
    """Request for extracting business rules from schema"""
    connection_id: str
    schema_context: str
    domain_hints: List[str] = Field(default_factory=list)
    existing_rules: List[BusinessRule] = Field(default_factory=list)


class RuleExtractionResponse(BaseModel):
    """Response from rule extraction process"""
    extracted_rules: List[BusinessRule]
    confidence_score: float
    extraction_notes: str
    suggested_template: Optional[BusinessRuleTemplate] = None


class TestQuery(BaseModel):
    """Test query generated for validation"""
    query_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    connection_id: str
    sql_query: str
    description: str
    expected_result_type: str = "rows"  # "rows", "single_value", "count", etc.
    confidence_score: float = 0.8
    business_context: str = ""
    validation_notes: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
