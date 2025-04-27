"""
A simple script to display the default models from app.py to verify our changes.
"""
from app import DEFAULT_PRESET_MODELS

print("DEFAULT_PRESET_MODELS in app.py:")
for preset_id, model_id in DEFAULT_PRESET_MODELS.items():
    print(f"  Preset {preset_id}: {model_id}")