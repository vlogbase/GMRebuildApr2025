"""
Script to find OpenRouter models that support the include_reasoning parameter
"""
import requests
import json
import os

def find_reasoning_models():
    """Find all OpenRouter models that support include_reasoning parameter"""
    
    # Check if we have the API key
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        print("⚠️  OPENROUTER_API_KEY not found. Please provide your OpenRouter API key.")
        return []
    
    # Set up headers for the API request
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://gloriamundo.com",
        "X-Title": "GloriaMundo Chatbot"
    }
    
    print("🔍 Fetching models from OpenRouter API...")
    
    try:
        # Make the API request
        response = requests.get("https://openrouter.ai/api/v1/models", headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch models. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return []
        
        # Parse the response
        data = response.json()
        models = data.get('data', [])
        
        if not models:
            print("❌ No models found in the API response")
            return []
        
        print(f"✅ Successfully fetched {len(models)} models from OpenRouter API")
        
        # Find models that support include_reasoning
        reasoning_models = []
        
        for model in models:
            model_id = model.get('id', 'unknown')
            model_name = model.get('name', model_id)
            supported_parameters = model.get('supported_parameters', [])
            
            # Check if include_reasoning is in the supported parameters
            if 'include_reasoning' in supported_parameters:
                reasoning_models.append({
                    'id': model_id,
                    'name': model_name,
                    'supported_parameters': supported_parameters
                })
        
        print(f"\n🧠 Found {len(reasoning_models)} models that support include_reasoning:")
        print("=" * 80)
        
        for i, model in enumerate(reasoning_models, 1):
            print(f"{i}. {model['name']}")
            print(f"   ID: {model['id']}")
            print(f"   Supported Parameters: {', '.join(model['supported_parameters'])}")
            print()
        
        # Save results to a file for reference
        with open('reasoning_models.json', 'w') as f:
            json.dump(reasoning_models, f, indent=2)
        
        print(f"💾 Results saved to reasoning_models.json")
        
        return reasoning_models
        
    except Exception as e:
        print(f"❌ Error fetching models: {e}")
        return []

if __name__ == "__main__":
    models = find_reasoning_models()
    
    if models:
        print(f"\n📋 Summary: {len(models)} reasoning-capable models found")
        model_ids = [model['id'] for model in models]
        print("\nModel IDs:")
        for model_id in model_ids:
            print(f"  - {model_id}")
    else:
        print("\n❌ No reasoning-capable models found or API call failed")