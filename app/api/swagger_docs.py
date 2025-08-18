"""
Swagger/OpenAPI documentation for the Configurator API.
"""
from fastapi import FastAPI
from typing import Dict, List, Optional, Any

# Swagger documentation configuration
swagger_config = {
    "title": "Retrieval Agent Configurator API",
    "description": """
## Retrieval Agent Configurator API

This API provides comprehensive functionality for configuring database connections and setting up RAG-based SQL query generation systems.

### Key Features:
- **Multi-Database Support**: PostgreSQL, MySQL, SQLite, Oracle, MSSQL, MongoDB
- **Intelligent Schema Analysis**: Automatic extraction of tables, columns, relationships, and constraints
- **AI-Powered Query Generation**: Generate test queries to validate understanding
- **Vector Storage**: Store schema information for semantic search and RAG
- **User Context Integration**: Collect business rules and domain knowledge
- **Production-Ready**: Session management, error handling, and monitoring

### Workflow:
1. **Database Connection**: Create and test database connections
2. **Schema Analysis**: Automatically analyze database structure
3. **User Input**: Collect business context and domain knowledge
4. **Vector Storage**: Store schema information for RAG capabilities
5. **Query Generation**: Generate test queries for validation
6. **Validation**: Assess system understanding and production readiness

### Authentication:
All endpoints require a `user_id` parameter to identify the user making the request.

### Error Handling:
All endpoints return standardized error responses with appropriate HTTP status codes.
    """,
    "version": "1.0.0",
    "contact": {
        "name": "API Support",
        "email": "support@example.com"
    },
    "license": {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
}

# Enhanced API documentation with examples
api_examples = {
    "database_connection_request": {
        "connection_name": "Production PostgreSQL",
        "database_type": "postgresql",
        "host": "db.example.com",
        "port": 5432,
        "database_name": "ecommerce_prod",
        "username": "db_user",
        "password": "secure_password",
        "ssl_enabled": True,
        "connection_params": {
            "sslmode": "require",
            "connect_timeout": 10
        }
    },
    "user_schema_input": {
        "connection_id": "550e8400-e29b-41d4-a716-446655440000",
        "business_rules": [
            "Users can have multiple orders",
            "Orders must have a valid user_id",
            "Products can be in multiple categories",
            "Inventory tracking is real-time"
        ],
        "table_descriptions": {
            "users": "Customer account information and profiles",
            "orders": "Purchase orders with payment and shipping details",
            "products": "Product catalog with pricing and inventory",
            "categories": "Product categorization hierarchy",
            "order_items": "Individual items within orders"
        },
        "column_descriptions": {
            "users.email": "Customer email address (unique, required for login)",
            "users.created_at": "Account creation timestamp",
            "orders.total": "Order total amount in USD (includes tax and shipping)",
            "orders.status": "Order status: pending, confirmed, shipped, delivered, cancelled",
            "products.price": "Current product price in USD",
            "products.inventory_count": "Available inventory quantity"
        },
        "data_quality_notes": [
            "Some legacy orders (pre-2022) may have null user_id",
            "Email validation was implemented in 2023",
            "Price history is maintained in separate audit table",
            "Inventory counts are updated via external system"
        ],
        "performance_notes": [
            "Users table has 1M+ records, indexed on email",
            "Orders table partitioned by date",
            "Products table has full-text search on name/description"
        ],
        "security_considerations": [
            "User passwords are hashed with bcrypt",
            "PII data is encrypted at rest",
            "Payment information stored in separate secure vault"
        ],
        "additional_context": "E-commerce platform serving 100K+ active users with real-time inventory management and multi-channel order processing"
    },
    "configuration_session_response": {
        "session_id": "123e4567-e89b-12d3-a456-426614174000",
        "status": "in_progress",
        "current_step": "schema_analysis",
        "completion_percentage": 40.0,
        "data": {
            "database_name": "ecommerce_prod",
            "table_count": 15,
            "view_count": 3,
            "relationship_count": 12,
            "enum_count": 2,
            "tables": [
                {
                    "name": "users",
                    "column_count": 12,
                    "row_count": 150000,
                    "has_foreign_keys": False
                },
                {
                    "name": "orders",
                    "column_count": 8,
                    "row_count": 500000,
                    "has_foreign_keys": True
                }
            ]
        }
    },
    "test_queries_response": [
        {
            "query_id": "query_001",
            "sql_query": "SELECT COUNT(*) FROM users WHERE created_at > '2024-01-01'",
            "natural_language_question": "How many users were created after January 1, 2024?",
            "expected_result_type": "single row",
            "confidence_score": 0.95,
            "validated": None,
            "validation_notes": None
        },
        {
            "query_id": "query_002",
            "sql_query": "SELECT u.email, COUNT(o.id) as order_count FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id, u.email ORDER BY order_count DESC LIMIT 10",
            "natural_language_question": "Who are the top 10 customers by number of orders?",
            "expected_result_type": "multiple rows",
            "confidence_score": 0.88,
            "validated": None,
            "validation_notes": None
        }
    ],
    "validation_report": {
        "overall_confidence": 0.87,
        "readiness_assessment": "production_ready",
        "strengths": [
            "Complete schema coverage with all tables analyzed",
            "Strong relationship understanding with 95% accuracy",
            "Comprehensive business context provided",
            "High-confidence test queries generated"
        ],
        "weaknesses": [
            "Some legacy data quality issues identified",
            "Complex view definitions may need manual review"
        ],
        "recommendations": [
            "Implement data quality monitoring for legacy records",
            "Add more specific column descriptions for calculated fields",
            "Consider creating materialized views for complex queries"
        ],
        "risk_factors": [
            "Large table sizes may impact query performance",
            "Some nullable foreign keys require careful handling"
        ],
        "coverage_analysis": {
            "tables_covered": 15,
            "relationships_tested": 12,
            "data_types_validated": 25
        },
        "metrics": {
            "total_queries": 10,
            "average_confidence": 0.87,
            "validation_rate": 0.9,
            "complexity_breakdown": {
                "simple": 4,
                "medium": 5,
                "complex": 1
            }
        }
    }
}

def add_swagger_examples(app: FastAPI):
    """Add comprehensive examples to FastAPI app for better documentation."""
    
    # Update OpenAPI schema with examples
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        from fastapi.openapi.utils import get_openapi
        openapi_schema = get_openapi(
            title=swagger_config["title"],
            version=swagger_config["version"],
            description=swagger_config["description"],
            routes=app.routes,
        )
        
        # Add examples to schema
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        if "examples" not in openapi_schema["components"]:
            openapi_schema["components"]["examples"] = {}
        
        # Add all examples
        for key, value in api_examples.items():
            openapi_schema["components"]["examples"][key] = {
                "summary": f"Example {key.replace('_', ' ').title()}",
                "value": value
            }
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    return app
