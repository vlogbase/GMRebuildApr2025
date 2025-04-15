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
        
        # Initialize OpenAI client for embeddings
        try:
            # Use Azure OpenAI if available
            if os.environ.get("AZURE_OPENAI_API_KEY") and os.environ.get("AZURE_OPENAI_ENDPOINT"):
                self.use_azure = True
                self.azure_api_key = os.environ.get("AZURE_OPENAI_API_KEY")
                self.azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
                self.embedding_deployment = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
                self.chat_deployment = os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
                
                # Initialize Azure OpenAI client
                self.openai_client = openai.AzureOpenAI(
                    api_key=self.azure_api_key,
                    api_version="2024-02-01",
                    azure_endpoint=self.azure_endpoint
                )
                logger.info("Azure OpenAI client initialized successfully")
            
            # Fall back to OpenRouter if Azure not configured
            elif os.environ.get("OPENROUTER_API_KEY"):
                self.use_azure = False
                self.openai_client = OpenAI(
                    api_key=os.environ.get("OPENROUTER_API_KEY"),
                    base_url="https://openrouter.ai/api/v1"
                )
                logger.info("OpenRouter client initialized successfully")
            
            else:
                logger.error("No API keys found for Azure OpenAI or OpenRouter")
                raise ValueError("No API keys found for embedding or chat models")
                
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
            
            logger.info("MongoDB indexes created successfully")
            
            # Note: Vector search indexes must be created via Atlas UI or API
            # They cannot be created via the driver directly
            # Index names should be 'idx_message_embedding_large' for chat_sessions
            # and 'idx_preference_embedding_large' for user_profiles
            
        except Exception as e:
            logger.error(f"Error creating MongoDB indexes: {e}")
            raise
    
    def _get_embedding(self, text: str) -> List[float]:
        """
        Generate a vector embedding for text using the text-embedding-3-large model.
        
        Args:
            text (str): The text to generate an embedding for
            
        Returns:
            List[float]: A 3072-dimension embedding vector
            
        Raises:
            Exception: If embedding generation fails
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * 3072  # Return zero vector for empty text
        
        try:
            # Use Azure OpenAI for embeddings
            if self.use_azure:
                response = self.openai_client.embeddings.create(
                    input=text,
                    model=self.embedding_deployment
                )
                return response.data[0].embedding
            
            # Use OpenRouter for embeddings (fallback)
            else:
                response = self.openai_client.embeddings.create(
                    input=text,
                    model="google/text-embedding-004"  # 768-dimensions, not full 3072
                )
                
                # Return the embedding, padded to 3072 if necessary
                embedding = response.data[0].embedding
                
                # Pad if needed (this is a workaround and not ideal for vector search)
                if len(embedding) < 3072:
                    logger.warning(f"Embedding has {len(embedding)} dimensions, padding to 3072")
                    embedding = embedding + [0.0] * (3072 - len(embedding))
                
                return embedding
                
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
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
            # Generate embedding for the content
            embedding = self._get_embedding(content)
            if not embedding:
                logger.error("Failed to generate embedding for message")
                return False
            
            # Create the message document
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.datetime.utcnow(),
                "embedding": embedding,
                "metadata": {"message_id": f"{session_id}_{datetime.datetime.utcnow().timestamp()}"}
            }
            
            # Update or create the chat session
            result = self.chat_sessions.update_one(
                {"session_id": session_id, "user_id": user_id},
                {
                    "$push": {"message_history": message},
                    "$set": {"updated_at": datetime.datetime.utcnow()},
                    "$setOnInsert": {
                        "user_id": user_id,
                        "created_at": datetime.datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            logger.info(f"Added message to session {session_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding message: {e}")
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
            # Get the most recent messages chronologically
            recent_messages_cursor = self.chat_sessions.aggregate([
                {"$match": {"session_id": session_id, "user_id": user_id}},
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
            
            # If query text is provided, perform vector similarity search
            similar_messages = []
            if query_text:
                # Generate embedding for the query text
                query_embedding = self._get_embedding(query_text)
                if query_embedding:
                    # Perform vector search using $vectorSearch
                    try:
                        vector_results = self.chat_sessions.aggregate([
                            {"$match": {"session_id": session_id, "user_id": user_id}},
                            {"$unwind": "$message_history"},
                            {"$vectorSearch": {
                                "index": "idx_message_embedding_large",
                                "path": "message_history.embedding",
                                "queryVector": query_embedding,
                                "numCandidates": 100,
                                "limit": vector_search_limit
                            }},
                            {"$project": {
                                "_id": 0,
                                "role": "$message_history.role",
                                "content": "$message_history.content",
                                "timestamp": "$message_history.timestamp",
                                "message_id": "$message_history.metadata.message_id",
                                "score": {"$meta": "vectorSearchScore"}
                            }}
                        ])
                        
                        similar_messages = list(vector_results)
                        
                    except OperationFailure as e:
                        # Vector search might fail if index is not set up
                        logger.error(f"Vector search failed: {e}")
                        # Fallback to recent messages only
            
            # Combine and deduplicate messages
            all_messages = recent_messages + similar_messages
            
            # Deduplicate based on message_id
            message_ids = set()
            unique_messages = []
            
            for message in all_messages:
                if message.get("message_id") not in message_ids:
                    message_ids.add(message.get("message_id"))
                    unique_messages.append(message)
            
            # Sort by timestamp
            unique_messages.sort(key=lambda x: x.get("timestamp", datetime.datetime.min))
            
            return unique_messages
            
        except Exception as e:
            logger.error(f"Error retrieving short-term memory: {e}")
            return []
    
    def retrieve_long_term_memory(
        self, 
        user_id: str, 
        query_text: str, 
        fact_filters: Dict = None, 
        vector_search_limit: int = 5
    ) -> Dict:
        """
        Retrieve user profile facts and semantically similar preferences.
        
        Args:
            user_id (str): The ID of the user
            query_text (str): The text to find semantically similar preferences for
            fact_filters (Dict): Filters to apply to the facts object
            vector_search_limit (int): The number of semantically similar preferences to retrieve
            
        Returns:
            Dict: A dictionary containing matching facts and similar preferences
        """
        try:
            # Build the match query
            match_query = {"user_id": user_id}
            if fact_filters:
                for key, value in fact_filters.items():
                    match_query[f"facts.{key}"] = value
            
            # Generate embedding for the query text
            query_embedding = None
            if query_text:
                query_embedding = self._get_embedding(query_text)
            
            if query_embedding:
                # Perform vector search
                try:
                    pipeline = [
                        {"$match": match_query},
                        {"$vectorSearch": {
                            "index": "idx_preference_embedding_large",
                            "path": "preferences_embeddings.embedding",
                            "queryVector": query_embedding,
                            "numCandidates": 100,
                            "limit": vector_search_limit
                        }},
                        {"$project": {
                            "_id": 0,
                            "facts": 1,
                            "similar_preferences": {
                                "$map": {
                                    "input": "$preferences_embeddings",
                                    "as": "pref",
                                    "in": {
                                        "text": "$$pref.text",
                                        "source_message_id": "$$pref.source_message_id",
                                        "timestamp": "$$pref.timestamp",
                                        "score": {"$meta": "vectorSearchScore"}
                                    }
                                }
                            }
                        }}
                    ]
                    
                    results = list(self.user_profiles.aggregate(pipeline))
                    
                    if results:
                        return {
                            "matching_facts": results[0].get("facts", {}),
                            "similar_preferences": results[0].get("similar_preferences", [])
                        }
                    
                except OperationFailure as e:
                    # Vector search might fail if index is not set up
                    logger.error(f"Vector search failed in long-term memory: {e}")
            
            # Fallback to standard query without vector search
            profile = self.user_profiles.find_one(
                match_query,
                {"_id": 0, "facts": 1}
            )
            
            if profile:
                return {
                    "matching_facts": profile.get("facts", {}),
                    "similar_preferences": []
                }
            
            return {"matching_facts": {}, "similar_preferences": []}
            
        except Exception as e:
            logger.error(f"Error retrieving long-term memory: {e}")
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
            
            # Use the appropriate client
            if self.use_azure:
                response = self.openai_client.chat.completions.create(
                    model=self.chat_deployment,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text}
                    ]
                )
            else:
                response = self.openai_client.chat.completions.create(
                    model="anthropic/claude-3-haiku-20240307",
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text}
                    ]
                )
            
            # Parse the JSON response
            import json
            content = response.choices[0].message.content
            extracted_info = json.loads(content)
            
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
            # Prepare updates for facts
            update_operations = {
                "$set": {"updated_at": datetime.datetime.utcnow()}
            }
            
            # Update simple fields
            for field in ["name", "location", "profession"]:
                if field in info and info[field]:
                    update_operations["$set"][f"facts.{field}"] = info[field]
            
            # Update lists using $addToSet to avoid duplicates
            for field in ["interests", "opinions"]:
                if field in info and info[field]:
                    update_operations["$addToSet"][f"facts.{field}"] = {"$each": info[field]}
            
            # Process preferences and generate embeddings
            if "preferences" in info and info["preferences"]:
                for pref in info["preferences"]:
                    # Generate embedding for the preference
                    pref_embedding = self._get_embedding(pref)
                    if pref_embedding:
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
            
            # Set created_at on insert
            update_operations["$setOnInsert"] = {
                "user_id": user_id,
                "created_at": datetime.datetime.utcnow()
            }
            
            # Update the user profile
            result = self.user_profiles.update_one(
                {"user_id": user_id},
                update_operations,
                upsert=True
            )
            
            logger.info(f"Updated profile for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
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
            
            # Use the appropriate client
            if self.use_azure:
                response = self.openai_client.chat.completions.create(
                    model=self.chat_deployment,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                )
            else:
                response = self.openai_client.chat.completions.create(
                    model="anthropic/claude-3-haiku-20240307",
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