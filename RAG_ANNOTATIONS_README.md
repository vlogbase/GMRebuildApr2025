# RAG System with OpenRouter Annotations

This document provides details on the implementation of our Retrieval Augmented Generation (RAG) system using OpenRouter Annotations for context persistence.

## Overview

The RAG system allows users to upload documents (PDFs) and images that the AI can reference during the conversation. OpenRouter's annotations mechanism is used to maintain context across conversation turns, so users can continue to ask questions about previously uploaded documents without re-uploading them.

## Key Components

### 1. Database Storage

- **Message.annotations**: A JSON column that stores the annotations from OpenRouter responses.
- **OpenRouterModel.supports_pdf**: A boolean flag that indicates which models support PDF processing.

### 2. Frontend Implementation

The frontend UI has been enhanced to:

- Show an "Attach File for RAG" button only for models that support PDFs
- Display UI indicators when documents are being processed
- Support both PDFs and images for multimodal models

### 3. Context Persistence

The system uses OpenRouter's annotations feature to:

- Store document content and context in the annotations field
- Pass annotations from previous messages to new requests
- Maintain context across multiple conversation turns

## Implementation Details

### Database Model Updates

The `Message` model includes an `annotations` column to store the rich context:

```python
class Message(db.Model):
    # ... existing fields ...
    annotations = db.Column(JSON, nullable=True)
```

The `OpenRouterModel` model includes a `supports_pdf` flag:

```python
class OpenRouterModel(db.Model):
    # ... existing fields ...
    supports_pdf = db.Column(db.Boolean, default=False)
```

### Price Updater Logic

The `price_updater.py` module detects which models support PDFs based on OpenRouter API data:

```python
supports_pdf = 'file' in input_modalities
```

### Frontend Model Selection

The JavaScript in `static/js/script.js` includes the `supports_pdf` flag when building model data:

```javascript
modelDataArray.push({
    // ... other properties ...
    supports_pdf: modelData.supports_pdf || false,
    // ... other properties ...
});
```

### RAG UI Logic

The `updateRagCapabilitiesForModel` function checks model capabilities and updates UI elements:

```javascript
function updateRagCapabilitiesForModel(modelId) {
    // Find the model in loadedModels
    const selectedModel = loadedModels.find(model => model.id === modelId);
    
    if (selectedModel) {
        // Update the global capabilities object
        currentModelCapabilitiesForRAG.is_multimodal = !!selectedModel.is_multimodal;
        currentModelCapabilitiesForRAG.supports_pdf = !!selectedModel.supports_pdf;
        
        // Update UI based on capabilities
        updateRagAttachButtonState();
    }
}
```

### Annotations Processing in Backend

When sending chat requests to OpenRouter, the system includes previous annotations:

```python
# Include annotations from previous message if available
if last_message and last_message.annotations:
    openrouter_payload['annotations'] = last_message.annotations
```

When receiving responses, the system stores returned annotations:

```python
# Store annotations from the response if available
if 'annotations' in response:
    message.annotations = response['annotations']
```

### Memory System Integration

The annotations are also integrated with the ChatMemoryManager system:

```python
# Enhanced memory integration with annotations support
memory_metadata = {
    'model': requested_model_id,
    'model_id_used': final_model_id_used,
    'prompt_tokens': final_prompt_tokens,
    'completion_tokens': final_completion_tokens,
    'message_id': assistant_message_id,
    'annotations': getattr(generate, 'captured_annotations', None)
}

save_message_with_memory(
    message_obj=assistant_message,
    user_id=memory_user_id,
    session_id=str(current_conv_id),
    response_metadata=memory_metadata
)
```

The save_message_with_memory function has been enhanced to handle annotations:

```python
if response_metadata and 'annotations' in response_metadata:
    # Store annotations for context persistence
    message_obj.annotations = response_metadata['annotations']
    logging.info(f"Stored annotations for message {message_obj.id} for context persistence")
```

## Testing and Verification

Two verification scripts are provided:

1. **check_rag_implementation.py**: Verifies the PDF capability detection and UI integration
2. **verify_rag_annotations_implementation.py**: Verifies the annotations handling for context persistence

## Usage

### For Users

1. Select a model that supports PDFs (like GPT-4o or Gemini 2.5 Pro)
2. Click the "Attach File for RAG" button
3. Upload a PDF document
4. Ask questions about the document

### For Developers

1. Run verification scripts to check implementation:
   ```
   python check_rag_implementation.py
   python verify_rag_annotations_implementation.py
   ```

2. When adding new models, ensure the `supports_pdf` flag is properly set

## Limitations

- Only certain models support PDFs (typically high-end models like GPT-4o and Gemini 2.5 Pro)
- Free models typically don't support document processing
- Very large documents may be truncated due to context length limitations

## Troubleshooting

If the RAG features aren't working correctly:

1. Verify the model has `supports_pdf=True` in the database
2. Check if annotations are being stored in the messages table
3. Ensure OpenRouter API key has access to PDF-capable models
4. Look for annotations in the OpenRouter API responses