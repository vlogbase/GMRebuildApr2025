"""
Quick test to verify preset 3 now shows reasoning models
"""
from app import app
from models import OpenRouterModel

def test_preset_3_models():
    """Test what models preset 3 would show"""
    with app.app_context():
        # Get non-free reasoning models (what preset 3 should show)
        reasoning_models = OpenRouterModel.query.filter(
            OpenRouterModel.supports_reasoning == True,
            OpenRouterModel.is_free == False,
            OpenRouterModel.model_is_active == True
        ).all()
        
        print(f"🧠 Preset 3 (Reasoning) would show {len(reasoning_models)} models:")
        print("=" * 60)
        
        for i, model in enumerate(reasoning_models[:10], 1):  # Show first 10
            print(f"{i:2d}. {model.name}")
            print(f"    ID: {model.model_id}")
            print(f"    Free: {model.is_free}, Reasoning: {model.supports_reasoning}")
            print()
        
        if len(reasoning_models) > 10:
            print(f"... and {len(reasoning_models) - 10} more reasoning models")
        
        # Check default model
        from app import DEFAULT_PRESET_MODELS
        default_model = DEFAULT_PRESET_MODELS.get("1")
        print(f"\n🎯 Default model (preset 1): {default_model}")
        
        # Verify Claude Sonnet 4 is in the reasoning list
        claude_in_list = any(m.model_id == 'anthropic/claude-sonnet-4' for m in reasoning_models)
        print(f"✅ Claude Sonnet 4 in reasoning models: {claude_in_list}")

if __name__ == "__main__":
    test_preset_3_models()