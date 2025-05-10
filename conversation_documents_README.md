# Conversation-Specific Document Context System

## Overview
This feature enhances the chatbot's document context management by associating documents with specific conversations rather than just users. This enables more precise control over which documents are used in each conversation's context, improving the relevance and accuracy of the chatbot's responses.

## Components

### Database Models
- `ConversationDocument` model establishes a many-to-many relationship between conversations and documents
- Each record tracks a document's active state within a specific conversation

### MongoDB Storage
- Document and chunk storage now includes `conversation_id` field
- MongoDB Atlas Vector Search index updated to filter by both user_id and conversation_id
- Document chunks can be filtered by both conversation and document active state

### API Endpoints
- `/api/conversation/<id>/documents` - Get all documents for a conversation
- `/api/conversation/<id>/document/<document_id>/toggle_context` - Toggle document active state

## Migration Process
1. Set up the environment variables:
   - `DATABASE_URL` - PostgreSQL connection string for SQL operations
   - `MONGODB_ATLAS_URI` or `MONGODB_URI` - MongoDB connection string (optional)

2. Run the migration script to create the necessary SQL schema:
   ```
   python run_migrations_conversation_documents.py
   ```

3. The migration will:
   - Create the ConversationDocument table if it doesn't exist
   - Create necessary indexes for performance
   - Associate existing documents with their owners' conversations (if MongoDB is available)
   - Skip document migration gracefully if MongoDB is unavailable
   
4. Update the MongoDB Atlas Vector Search index with the new definition in `mongodb_vector_index_definition.json`

### MongoDB Environment Variables
The system now supports two environment variable names for MongoDB connection:
- `MONGODB_ATLAS_URI` (preferred)
- `MONGODB_URI` (fallback)

If either variable is set, the system will use it to connect to MongoDB. MongoDB connection is optional for the SQL schema migration but required for document processing.

## Usage
When uploading documents, you can now specify a `conversation_id` parameter to associate the document with a specific conversation. The document will be active by default. You can toggle a document's active state through the API endpoint.

The chat endpoint automatically uses conversation-specific document context if available, falling back to user-level documents if needed.

## Implementation Notes
- Document processing now happens in the context of a specific conversation
- Vector searches filter by both user_id and conversation_id
- Documents can be active or inactive within each conversation
- The system maintains backward compatibility with the previous user-level document approach

### Error Handling and Robustness
- The migration script handles various failure scenarios gracefully:
  - Missing MongoDB connection: SQL schema still created successfully
  - Temporary user IDs: Documents with temporary IDs (`temp_*`) are skipped but logged
  - Database constraint violations: Existing records are detected and skipped
  - Transaction management: SQL changes are committed only after successful processing
  
- The document processing pipeline includes:
  - Detailed error logging with document and conversation IDs
  - Proper handling of optional conversation_id parameters
  - Graceful degradation when MongoDB is unavailable
  
### Temporary User ID Handling
Documents associated with temporary user IDs (anonymous sessions) are handled specially:
1. During migration, they are identified by the `temp_` prefix and skipped
2. For new uploads, they are stored with the temporary ID
3. If a user later authenticates, these documents remain accessible to their original session

### Performance Considerations
- SQL indexes are created on both conversation_id and document_identifier
- MongoDB indexes support efficient filtering by user_id and conversation_id
- SQL operations use parameterized queries to prevent SQL injection
- Document chunks are stored with conversation_id to enable efficient vector search filtering