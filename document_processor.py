"""
Document Processor Module for the RAG (Retrieval-Augmented Generation) functionality.

This module handles document processing, text extraction, chunking, embedding generation, 
and MongoDB storage for various document types.
"""
import os
import re
import json
import logging
import tempfile
from typing import BinaryIO, Dict, List, Optional, Union, Any
from io import BytesIO
from datetime import datetime
import hashlib
from zipfile import ZipFile

# Document parsing libraries
try:
    import docx
    from pypdf import PdfReader
    from striprtf.striprtf import rtf_to_text
    from bs4 import BeautifulSoup
except ImportError as e:
    logging.warning(f"Some document processing libraries could not be imported: {e}")

# MongoDB for vector storage
try:
    import pymongo
    from pymongo.errors import PyMongoError
except ImportError as e:
    logging.warning(f"MongoDB libraries could not be imported: {e}")

# Logging configuration
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Custom logging formatter for RAG
def _log_rag(message, level='info'):
    """Helper function to log with RAG prefix"""
    prefix = "RAG [Processor]:"
    if level == 'debug':
        logger.debug(f"{prefix} {message}")
    elif level == 'info':
        logger.info(f"{prefix} {message}")
    elif level == 'warning':
        logger.warning(f"{prefix} {message}")
    elif level == 'error':
        logger.error(f"{prefix} {message}")
    elif level == 'critical':
        logger.critical(f"{prefix} {message}")

