# GloriaMundo Chat Application

A Flask-based chatbot interface that mimics the GloriaMundo design with OpenRouter API integration, real-time response streaming, and advanced memory capabilities.

## Features

- **Modern Chat Interface**: Clean, responsive design with dark/light mode support
- **Model Selection**: Choose from multiple AI models (GPT-4, Claude, Gemini, etc.)
- **Real-time Streaming**: Responses stream in real-time for a better user experience
- **Conversation History**: Automatically saves chat sessions in a PostgreSQL database
- **Advanced Memory System**: Optional MongoDB-based memory system with:
  - Vector search for finding semantically similar previous messages
  - User profile storage with facts and preferences
  - Contextual prompt enrichment based on memory
  - Automatic information extraction from user messages

## Setup

### Basic Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables by copying `.env.example` to `.env` and filling in your values:
   ```bash
   cp .env.example .env
   # Edit the .env file with your credentials
   ```

3. Run the application:
   ```bash
   gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
   ```

### Memory System Setup (Optional)

The advanced memory system uses MongoDB Atlas for storing and retrieving memory with vector search capabilities. To enable it:

1. Create a MongoDB Atlas account and cluster
2. Create a database named `chatbot_memory_large`
3. Create two collections: `chat_sessions` and `user_profiles`
4. Set up the following Vector Search indexes in MongoDB Atlas:
   - For `chat_sessions`: Index name `idx_message_embedding_large` on field `message_history.embedding` (3072 dimensions)
   - For `user_profiles`: Index name `idx_preference_embedding_large` on field `preferences_embeddings.embedding` (3072 dimensions)
5. Set the following environment variables:
   ```
   ENABLE_MEMORY_SYSTEM=true
   MONGODB_ATLAS_URI=your_mongodb_connection_string
   ```
6. For best results, set up Azure OpenAI with a text-embedding-3-large model deployment and configure the Azure environment variables in `.env`

## Architecture

### Core Components

- **Flask Backend**: Manages routing, API calls, and database interactions
- **PostgreSQL Database**: Stores user accounts, conversations, and messages
- **OpenRouter Integration**: Provides access to various AI models
- **Memory System**: Enhances conversations with contextual memory (optional)

### Memory System Architecture

The memory system consists of the following components:

- **ChatMemoryManager**: Core class that handles memory operations
  - Connects to MongoDB Atlas
  - Generates embeddings using Azure OpenAI or OpenRouter
  - Stores and retrieves messages with vector search
  - Extracts structured information from user messages
  - Maintains user profiles with facts and preferences

- **Memory Integration Layer**: Connects the memory system to the chat application
  - Asynchronously saves messages to avoid blocking the response stream
  - Enriches prompts with relevant context from memory
  - Handles error cases gracefully to ensure core functionality continues to work

## Configuration Options

The application supports the following environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `OPENROUTER_API_KEY`: API key for OpenRouter
- `SESSION_SECRET`: Secret key for Flask sessions
- `ENABLE_MEMORY_SYSTEM`: Set to "true" to enable the memory system
- `MONGODB_ATLAS_URI`: MongoDB Atlas connection string
- `AZURE_OPENAI_API_KEY`: Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint URL
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME`: Name of the embedding model deployment
- `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME`: Name of the chat model deployment

## Development

To check if your environment is properly configured:

```bash
python check_env.py
```

To run the test script for the memory manager:

```bash
python test_memory_manager.py
```