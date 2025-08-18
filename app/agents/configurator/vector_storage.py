"""
Vector storage utilities for storing and retrieving database schema information.
"""
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.docstore.document import Document
from .models import DatabaseSchema, TableSchema, UserSchemaInput
from app.core.config import settings

logger = logging.getLogger(__name__)


class SchemaVectorStore:
    """Manages vector storage for database schema information."""
    
    def __init__(self, persist_directory: str = "./chroma_db_schemas"):
        self.persist_directory = persist_directory
        self.embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
        
        # Connect to remote ChromaDB instance
        try:
            self.client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT
            )
            logger.info(f"Connected to remote ChromaDB at {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")
        except Exception as e:
            logger.warning(f"Failed to connect to remote ChromaDB: {e}. Falling back to local instance.")
            self.client = chromadb.PersistentClient(path=persist_directory)
        
    def _get_collection_name(self, connection_id: str) -> str:
        """Generate collection name for a specific database connection."""
        return f"schema_{connection_id.replace('-', '_')}"
    
    async def store_database_schema(
        self, 
        connection_id: str, 
        schema: DatabaseSchema, 
        user_input: Optional[UserSchemaInput] = None
    ) -> bool:
        """Store database schema in vector database."""
        try:
            collection_name = self._get_collection_name(connection_id)
            
            # Create or get collection
            try:
                collection = self.client.get_collection(collection_name)
                # Clear existing data
                collection.delete()
            except:
                pass
            
            # Create collection with cosine similarity for text embeddings
            # ChromaDB's default is L2, but cosine is better for text semantic search
            from chromadb.utils import embedding_functions
            
            collection = self.client.create_collection(
                name=collection_name,
                metadata={
                    "connection_id": connection_id, 
                    "created_at": str(datetime.now()),
                    "hnsw:space": "cosine"  # Use cosine distance for text embeddings
                }
            )
            
            # Prepare documents for embedding
            documents = []
            metadatas = []
            ids = []
            
            # Store overall database information
            db_doc = self._create_database_overview_document(schema, user_input)
            documents.append(db_doc.page_content)
            metadatas.append(db_doc.metadata)
            ids.append(f"{connection_id}_overview")
            
            # Store table information
            for table in schema.tables:
                table_doc = self._create_table_document(table, schema, user_input)
                documents.append(table_doc.page_content)
                metadatas.append(table_doc.metadata)
                ids.append(f"{connection_id}_table_{table.table_name}")
                
                # Store column information for complex tables
                if len(table.columns) > 10:  # For large tables, create separate column documents
                    for i, column_group in enumerate(self._chunk_columns(table.columns, 5)):
                        col_doc = self._create_column_group_document(table.table_name, column_group, user_input)
                        documents.append(col_doc.page_content)
                        metadatas.append(col_doc.metadata)
                        ids.append(f"{connection_id}_table_{table.table_name}_cols_{i}")
            
            # Store relationship information
            if schema.relationships:
                rel_doc = self._create_relationships_document(schema.relationships, user_input)
                documents.append(rel_doc.page_content)
                metadatas.append(rel_doc.metadata)
                ids.append(f"{connection_id}_relationships")
            
            # Store enum and custom type information
            if schema.enums or schema.custom_types:
                types_doc = self._create_types_document(schema.enums, schema.custom_types)
                documents.append(types_doc.page_content)
                metadatas.append(types_doc.metadata)
                ids.append(f"{connection_id}_types")
            
            # Create embeddings and store
            embeddings = self.embeddings.embed_documents(documents)
            
            collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Successfully stored schema for connection {connection_id} with {len(documents)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Error storing schema in vector database: {str(e)}")
            return False
    
    def _create_database_overview_document(self, schema: DatabaseSchema, user_input: Optional[UserSchemaInput]) -> Document:
        """Create overview document for the database."""
        content = f"""
Database: {schema.database_name}
Connection ID: {schema.connection_id}
Total Tables: {len(schema.tables)}
Total Views: {len(schema.views)}
Schema Version: {schema.version}

Tables Overview:
{', '.join([table.table_name for table in schema.tables])}

Views Overview:
{', '.join([view.get('name', 'Unknown') for view in schema.views])}
        """
        
        if user_input and user_input.additional_context:
            content += f"\n\nAdditional Context:\n{user_input.additional_context}"
        
        if user_input and user_input.business_rules:
            content += f"\n\nBusiness Rules:\n" + "\n".join([f"- {rule}" for rule in user_input.business_rules])
        
        if schema.schema_notes:
            content += f"\n\nSchema Notes:\n{schema.schema_notes}"
        
        return Document(
            page_content=content.strip(),
            metadata={
                "type": "database_overview",
                "connection_id": schema.connection_id,
                "database_name": schema.database_name,
                "table_count": len(schema.tables),
                "gathered_at": str(schema.gathered_at)
            }
        )
    
    def _create_table_document(self, table: TableSchema, schema: DatabaseSchema, user_input: Optional[UserSchemaInput]) -> Document:
        """Create document for a specific table."""
        content = f"""
Table: {table.table_name}
Database: {schema.database_name}
Row Count: {table.row_count or 'Unknown'}
Primary Keys: {', '.join(table.primary_keys) if table.primary_keys else 'None'}

Columns ({len(table.columns)}):
"""
        
        for col in table.columns:
            name = col.get('name', '') or col.get('column_name', 'Unknown')
            dtype = col.get('data_type') or col.get('type', 'Unknown')
            nullable = col.get('is_nullable', col.get('nullable', True))
            default_val = col.get('default_value', col.get('default'))
            col_info = f"- {name}: {dtype}"
            if not nullable:
                col_info += " (NOT NULL)"
            if default_val is not None:
                col_info += f" DEFAULT {default_val}"
            content += col_info + "\n"
            # Add LLM-enriched annotations if present
            if col.get('llm_description'):
                content += f"  Description: {col.get('llm_description')}\n"
            if col.get('semantic_role'):
                role = col.get('semantic_role')
                unit = col.get('unit')
                content += f"  Role: {role}{f' [{unit}]' if unit else ''}\n"
            if col.get('sensitivity'):
                content += f"  Sensitivity: {col.get('sensitivity')}\n"
            if col.get('aliases'):
                try:
                    aliases = ", ".join([str(a) for a in (col.get('aliases') or [])])
                    if aliases:
                        content += f"  Aliases: {aliases}\n"
                except Exception:
                    pass
            if col.get('business_rules'):
                try:
                    rules = "; ".join([str(r) for r in (col.get('business_rules') or [])])
                    if rules:
                        content += f"  Business Rules: {rules}\n"
                except Exception:
                    pass
            if col.get('quality_notes'):
                try:
                    qn = "; ".join([str(q) for q in (col.get('quality_notes') or [])])
                    if qn:
                        content += f"  Quality Notes: {qn}\n"
                except Exception:
                    pass
        
        if table.foreign_keys:
            content += f"\nForeign Keys:\n"
            for fk in table.foreign_keys:
                content += f"- {', '.join(fk.get('constrained_columns', []))} -> {fk.get('referred_table', 'Unknown')}.{', '.join(fk.get('referred_columns', []))}\n"
        
        if table.indexes:
            content += f"\nIndexes:\n"
            for idx in table.indexes:
                content += f"- {idx.get('name', 'Unknown')}: {', '.join(idx.get('column_names', []))}\n"
        
        if table.table_comment:
            content += f"\nTable Comment: {table.table_comment}"
        
        # Add user-provided descriptions
        if user_input and user_input.table_descriptions and table.table_name in user_input.table_descriptions:
            content += f"\nUser Description: {user_input.table_descriptions[table.table_name]}"
        
        # Add column descriptions from user input
        if user_input and user_input.column_descriptions:
            user_col_descriptions = []
            for col in table.columns:
                col_name = col.get('name', '')
                full_col_name = f"{table.table_name}.{col_name}"
                if full_col_name in user_input.column_descriptions:
                    user_col_descriptions.append(f"- {col_name}: {user_input.column_descriptions[full_col_name]}")
            
            if user_col_descriptions:
                content += f"\n\nColumn Descriptions:\n" + "\n".join(user_col_descriptions)
        
        return Document(
            page_content=content.strip(),
            metadata={
                "type": "table",
                "connection_id": schema.connection_id,
                "database_name": schema.database_name,
                "table_name": table.table_name,
                "column_count": len(table.columns),
                "row_count": table.row_count if table.row_count is not None else 0,
                "has_foreign_keys": len(table.foreign_keys) > 0
            }
        )
    
    def _create_column_group_document(self, table_name: str, columns: List[Dict], user_input: Optional[UserSchemaInput]) -> Document:
        """Create document for a group of columns."""
        content = f"Table: {table_name}\nColumn Details:\n"
        
        for col in columns:
            name = col.get('name', '') or col.get('column_name', 'Unknown')
            dtype = col.get('data_type') or col.get('type', 'Unknown')
            nullable = col.get('is_nullable', col.get('nullable', True))
            default_val = col.get('default_value', col.get('default'))
            col_info = f"- {name}: {dtype}"
            if not nullable:
                col_info += " (NOT NULL)"
            if default_val is not None:
                col_info += f" DEFAULT {default_val}"
            if col.get('comment'):
                col_info += f" -- {col.get('comment')}"
            content += col_info + "\n"
            # Add LLM-enriched annotations if present
            if col.get('llm_description'):
                content += f"  Description: {col.get('llm_description')}\n"
            if col.get('semantic_role'):
                role = col.get('semantic_role')
                unit = col.get('unit')
                content += f"  Role: {role}{f' [{unit}]' if unit else ''}\n"
            if col.get('sensitivity'):
                content += f"  Sensitivity: {col.get('sensitivity')}\n"
            if col.get('aliases'):
                try:
                    aliases = ", ".join([str(a) for a in (col.get('aliases') or [])])
                    if aliases:
                        content += f"  Aliases: {aliases}\n"
                except Exception:
                    pass
            if col.get('business_rules'):
                try:
                    rules = "; ".join([str(r) for r in (col.get('business_rules') or [])])
                    if rules:
                        content += f"  Business Rules: {rules}\n"
                except Exception:
                    pass
            if col.get('quality_notes'):
                try:
                    qn = "; ".join([str(q) for q in (col.get('quality_notes') or [])])
                    if qn:
                        content += f"  Quality Notes: {qn}\n"
                except Exception:
                    pass
            
            # Add user descriptions
            if user_input and user_input.column_descriptions:
                full_col_name = f"{table_name}.{col.get('name', '')}"
                if full_col_name in user_input.column_descriptions:
                    content += f"  Description: {user_input.column_descriptions[full_col_name]}\n"
        
        return Document(
            page_content=content.strip(),
            metadata={
                "type": "columns",
                "table_name": table_name,
                "column_count": len(columns)
            }
        )
    
    def _create_relationships_document(self, relationships: List[Dict], user_input: Optional[UserSchemaInput]) -> Document:
        """Create document for table relationships."""
        content = "Database Relationships:\n\n"
        
        for rel in relationships:
            content += f"- {rel.get('source_table', 'Unknown')}.{', '.join(rel.get('source_columns', []))} -> "
            content += f"{rel.get('target_table', 'Unknown')}.{', '.join(rel.get('target_columns', []))}\n"
            content += f"  Type: {rel.get('relationship_type', 'Unknown')}\n"
            if rel.get('constraint_name'):
                content += f"  Constraint: {rel.get('constraint_name')}\n"
            content += "\n"
        
        # Add user-defined relationships
        if user_input and user_input.table_relationships:
            content += "User-Defined Relationships:\n"
            for rel in user_input.table_relationships:
                content += f"- {rel.get('description', 'No description')}\n"
        
        return Document(
            page_content=content.strip(),
            metadata={
                "type": "relationships",
                "relationship_count": len(relationships)
            }
        )
    
    def _create_types_document(self, enums: List[Dict], custom_types: List[Dict]) -> Document:
        """Create document for enums and custom types."""
        content = ""
        
        if enums:
            content += "Database Enums:\n"
            for enum in enums:
                content += f"- {enum.get('name', 'Unknown')}: {', '.join(enum.get('values', []))}\n"
            content += "\n"
        
        if custom_types:
            content += "Custom Types:\n"
            for ctype in custom_types:
                content += f"- {ctype.get('name', 'Unknown')}: {ctype.get('type', 'Unknown')}\n"
        
        return Document(
            page_content=content.strip(),
            metadata={
                "type": "types",
                "enum_count": len(enums),
                "custom_type_count": len(custom_types)
            }
        )
    
    def _chunk_columns(self, columns: List[Dict], chunk_size: int) -> List[List[Dict]]:
        """Chunk columns into smaller groups."""
        return [columns[i:i + chunk_size] for i in range(0, len(columns), chunk_size)]
    
    async def search_schema_information(
        self, 
        connection_id: str, 
        query: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for relevant schema information."""
        try:
            collection_name = self._get_collection_name(connection_id)
            collection = self.client.get_collection(collection_name)
            
            # Create query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            formatted_results = []
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    'content': doc,
                    'metadata': results['metadatas'][0][i],
                    'similarity_score': 1 - results['distances'][0][i]  # Convert distance to similarity
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching schema information: {str(e)}")
            return []
    
    async def get_all_schema_context(self, connection_id: str) -> str:
        """Get all schema context for a connection."""
        try:
            collection_name = self._get_collection_name(connection_id)
            collection = self.client.get_collection(collection_name)
            
            # Get all documents
            all_docs = collection.get(include=['documents', 'metadatas'])
            
            context = "Complete Database Schema Context:\n\n"
            for i, doc in enumerate(all_docs['documents']):
                metadata = all_docs['metadatas'][i]
                context += f"=== {metadata.get('type', 'Unknown').upper()} ===\n"
                context += doc + "\n\n"
            
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving all schema context: {str(e)}")
            return ""
    
    async def delete_schema(self, connection_id: str) -> bool:
        """Delete schema information for a connection."""
        try:
            collection_name = self._get_collection_name(connection_id)
            self.client.delete_collection(collection_name)
            logger.info(f"Successfully deleted schema for connection {connection_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting schema: {str(e)}")
            return False
