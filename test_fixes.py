#!/usr/bin/env python3
"""
Test script to verify the model capability and fallback fixes
"""

import sys
import os
sys.path.append('.')

from app import app, db
from models import OpenRouterModel
import model_validator
import json

def test_model_api_serialization():
    """Test that the /models API correctly serializes boolean fields"""
    print("=== Testing Model API Serialization ===")
    
    with app.app_context():
        # Get Llama 4 Maverick from database
        llama_model = OpenRouterModel.query.filter_by(model_id='meta-llama/llama-4-maverick').first()
        
        if not llama_model:
            print("❌ Llama 4 Maverick not found in database")
            return False
            
        print(f"✅ Found model in DB: {llama_model.model_id}")
        print(f"   Database is_multimodal: {llama_model.is_multimodal} (type: {type(llama_model.is_multimodal)})")
        print(f"   Database supports_pdf: {llama_model.supports_pdf} (type: {type(llama_model.supports_pdf)})")
        
        # Test the serialization logic from the API endpoint
        model_data = {
            'id': llama_model.model_id,
            'name': llama_model.name,
            'is_multimodal': bool(llama_model.is_multimodal),
            'supports_vision': bool(llama_model.is_multimodal),
            'supports_pdf': bool(llama_model.supports_pdf)
        }
        
        print(f"   Serialized is_multimodal: {model_data['is_multimodal']} (type: {type(model_data['is_multimodal'])})")
        print(f"   Serialized supports_vision: {model_data['supports_vision']} (type: {type(model_data['supports_vision'])})")
        print(f"   Serialized supports_pdf: {model_data['supports_pdf']} (type: {type(model_data['supports_pdf'])})")
        
        # Verify JSON serialization works
        json_str = json.dumps(model_data)
        parsed_back = json.loads(json_str)
        
        print(f"   After JSON round-trip - is_multimodal: {parsed_back['is_multimodal']} (type: {type(parsed_back['is_multimodal'])})")
        print(f"   After JSON round-trip - supports_vision: {parsed_back['supports_vision']} (type: {type(parsed_back['supports_vision'])})")
        
        success = (
            isinstance(model_data['is_multimodal'], bool) and
            isinstance(model_data['supports_vision'], bool) and
            model_data['is_multimodal'] is True and
            model_data['supports_vision'] is True
        )
        
        print(f"   Serialization test: {'✅ PASSED' if success else '❌ FAILED'}")
        return success

def test_model_availability_check():
    """Test the model availability checking system"""
    print("\n=== Testing Model Availability System ===")
    
    # Test get_available_models function
    print("Getting available models...")
    available_models = model_validator.get_available_models()
    
    print(f"✅ Retrieved {len(available_models)} available models")
    print(f"   Sample models: {available_models[:5]}")
    
    # Test specific model availability
    test_model = 'meta-llama/llama-4-maverick'
    print(f"\nTesting availability of: {test_model}")
    
    is_available = model_validator.is_model_available(test_model, available_models)
    print(f"   Availability result: {is_available}")
    
    # Check if model is in the list
    in_list = test_model in available_models
    print(f"   Model in available_models list: {in_list}")
    
    success = is_available and in_list
    print(f"   Availability test: {'✅ PASSED' if success else '❌ FAILED'}")
    
    return success

def test_fallback_selection():
    """Test the fallback model selection"""
    print("\n=== Testing Fallback Selection ===")
    
    available_models = model_validator.get_available_models()
    
    # Test multimodal fallback
    fallback_model = model_validator.select_multimodal_fallback(
        has_image_content=True,
        available_models=available_models,
        has_rag_content=False
    )
    
    print(f"   Multimodal fallback selected: {fallback_model}")
    
    # Test reasoning fallback  
    reasoning_fallback = model_validator.select_multimodal_fallback(
        has_image_content=False,
        available_models=available_models,
        has_rag_content=True
    )
    
    print(f"   Reasoning fallback selected: {reasoning_fallback}")
    
    success = fallback_model is not None and reasoning_fallback is not None
    print(f"   Fallback test: {'✅ PASSED' if success else '❌ FAILED'}")
    
    return success

if __name__ == "__main__":
    print("Testing Model Capability and Fallback Fixes")
    print("=" * 50)
    
    results = []
    
    # Run all tests
    results.append(test_model_api_serialization())
    results.append(test_model_availability_check())
    results.append(test_fallback_selection())
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Fixes are working correctly.")
    else:
        print("⚠️  Some tests failed. Issues need further investigation.")
        
    sys.exit(0 if passed == total else 1)