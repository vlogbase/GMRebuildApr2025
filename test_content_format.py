"""
Test script to diagnose and validate the content format adaptation logic.

This script simulates different types of message content and shows
how the adaptation logic would transform them based on model capabilities.
"""

import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Multimodal model patterns (copied from app.py)
MULTIMODAL_MODELS = [
    # Specific model IDs
    "google/gemini",  # This will match all Gemini models
    "anthropic/claude-3", # This will match all Claude 3 models
    "anthropic/claude-3.5", # Claude 3.5 models
    "anthropic/claude-3.7", # Claude 3.7 models
    "openai/gpt-4o", 
    "openai/gpt-4-turbo", 
    "openai/gpt-4-vision",
    
    # Generic model patterns - these partial matches help catch model variations
    "claude-3",
    "gemini",
    "gpt-4-vision",
    "gpt-4o",
    "vision",
    "multimodal"
]

def adapt_content_for_model(messages, model_id):
    """
    Transform message content format based on model capabilities.
    This is a standalone version of the logic in app.py.
    
    Args:
        messages (list): List of message objects
        model_id (str): The model ID to check for multimodal support
        
    Returns:
        list: Processed messages with correct content format
    """
    # Check if model supports multimodal content
    model_supports_multimodal = False
    matching_pattern = None
    for pattern in MULTIMODAL_MODELS:
        if pattern.lower() in model_id.lower():
            model_supports_multimodal = True
            matching_pattern = pattern
            break
    
    logger.info(f"Model {model_id} supports multimodal: {model_supports_multimodal}" + 
               (f" (matching pattern: {matching_pattern})" if matching_pattern else ""))
    
    # Transform messages if needed to match model capabilities
    processed_messages = []
    for msg in messages:
        role = msg.get('role', '')
        content = msg.get('content', '')
        
        # Only user and assistant messages need content format adaptation
        if role in ['user', 'assistant']:
            # Handle array content for multimodal messages
            if isinstance(content, list):
                if model_supports_multimodal:
                    # Keep multimodal format for models that support it
                    processed_messages.append(msg)
                    logger.info(f"Keeping multimodal content format for {role} message")
                else:
                    # For non-multimodal models, extract just the text content
                    text_content = None
                    for item in content:
                        if item.get('type') == 'text':
                            text_content = item.get('text', '')
                            break
                    
                    if text_content:
                        # Create a text-only message
                        processed_messages.append({
                            'role': role,
                            'content': text_content  # Plain string content
                        })
                        logger.info(f"Converted multimodal content to text-only: '{text_content[:30]}...'")
                    else:
                        # Fallback if no text content found
                        logger.warning(f"No text content found in multimodal message, using empty string")
                        processed_messages.append({
                            'role': role,
                            'content': ""
                        })
            else:
                # Regular text message, no conversion needed
                processed_messages.append(msg)
                logger.info(f"Text-only message passed through unchanged: '{content[:30]}...'")
        else:
            # System messages and others pass through unchanged
            processed_messages.append(msg)
            logger.info(f"System message passed through unchanged")
    
    # Log the transformation summary
    logger.info(f"Message format adaptation: {len(messages)} original messages → {len(processed_messages)} processed messages")
    
    return processed_messages

def test_adaptation():
    """Run test cases for content format adaptation"""
    # Test cases
    test_cases = [
        {
            "name": "Text-only message with multimodal model",
            "model_id": "google/gemini-1.5-pro",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What's the weather today?"}
            ]
        },
        {
            "name": "Text-only message with non-multimodal model",
            "model_id": "anthropic/claude-instant-v1",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What's the weather today?"}
            ]
        },
        {
            "name": "Multimodal message with multimodal model",
            "model_id": "openai/gpt-4-vision-preview",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
                ]}
            ]
        },
        {
            "name": "Multimodal message with non-multimodal model",
            "model_id": "openai/gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
                ]}
            ]
        },
        {
            "name": "Mixed messages with multimodal model",
            "model_id": "claude-3-opus-20240229",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Tell me about cats."},
                {"role": "assistant", "content": "Cats are wonderful pets..."},
                {"role": "user", "content": [
                    {"type": "text", "text": "Is this a cat?"},
                    {"type": "image_url", "image_url": {"url": "https://example.com/cat.jpg"}}
                ]}
            ]
        },
        {
            "name": "Mixed messages with non-multimodal model",
            "model_id": "mistralai/mistral-medium",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Tell me about cats."},
                {"role": "assistant", "content": "Cats are wonderful pets..."},
                {"role": "user", "content": [
                    {"type": "text", "text": "Is this a cat?"},
                    {"type": "image_url", "image_url": {"url": "https://example.com/cat.jpg"}}
                ]}
            ]
        }
    ]
    
    # Run test cases
    for i, test_case in enumerate(test_cases):
        print("\n" + "=" * 70)
        print(f"TEST CASE {i+1}: {test_case['name']}")
        print("=" * 70)
        
        model_id = test_case["model_id"]
        messages = test_case["messages"]
        
        print(f"\nOriginal Messages:")
        print(json.dumps(messages, indent=2))
        
        processed = adapt_content_for_model(messages, model_id)
        
        print(f"\nProcessed Messages for {model_id}:")
        print(json.dumps(processed, indent=2))
        
        # Compare original and processed
        if messages == processed:
            print("\nRESULT: Messages unchanged")
        else:
            print("\nRESULT: Messages transformed")

if __name__ == "__main__":
    test_adaptation()