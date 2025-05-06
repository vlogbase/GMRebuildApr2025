# GloriaMundo Chat Application Architecture

## Overview

GloriaMundo is a Flask-based chatbot application that provides a modern chat interface with advanced AI capabilities. The application integrates with various AI models through OpenRouter API, supports real-time response streaming, and includes advanced memory and retrieval-augmented generation (RAG) features. The system is designed as a web application with both synchronous and asynchronous components to handle different types of operations efficiently.

## System Architecture

The GloriaMundo Chat Application follows a monolithic architecture pattern with modular components. The key architectural layers include:

1. **Web Server Layer**: Flask web application served using Gunicorn with Gevent workers for handling concurrent connections
2. **Application Layer**: Core business logic implemented in Python
3. **Persistence Layer**: Multiple database solutions for different types of data
   - PostgreSQL for relational data (user accounts, conversations, transactions)
   - MongoDB Atlas for vector databases (memory system, RAG functionality)
4. **External Service Layer**: Integration with various AI and cloud services
   - OpenRouter API for AI model access
   - Azure OpenAI for embeddings
   - Stripe for payment processing
   - Google OAuth for authentication

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Browser                         │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                    Gunicorn + Gevent                        │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                    Flask Application                        │
├─────────────────────┬─────────────────────┬─────────────────┤
│   Authentication    │     Chat Engine     │  Billing System │
│   (Google OAuth)    │                     │    (Stripe)     │
└─────────────────────┴─────────┬───────────┴─────────────────┘
                                │
┌──────────────┬────────────────▼───────────────┬─────────────┐
│  PostgreSQL  │      OpenRouter API           │  MongoDB    │
│  (User data, │     (AI Model Access)         │  (Memory &  │
│conversations)│                               │  RAG data)  │
└──────────────┴────────────────┬──────────────┴─────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                   Azure OpenAI API                          │
│                   (Embeddings)                              │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Flask Web Application (`app.py`)

The core of the system is a Flask web application that handles HTTP requests, renders templates, and manages user sessions. The application uses the following extensions:
- Flask-SQLAlchemy for ORM
- Flask-Login for user authentication
- Flask-WTF for form handling and CSRF protection

### 2. Database Models (`models.py`)

The application uses SQLAlchemy models to define its database schema:
- `User`: Stores user information, authentication details, and credit balance
- `Conversation`: Stores chat conversations
- `Message`: Stores individual messages within conversations
- `Transaction`: Tracks payment transactions
- `Usage`: Records model usage and token consumption
- `Package`: Defines credit packages available for purchase
- `UserPreference`: Stores user preferences for models

### 3. Memory System (`chat_memory_manager.py`, `memory_integration.py`)

An advanced memory system that uses MongoDB Atlas to store and retrieve:
- Short-term memory (recent conversation history)
- Long-term memory (user preferences and facts)
- Vector embeddings for semantic search

The memory system is optional and can be enabled/disabled via environment variables.

### 4. RAG (Retrieval-Augmented Generation) System (`document_processor.py`)

A system for processing documents, extracting text, generating embeddings, and storing them in MongoDB for later retrieval. This allows the chatbot to reference uploaded documents when generating responses.

### 5. Authentication System

The application supports two authentication methods:
- Traditional username/password authentication
- Google OAuth integration for social login

### 6. Billing System (`billing.py`, `stripe_config.py`)

A credit-based billing system integrated with Stripe for payment processing. Key features include:
- Credit packages that users can purchase
- Usage tracking based on token consumption
- Different pricing for different AI models

### 7. Image Handling

Support for multimodal capabilities, including:
- Image upload functionality
- Storage in Azure Blob Storage
- Passing images to compatible AI models for analysis

## Data Flow

### 1. User Authentication Flow

1. User logs in via Google OAuth or username/password
2. On successful authentication, user session is created
3. User preferences and conversation history are loaded

### 2. Chat Conversation Flow

1. User sends a message (optionally with images)
2. If memory system is enabled, context is enriched with relevant memories
3. Request is sent to OpenRouter API with the enriched prompt
4. Streaming response is received from AI model and sent to client
5. Conversation and message are saved to PostgreSQL
6. If memory system is enabled, message content is processed to extract and store facts

### 3. Billing and Credits Flow

1. User purchases credits through Stripe integration
2. Transaction is recorded in the database
3. User's credit balance is updated
4. When user sends messages, credits are deducted based on model pricing and token usage

## External Dependencies

### AI Services
- **OpenRouter API**: Gateway to access various AI models (GPT-4, Claude, Gemini, etc.)
- **Azure OpenAI API**: Used for generating embeddings for the memory and RAG systems

### Storage Services
- **MongoDB Atlas**: Vector database for memory system and RAG functionality
- **Azure Blob Storage**: For storing uploaded images

### Payment Processing
- **Stripe**: For handling credit purchases and payment processing

### Authentication
- **Google OAuth**: For social login functionality

## Deployment Strategy

The application is configured for deployment on Replit with autoscaling. Key deployment configurations include:

1. **Web Server**: Gunicorn with Gevent workers
   - `-k gevent`: Uses Gevent worker for asynchronous processing
   - `-w 4`: Runs 4 worker processes
   - `--timeout 300`: Sets a 5-minute timeout for requests

2. **Environment Configuration**:
   - `.env` file for environment-specific configuration
   - Separate environment variables for feature flags (memory system, RAG, Azure embeddings)

3. **Database Migration**:
   - Migration scripts for updating database schema when necessary

4. **Scalability Considerations**:
   - Memory system designed to work with MongoDB Atlas for horizontal scaling
   - Gunicorn configured with multiple workers for handling concurrent requests
   - OpenRouter API provides access to various AI models for scaling based on needs and costs

## Security Considerations

1. **Authentication**: Secure user authentication via Google OAuth and password hashing
2. **Data Protection**: CSRF protection via Flask-WTF
3. **API Keys**: Environment variables for storing sensitive API keys
4. **Content Security**: Validation of user inputs and uploaded files

## Future Architectural Considerations

1. **Microservices**: Consider splitting into separate services for chat, billing, and document processing
2. **Caching Layer**: Implement Redis for caching frequent operations
3. **Async Processing**: More extensive use of background tasks for non-real-time operations