class DocumentProcessor:
    """
    Handles document processing for RAG functionality including:
    - Text extraction from various file formats
    - Chunking extracted text
    - Generating embeddings
    - Storing in MongoDB with vector search capabilities
    """
    
    def __init__(self):
        """
        Initialize the DocumentProcessor with MongoDB connection.
        Reuses the existing embedding generation capabilities.
        """
        # Load environment variables
        self.mongo_uri = os.environ.get('MONGODB_ATLAS_URI')
        self.openai_api_key = os.environ.get('AZURE_OPENAI_API_KEY') or os.environ.get('OPENROUTER_API_KEY')
        
        # Set up MongoDB collections if MongoDB URI is available
        self.db_initialized = False
        if self.mongo_uri:
            try:
                self.client = pymongo.MongoClient(self.mongo_uri)
                self.db = self.client['memory']
                self.documents_collection = self.db['documents']
                self.chunks_collection = self.db['document_chunks']
                self.db_initialized = True
                
                # Create indexes if they don't exist
                self._ensure_indexes()
                logger.info("MongoDB connected successfully for document storage")
            except PyMongoError as e:
                logger.error(f"Error connecting to MongoDB: {e}")
                self.client = None
                self.db = None
                self.documents_collection = None
                self.chunks_collection = None
                self.db_initialized = False
        else:
            logger.warning("MONGODB_ATLAS_URI not set. Document storage will not be available.")
            self.client = None
            self.db = None
            self.documents_collection = None
            self.chunks_collection = None
            self.db_initialized = False
        
        # Check for Azure OpenAI credentials
        azure_key = os.environ.get('AZURE_OPENAI_API_KEY')
        azure_endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')
        azure_deployment = os.environ.get('AZURE_OPENAI_DEPLOYMENT')
        
        if not (azure_key and azure_endpoint and azure_deployment):
            _log_rag("Azure OpenAI credentials are not properly configured!", level='error')
            _log_rag("RAG functionality requires AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_DEPLOYMENT", level='error')
            # The system will still initialize but embedding functionality will not work
            # The _get_embedding method will raise exceptions when called
        else:
            _log_rag(f"Azure OpenAI credentials found for embeddings (deployment: {azure_deployment})", level='info')
            
        # Import the embedding function from the memory module if available
        try:
            from chat_memory_manager import ChatMemoryManager
            self.memory_manager = ChatMemoryManager()
            # Use our own method which calls the memory manager but with better error handling
            self._get_embedding = self._get_embedding_azure
            _log_rag("Using Azure OpenAI for embeddings via ChatMemoryManager", level='info')
        except ImportError:
            _log_rag("ChatMemoryManager not available - embedding generation will not work", level='error')
            # Define a method that will raise an appropriate exception
            def _embedding_not_available(text: str) -> List[float]:
                raise RuntimeError("Azure OpenAI embedding generation is not available - ChatMemoryManager could not be imported")
            self._get_embedding = _embedding_not_available
    
    def _ensure_indexes(self):
        """
        Create necessary standard indexes on MongoDB collections.
        Note: The vector search index (named 'vector_index') must be created manually 
        in the MongoDB Atlas UI on the 'memory.document_chunks' collection.
        """
        if not self.db_initialized:
            logger.warning("MongoDB not available. Skipping index creation.")
            return
        
        try:
            # Index for documents collection
            self.documents_collection.create_index([("user_id", pymongo.ASCENDING)])
            self.documents_collection.create_index([("filename", pymongo.ASCENDING)])
            
            # Indexes for document chunks collection
            self.chunks_collection.create_index([("document_id", pymongo.ASCENDING)])
            self.chunks_collection.create_index([("user_id", pymongo.ASCENDING)])
            
            # Note: The vector search index named 'vector_index' must be created manually
            # in the MongoDB Atlas UI, configured for the 'embedding' field with the
            # correct dimensionality (3072) and similarity metric.
            
            logger.info("MongoDB standard indexes created successfully")
        except PyMongoError as e:
            logger.error(f"Error creating MongoDB indexes: {e}")
    
    def _get_embedding_azure(self, text: str) -> List[float]:
        """
        Get an embedding from Azure OpenAI with detailed error handling.
        
        Args:
            text: The text to generate an embedding for
            
        Returns:
            A vector embedding (3072 dimensions) from Azure OpenAI
        
        Raises:
            RuntimeError: If the embedding can't be generated using Azure OpenAI
        """
        try:
            # Forward the embedding request to the memory manager
            _log_rag(f"Getting Azure embedding for text: '{text[:50]}...'", level='debug')
            
            # Use memory manager's embedding function (which uses Azure OpenAI)
            embedding = self.memory_manager._get_embedding(text)
            
            # Validate the embedding
            if embedding and isinstance(embedding, list) and len(embedding) > 0:
                _log_rag(f"Successfully generated Azure embedding with {len(embedding)} dimensions", level='debug')
                return embedding
            else:
                raise RuntimeError("Azure OpenAI returned empty or invalid embedding")
                
        except Exception as e:
            error_msg = f"Failed to generate Azure OpenAI embedding: {e}"
            _log_rag(error_msg, level='error')
            # Re-raise with a clear error message
            raise RuntimeError(error_msg)
    
    def extract_text(self, file_stream: BinaryIO, filename: str) -> Optional[str]:
        """
        Extract text from various file formats.
        
        Args:
            file_stream: The file stream
            filename: The name of the file (used to determine file type)
            
        Returns:
            str: Extracted text or None if extraction failed
        """
        try:
            file_ext = os.path.splitext(filename)[1].lower()
            
            # Create a copy of the file stream to avoid consuming it
            file_data = file_stream.read()
            file_stream.seek(0)
            
            # Extract text based on file type
            if file_ext == '.pdf':
                # Extract text from PDF
                pdf = PdfReader(BytesIO(file_data))
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
                return text
                
            elif file_ext == '.docx':
                # Extract text from Word document
                doc = docx.Document(BytesIO(file_data))
                text = ""
                for para in doc.paragraphs:
                    text += para.text + "\n"
                return text
                
            elif file_ext == '.txt':
                # Extract text from plain text file
                return file_data.decode('utf-8', errors='replace')
                
            elif file_ext == '.rtf':
                # Extract text from RTF
                rtf_text = file_data.decode('utf-8', errors='replace')
                return rtf_to_text(rtf_text)
                
            elif file_ext in ['.html', '.htm']:
                # Extract text from HTML
                html = file_data.decode('utf-8', errors='replace')
                soup = BeautifulSoup(html, 'lxml')
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.extract()
                # Get text
                text = soup.get_text(separator="\n")
                # Remove multiple newlines
                text = re.sub(r'\n+', '\n\n', text)
                return text
                
            elif file_ext in ['.json']:
                # Extract text from JSON
                json_data = json.loads(file_data.decode('utf-8', errors='replace'))
                return json.dumps(json_data, indent=2)
                
            elif file_ext in ['.csv', '.tsv']:
                # Extract text from CSV/TSV
                return file_data.decode('utf-8', errors='replace')
                
            elif file_ext in ['.xml']:
                # Extract text from XML
                try:
                    xml_text = file_data.decode('utf-8', errors='replace')
                    soup = BeautifulSoup(xml_text, 'xml')
                    # Remove tags but keep their content
                    text = soup.get_text(separator="\n")
                    return text
                except Exception as e:
                    logger.warning(f"Error parsing XML file {filename}: {e}")
                    # Fallback to plain text
                    return file_data.decode('utf-8', errors='replace')
                    
            elif file_ext in ['.odt']:
                # Extract text from ODT (OpenDocument Text)
                try:
                    # ODT files are ZIP archives with content in content.xml
                    with ZipFile(BytesIO(file_data)) as odt_zip:
                        if 'content.xml' in odt_zip.namelist():
                            content_xml = odt_zip.read('content.xml').decode('utf-8')
                            soup = BeautifulSoup(content_xml, 'xml')
                            text = soup.get_text(separator="\n")
                            return text
                    logger.warning(f"Could not find content.xml in ODT file: {filename}")
                    return None
                except Exception as e:
                    logger.warning(f"Error extracting text from ODT file {filename}: {e}")
                    return None
                    
            else:
                # For unsupported formats, try to extract as plain text
                try:
                    return file_data.decode('utf-8', errors='replace')
                except UnicodeDecodeError:
                    logger.warning(f"Cannot extract text from {filename}: unsupported format")
                    return None
        
        except Exception as e:
            logger.exception(f"Error extracting text from {filename}: {e}")
            return None
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """
        Split text into chunks of specified size with overlap.
        
        Args:
            text: The text to chunk
            chunk_size: Maximum characters per chunk
            overlap: Number of overlapping characters between chunks
            
        Returns:
            List[str]: List of text chunks
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Get the end position for this chunk
            end = start + chunk_size
            
            # If this is not the last chunk, try to break at a sentence or paragraph boundary
            if end < len(text):
                # Try to find paragraph break first
                paragraph_break = text.rfind('\n\n', start, end)
                
                # Try to find sentence break if paragraph break not found or too far back
                sentence_break = text.rfind('. ', start, end)
                
                # Find a reasonable breakpoint
                half_chunk = start + int(chunk_size * 0.5)
                if paragraph_break > half_chunk:
                    end = paragraph_break + 2  # Include the newlines
                elif sentence_break > half_chunk:
                    end = sentence_break + 2  # Include the period and space
            
            # Extract the chunk
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move to the next chunk start position with overlap
            start = end - overlap if end < len(text) else len(text)
        
        return chunks
    
    def process_and_store_document(self, file_stream: BinaryIO, filename: str, user_id: Union[str, int]) -> Dict[str, Any]:
        """
        Process a document: extract text, chunk it, generate embeddings, and store in MongoDB.
        
        Args:
            file_stream: The file stream
            filename: The name of the file
            user_id: The ID of the user uploading the document
            
        Returns:
            Dict: Status information about the processing
        """
        if not self.db_initialized:
            _log_rag("MongoDB not available for document storage", level='error')
            return {
                "success": False,
                "error": "MongoDB not available for document storage"
            }
        
        try:
            # Extract text from the document
            _log_rag(f"Starting text extraction from {filename} for user {user_id}", level='info')
            extracted_text = self.extract_text(file_stream, filename)
            if not extracted_text:
                _log_rag(f"Could not extract text from {filename}", level='error')
                return {
                    "success": False,
                    "error": f"Could not extract text from {filename}"
                }
            
            _log_rag(f"Successfully extracted {len(extracted_text)} characters from {filename}", level='info')
            
            # Create document entry
            document = {
                "user_id": str(user_id),
                "filename": filename,
                "file_type": os.path.splitext(filename)[1].lower(),
                "upload_timestamp": datetime.utcnow(),
                "text_length": len(extracted_text),
                "processed": True
            }
            
            # Store document in MongoDB
            document_id = self.documents_collection.insert_one(document).inserted_id
            _log_rag(f"Created document record with ID: {document_id}", level='info')
            
            # Chunk the text
            chunks = self.chunk_text(extracted_text)
            _log_rag(f"Split document into {len(chunks)} chunks", level='info')
            
            # Process and store each chunk
            chunk_count = 0
            for i, chunk_text in enumerate(chunks):
                # Generate embedding for the chunk
                _log_rag(f"Generating embedding for chunk {i+1}/{len(chunks)}", level='debug')
                embedding = self._get_embedding(chunk_text)
                
                # Create chunk entry
                chunk = {
                    "document_id": document_id,
                    "user_id": str(user_id),  # Keep this for backward compatibility
                    "userId": str(user_id),   # Add this to match the index filter field
                    "chunk_index": i,
                    "text_chunk": chunk_text,
                    "embedding": embedding,
                    "source_document_name": filename,
                    "timestamp": datetime.utcnow()
                }
                
                # Store chunk in MongoDB
                self.chunks_collection.insert_one(chunk)
                chunk_count += 1
                
                # Log progress periodically
                if chunk_count % 5 == 0 or chunk_count == len(chunks):
                    _log_rag(f"Processed and stored {chunk_count}/{len(chunks)} chunks", level='info')
            
            # Update the document with chunk count
            self.documents_collection.update_one(
                {"_id": document_id},
                {"$set": {"chunk_count": chunk_count}}
            )
            
            _log_rag(f"Document processing complete: {filename}, {chunk_count} chunks, {len(extracted_text)} chars", level='info')
            return {
                "success": True,
                "document_id": str(document_id),
                "filename": filename,
                "chunk_count": chunk_count,
                "text_length": len(extracted_text)
            }
            
        except Exception as e:
            _log_rag(f"Error processing document {filename}: {e}", level='error')
            return {
                "success": False,
                "error": str(e)
            }
    
    def diagnostic_fetch_chunks(self, user_id: Union[str, int], limit: int = 5) -> Dict[str, Any]:
        """
        Diagnostic function to check what chunks exist for a user without using vector search.
        
        Args:
            user_id: The ID of the user
            limit: Maximum number of chunks to return
            
        Returns:
            Dict: Diagnostic information about stored chunks
        """
        if not self.db_initialized:
            _log_rag("MongoDB not available for diagnostics", level='warning')
            return {"error": "MongoDB not initialized"}
        
        try:
            # Convert user_id to string for consistency
            user_id_str = str(user_id)
            
            # Check for documents with user_id field
            user_id_count = self.chunks_collection.count_documents({"user_id": user_id_str})
            
            # Check for documents with userId field (used by vector search)
            userId_count = self.chunks_collection.count_documents({"userId": user_id_str})
            
            # Check for documents with both fields
            both_fields_count = self.chunks_collection.count_documents({
                "$and": [
                    {"user_id": {"$exists": True}},
                    {"userId": {"$exists": True}}
                ]
            })
            
            # Count inconsistent documents
            inconsistent_count = user_id_count + userId_count - (2 * both_fields_count)
            
            # Fetch sample documents using combined query
            combined_samples = list(self.chunks_collection.find(
                {"$or": [{"user_id": user_id_str}, {"userId": user_id_str}]}, 
                {
                    "text_chunk": 1, 
                    "source_document_name": 1, 
                    "user_id": 1,
                    "userId": 1,
                    "_id": 0
                }
            ).limit(limit))
            
            # Check if embeddings exist and their format
            embedding_sample = None
            if user_id_count > 0:
                sample_doc = self.chunks_collection.find_one({"user_id": user_id_str})
                if sample_doc and "embedding" in sample_doc:
                    embedding = sample_doc["embedding"]
                    embedding_sample = {
                        "type": str(type(embedding)),
                        "length": len(embedding) if isinstance(embedding, list) else "N/A",
                        "sample": str(embedding[:3]) + "..." if isinstance(embedding, list) and len(embedding) > 3 else "N/A"
                    }
            
            return {
                "user_id_field_count": user_id_count,
                "userId_field_count": userId_count,
                "both_fields_count": both_fields_count,
                "inconsistent_count": inconsistent_count,
                "document_samples": combined_samples,
                "embedding_sample": embedding_sample
            }
            
        except Exception as e:
            _log_rag(f"Error in diagnostic fetch: {e}", level='error')
            return {"error": str(e)}

    def retrieve_relevant_chunks(self, query_text: str, user_id: Union[str, int], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve text chunks relevant to a query using MongoDB Atlas Vector Search.
        
        Args:
            query_text: The query text
            user_id: The ID of the user
            limit: Maximum number of chunks to retrieve
            
        Returns:
            List[Dict]: List of relevant text chunks with metadata
        """
        if not self.db_initialized:
            _log_rag("MongoDB not available for retrieving chunks", level='warning')
            return []
        
        try:
            _log_rag(f"Retrieving chunks for user '{user_id}' with query: '{query_text[:50]}...'", level='info')
            
            # Generate embedding for the query
            query_embedding = self._get_embedding(query_text)
            if not query_embedding:
                _log_rag("Could not generate query embedding", level='warning')
                return []
                
            # Detailed embedding validation
            embedding_type = type(query_embedding)
            embedding_len = len(query_embedding) if isinstance(query_embedding, list) else 'N/A'
            embedding_sample = str(query_embedding[:3]) + '...' if isinstance(query_embedding, list) and len(query_embedding) > 3 else 'N/A'
            embedding_stats = f"Type: {embedding_type}, Length: {embedding_len}, Sample: {embedding_sample}"
            _log_rag(f"Generated query embedding: {embedding_stats}", level='info')
            
            # Check if we have a valid embedding (expected to be a list of 3072 floats)
            if not isinstance(query_embedding, list) or len(query_embedding) != 3072:
                _log_rag(f"WARNING: Query embedding has unexpected format. {embedding_stats}", level='warning')
            
            # Perform aggregation using Atlas Vector Search
            pipeline = [
                {
                    '$vectorSearch': {
                        'index': 'vector_index',  # Use the correct Atlas Vector Search index name
                        'path': 'embedding',      # Field containing the vectors
                        'queryVector': query_embedding, # The embedding vector of the query
                        'numCandidates': 150,  # Number of candidates to consider
                        'limit': limit,          # Max number of results to return
                        'filter': {
                            '$or': [
                                {'userId': str(user_id)},  # Field as defined in the index
                                {'user_id': str(user_id)}  # Field for backward compatibility
                            ]
                        }
                    }
                },
                { # Project the desired fields and the relevance score
                    '$project': {
                        '_id': 0,
                        'text_chunk': 1,
                        'source_document_name': 1,
                        'chunk_index': 1,
                        'score': { '$meta': 'vectorSearchScore' } # Get the relevance score from $vectorSearch
                    }
                }
            ]
            
            _log_rag("Executing $vectorSearch pipeline...", level='info')
            results = [] # Initialize results
            try:
                results = list(self.chunks_collection.aggregate(pipeline))
                _log_rag("$vectorSearch aggregation successful", level='info')
            except Exception as agg_error:
                _log_rag(f"Error during $vectorSearch aggregation: {agg_error}", level='error')
                return [] # Return empty on error
            
            _log_rag(f"Retrieved {len(results)} relevant chunks", level='info')
            
            # Log the top result if available
            if results and len(results) > 0:
                top_result = results[0]
                _log_rag(f"Top result: '{top_result['text_chunk'][:100]}...' from {top_result['source_document_name']} (score: {top_result.get('score', 'N/A')})", level='info')
            
            return results
            
        except Exception as e:
            _log_rag(f"Error retrieving relevant chunks: {e}", level='error')
            return []