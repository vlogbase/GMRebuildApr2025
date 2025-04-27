"""
A simple script to display the default models from app.py to verify our changes.
"""
from app import DEFAULT_PRESET_MODELS
import requests
import json

print("DEFAULT_PRESET_MODELS in app.py:")
for preset_id, model_id in DEFAULT_PRESET_MODELS.items():
    print(f"  Preset {preset_id}: {model_id}")

print("\nAttempting to verify through API:")
try:
    # Make a request to the preferences endpoint to see what models would be returned
    response = requests.get("http://localhost:5000/get_preferences")
    if response.status_code == 200:
        data = response.json()
        print("\nPreferences from API:")
        for preset_id, model_id in data.get('preferences', {}).items():
            print(f"  Preset {preset_id}: {model_id}")
    else:
        print(f"Error getting preferences: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error making request: {e}")