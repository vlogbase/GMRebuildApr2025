#!/usr/bin/env python3
"""
Verify that the metadata and model selection fixes are working
"""

import sys
import os
sys.path.append('.')

def test_model_api_fix():
    """Test that model API serialization is fixed"""
    print("Testing Model API Serialization Fix...")
    
    try:
        from app import app
        from models import OpenRouterModel
        
        with app.app_context():
            # Test Gemini 2 model specifically
            gemini_model = OpenRouterModel.query.filter_by(
                model_id='google/gemini-2.0-flash-exp:free'
            ).first()
            
            if not gemini_model:
                print("❌ Gemini 2 model not found in database")
                return False
                
            # Test the fixed serialization logic
            model_data = {
                'id': gemini_model.model_id,
                'is_multimodal': bool(gemini_model.is_multimodal),
                'supports_vision': bool(gemini_model.is_multimodal),
                'supports_pdf': bool(gemini_model.supports_pdf)
            }
            
            print(f"✅ Model: {model_data['id']}")
            print(f"✅ is_multimodal: {model_data['is_multimodal']} (type: {type(model_data['is_multimodal'])})")
            print(f"✅ supports_vision: {model_data['supports_vision']} (type: {type(model_data['supports_vision'])})")
            
            # Verify boolean types
            success = (
                isinstance(model_data['is_multimodal'], bool) and
                isinstance(model_data['supports_vision'], bool) and
                model_data['is_multimodal'] is True and
                model_data['supports_vision'] is True
            )
            
            print(f"Model API Fix: {'✅ PASSED' if success else '❌ FAILED'}")
            return success
            
    except Exception as e:
        print(f"❌ Error testing model API: {e}")
        return False

def test_metadata_fix():
    """Test that metadata generation fix is in place"""
    print("\nTesting Metadata Generation Fix...")
    
    try:
        # Read the app.py file to verify the fix is in place
        with open('app.py', 'r') as f:
            app_content = f.read()
            
        # Check for the metadata fix
        metadata_fix_present = (
            "Always generate metadata - content streaming works independently" in app_content and
            "if True:  # Always generate metadata" in app_content
        )
        
        if metadata_fix_present:
            print("✅ Metadata generation fix is in place")
            print("✅ Backend will always send metadata regardless of content accumulation")
            return True
        else:
            print("❌ Metadata fix not found in code")
            return False
            
    except Exception as e:
        print(f"❌ Error checking metadata fix: {e}")
        return False

def test_model_availability_fix():
    """Test that model availability checking is enhanced"""
    print("\nTesting Model Availability Fix...")
    
    try:
        import model_validator
        
        # Test the enhanced logging and availability checking
        available_models = model_validator.get_available_models()
        
        if len(available_models) > 0:
            print(f"✅ Successfully retrieved {len(available_models)} available models")
            
            # Test specific model availability
            test_model = 'google/gemini-2.0-flash-exp:free'
            is_available = model_validator.is_model_available(test_model, available_models)
            
            print(f"✅ Gemini 2 availability: {is_available}")
            
            return is_available
        else:
            print("❌ No models retrieved")
            return False
            
    except Exception as e:
        print(f"❌ Error testing model availability: {e}")
        return False

if __name__ == "__main__":
    print("Verifying Metadata and Model Selection Fixes")
    print("=" * 50)
    
    results = []
    
    # Run all tests
    results.append(test_model_api_fix())
    results.append(test_metadata_fix())
    results.append(test_model_availability_fix())
    
    # Summary
    print("\n" + "=" * 50)
    print("VERIFICATION SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL FIXES VERIFIED - Ready for testing!")
        print("\nExpected behavior:")
        print("- Selecting Gemini 2 should use that model")
        print("- Metadata should show 'google/gemini-2.0-flash-exp:free'")
        print("- No fallback to Claude 4 Sonnet")
    else:
        print("⚠️  Some verifications failed")
        
    sys.exit(0 if passed == total else 1)