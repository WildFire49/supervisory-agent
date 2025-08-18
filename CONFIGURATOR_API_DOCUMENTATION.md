# Retrieval Agent Configurator API Documentation

## Overview

The Configurator API provides comprehensive functionality for setting up RAG-based SQL query generation systems. It handles database connections, schema analysis, user input collection, vector storage, and validation.

## Database Schema Status

The configurator creates the following PostgreSQL tables automatically:

```sql
-- Database connections storage
CREATE TABLE retrieval_database_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    database_type VARCHAR NOT NULL,
    host VARCHAR NOT NULL,
    port INTEGER NOT NULL,
    database_name VARCHAR NOT NULL,
    username VARCHAR NOT NULL,
    password VARCHAR NOT NULL, -- Encrypted in production
    ssl_enabled BOOLEAN DEFAULT FALSE,
    connection_params JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Schema information storage
CREATE TABLE retrieval_database_schemas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID NOT NULL,
    database_name VARCHAR NOT NULL,
    schema_data JSONB NOT NULL,
    schema_notes TEXT,
    version VARCHAR DEFAULT '1.0',
    gathered_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- User input storage
CREATE TABLE retrieval_user_schema_inputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID NOT NULL,
    user_id VARCHAR NOT NULL,
    input_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Configuration sessions
CREATE TABLE retrieval_configuration_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR UNIQUE NOT NULL,
    user_id VARCHAR NOT NULL,
    connection_id UUID,
    status VARCHAR NOT NULL DEFAULT 'in_progress',
    current_step VARCHAR NOT NULL,
    session_data JSONB DEFAULT '{}',
    schema_gathered BOOLEAN DEFAULT FALSE,
    user_input_collected BOOLEAN DEFAULT FALSE,
    vector_db_indexed BOOLEAN DEFAULT FALSE,
    test_queries_generated BOOLEAN DEFAULT FALSE,
    completion_percentage FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Test queries storage
CREATE TABLE retrieval_test_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id VARCHAR UNIQUE NOT NULL,
    connection_id UUID NOT NULL,
    sql_query TEXT NOT NULL,
    natural_language_question TEXT NOT NULL,
    expected_result_type VARCHAR NOT NULL,
    confidence_score FLOAT NOT NULL,
    validated BOOLEAN,
    validation_notes TEXT,
    generated_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Complete configurations
CREATE TABLE retrieval_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id VARCHAR UNIQUE NOT NULL,
    user_id VARCHAR NOT NULL,
    connection_id UUID NOT NULL,
    configuration_data JSONB NOT NULL,
    vector_embeddings_id VARCHAR,
    status VARCHAR NOT NULL DEFAULT 'configuring',
    is_production_ready BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## API Base URL

```
http://localhost:8000/configurator
```

## cURL Examples

### 1. Health Check

```bash
curl -X GET "http://localhost:8000/configurator/health" \
  -H "accept: application/json"
```

**Response:**
```json
{
  "status": "healthy",
  "components": {
    "database": "healthy",
    "vector_store": "healthy"
  }
}
```

### 2. Create Database Connection

```bash
curl -X POST "http://localhost:8000/configurator/connections?user_id=user123" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "connection_name": "Production PostgreSQL",
    "database_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database_name": "ecommerce_prod",
    "username": "db_user",
    "password": "secure_password",
    "ssl_enabled": true,
    "connection_params": {
      "sslmode": "require",
      "connect_timeout": 10
    }
  }'
```

**Response:**
```json
{
  "connection_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "created"
}
```

### 3. Test Database Connection

```bash
curl -X POST "http://localhost:8000/configurator/connections/test" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "connection_details": {
      "connection_name": "Test Connection",
      "database_type": "postgresql",
      "host": "localhost",
      "port": 5432,
      "database_name": "testdb",
      "username": "test_user",
      "password": "test_password",
      "ssl_enabled": false
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Connection successful",
  "connection_time": 0.5
}
```

### 4. List User Connections

```bash
curl -X GET "http://localhost:8000/configurator/connections?user_id=user123" \
  -H "accept: application/json"
