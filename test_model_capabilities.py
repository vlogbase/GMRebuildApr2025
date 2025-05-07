#!/usr/bin/env python
"""
Test model capabilities detection and content format adaptation.

This script tests our model capability detection logic and ensures proper content format
adaptation between multimodal and text-only models.
"""
import os
import json
import logging
import traceback
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('model_capabilities_test.log')
    ]
)
logger = logging.getLogger(__name__)

# Import the model capability detection logic from app.py
# This is a simplified version that mimics what we have in app.py
MULTIMODAL_MODELS = [
    # Specific model IDs - full matches for more safety
    "google/gemini-1.5-pro",
    "google/gemini-1.5-flash",
    "google/gemini-1.0-pro",
    "anthropic/claude-3-opus",
    "anthropic/claude-3-sonnet",
    "anthropic/claude-3-haiku",
    "openai/gpt-4o",
    "openai/gpt-4-turbo",
    "openai/gpt-4-vision-preview",
    
    # Generic model patterns - these partial matches help catch model variations
    "google/gemini",  # This will match all Gemini models
    "anthropic/claude-3", # This will match all Claude 3 models
    "claude-3",
    "gemini",
    "gpt-4-vision",
    "gpt-4o",
    "vision",
    "multimodal"
]

def get_test_models():
    """Get list of models to test."""
    return [
        # Definitely multimodal models
        "google/gemini-1.5-pro",
        "anthropic/claude-3-opus",
        "openai/gpt-4o",
        
        # Definitely text-only models
        "google/gemma-2-2b",
        "cohere/command-r",
        "meta-llama/llama-3-8b",
        
        # Ambiguous models - requires pattern matching
        "google/gemini-2.0-flash-exp:free",
        "anthropic/claude-3-plus",
        "mistralai/mistral-7b",
        
        # Non-existent models to test fallback
        "nonexistent/model",
        "custom/claude-like",
        "test/gemini-variant"
    ]

def is_model_multimodal(model_id):
    """Check if a model is multimodal using our pattern matching logic."""
    for pattern in MULTIMODAL_MODELS:
        if pattern.lower() in model_id.lower():
            return True
    return False

def adapt_message_format(messages, model_supports_multimodal):
    """
    Adapt message format based on model capabilities.
    This is a simplified version of our content adaptation logic.
    
    Args:
        messages (list): List of message objects
        model_supports_multimodal (bool): Whether the model supports multimodal content
        
    Returns:
        list: Processed messages with appropriate format for the model
    """
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
                        logger.info(f"Converted multimodal content to text-only for {role} message")
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
        else:
            # System messages and others pass through unchanged
            processed_messages.append(msg)
    
    return processed_messages

def run_test():
    """Run the model capability and content adaptation tests."""
    test_models = get_test_models()
    
    # Test cases for message formats
    test_messages = [
        # Simple text message
        [
            {'role': 'user', 'content': 'Tell me about the solar system'}
        ],
        
        # Multimodal message with image
        [
            {'role': 'user', 'content': [
                {'type': 'text', 'text': 'What is this image showing?'},
                {'type': 'image_url', 'image_url': {'url': 'https://example.com/image.jpg'}}
            ]}
        ],
        
        # Conversation with mix of text and multimodal
        [
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': 'Tell me about this image.'},
            {'role': 'assistant', 'content': 'I need to see the image first.'},
            {'role': 'user', 'content': [
                {'type': 'text', 'text': 'Here it is. What is it?'},
                {'type': 'image_url', 'image_url': {'url': 'https://example.com/image2.jpg'}}
            ]}
        ]
    ]
    
    results = []
    
    # Test each model with each message format
    for model_id in test_models:
        logger.info(f"\n{'-'*40}\nTesting model: {model_id}")
        
        # Check if model is multimodal
        model_supports_multimodal = is_model_multimodal(model_id)
        logger.info(f"Model capability detection: multimodal={model_supports_multimodal}")
        
        model_results = {
            "model_id": model_id,
            "multimodal_support_detected": model_supports_multimodal,
            "test_cases": []
        }
        
        # Test each message format
        for i, messages in enumerate(test_messages):
            logger.info(f"\nTest case {i+1}: {len(messages)} messages")
            
            # Log the original messages format
            has_multimodal = any(isinstance(msg.get('content'), list) for msg in messages)
            logger.info(f"Original messages have multimodal content: {has_multimodal}")
            
            # Process messages based on model capabilities
            processed_messages = adapt_message_format(messages, model_supports_multimodal)
            
            # Check the processed format
            processed_has_multimodal = any(isinstance(msg.get('content'), list) for msg in processed_messages)
            logger.info(f"Processed messages have multimodal content: {processed_has_multimodal}")
            
            # Verify format matches model capabilities
            format_matches_capability = (model_supports_multimodal == processed_has_multimodal) or not has_multimodal
            if not format_matches_capability:
                logger.error(f"❌ Format mismatch: model={model_supports_multimodal}, content={processed_has_multimodal}")
            else:
                logger.info(f"✅ Format correctly matched to model capability")
            
            test_case_result = {
                "test_case": i+1,
                "original_format": "multimodal" if has_multimodal else "text",
                "processed_format": "multimodal" if processed_has_multimodal else "text",
                "format_matches_capability": format_matches_capability
            }
            
            model_results["test_cases"].append(test_case_result)
        
        results.append(model_results)
    
    return results

