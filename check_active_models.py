"""
Check if the specified models are active in the database.
"""
from app import app
from models import OpenRouterModel

# Models we want to check
MODEL_IDS = [
    'google/gemini-2.5-pro-preview',
    'meta-llama/llama-4-maverick',
    'openai/o4-mini-high',
    'openai/gpt-4o-2024-11-20',
    'perplexity/sonar-pro',
    'google/gemini-2.0-flash-exp:free'
]

def check_models():
    with app.app_context():
        print("Checking if required models are active:")
        for model_id in MODEL_IDS:
            model = OpenRouterModel.query.filter_by(model_id=model_id).first()
            if model:
                print(f"✓ {model_id}: Active={model.model_is_active}")
            else:
                print(f"✗ {model_id}: Not found in database")

if __name__ == "__main__":
    check_models()