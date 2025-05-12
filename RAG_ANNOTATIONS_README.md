# RAG Context Persistence with OpenRouter Annotations

This implementation enhances the RAG (Retrieval-Augmented Generation) system to support context persistence across multiple messages using OpenRouter's annotations mechanism.

## Key Features

1. **Context Persistence**: OpenRouter annotations are captured, stored, and reused in subsequent requests to maintain context across chat messages.
2. **Database Support**: The Message model has been extended with an `annotations` field to store annotations from OpenRouter responses.
3. **Automated Context Chain**: Annotations from previous assistant messages are automatically included in new requests.

## Implementation Details

### Database Changes

1. **New Message Column**: Added `annotations` JSON column to the Message table
2. **Migration Script**: Created `migrations_annotations.py` to handle the database schema update

### Code Changes

1. **Capturing Annotations**: Modified streaming handler to extract and store annotations
2. **Message Storage**: Updated message saving to include captured annotations
3. **Request Construction**: Added code to include previous annotations in new requests

## How It Works

1. When a message containing documents is sent to OpenRouter, the AI analyzes these documents and creates annotations.
2. These annotations are returned in the response and stored in the Message record.
3. In subsequent messages in the same conversation, the annotations are included, allowing the AI to reference the content of previously uploaded documents without reprocessing them.

## Testing

To test this functionality:

1. Run the migration: `python run_annotations_migration.py`
2. Start the application: `python rag_annotations_workflow.py`
3. Upload a document and ask a question about it
4. Ask a follow-up question without uploading the document again - the model should still have context about the previously uploaded document

## Implementation Files

- `migrations_annotations.py`: Database migration for the annotations column
- `run_annotations_migration.py`: Script to run the migration
- `rag_annotations_workflow.py`: Workflow to run the Flask app with annotations support

## OpenRouter Annotations Format

OpenRouter may return annotations in various formats depending on the model and content. Examples:

```json
{
  "annotations": {
    "documents": [
      {
        "id": "doc_123",
        "content": "Document content for retrieval",
        "metadata": {
          "source": "user_uploaded",
          "filename": "example.pdf"
        }
      }
    ]
  }
}
```

The exact format varies by model, but our implementation preserves these annotations without modifying them, ensuring full compatibility with OpenRouter's context persistence mechanism.