def generate_report(results):
    """Generate a test report from results."""
    report = [
        "\n" + "="*80,
        "MODEL CAPABILITY DETECTION AND CONTENT ADAPTATION TEST RESULTS",
        "="*80,
    ]
    
    # Count models by detected capability
    multimodal_models = [r for r in results if r["multimodal_support_detected"]]
    text_models = [r for r in results if not r["multimodal_support_detected"]]
    
    report.append(f"\nModels tested: {len(results)}")
    report.append(f"Models detected as multimodal: {len(multimodal_models)}")
    report.append(f"Models detected as text-only: {len(text_models)}")
    
    # Count successful format adaptations
    total_test_cases = sum(len(r["test_cases"]) for r in results)
    successful_adaptations = sum(
        sum(1 for tc in r["test_cases"] if tc["format_matches_capability"])
        for r in results
    )
    
    report.append(f"\nTotal test cases: {total_test_cases}")
    report.append(f"Successful format adaptations: {successful_adaptations} ({successful_adaptations/total_test_cases*100:.1f}%)")
    
    # Report model-specific results
    report.append("\nDETAILED MODEL RESULTS:")
    
    for r in results:
        model_id = r["model_id"]
        capability = "multimodal" if r["multimodal_support_detected"] else "text-only"
        
        # Count successful adaptations for this model
        model_cases = len(r["test_cases"])
        model_successes = sum(1 for tc in r["test_cases"] if tc["format_matches_capability"])
        
        status = "✅" if model_successes == model_cases else "❌"
        report.append(f"\n{status} {model_id}: Detected as {capability}")
        report.append(f"  - Successful adaptations: {model_successes}/{model_cases}")
        
        # Report issues if any
        if model_successes < model_cases:
            report.append("  - Issues:")
            for tc in r["test_cases"]:
                if not tc["format_matches_capability"]:
                    report.append(f"    - Test case {tc['test_case']}: Original={tc['original_format']}, Processed={tc['processed_format']}")
    
    # Conclusion
    report.append("\nCONCLUSION:")
    if successful_adaptations == total_test_cases:
        report.append("✅ All content format adaptations were successful")
    else:
        report.append(f"⚠️ {total_test_cases - successful_adaptations} out of {total_test_cases} adaptations failed")
        
        # Check for patterns in failures
        multimodal_failures = any(
            not tc["format_matches_capability"] and tc["original_format"] == "multimodal"
            for r in results for tc in r["test_cases"]
        )
        
        if multimodal_failures:
            report.append("❗ Issues detected with multimodal content adaptation")
    
    return "\n".join(report)

if __name__ == "__main__":
    try:
        logger.info("Starting model capability and content adaptation tests...")
        
        # Run tests
        results = run_test()
        
        # Generate and log report
        report = generate_report(results)
        logger.info(report)
        
        # Save results
        with open("model_capabilities_results.json", "w") as f:
            json.dump(results, f, indent=2)
            
        with open("model_capabilities_report.txt", "w") as f:
            f.write(report)
            
        logger.info("Tests completed. Results saved to model_capabilities_results.json and model_capabilities_report.txt")
        
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        logger.error(traceback.format_exc())