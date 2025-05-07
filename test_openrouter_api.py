#!/usr/bin/env python
"""
Diagnostic test for OpenRouter API connections.

This script tests various model and content type combinations to identify which
specific configurations cause HTTP 400 errors vs. which ones work correctly.
"""
import os
import json
import logging
import requests
import traceback
from urllib.parse import urlparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('openrouter_test.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'

# Text prompt for all models
TEXT_PROMPT = "Explain why the sky is blue in one brief paragraph."

# Test image URL - public and hosted on a major CDN for maximum compatibility
TEST_IMAGE_URL = "https://upload.wikimedia.org/wikipedia/commons/a/a4/Anatomy_of_a_Sunset-2.jpg"

# Model categories to test with verified available model IDs
MODELS_TO_TEST = {
    "Gemini": [
        "google/gemini-pro-vision",
        "google/gemini-pro"
    ],
    "Claude": [
        "anthropic/claude-3-opus-20240229",
        "anthropic/claude-3-sonnet-20240229",
        "anthropic/claude-3-haiku-20240307"
    ],
    "GPT": [
        "openai/gpt-4-vision-preview",
        "openai/gpt-4o-2024-05-13"
    ],
    "Non-multimodal": [
        "meta-llama/llama-3-8b",
        "mistralai/mistral-7b"
    ]
}

def get_openrouter_api_key():
    """Get OpenRouter API key from environment variable."""
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable not set")
    return api_key

def prepare_headers(api_key):
    """Prepare request headers."""
    return {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://gloriamundo.replit.app',
    }

def prepare_text_only_payload(model_id):
    """Prepare text-only payload for the given model."""
    return {
        'model': model_id,
        'messages': [
            {
                'role': 'user', 
                'content': TEXT_PROMPT
            }
        ]
    }

def prepare_multimodal_payload(model_id):
    """Prepare multimodal payload for the given model."""
    return {
        'model': model_id,
        'messages': [
            {
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': TEXT_PROMPT},
                    {'type': 'image_url', 'image_url': {'url': TEST_IMAGE_URL}}
                ]
            }
        ]
    }

def test_model_with_content_type(model_id, content_type):
    """
    Test a specific model with a specific content type.
    
    Args:
        model_id (str): The model ID to test
        content_type (str): Either "text" or "multimodal"
        
    Returns:
        dict: Result of the test containing success status and details
    """
    logger.info(f"Testing {model_id} with {content_type} content...")
    
    try:
        # Get API key
        api_key = get_openrouter_api_key()
        headers = prepare_headers(api_key)
        
        # Prepare appropriate payload
        if content_type == "text":
            payload = prepare_text_only_payload(model_id)
        else:  # multimodal
            payload = prepare_multimodal_payload(model_id)
        
        # Make the request
        logger.info(f"Sending request to OpenRouter API for {model_id}...")
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=20.0
        )
        
        # Process response
        success = response.status_code == 200
        
        if success:
            logger.info(f"✅ {model_id} with {content_type} content: SUCCESS")
            return {
                "model_id": model_id,
                "content_type": content_type,
                "success": True,
                "status_code": response.status_code
            }
        else:
            error_text = response.text
            try:
                error_json = response.json()
                error_detail = error_json.get('error', {}).get('message', '')
                if error_detail:
                    error_text = f"{error_text} - Detail: {error_detail}"
            except:
                pass
                
            logger.error(f"❌ {model_id} with {content_type} content: FAILED - {response.status_code} - {error_text}")
            return {
                "model_id": model_id,
                "content_type": content_type,
                "success": False,
                "status_code": response.status_code,
                "error": error_text
            }
            
    except Exception as e:
        logger.error(f"💥 Error testing {model_id} with {content_type} content: {e}")
        logger.error(traceback.format_exc())
        return {
            "model_id": model_id,
            "content_type": content_type,
            "success": False,
            "status_code": None,
            "error": str(e)
        }

def run_all_tests():
    """Run tests for all model and content type combinations."""
    results = []
    
    # Test each model category
    for category, models in MODELS_TO_TEST.items():
        logger.info(f"\n{'-'*40}\nTesting {category} models\n{'-'*40}")
        
        for model_id in models:
            # Test with text content
            text_result = test_model_with_content_type(model_id, "text")
            results.append(text_result)
            
            # Test with multimodal content
            multimodal_result = test_model_with_content_type(model_id, "multimodal")
            results.append(multimodal_result)
    
    return results

