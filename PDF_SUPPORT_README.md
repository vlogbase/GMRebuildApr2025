# PDF Support Implementation

## Overview
This document explains how PDF support was added to the chatbot application, including critical fixes for conversation creation.

## Database Schema
The Conversation model includes a `conversation_uuid` field that is required by the database but was previously missing from the SQLAlchemy model definition. This has been fixed in models.py.

## Issue Fixed
When users uploaded PDFs before sending any messages, the system would try to create a new conversation without a `conversation_uuid` field, resulting in a 500 error:

```
ERROR:app:Error creating conversation for PDF: 'conversation_uuid' is an invalid keyword argument for Conversation
```

## Changes Made

1. Added the `conversation_uuid` field to the SQLAlchemy model in `models.py`:
```python
conversation_uuid = db.Column(db.String(36), unique=True, nullable=True)  # UUID for conversation identification
```

2. Updated all Conversation creation points in app.py to include the conversation_uuid field:
   - In `chat()` function when creating a new conversation
   - In `clear_conversations()` function when creating a replacement conversation
   - In `get_conversations()` function when creating an initial conversation

3. Added logging to help diagnose any further issues

## Upload Flow
1. User uploads a PDF via the `upload_file` endpoint
2. If no conversation_id is provided, a new conversation is created with a conversation_uuid
3. The PDF is processed and stored in Azure Blob Storage
4. A Message object is created with the PDF URL and filename

## Testing
The `test_conversation_uuid_fix.py` script verifies that conversations can be created with a conversation_uuid field and that it persists correctly in the database.

## Future Considerations
- Consider making conversation_uuid non-nullable in the database schema for consistency
- Ensure PDFs can be properly accessed when using the conversation sharing feature
- Add proper validation for the conversation_uuid format