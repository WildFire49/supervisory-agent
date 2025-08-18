# Retrieval Agent Configurator - Frontend Integration Guide

## Overview

This guide provides everything you need to build a frontend for the Retrieval Agent Configurator system. The backend provides a comprehensive API for configuring database connections, analyzing schemas, and setting up RAG-based SQL query generation.

## API Base URL

```
http://localhost:8000/configurator
```

## Authentication

All API endpoints require a `user_id` parameter to identify the user. This should be passed as a query parameter or in the request body as appropriate.

## API Endpoints Reference

### 1. Database Connection Management

#### Create Database Connection
```http
POST /configurator/connections?user_id={user_id}
Content-Type: application/json

{
  "connection_name": "My PostgreSQL DB",
  "database_type": "postgresql",
  "host": "localhost",
  "port": 5432,
  "database_name": "mydb",
  "username": "user",
  "password": "password",
  "ssl_enabled": false,
  "connection_params": {}
}

Response:
{
  "connection_id": "uuid-string",
  "status": "created"
}
```

#### List User Connections
```http
GET /configurator/connections?user_id={user_id}

Response:
[
  {
    "id": "uuid-string",
    "name": "My PostgreSQL DB",
    "database_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database_name": "mydb",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### Test Database Connection
```http
POST /configurator/connections/test
Content-Type: application/json

{
  "connection_details": {
    "connection_name": "Test Connection",
    "database_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database_name": "testdb",
    "username": "user",
    "password": "password",
    "ssl_enabled": false
  }
}

Response:
{
  "success": true,
  "message": "Connection successful",
  "connection_time": 0.5
}
```

### 2. Configuration Session Management

#### Create Configuration Session
```http
POST /configurator/sessions?user_id={user_id}
Content-Type: application/json

{
  "connection_id": "uuid-string"  // optional
}

Response:
{
  "session_id": "uuid-string",
  "status": "in_progress",
  "current_step": "connection_setup",
  "completion_percentage": 0.0
}
```

#### Get Session Status
```http
GET /configurator/sessions/{session_id}

Response:
{
  "session_id": "uuid-string",
  "status": "in_progress",
  "current_step": "schema_analysis",
  "completion_percentage": 40.0,
  "data": {
    "database_name": "mydb",
    "table_count": 15,
    "view_count": 3
  }
}
```

#### Run Configuration Step
```http
POST /configurator/sessions/{session_id}/configure
Content-Type: application/json

// For connection setup:
{
  "connection_details": {
    "connection_name": "My DB",
    "database_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database_name": "mydb",
    "username": "user",
    "password": "password",
    "ssl_enabled": false
  }
}

// For user schema input:
{
  "user_schema_input": {
    "business_rules": ["Rule 1", "Rule 2"],
    "table_descriptions": {
      "users": "User account information",
      "orders": "Customer orders"
    },
    "column_descriptions": {
      "users.email": "User email address",
      "orders.total": "Order total amount"
    },
    "additional_context": "This is an e-commerce database"
  }
}

Response:
{
  "status": "success",
  "session_id": "uuid-string",
  "current_step": "vector_storage",
  "data": {
    "message": "Schema analyzed successfully",
    "table_count": 15,
    "relationship_count": 8
  },
  "error": null
}
```

### 3. Schema and Query Management

#### Submit User Schema Input
```http
POST /configurator/sessions/{session_id}/user-input
Content-Type: application/json

