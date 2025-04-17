import os
import logging
import datetime
from typing import List, Dict, Any, Optional, Union
from urllib.parse import quote_plus

import pymongo
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, OperationFailure

import openai
from openai import OpenAI
import tiktoken
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ChatMemoryManager")

class ChatMemoryManager:
    """
    A class to manage chatbot memory using MongoDB Atlas for storage and
    Azure OpenAI or OpenRouter for embeddings and LLM operations.
    
    This implementation supports:
    - Short-term memory (recent conversation history)
    - Long-term memory (user preferences and facts)
    - Vector search using embeddings (3072 dimensions)
    """
    
    def __init__(self):
        """
        Initialize the ChatMemoryManager with connections to MongoDB Atlas
        and Azure OpenAI or OpenRouter.
        """
        # Load environment variables
        load_dotenv()
        
        # Initialize MongoDB connection
        try:
            # Get MongoDB connection string
            mongodb_uri = os.environ.get("MONGODB_ATLAS_URI")
            if not mongodb_uri:
                logger.error("MONGODB_ATLAS_URI not found in environment variables")
                raise ValueError("MongoDB connection URI not provided")
            
            # Connect to MongoDB
            self.mongo_client = MongoClient(mongodb_uri)
            
            # Test the connection
            self.mongo_client.admin.command('ping')
            logger.info("Connected to MongoDB Atlas successfully")
            
            # Set up database and collections
            self.db = self.mongo_client.get_database("chatbot_memory_large")
            self.chat_sessions = self.db.get_collection("chat_sessions")
            self.user_profiles = self.db.get_collection("user_profiles")
            
            # Create indexes for efficient querying
            self._ensure_indexes()
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB Atlas: {e}")
            raise
        except Exception as e:
            logger.error(f"Error initializing MongoDB: {e}")
            raise
        
        # Initialize OpenAI clients - one for Azure embeddings, one for OpenRouter chat
        try:
            # Prefer secrets over environment variables for secure access
            self.azure_api_key = os.environ.get("AZURE_OPENAI_API_KEY")
            self.azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
            self.embedding_deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
            
            if self.azure_api_key and self.azure_endpoint and self.embedding_deployment:
                self.use_azure_embeddings = True
                
                # Initialize Azure OpenAI client for embeddings
                self.azure_client = openai.AzureOpenAI(
                    api_key=self.azure_api_key,
                    api_version="2024-02-01",
                    azure_endpoint=self.azure_endpoint
                )
                logger.info(f"Azure OpenAI client initialized successfully for embeddings (deployment: {self.embedding_deployment})")
            else:
                self.use_azure_embeddings = False
                missing_params = []
                if not self.azure_api_key: missing_params.append("AZURE_OPENAI_API_KEY")
                if not self.azure_endpoint: missing_params.append("AZURE_OPENAI_ENDPOINT")
                if not self.embedding_deployment: missing_params.append("AZURE_OPENAI_DEPLOYMENT")
                logger.error(f"Azure OpenAI not fully configured: missing {', '.join(missing_params)}")
            
            # Initialize OpenRouter client for chat completion
            if os.environ.get("OPENROUTER_API_KEY"):
                self.openrouter_client = OpenAI(
                    api_key=os.environ.get("OPENROUTER_API_KEY"),
                    base_url="https://openrouter.ai/api/v1"
                )
                logger.info("OpenRouter client initialized successfully for chat")
            else:
                logger.error("OPENROUTER_API_KEY not found in environment variables")
                raise ValueError("OpenRouter API key not provided")
                
            # Verify we have at least one embedding source
            if not self.use_azure_embeddings and not os.environ.get("OPENROUTER_API_KEY"):
                logger.error("No API keys found for Azure OpenAI embeddings or OpenRouter fallback")
                raise ValueError("No API keys found for embedding models")
                
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {e}")
            raise

    def _ensure_indexes(self):
        """
        Create necessary indexes on MongoDB collections for efficient querying.
        This includes standard indexes and vector search indexes.
        """
        try:
            # Standard indexes for chat_sessions
            self.chat_sessions.create_index([("session_id", pymongo.ASCENDING)], unique=True)
            self.chat_sessions.create_index([("user_id", pymongo.ASCENDING)])
            
            # Standard indexes for user_profiles
            self.user_profiles.create_index([("user_id", pymongo.ASCENDING)], unique=True)
            
            # Ensure we also have an index on the userId field for vector search compatibility
            try:
                self.user_profiles.create_index([("userId", pymongo.ASCENDING)])
                logger.info("Added userId index for vector search compatibility")
            except Exception as idx_err:
                logger.warning(f"Could not create userId index: {idx_err}")
            
            logger.info("MongoDB standard indexes created successfully")
            
            # Log detailed instructions for creating vector search indexes in MongoDB Atlas
            logger.info("""
MEMORY: MongoDB Atlas Search Configuration for Long-Term Memory
----------------------------------------------------------------------
For the long-term memory functionality to work properly, you need to create TWO indexes in MongoDB Atlas:

1. First index: Vector Search Index for semantic similarity (REQUIRED)
   - Index Name: 'memory_vector_index'
   - Database and Collection: 'chatbot_memory_large.user_profiles'
   - JSON Definition:

{
  "fields": [
    {
      "type": "vector",
      "path": "preferences_embeddings.embedding",
      "numDimensions": 3072,
      "similarity": "cosine"
    },
    {
      "path": "userId",
      "type": "filter"
    }
  ]
}

2. Second index: Standard Search Index for filtering (REQUIRED)
   - Index Name: 'memory_standard_filter_index'
   - Database and Collection: 'chatbot_memory_large.user_profiles'
   - JSON Definition:

{
  "mappings": {
    "dynamic": false,
    "fields": {
      "userId": {
        "type": "token"
      }
    }
  }
}

Step-by-step instructions:
1. Go to MongoDB Atlas Console (https://cloud.mongodb.com)
2. Select your cluster and navigate to the 'Search' tab
3. Click 'Create Index' and choose 'JSON Editor'
4. Paste the first index definition, set the index name to 'memory_vector_index'
5. Set Database and Collection to 'chatbot_memory_large.user_profiles'
6. Click 'Create Index'
7. Repeat steps 3-6 for the second index definition with name 'memory_standard_filter_index'

BOTH indexes are required for proper long-term memory functionality.
Without these indexes, the long-term memory retrieval will fall back to using only facts.

MEMORY: MongoDB Atlas Search Configuration for Short-Term Memory
----------------------------------------------------------------------
For the short-term memory functionality, you also need to create a vector search index:

- Index Name: 'short_term_memory_vector_index'
- Database and Collection: 'chatbot_memory_large.chat_sessions'
- JSON Definition:

{
  "fields": [
    {
      "type": "vector",
      "path": "message_history.embedding",
      "numDimensions": 3072,
      "similarity": "cosine"
    },
    {
      "path": "session_id",
      "type": "filter"
    },
    {
      "path": "userId",
      "type": "filter"
    }
  ]
}

Follow the same steps as above to create this index.
----------------------------------------------------------------------
""")
            
        except Exception as e:
            logger.error(f"Error creating MongoDB indexes: {e}")
            # Continue without indexes rather than fail entirely
    
    def _get_embedding(self, text: str) -> List[float]:
        """
        Generate a vector embedding for text using Azure's text-embedding-3-large model.
        
        Args:
            text (str): The text to generate an embedding for
            
        Returns:
            List[float]: A 3072-dimension embedding vector
            
        Raises:
            RuntimeError: If Azure OpenAI is not configured or the API call fails
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * 3072  # Return zero vector for empty text
        
        # Check if Azure OpenAI is properly configured
        if not self.use_azure_embeddings:
            error_msg = "Azure OpenAI is not properly configured for embedding generation."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
            
        try:
            # Use Azure OpenAI for embeddings
            logger.debug(f"Generating Azure embedding for text: '{text[:50]}...'")
            
            response = self.azure_client.embeddings.create(
                input=text,
                model=self.embedding_deployment
            )
            
            # Validate the response
            if not response or not hasattr(response, 'data') or not response.data:
                error_msg = "Azure OpenAI returned empty response"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
                
            # Extract the embedding from the response
            embedding = response.data[0].embedding
            
            # Validate the embedding
            if not embedding or not isinstance(embedding, list) or len(embedding) == 0:
                error_msg = "Azure OpenAI returned invalid embedding"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
                
            logger.info(f"Successfully generated Azure embedding with {len(embedding)} dimensions for text: '{text[:30]}...'")
            return embedding
                
        except Exception as e:
            error_msg = f"Azure OpenAI embedding generation failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def add_message(self, session_id: str, user_id: str, role: str, content: str) -> bool:
        """
        Add a message to a chat session and generate an embedding for it.
        
        Args:
            session_id (str): The ID of the chat session
            user_id (str): The ID of the user
            role (str): Either "user" or "assistant"
            content (str): The message content
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert user_id to string for consistency
            user_id_str = str(user_id)
            logger.info(f"MEMORY: Adding message to session {session_id} for user {user_id_str}, role: {role}")
            
            # Generate embedding for the content
            logger.info(f"MEMORY: Generating embedding for content: '{content[:50]}...'")
            embedding = self._get_embedding(content)
            
            if not embedding:
                logger.error("MEMORY: Failed to generate embedding for message")
                return False
                
            # Log embedding details for debugging
            embed_dims = len(embedding)
            logger.info(f"MEMORY: Generated embedding with {embed_dims} dimensions")
            logger.debug(f"MEMORY: Sample values from embedding: {embedding[:3]}...")
            
            # Create the message document with message_id
            message_id = f"{session_id}_{datetime.datetime.utcnow().timestamp()}"
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.datetime.utcnow(),
                "embedding": embedding,
                "metadata": {"message_id": message_id}
            }
            
            # First check if the document already exists (using standardized userId field)
            query = {"session_id": session_id, "userId": user_id_str}
            existing = self.chat_sessions.find_one(query)
            
            # Build the update operation based on what exists
            update_op = {
                "$push": {"message_history": message},
                "$set": {
                    "updated_at": datetime.datetime.utcnow(),
                    "userId": user_id_str  # Always ensure userId is set correctly
                }
            }
            
            # For existing documents, ensure user_id exists for backward compatibility
            if existing:
                if "user_id" not in existing:
                    update_op["$set"]["user_id"] = user_id_str
                    logger.info(f"MEMORY: Adding 'user_id' field for backward compatibility")
            else:
                # For new documents, set both field names and creation time
                logger.info(f"MEMORY: Creating new chat session")
                update_op["$setOnInsert"] = {
                    "user_id": user_id_str,  # Keep for backward compatibility
                    "created_at": datetime.datetime.utcnow()
                }
            
            # Use standardized userId field in query to avoid duplication
            result = self.chat_sessions.update_one(
                {"session_id": session_id, "userId": user_id_str},
                update_op,
                upsert=True
            )
            
            if result.acknowledged:
                logger.info(f"MEMORY: Successfully added message {message_id} to session {session_id}")
                logger.debug(f"MEMORY: MongoDB result - matched: {result.matched_count}, modified: {result.modified_count}, upserted_id: {result.upserted_id}")
            else:
                logger.warning("MEMORY: MongoDB operation not acknowledged")
                
            return True
            
        except Exception as e:
            logger.error(f"MEMORY: Error adding message: {e}")
            return False
    
    def retrieve_short_term_memory(
        self, 
        session_id: str, 
        user_id: str, 
        query_text: str, 
        last_n: int = 10, 
        vector_search_limit: int = 5
    ) -> List[Dict]:
        """
        Retrieve the most recent messages and semantically similar messages from a chat session.
        
        Args:
            session_id (str): The ID of the chat session
            user_id (str): The ID of the user
            query_text (str): The text to find semantically similar messages for
            last_n (int): The number of most recent messages to retrieve
            vector_search_limit (int): The number of semantically similar messages to retrieve
            
        Returns:
            List[Dict]: A list of message dictionaries
        """
        try:
            # Convert user_id to string for consistency
            user_id_str = str(user_id)
            logger.info(f"MEMORY: Retrieving short-term memory for session {session_id}, user {user_id_str}")
            
            # Get the most recent messages chronologically (standardize on userId)
            recent_messages_cursor = self.chat_sessions.aggregate([
                {"$match": {
                    "session_id": session_id, 
                    "userId": user_id_str
                }},
                {"$unwind": "$message_history"},
                {"$sort": {"message_history.timestamp": -1}},
                {"$limit": last_n},
                {"$project": {
                    "_id": 0,
                    "role": "$message_history.role",
                    "content": "$message_history.content",
                    "timestamp": "$message_history.timestamp",
                    "message_id": "$message_history.metadata.message_id"
                }}
            ])
            
            recent_messages = list(recent_messages_cursor)
            logger.info(f"MEMORY: Retrieved {len(recent_messages)} recent messages chronologically")
            
            # If query text is provided, perform vector similarity search
            similar_messages = []
            if query_text:
                # Generate embedding for the query text
                logger.info(f"MEMORY: Generating embedding for query: '{query_text[:50]}...'")
                query_embedding = self._get_embedding(query_text)
                
                if query_embedding:
                    logger.info(f"MEMORY: Generated query embedding with {len(query_embedding)} dimensions")
                    
                    # Use $vectorSearch directly on chat_sessions collection
                    try:
                        logger.info(f"MEMORY: Executing $vectorSearch for session {session_id}")
                        
                        # Define the $vectorSearch pipeline
                        vector_pipeline = [
                            {
                                '$vectorSearch': {
                                    'index': 'short_term_memory_vector_index',  # Index name to be created manually in MongoDB Atlas
                                    'path': 'message_history.embedding',  # Path to the embedding field
                                    'queryVector': query_embedding,
                                    'numCandidates': 100,  # Number of candidates to consider
                                    'limit': vector_search_limit * 2,  # Get more than we need to account for possible filtering
                                    'filter': {
                                        'session_id': session_id,
                                        'userId': user_id_str
                                    }
                                }
                            },
                            {
                                '$unwind': '$message_history'  # Unwind the array to access individual messages
                            },
                            {
                                '$match': {
                                    '$expr': {
                                        '$eq': ['$message_history.embedding', '$$SEARCH_META.embedding']
                                    }
                                }
                            },
                            {
                                '$project': {
                                    '_id': 0,
                                    'role': '$message_history.role',
                                    'content': '$message_history.content',
                                    'timestamp': '$message_history.timestamp',
                                    'message_id': {'$ifNull': ['$message_history.metadata.message_id', '']},
                                    'score': {
                                        '$meta': 'vectorSearchScore'
                                    }
                                }
                            },
                            {
                                '$limit': vector_search_limit  # Final limit
                            }
                        ]
                        
                        # Execute the $vectorSearch pipeline
                        vector_results_cursor = self.chat_sessions.aggregate(vector_pipeline)
                        similar_messages = list(vector_results_cursor)
                        
                        logger.info(f"MEMORY: $vectorSearch returned {len(similar_messages)} semantically similar messages")
                        
                        # Log the top result if available
                        if similar_messages:
                            top_result = similar_messages[0]
                            logger.info(f"MEMORY: Top similar message: '{top_result.get('content', '')[:50]}...' (score: {top_result.get('score', 'N/A')})")
                        
                    except Exception as ve:
                        logger.error(f"MEMORY: $vectorSearch failed: {ve}")
                        logger.info("MEMORY: Note that you must create the 'short_term_memory_vector_index' index in MongoDB Atlas manually")
                        logger.info("MEMORY: Falling back to chronological messages only")
                else:
                    logger.error("MEMORY: Failed to generate embedding for query text")
            
            # Combine and deduplicate messages
            all_messages = recent_messages + similar_messages
            
            # Deduplicate based on message_id
            message_ids = set()
            unique_messages = []
            
            for message in all_messages:
                msg_id = message.get("message_id")
                if msg_id and msg_id not in message_ids:
                    message_ids.add(msg_id)
                    unique_messages.append(message)
            
            # Sort by timestamp
            unique_messages.sort(key=lambda x: x.get("timestamp", datetime.datetime.min))
            
            logger.info(f"MEMORY: Returning {len(unique_messages)} unique messages (combined chronological and vector search)")
            return unique_messages
            
        except Exception as e:
            logger.error(f"MEMORY: Error retrieving short-term memory: {e}")
            return []
    
    def retrieve_long_term_memory(
        self, 
        user_id: str, 
        query_text: str, 
        fact_filters: Dict = None, 
        vector_search_limit: int = 5
    ) -> Dict:
        """
        Retrieve user profile facts and semantically similar preferences using MongoDB Atlas Vector Search.
        
        Args:
            user_id (str): The ID of the user
            query_text (str): The text to find semantically similar preferences for
            fact_filters (Dict): Filters to apply to the facts object
            vector_search_limit (int): The number of semantically similar preferences to retrieve
            
        Returns:
            Dict: A dictionary containing matching facts and similar preferences
        """
        try:
            logger.info(f"MEMORY: Retrieving long-term memory for user {user_id}")
            logger.info(f"MEMORY: Query text: '{query_text[:50]}...'")
            
            # Convert user_id to string for consistency
            user_id_str = str(user_id)
            
            # Get the user's facts first (standard query)
            # Use userId field for compatibility with MongoDB Atlas vector search
            match_query = {"userId": user_id_str}
            if fact_filters:
                for key, value in fact_filters.items():
                    match_query[f"facts.{key}"] = value
                logger.debug(f"MEMORY: Applied fact filters: {fact_filters}")
            
            logger.debug(f"MEMORY: Using match query for facts: {match_query}")
            
            # Fetch the user profile for facts
            profile_data = self.user_profiles.find_one(match_query)
            facts = {} if not profile_data else profile_data.get("facts", {})
            
            # Initialize result structure
            result = {
                "matching_facts": facts,
                "similar_preferences": []
            }
            
            # If no query text provided, return just the facts
            if not query_text:
                logger.info(f"MEMORY: No query text provided, returning only facts")
                return result
                
            # Generate embedding for the query text
            logger.info(f"MEMORY: Generating embedding for query text")
            query_embedding = self._get_embedding(query_text)
            if not query_embedding:
                logger.error("MEMORY: Failed to generate embedding for query text")
                return result
                
            embed_dims = len(query_embedding)
            logger.info(f"MEMORY: Generated query embedding with {embed_dims} dimensions")
            
            # Prepare $vectorSearch aggregation pipeline
            try:
                logger.info(f"MEMORY: Running $vectorSearch for semantic similarity")
                
                # Define the $vectorSearch pipeline
                pipeline = [
                    {
                        '$vectorSearch': {
                            'index': 'memory_vector_index',  # Index name to be created manually in MongoDB Atlas
                            'path': 'preferences_embeddings.embedding',  # Path to the embedding field
                            'queryVector': query_embedding,
                            'numCandidates': 100,  # Number of candidates to consider
                            'limit': vector_search_limit,  # Max number of results to return
                            'filter': {
                                'userId': user_id_str  # Filter by the correct user ID field
                            }
                        }
                    },
                    {
                        '$unwind': '$preferences_embeddings'  # Unwind the array to access individual preferences
                    },
                    {
                        '$match': {
                            '$expr': {
                                '$eq': ['$preferences_embeddings.embedding', '$$SEARCH_META.embedding']
                            }
                        }
                    },
                    {
                        '$project': {
                            '_id': 0,
                            'text': '$preferences_embeddings.text',
                            'source_message_id': '$preferences_embeddings.source_message_id',
                            'timestamp': '$preferences_embeddings.timestamp',
                            'score': {
                                '$meta': 'vectorSearchScore'
                            }
                        }
                    }
                ]
                
                # Execute the pipeline
                vector_results = list(self.user_profiles.aggregate(pipeline))
                logger.info(f"MEMORY: $vectorSearch returned {len(vector_results)} similar preferences")
                
                # Add the vector search results to the output
                if vector_results:
                    # Log the top result
                    top_result = vector_results[0]
                    logger.info(f"MEMORY: Top similar preference: '{top_result.get('text', '')[:50]}...' (score: {top_result.get('score', 'N/A')})")
                    
                    # Update the result with the similar preferences
                    result["similar_preferences"] = vector_results
                
            except Exception as search_error:
                logger.error(f"MEMORY: Error during $vectorSearch: {search_error}")
                logger.info("MEMORY: Note that you must create the 'memory_vector_index' index in MongoDB Atlas manually")
                
                # Fallback to just returning facts if vector search fails
                logger.info(f"MEMORY: Falling back to facts-only response due to search error")
            
            return result
            
        except Exception as e:
            logger.error(f"MEMORY: Error retrieving long-term memory: {e}")
            return {"matching_facts": {}, "similar_preferences": []}
    
    def extract_structured_info(self, text: str) -> Dict:
        """
        Extract structured information from text using an LLM.
        
        Args:
            text (str): The text to extract information from
            
        Returns:
            Dict: Structured information extracted from the text
        """
        try:
            # Define the extraction prompt
            system_prompt = """
            Extract structured information from the user's message. Focus on:
            - Personal facts (name, location, profession, etc.)
            - Preferences and interests
            - Opinions and beliefs
            
            Format the output as a JSON object with these fields:
            {
                "name": str or null,
                "location": str or null,
                "profession": str or null,
                "interests": [list of strings] or [],
                "preferences": [list of strings] or [],
                "opinions": [list of strings] or []
            }
            
            Only extract information explicitly stated in the text. Don't infer or make assumptions.
            If a field has no relevant information, set it to null or an empty list.
            """
            
            # Use OpenRouter client for chat completion
            response = self.openrouter_client.chat.completions.create(
                model="anthropic/claude-3.7-sonnet",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ]
            )
            
            # Parse the JSON response
            import json
            content = response.choices[0].message.content
            
            # Debugging log
            logger.debug(f"Raw JSON content: {content}")
            
            # Better error handling for JSON parsing
            try:
                # Try to parse as-is first
                extracted_info = json.loads(content)
            except json.JSONDecodeError as json_err:
                logger.warning(f"Initial JSON parsing failed: {json_err}")
                
                # Try to clean up the content - sometimes models add text before/after JSON
                import re
                json_match = re.search(r'(\{.*\})', content, re.DOTALL)
                if json_match:
                    try:
                        # Try to parse just the JSON object part
                        json_part = json_match.group(1)
                        logger.debug(f"Extracted JSON part: {json_part}")
                        extracted_info = json.loads(json_part)
                    except json.JSONDecodeError:
                        # If that fails, return an empty object
                        logger.error(f"Failed to parse extracted JSON part")
                        return {}
                else:
                    # If we can't find JSON pattern, return empty object
                    logger.error(f"No JSON object found in response")
                    return {}
            
            return extracted_info
            
        except Exception as e:
            logger.error(f"Error extracting structured info: {e}")
            return {}
    
    def update_user_profile(self, user_id: str, info: Dict) -> bool:
        """
        Update a user profile with structured information.
        
        Args:
            user_id (str): The ID of the user
            info (Dict): Structured information to update the profile with
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert user_id to string for consistency
            user_id_str = str(user_id)
            logger.info(f"MEMORY: Updating user profile for user {user_id_str}")
            logger.debug(f"MEMORY: Profile update info: {info}")
            
            # First check if the document already exists (using standardized userId field)
            existing = self.user_profiles.find_one({"userId": user_id_str})
            
            # If not found with userId, try the user_id field for backward compatibility
            if not existing:
                existing = self.user_profiles.find_one({"user_id": user_id_str})
                if existing:
                    logger.info(f"MEMORY: Found profile using legacy 'user_id' field")
            
            # Prepare updates for facts
            update_operations = {
                "$set": {
                    "updated_at": datetime.datetime.utcnow(),
                    "userId": user_id_str  # Always ensure userId is set correctly
                }
            }
            
            # For existing documents, ensure user_id exists for backward compatibility
            if existing and "user_id" not in existing:
                update_operations["$set"]["user_id"] = user_id_str
                logger.info(f"MEMORY: Adding 'user_id' field for backward compatibility")
            
            # Update simple fields
            for field in ["name", "location", "profession"]:
                if field in info and info[field]:
                    logger.info(f"MEMORY: Updating fact '{field}' to '{info[field]}'")
                    update_operations["$set"][f"facts.{field}"] = info[field]
            
            # Update lists using $addToSet to avoid duplicates
            if any(field in info and info[field] for field in ["interests", "opinions"]):
                update_operations["$addToSet"] = {}
                
                for field in ["interests", "opinions"]:
                    if field in info and info[field] and isinstance(info[field], list):
                        logger.info(f"MEMORY: Adding {len(info[field])} items to '{field}'")
                        update_operations["$addToSet"][f"facts.{field}"] = {"$each": info[field]}
            
            # Process preferences and generate embeddings
            if "preferences" in info and info["preferences"] and isinstance(info["preferences"], list):
                pref_count = len(info["preferences"])
                logger.info(f"MEMORY: Processing {pref_count} preferences for embedding")
                
                successful_prefs = 0
                for pref in info["preferences"]:
                    # Generate embedding for the preference
                    logger.debug(f"MEMORY: Generating embedding for preference: '{pref[:30]}...'")
                    pref_embedding = self._get_embedding(pref)
                    
                    if pref_embedding:
                        # Log embedding details
                        embed_dims = len(pref_embedding)
                        logger.debug(f"MEMORY: Generated embedding with {embed_dims} dimensions")
                        
                        # Create preference object
                        pref_obj = {
                            "text": pref,
                            "embedding": pref_embedding,
                            "timestamp": datetime.datetime.utcnow(),
                            "source_message_id": f"extract_{datetime.datetime.utcnow().timestamp()}"
                        }
                        
                        # Add to update operations
                        if "$push" not in update_operations:
                            update_operations["$push"] = {}
                        
                        if "preferences_embeddings" not in update_operations["$push"]:
                            update_operations["$push"]["preferences_embeddings"] = {"$each": []}
                        
                        update_operations["$push"]["preferences_embeddings"]["$each"].append(pref_obj)
                        successful_prefs += 1
                    else:
                        logger.error(f"MEMORY: Failed to generate embedding for preference: '{pref[:30]}...'")
                
                logger.info(f"MEMORY: Successfully embedded {successful_prefs}/{pref_count} preferences")
            
            # Set created_at on insert and ensure both user_id and userId exist
            update_operations["$setOnInsert"] = {
                "user_id": user_id_str,  # Keep for backward compatibility
                "created_at": datetime.datetime.utcnow()
            }
            
            # Use standardized userId field in query for MongoDB Atlas vector search compatibility
            query = {"userId": user_id_str}
            
            # Perform the update
            result = self.user_profiles.update_one(
                query,
                update_operations,
                upsert=True
            )
            
            if result.acknowledged:
                logger.info(f"MEMORY: Successfully updated profile for user {user_id_str}")
                logger.debug(f"MEMORY: MongoDB result - matched: {result.matched_count}, modified: {result.modified_count}, upserted_id: {result.upserted_id}")
            else:
                logger.warning("MEMORY: MongoDB operation not acknowledged")
                
            return True
            
        except Exception as e:
            logger.error(f"MEMORY: Error updating user profile: {e}")
            return False
    
    def rewrite_query(self, chat_history: List[Dict], follow_up_query: str) -> str:
        """
        Rewrite a follow-up query to include context from chat history.
        
        Args:
            chat_history (List[Dict]): Recent chat history
            follow_up_query (str): The follow-up query to rewrite
            
        Returns:
            str: The rewritten query
        """
        try:
            # Prepare conversation history for the prompt
            conversation_context = ""
            for msg in chat_history[-5:]:  # Use last 5 messages for context
                role = msg.get("role", "")
                content = msg.get("content", "")
                conversation_context += f"{role}: {content}\n"
            
            # Define the rewrite prompt
            system_prompt = """
            You are an AI assistant helping to rewrite a follow-up query into a standalone query.
            The follow-up query may reference context from the conversation history.
            Your task is to create a clear, self-contained query that incorporates any necessary context.
            Do not add information that isn't implied by the conversation.
            Make the query concise and focused.
            """
            
            user_prompt = f"""
            Conversation history:
            {conversation_context}
            
            Follow-up query: {follow_up_query}
            
            Rewrite this as a standalone query that includes all necessary context:
            """
            
            # Use OpenRouter client for chat completion
            response = self.openrouter_client.chat.completions.create(
                model="anthropic/claude-3.7-sonnet",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Get the rewritten query
            rewritten_query = response.choices[0].message.content.strip()
            
            logger.info(f"Rewrote query: '{follow_up_query}' -> '{rewritten_query}'")
            return rewritten_query
            
        except Exception as e:
            logger.error(f"Error rewriting query: {e}")
            return follow_up_query  # Return original query on error