def analyze_results(results):
    """Analyze test results and produce a summary report."""
    # Count successes and failures
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["success"])
    failed_tests = total_tests - successful_tests
    
    # Count by content type
    text_tests = [r for r in results if r["content_type"] == "text"]
    text_success = sum(1 for r in text_tests if r["success"])
    
    multimodal_tests = [r for r in results if r["content_type"] == "multimodal"]
    multimodal_success = sum(1 for r in multimodal_tests if r["success"])
    
    # Group failures by status code
    failures_by_code = {}
    for r in results:
        if not r["success"]:
            code = r["status_code"] or "Exception"
            if code not in failures_by_code:
                failures_by_code[code] = []
            failures_by_code[code].append(r)
    
    # Prepare report
    report = [
        "\n" + "="*80,
        "OPENROUTER API TEST RESULTS",
        "="*80,
        f"Total Tests Run: {total_tests}",
        f"Successful Tests: {successful_tests} ({successful_tests/total_tests*100:.1f}%)",
        f"Failed Tests: {failed_tests} ({failed_tests/total_tests*100:.1f}%)",
        "",
        f"Text-Only Content: {text_success}/{len(text_tests)} successful ({text_success/len(text_tests)*100:.1f}%)",
        f"Multimodal Content: {multimodal_success}/{len(multimodal_tests)} successful ({multimodal_success/len(multimodal_tests)*100:.1f}%)",
        "",
        "FAILURES BY STATUS CODE:",
    ]
    
    for code, failures in failures_by_code.items():
        report.append(f"\nStatus Code {code}: {len(failures)} failures")
        for f in failures:
            model = f["model_id"]
            content = f["content_type"]
            error = f.get("error", "Unknown error")
            if len(error) > 100:
                error = error[:100] + "..."
            report.append(f"  - {model} with {content} content: {error}")
    
    report.append("\nDETAILED MODEL COMPATIBILITY:")
    
    for category, models in MODELS_TO_TEST.items():
        report.append(f"\n{category} Models:")
        for model_id in models:
            text_result = next((r for r in results if r["model_id"] == model_id and r["content_type"] == "text"), None)
            multimodal_result = next((r for r in results if r["model_id"] == model_id and r["content_type"] == "multimodal"), None)
            
            text_status = "✅" if text_result and text_result["success"] else "❌"
            mm_status = "✅" if multimodal_result and multimodal_result["success"] else "❌"
            
            report.append(f"  {model_id}:")
            report.append(f"    - Text: {text_status}")
            report.append(f"    - Multimodal: {mm_status}")
    
    report.append("\nCONCLUSION:")
    
    # Identify patterns of success/failure and make recommendations
    if multimodal_success == 0:
        report.append("❗ All multimodal requests are failing - likely a fundamental issue with multimodal format")
    
    if text_success == 0:
        report.append("❗ All requests are failing - likely an API key or connectivity issue")
    
    # Look for model-specific patterns
    model_success_rates = {}
    for category, models in MODELS_TO_TEST.items():
        category_results = [r for r in results if r["model_id"] in models]
        success_rate = sum(1 for r in category_results if r["success"]) / len(category_results)
        model_success_rates[category] = success_rate
    
    # Report on model-specific issues
    for category, rate in model_success_rates.items():
        if rate == 0:
            report.append(f"❗ All {category} model tests failed - possible issue with {category} model access")
        elif rate < 0.5:
            report.append(f"⚠️ Most {category} model tests failed - check {category} model configuration")
    
    return "\n".join(report)

if __name__ == "__main__":
    try:
        logger.info("Starting OpenRouter API diagnostic tests...")
        
        # Run all tests
        results = run_all_tests()
        
        # Analyze and report results
        report = analyze_results(results)
        logger.info(report)
        
        # Save results to file
        with open("openrouter_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        with open("openrouter_test_report.txt", "w") as f:
            f.write(report)
            
        logger.info("Tests completed. Results saved to openrouter_test_results.json and openrouter_test_report.txt")
        
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        logger.error(traceback.format_exc())