```

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Production PostgreSQL",
    "database_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database_name": "ecommerce_prod",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

### 5. Create Configuration Session

```bash
curl -X POST "http://localhost:8000/configurator/sessions?user_id=user123" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "connection_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

**Response:**
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "in_progress",
  "current_step": "connection_setup",
  "completion_percentage": 0.0
}
```

### 6. Run Configuration Step (Connection Setup)

```bash
curl -X POST "http://localhost:8000/configurator/sessions/123e4567-e89b-12d3-a456-426614174000/configure" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "connection_details": {
      "connection_name": "My Database",
      "database_type": "postgresql",
      "host": "localhost",
      "port": 5432,
      "database_name": "mydb",
      "username": "user",
      "password": "password",
      "ssl_enabled": false
    }
  }'
```

**Response:**
```json
{
  "status": "success",
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "current_step": "schema_analysis",
  "data": {
    "message": "Database connection successful",
    "database_name": "mydb",
    "table_count": 15,
    "view_count": 3
  },
  "error": null
}
```

### 7. Submit User Schema Input

```bash
curl -X POST "http://localhost:8000/configurator/sessions/123e4567-e89b-12d3-a456-426614174000/user-input" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "connection_id": "550e8400-e29b-41d4-a716-446655440000",
    "business_rules": [
      "Users can have multiple orders",
      "Orders must have a valid user_id",
      "Products can be in multiple categories"
    ],
    "table_descriptions": {
      "users": "Customer account information",
      "orders": "Purchase orders",
      "products": "Product catalog"
    },
    "column_descriptions": {
      "users.email": "Customer email address (unique)",
      "orders.total": "Order total in USD",
      "products.price": "Product price in USD"
    },
    "data_quality_notes": [
      "Some old orders may have null user_id",
      "Email validation was added in 2023"
    ],
    "additional_context": "E-commerce platform with 100K+ users"
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "User input submitted successfully"
}
```

### 8. Get Configuration Session Status

```bash
curl -X GET "http://localhost:8000/configurator/sessions/123e4567-e89b-12d3-a456-426614174000" \
  -H "accept: application/json"
```

**Response:**
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "in_progress",
  "current_step": "query_generation",
  "completion_percentage": 80.0,
  "data": {
    "database_name": "mydb",
    "table_count": 15,
    "relationship_count": 8,
    "queries_generated": 10
  }
}
```

### 9. Get Test Queries

```bash
curl -X GET "http://localhost:8000/configurator/connections/550e8400-e29b-41d4-a716-446655440000/test-queries" \
  -H "accept: application/json"
```

**Response:**
```json
[
  {
    "query_id": "query_001",
    "sql_query": "SELECT COUNT(*) FROM users WHERE created_at > '2024-01-01'",
    "natural_language_question": "How many users were created after January 1, 2024?",
    "expected_result_type": "single row",
    "confidence_score": 0.95,
    "validated": null,
    "validation_notes": null
  },
  {
    "query_id": "query_002",
    "sql_query": "SELECT u.email, COUNT(o.id) as order_count FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id, u.email ORDER BY order_count DESC LIMIT 10",
    "natural_language_question": "Who are the top 10 customers by number of orders?",
    "expected_result_type": "multiple rows",
    "confidence_score": 0.88,
    "validated": null,
    "validation_notes": null
  }
]
```

### 10. Validate Query Result

```bash
curl -X POST "http://localhost:8000/configurator/queries/validate" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "connection_id": "550e8400-e29b-41d4-a716-446655440000",
    "query_id": "query_001",
    "is_valid": true,
    "validation_notes": "Query returned expected result format"
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Query validation recorded",
  "query_id": "query_001",
  "is_valid": true
}
```

### 11. Search Schema Information

```bash
curl -X GET "http://localhost:8000/configurator/connections/550e8400-e29b-41d4-a716-446655440000/schema-search?query=user%20table&limit=5" \
  -H "accept: application/json"
```

