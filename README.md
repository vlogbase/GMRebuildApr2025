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
   - For `user_profiles`: Index name `memory_vector_index` on field `preferences_embeddings.embedding` (3072 dimensions)
5. Set the following environment variables:
   ```
   ENABLE_MEMORY_SYSTEM=true
   MONGODB_ATLAS_URI=your_mongodb_connection_string
   ```
6. For best results, set up Azure OpenAI with a text-embedding-3-large model deployment and configure the Azure environment variables in `.env`

### MongoDB Atlas Vector Search Configuration

To create the required vector search index for the long-term memory system:

1. Go to MongoDB Atlas Console (https://cloud.mongodb.com)
2. Select your cluster and navigate to the 'Search' tab
3. Click 'Create Index' and choose 'JSON Editor'
4. Use this index definition:

```json
{
  "mappings": {
    "dynamic": true,
    "fields": {
      "preferences_embeddings": {
        "fields": {
          "embedding": {
            "dimensions": 3072,
            "similarity": "cosine",
            "type": "vector"
          }
        },
        "type": "document"
      },
      "userId": {
        "type": "string"
      }
    }
  },
  "vectorSearchIndexVersion": 1
}
```

5. Set 'Index Name' to `memory_vector_index`
6. Set 'Database and Collection' to `chatbot_memory_large.user_profiles`
7. Click 'Create Index'

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
  - Implements direct MongoDB Atlas $vectorSearch for efficient similarity search

- **Memory Integration Layer**: Connects the memory system to the chat application
  - Asynchronously saves messages to avoid blocking the response stream
  - Enriches prompts with relevant context from memory
  - Handles error cases gracefully to ensure core functionality continues to work

- **Vector Search Implementation**:
  - Uses MongoDB Atlas Vector Search capabilities directly
  - Eliminates need for temporary collections and manual similarity calculations
  - Properly handles field name differences (user_id and userId)
  - Includes fall-back mechanisms for when vector search is unavailable

### Long-Term Memory Implementation

The refactored long-term memory system uses MongoDB Atlas's native $vectorSearch aggregation stage to perform similarity search directly on the database server, which offers several advantages:

1. **Performance**: Vector operations happen on the database server side, reducing data transfer and client-side processing
2. **Scalability**: MongoDB Atlas vector indexing scales better than client-side vector operations
3. **Maintenance**: No need to create temporary collections for each search operation
4. **Reliability**: Fewer moving parts means fewer points of failure

The retrieval pipeline:
1. Converts the user's query to an embedding vector using Azure OpenAI
2. Executes a $vectorSearch aggregation pipeline on the MongoDB Atlas server 
3. Returns semantically relevant preferences and user facts
4. Falls back gracefully to fact-only retrieval if vector search is unavailable

To use the refactored implementation, you must create a vector search index named `memory_vector_index` in your MongoDB Atlas cluster as described in the setup section.

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

To test the memory management system:

```bash
# Test basic memory functionality
python test_memory_manager.py

# Test field name consistency and fixes 
python test_memory_fix.py

# Test the refactored vector search implementation
python test_memory_vector_search.py
```

The test scripts validate different aspects of the memory system:
- `test_memory_manager.py`: Basic functionality of the ChatMemoryManager
- `test_memory_fix.py`: Verifies field name consistency between user_id and userId
- `test_memory_vector_search.py`: Tests the refactored MongoDB Atlas $vectorSearch implementation