{
  "connection_id": "uuid-string",
  "business_rules": [
    "Users can have multiple orders",
    "Orders must have a valid user_id"
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
}

Response:
{
  "status": "success",
  "message": "User input submitted successfully"
}
```

#### Get Test Queries
```http
GET /configurator/connections/{connection_id}/test-queries

Response:
[
  {
    "query_id": "query-uuid",
    "sql_query": "SELECT COUNT(*) FROM users WHERE created_at > '2024-01-01'",
    "natural_language_question": "How many users were created after January 1, 2024?",
    "expected_result_type": "single row",
    "confidence_score": 0.95,
    "validated": null,
    "validation_notes": null
  }
]
```

#### Validate Query Result
```http
POST /configurator/queries/validate
Content-Type: application/json

{
  "connection_id": "uuid-string",
  "query_id": "query-uuid",
  "is_valid": true,
  "validation_notes": "Query returned expected result format"
}

Response:
{
  "status": "success",
  "message": "Query validation recorded",
  "query_id": "query-uuid",
  "is_valid": true
}
```

#### Search Schema Information
```http
GET /configurator/connections/{connection_id}/schema-search?query=user%20table&limit=5

Response:
{
  "query": "user table",
  "results": [
    {
      "content": "Table: users\nColumns: id, email, name, created_at...",
      "metadata": {
        "type": "table",
        "table_name": "users"
      },
      "similarity_score": 0.95
    }
  ]
}
```

### 4. Health Check
```http
GET /configurator/health

Response:
{
  "status": "healthy",
  "components": {
    "database": "healthy",
    "vector_store": "healthy"
  }
}
```

## Supported Database Types

```typescript
enum DatabaseType {
  POSTGRESQL = "postgresql",
  MYSQL = "mysql",
  SQLITE = "sqlite",
  ORACLE = "oracle",
  MSSQL = "mssql",
  MONGODB = "mongodb"
}
```

## Frontend User Flow

### Step 1: Database Connection Setup
1. **Connection Selection**: Show existing connections or create new one
2. **Connection Form**: Database type, host, port, credentials
3. **Test Connection**: Validate connection before proceeding
4. **Connection Creation**: Save connection for future use

### Step 2: Schema Analysis
1. **Automatic Analysis**: Backend analyzes database schema
2. **Schema Overview**: Display tables, columns, relationships
3. **Progress Indicator**: Show analysis progress

### Step 3: User Input Collection
1. **Business Rules**: Text area for business logic
2. **Table Descriptions**: Key-value pairs for table descriptions
3. **Column Descriptions**: Key-value pairs for important columns
4. **Data Quality Notes**: Known issues or constraints
5. **Additional Context**: Free-form context about the database

### Step 4: Vector Storage
1. **Progress Indicator**: Show embedding creation progress
2. **Status Updates**: Real-time updates on storage process

### Step 5: Query Generation
1. **Generated Queries**: Display test queries with confidence scores
2. **Query Preview**: Show SQL and natural language description
3. **Query Validation**: Allow user to mark queries as valid/invalid

### Step 6: Validation Report
1. **Confidence Score**: Overall system confidence
2. **Coverage Analysis**: What's covered and what's missing
3. **Recommendations**: Suggestions for improvement
4. **Production Readiness**: Assessment of readiness

## Frontend Component Structure

```
ConfiguratorDashboard/
├── DatabaseConnectionForm/
│   ├── ConnectionSelector
│   ├── ConnectionForm
│   └── ConnectionTest
├── SchemaAnalysisView/
│   ├── SchemaOverview
│   ├── TableList
│   └── RelationshipDiagram
├── UserInputForm/
│   ├── BusinessRulesInput
│   ├── TableDescriptions
│   ├── ColumnDescriptions
│   └── AdditionalContext
├── TestQueriesView/
│   ├── QueryList
│   ├── QueryPreview
│   └── QueryValidation
└── ValidationReport/
    ├── ConfidenceMetrics
    ├── CoverageAnalysis
    └── RecommendationsList
```

## State Management

```typescript
interface ConfiguratorState {
  // Session Management
  currentSession: ConfigurationSession | null;
  activeStep: number;
  loading: boolean;
  error: string | null;
  
  // Database Connections
  connections: DatabaseConnection[];
  selectedConnection: DatabaseConnection | null;
  
  // Schema Data
  schemaData: DatabaseSchema | null;
  userInput: UserSchemaInput | null;
  
  // Queries and Validation
  testQueries: TestQuery[];
  validationReport: ValidationReport | null;
  
  // UI State
  stepperCompleted: boolean[];
  notifications: Notification[];
}
```

## Key UI/UX Requirements

### Design System
- Use Material-UI components for consistency
- Responsive design with MUI Grid system
- Material Icons (no emojis)
- Tooltips for helper text and guidance
- Loading states and progress indicators

### User Experience
1. **Progressive Disclosure**: Show information as needed
2. **Clear Navigation**: Step-by-step wizard interface
3. **Validation Feedback**: Real-time validation and error messages
4. **Progress Tracking**: Visual progress indicators
5. **Help System**: Contextual help and tooltips

### Accessibility
- ARIA labels for screen readers
- Keyboard navigation support
- High contrast mode compatibility
- Focus management

## Error Handling

```typescript
interface ApiError {
  status: number;
  message: string;
  details?: any;
}

// Common error scenarios:
// - Connection timeout
// - Invalid credentials
// - Schema analysis failure
// - Vector storage issues
// - Query generation errors
```

## Testing Strategy

### Frontend Testing
1. **Unit Tests**: Component logic and API calls
2. **Integration Tests**: End-to-end user flows
3. **Accessibility Tests**: Screen reader and keyboard navigation
4. **Responsive Tests**: Mobile and desktop layouts

### API Testing
1. **Connection Testing**: All database types
2. **Schema Analysis**: Various database structures
3. **Error Scenarios**: Network failures, invalid data
4. **Performance**: Large schema handling

## Production Considerations

### Security
- Encrypt database passwords in storage
- Use HTTPS for all API calls
- Implement proper authentication/authorization
- Sanitize user inputs

### Performance
- Lazy loading for large schema data
- Pagination for query lists
- Debounced search inputs
- Optimistic UI updates

### Monitoring
- Track user completion rates
- Monitor API response times
- Log configuration errors
- Analytics on database types used

## Sample Frontend Implementation Snippets

### API Service Layer
```typescript
class ConfiguratorApiService {
  private baseUrl = 'http://localhost:8000/configurator';
  
  async createConnection(userId: string, connection: DatabaseConnectionRequest) {
    const response = await fetch(`${this.baseUrl}/connections?user_id=${userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(connection)
    });
    return response.json();
  }
  
  async testConnection(connectionDetails: DatabaseConnectionRequest) {
    const response = await fetch(`${this.baseUrl}/connections/test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ connection_details: connectionDetails })
    });
    return response.json();
  }
  
  // ... other methods
}
```

### React Hook for Configuration
```typescript
const useConfigurator = (userId: string) => {
  const [state, setState] = useState<ConfiguratorState>(initialState);
  
  const createSession = async (connectionId?: string) => {
    setState(prev => ({ ...prev, loading: true }));
    try {
      const session = await api.createSession(userId, connectionId);
      setState(prev => ({ ...prev, currentSession: session, loading: false }));
    } catch (error) {
      setState(prev => ({ ...prev, error: error.message, loading: false }));
    }
  };
  
  const runConfigurationStep = async (stepData: any) => {
    // Implementation
  };
  
  return {
    ...state,
    createSession,
    runConfigurationStep,
    // ... other methods
  };
};
```

This comprehensive guide provides everything needed to build a production-ready frontend for the Retrieval Agent Configurator system. The backend is fully implemented and ready to support your frontend development!