**Response:**
```json
{
  "query": "user table",
  "results": [
    {
      "content": "Table: users\nDatabase: mydb\nRow Count: 150000\nPrimary Keys: id\n\nColumns (12):\n- id: integer (NOT NULL)\n- email: varchar (NOT NULL)\n- name: varchar\n- created_at: timestamp DEFAULT now()",
      "metadata": {
        "type": "table",
        "connection_id": "550e8400-e29b-41d4-a716-446655440000",
        "database_name": "mydb",
        "table_name": "users",
        "column_count": 12,
        "row_count": 150000
      },
      "similarity_score": 0.95
    }
  ]
}
```

## Supported Database Types

| Database Type | Connection String Format | Required Dependencies |
|---------------|-------------------------|----------------------|
| PostgreSQL | `postgresql://user:pass@host:port/db` | `psycopg2-binary` |
| MySQL | `mysql+pymysql://user:pass@host:port/db` | `pymysql` |
| SQLite | `sqlite:///path/to/db.sqlite` | Built-in |
| Oracle | `oracle+cx_oracle://user:pass@host:port/db` | `cx_oracle` |
| SQL Server | `mssql+pyodbc://user:pass@host:port/db` | `pyodbc` |
| MongoDB | `mongodb://user:pass@host:port/db` | `pymongo` |

## Configuration Workflow

### Step 1: Database Connection (0-20%)
- Create or select database connection
- Test connection validity
- Store connection details securely

### Step 2: Schema Analysis (20-40%)
- Extract table structures
- Identify relationships and constraints
- Analyze data types and indexes
- Detect enums and custom types

### Step 3: User Input Collection (40-60%)
- Collect business rules
- Gather table/column descriptions
- Document data quality notes
- Add performance considerations

### Step 4: Vector Storage (60-80%)
- Create embeddings for schema information
- Store in ChromaDB for semantic search
- Index relationships and metadata

### Step 5: Query Generation (80-90%)
- Generate test queries using AI
- Create natural language descriptions
- Assign confidence scores
- Validate query correctness

### Step 6: Validation & Completion (90-100%)
- Generate confidence report
- Assess production readiness
- Provide recommendations
- Complete configuration

## Error Handling

All endpoints return standardized error responses:

```json
{
  "detail": "Error message description",
  "status_code": 400,
  "error_type": "validation_error",
  "context": {
    "field": "database_type",
    "value": "invalid_type"
  }
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (validation errors)
- `404`: Not Found (session/connection not found)
- `500`: Internal Server Error

## Security Considerations

### Production Deployment:
1. **Encrypt Database Passwords**: Use proper encryption for stored credentials
2. **Use HTTPS**: All API calls should use SSL/TLS
3. **Authentication**: Implement proper user authentication
4. **Authorization**: Validate user permissions for database access
5. **Input Validation**: Sanitize all user inputs
6. **Rate Limiting**: Implement API rate limiting
7. **Audit Logging**: Log all configuration activities

### Environment Variables:
```bash
# Required for configurator
DATABASE_URL=postgresql://user:pass@localhost:5432/supervisory_agent
OPENAI_API_KEY=your_openai_api_key
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Optional for enhanced features
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
SENTRY_DSN=your_sentry_dsn
```

## Monitoring and Analytics

The configurator provides built-in monitoring:

### Health Checks:
- Database connectivity
- Vector store status
- API response times

### Metrics:
- Configuration completion rates
- Database type usage
- Query generation success rates
- User satisfaction scores

### Logging:
- All configuration steps
- Error conditions
- Performance metrics
- User interactions

## Integration with Main Chat System

You can also use the configurator through the main chat interface:

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "message": "I want to configure a database connection for RAG",
    "conversation_id": "conv123"
  }'
```

The supervisor agent will route to the configurator automatically when it detects configuration-related requests.

## Next Steps

1. **Initialize Database**: Run `python3 init_configurator_db.py` to create tables
2. **Install Dependencies**: `pip install -r requirements.txt`
3. **Start Server**: `uvicorn app.main:app --reload`
4. **Test API**: Use the cURL examples above
5. **Build Frontend**: Use the integration guide to build your UI

The configurator is now ready for production use with comprehensive database support, AI-powered analysis, and robust error handling!
