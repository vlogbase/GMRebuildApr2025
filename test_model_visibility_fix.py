#!/usr/bin/env python3
"""
Test script to validate the model visibility fix
Tests that the three previously missing models now appear in the pricing table
"""

import sys
sys.path.append('.')

from app import app, db
from models import OpenRouterModel
import requests
import json

def test_missing_models():
    """Test that the previously missing models are now visible"""
    
    # The models that were falling through the cracks
    test_models = [
        'mistralai/devstral-small:free',
        'mistralai/devstral-small', 
        'google/gemma-3n-e4b-it:free'
    ]
    
    print("🔍 Testing Model Visibility Fix")
    print("=" * 50)
    
    with app.app_context():
        # Check if models are in database
        print("\n1. Checking database presence:")
        for model_id in test_models:
            model = OpenRouterModel.query.filter_by(model_id=model_id).first()
            if model:
                print(f"✅ {model_id}: Found in database")
                print(f"   - Active: {model.model_is_active}")
                print(f"   - Cost band: '{model.cost_band}' (empty: {not model.cost_band or model.cost_band.strip() == ''})")
                print(f"   - Is free: {model.is_free}")
            else:
                print(f"❌ {model_id}: NOT found in database")
    
    # Test pricing API
    print("\n2. Testing pricing API visibility:")
    try:
        with app.test_client() as client:
            response = client.get('/api/get_model_prices')
            if response.status_code == 200:
                data = response.get_json()
                pricing_models = set(data.get('prices', {}).keys())
                
                for model_id in test_models:
                    if model_id in pricing_models:
                        print(f"✅ {model_id}: Visible in pricing API")
                    else:
                        print(f"❌ {model_id}: Missing from pricing API")
            else:
                print(f"❌ Pricing API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing pricing API: {e}")
    
    # Test visibility audit
    print("\n3. Running visibility audit:")
    try:
        with app.test_client() as client:
            response = client.get('/api/model-visibility-audit')
            if response.status_code == 200:
                audit_data = response.get_json()
                print(f"✅ Audit completed successfully")
                print(f"   - Total DB models: {audit_data.get('total_db_models', 0)}")
                print(f"   - Total pricing models: {audit_data.get('total_pricing_models', 0)}")
                print(f"   - Missing from pricing: {audit_data.get('missing_from_pricing_count', 0)}")
                print(f"   - Visibility percentage: {audit_data.get('visibility_percentage', 0):.1f}%")
                
                missing_models = audit_data.get('missing_from_pricing', [])
                if missing_models:
                    print(f"   - Still missing: {missing_models[:5]}{'...' if len(missing_models) > 5 else ''}")
                else:
                    print(f"   - No models missing! 🎉")
            else:
                print(f"❌ Audit API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error running audit: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed! Check results above.")

if __name__ == "__main__":
    test_missing_models()