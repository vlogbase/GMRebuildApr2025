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
            logger.info(f"MEMORY: Adding message to session {session_id} for user {user_id}, role: {role}")
            
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
            
            # First check if the document already exists (check both field names)
            query = {"session_id": session_id, "$or": [{"user_id": user_id}, {"userId": user_id}]}
            existing = self.chat_sessions.find_one(query)
            
            # Build the update operation based on what exists
            update_op = {
                "$push": {"message_history": message},
                "$set": {"updated_at": datetime.datetime.utcnow()}
            }
            
            # For existing documents, check for field consistency
            if existing:
                # Check for mismatched field names
                user_id_exists = "user_id" in existing
                userId_exists = "userId" in existing
                
                # Only add missing fields
                if user_id_exists and not userId_exists:
                    update_op["$set"]["userId"] = user_id
                    logger.info(f"MEMORY: Adding missing 'userId' field to chat session")
                elif userId_exists and not user_id_exists:
                    update_op["$set"]["user_id"] = user_id
                    logger.info(f"MEMORY: Adding missing 'user_id' field to chat session")
            else:
                # For new documents, set both field names and creation time
                logger.info(f"MEMORY: Creating new chat session with both field names")
                update_op["$setOnInsert"] = {
                    "user_id": user_id,
                    "userId": user_id,
                    "created_at": datetime.datetime.utcnow()
                }
            
            # Store both user_id and userId for compatibility with MongoDB Atlas Vector Search
            result = self.chat_sessions.update_one(
                {"session_id": session_id, "$or": [{"user_id": user_id}, {"userId": user_id}]},
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
            # Get the most recent messages chronologically (use both field names)
            recent_messages_cursor = self.chat_sessions.aggregate([
                {"$match": {
                    "session_id": session_id, 
                    "$or": [
                        {"user_id": user_id},
                        {"userId": user_id}
                    ]
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
            
            # If query text is provided, perform vector similarity search
            similar_messages = []
            if query_text:
                # Generate embedding for the query text
                query_embedding = self._get_embedding(query_text)
                if query_embedding:
                    # Perform vector search using $vectorSearch
                    try:
                        # MongoDB Atlas requires $vectorSearch to be the first stage in the pipeline
                        # Extract session first, then use $vectorSearch on the message_history
                        # Use both field names for compatibility
                        session_data = self.chat_sessions.find_one({
                            "session_id": session_id, 
                            "$or": [
                                {"user_id": user_id},
                                {"userId": user_id}
                            ]
                        })
                        
                        if session_data and "message_history" in session_data:
                            # Now we can run vector search on the messages
                            message_docs = []
                            for msg in session_data["message_history"]:
                                # Add each message as a document for vector search
                                if "embedding" in msg:
                                    msg_doc = {
                                        "embedding": msg["embedding"],
                                        "role": msg["role"],
                                        "content": msg["content"],
                                        "timestamp": msg["timestamp"],
                                        "message_id": msg["metadata"]["message_id"] if "metadata" in msg and "message_id" in msg["metadata"] else ""
                                    }
                                    message_docs.append(msg_doc)
                            
                            # If we have messages with embeddings, create a temporary collection for vector search
                            if message_docs:
                                # Create a unique temp collection name
                                import uuid
                                temp_coll_name = f"temp_vector_search_{uuid.uuid4().hex[:8]}"
                                temp_coll = self.db.get_collection(temp_coll_name)
                                
                                # Insert the message documents
                                temp_coll.insert_many(message_docs)
                                
                                # Create the index on the temp collection
                                temp_coll.create_index([("embedding", pymongo.ASCENDING)])
                                
                                # Now run a simple vector similarity search (not using $vectorSearch)
                                # We'll approximate it using dot product
                                pipeline = [
                                    {"$project": {
                                        "role": 1,
                                        "content": 1,
                                        "timestamp": 1,
                                        "message_id": 1,
                                        "similarity": {
                                            "$reduce": {
                                                "input": {"$zip": {"inputs": ["$embedding", query_embedding]}},
                                                "initialValue": 0,
                                                "in": {"$add": ["$$value", {"$multiply": [{"$arrayElemAt": ["$$this", 0]}, {"$arrayElemAt": ["$$this", 1]}]}]}
                                            }
                                        }
                                    }},
                                    {"$sort": {"similarity": -1}},
                                    {"$limit": vector_search_limit},
                                    {"$project": {
                                        "_id": 0,
                                        "role": 1,
                                        "content": 1,
                                        "timestamp": 1,
                                        "message_id": 1,
                                        "score": "$similarity"
                                    }}
                                ]
                                
                                vector_results = temp_coll.aggregate(pipeline)
                                
                                # Clean up the temp collection after use
                                self.db.drop_collection(temp_coll_name)
                            else:
                                # No messages with embeddings
                                vector_results = []
                        else:
                            # No session data
                            vector_results = []
                        
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
            logger.info(f"MEMORY: Retrieving long-term memory for user {user_id}")
            logger.info(f"MEMORY: Query text: '{query_text[:50]}...'")
            
            # Build the match query - include both user_id and userId for compatibility
            match_query = {"$or": [{"user_id": user_id}, {"userId": user_id}]}
            if fact_filters:
                for key, value in fact_filters.items():
                    match_query[f"facts.{key}"] = value
                logger.debug(f"MEMORY: Applied fact filters: {fact_filters}")
            
            logger.debug(f"MEMORY: Using match query: {match_query}")
            
            # Generate embedding for the query text
            query_embedding = None
            if query_text:
                logger.info(f"MEMORY: Generating embedding for query text")
                query_embedding = self._get_embedding(query_text)
                if query_embedding:
                    embed_dims = len(query_embedding)
                    logger.info(f"MEMORY: Generated query embedding with {embed_dims} dimensions")
                else:
                    logger.error("MEMORY: Failed to generate embedding for query text")
            
            if query_embedding:
                # Perform vector search
                try:
                    # First, get the user profile data
                    logger.info(f"MEMORY: Retrieving user profile data")
                    profile_data = self.user_profiles.find_one(match_query)
                    
                    if profile_data:
                        logger.info(f"MEMORY: Found user profile with ID: {profile_data.get('_id')}")
                        
                        # Ensure the profile has both user_id and userId fields
                        try:
                            # Add missing fields if needed
                            if "user_id" in profile_data and "userId" not in profile_data:
                                self.user_profiles.update_one(
                                    {"_id": profile_data["_id"]},
                                    {"$set": {"userId": profile_data["user_id"]}}
                                )
                                logger.info(f"MEMORY: Added missing userId field to profile")
                            elif "userId" in profile_data and "user_id" not in profile_data:
                                self.user_profiles.update_one(
                                    {"_id": profile_data["_id"]},
                                    {"$set": {"user_id": profile_data["userId"]}}
                                )
                                logger.info(f"MEMORY: Added missing user_id field to profile")
                        except Exception as fix_error:
                            logger.error(f"MEMORY: Error fixing user ID fields: {fix_error}")
                        
                    if profile_data and "preferences_embeddings" in profile_data:
                        # Get facts from profile
                        facts = profile_data.get("facts", {})
                        
                        # Prepare preference documents for similarity search
                        pref_docs = []
                        for pref in profile_data["preferences_embeddings"]:
                            if "embedding" in pref:
                                pref_doc = {
                                    "embedding": pref["embedding"],
                                    "text": pref.get("text", ""),
                                    "source_message_id": pref.get("source_message_id", ""),
                                    "timestamp": pref.get("timestamp", datetime.datetime.utcnow())
                                }
                                pref_docs.append(pref_doc)
                        
                        # If we have preferences with embeddings
                        if pref_docs:
                            # Create a temporary collection
                            import uuid
                            temp_coll_name = f"temp_pref_search_{uuid.uuid4().hex[:8]}"
                            temp_coll = self.db.get_collection(temp_coll_name)
                            
                            # Insert preference documents
                            temp_coll.insert_many(pref_docs)
                            
                            # Create the index
                            temp_coll.create_index([("embedding", pymongo.ASCENDING)])
                            
                            # Run similarity search
                            pipeline = [
                                {"$project": {
                                    "text": 1,
                                    "source_message_id": 1,
                                    "timestamp": 1,
                                    "similarity": {
                                        "$reduce": {
                                            "input": {"$zip": {"inputs": ["$embedding", query_embedding]}},
                                            "initialValue": 0,
                                            "in": {"$add": ["$$value", {"$multiply": [{"$arrayElemAt": ["$$this", 0]}, {"$arrayElemAt": ["$$this", 1]}]}]}
                                        }
                                    }
                                }},
                                {"$sort": {"similarity": -1}},
                                {"$limit": vector_search_limit},
                                {"$project": {
                                    "_id": 0,
                                    "text": 1,
                                    "source_message_id": 1,
                                    "timestamp": 1,
                                    "score": "$similarity"
                                }}
                            ]
                            
                            similar_prefs = list(temp_coll.aggregate(pipeline))
                            
                            # Clean up
                            self.db.drop_collection(temp_coll_name)
                            
                            # Prepare result
                            result = {
                                "matching_facts": facts,
                                "similar_preferences": similar_prefs
                            }
                            
                            return result
                    
                    # Return an empty result with just the facts
                    if profile_data:
                        results = [{
                            "facts": profile_data.get("facts", {}),
                            "similar_preferences": []
                        }]
                    else:
                        results = []
                    
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
            logger.info(f"MEMORY: Updating user profile for user {user_id}")
            logger.debug(f"MEMORY: Profile update info: {info}")
            
            # First check if the document already exists (check both field names)
            existing = self.user_profiles.find_one({"$or": [{"user_id": user_id}, {"userId": user_id}]})
            
            # Prepare updates for facts
            update_operations = {
                "$set": {
                    "updated_at": datetime.datetime.utcnow()
                }
            }
            
            # Check for mismatched field names
            if existing:
                user_id_exists = "user_id" in existing
                userId_exists = "userId" in existing
                
                if user_id_exists and not userId_exists:
                    logger.info(f"MEMORY: Adding missing 'userId' field to existing profile")
                    update_operations["$set"]["userId"] = user_id
                elif userId_exists and not user_id_exists:
                    logger.info(f"MEMORY: Adding missing 'user_id' field to existing profile")
                    update_operations["$set"]["user_id"] = existing["userId"]
            
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
                "user_id": user_id,
                "userId": user_id,  # Add userId field to match Atlas vector search index path
                "created_at": datetime.datetime.utcnow()
            }
            
            # Define query - use both fields if existing, just user_id if new
            if existing:
                query = {"$or": [{"user_id": user_id}, {"userId": user_id}]}
            else:
                query = {"user_id": user_id}
            
            # Perform the update
            result = self.user_profiles.update_one(
                query,
                update_operations,
                upsert=True
            )
            
            if result.acknowledged:
                logger.info(f"MEMORY: Successfully updated profile for user {user_id}")
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