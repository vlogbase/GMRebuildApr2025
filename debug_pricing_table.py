#!/usr/bin/env python3
"""
Debug script to compare pricing data between /info page and account page
"""

import requests
import json
from datetime import datetime

def test_api_endpoint():
    """Test the /api/get_model_prices endpoint directly"""
    print("Testing /api/get_model_prices endpoint...")
    
    try:
        # Test with localhost since we're running locally
        response = requests.get('http://localhost:5000/api/get_model_prices', timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"API Response Status: {response.status_code}")
            print(f"Response keys: {list(data.keys())}")
            
            if 'prices' in data:
                prices = data['prices']
                print(f"Number of models in prices: {len(prices)}")
                
                # Show sample models
                print("\nFirst 10 models:")
                for i, (model_id, details) in enumerate(list(prices.items())[:10]):
                    print(f"  {i+1}. {model_id} - {details.get('model_name', 'No name')}")
                
                # Count by provider
                providers = {}
                for model_id in prices.keys():
                    provider = model_id.split('/')[0]
                    providers[provider] = providers.get(provider, 0) + 1
                
                print(f"\nModels by provider:")
                for provider, count in sorted(providers.items()):
                    print(f"  {provider}: {count} models")
                
                # Check for specific models that might be missing
                test_models = [
                    'google/gemini-2.5-pro-experimental',
                    'x-ai/grok-3-beta', 
                    'anthropic/claude-sonnet-4',
                    'openai/gpt-4o-2024-11-20',
                    'perplexity/sonar-pro',
                    'google/gemini-2.0-flash-exp:free'
                ]
                
                print(f"\nChecking for preset models:")
                for model in test_models:
                    if model in prices:
                        print(f"  ✓ {model} - Found")
                    else:
                        print(f"  ✗ {model} - Missing")
                        
            else:
                print("No 'prices' key in response")
                print(f"Response data: {json.dumps(data, indent=2)[:500]}...")
        else:
            print(f"API Error: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            
    except requests.exceptions.ConnectionError:
        print("Connection error - server may not be running")
    except Exception as e:
        print(f"Error testing API: {e}")

def check_database_models():
    """Check what models are in the database"""
    print("\nChecking database models...")
    
    try:
        import sys
        sys.path.append('.')
        from app import app, db
        from models import OpenRouterModel
        
        with app.app_context():
            # Get model counts
            total = OpenRouterModel.query.count()
            active = OpenRouterModel.query.filter_by(model_is_active=True).count()
            
            print(f"Database stats:")
            print(f"  Total models: {total}")
            print(f"  Active models: {active}")
            
            # Check for preset models in database
            test_models = [
                'google/gemini-2.5-pro-experimental',
                'x-ai/grok-3-beta', 
                'anthropic/claude-sonnet-4',
                'openai/gpt-4o-2024-11-20',
                'perplexity/sonar-pro',
                'google/gemini-2.0-flash-exp:free'
            ]
            
            print(f"\nChecking preset models in database:")
            for model_id in test_models:
                model = OpenRouterModel.query.filter_by(model_id=model_id).first()
                if model:
                    print(f"  ✓ {model_id} - Active: {model.model_is_active}")
                else:
                    print(f"  ✗ {model_id} - Not in database")
                    
            # Show provider breakdown in database
            providers = {}
            models = OpenRouterModel.query.filter_by(model_is_active=True).all()
            for model in models:
                provider = model.model_id.split('/')[0]
                providers[provider] = providers.get(provider, 0) + 1
                
            print(f"\nActive models by provider in database:")
            for provider, count in sorted(providers.items()):
                print(f"  {provider}: {count} models")
                
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == "__main__":
    print(f"Pricing Table Debug Script - {datetime.now()}")
    print("=" * 50)
    
    check_database_models()
    test_api_endpoint()