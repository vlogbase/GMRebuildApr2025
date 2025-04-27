import requests
import json

def test_reset_endpoint():
    """
    Test that the reset_preferences endpoint correctly resets models to our updated defaults.
    """
    # Test resetting a specific preset (preset 2)
    preset_id = 2
    response = requests.post(
        'http://localhost:5000/reset_preferences',
        json={'preset_id': preset_id},
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Response for resetting preset {preset_id}:")
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json() if response.status_code == 200 else response.text}")
    print()
    
    # Get preferences to verify the reset worked
    response = requests.get('http://localhost:5000/get_preferences')
    print("Current preferences after reset:")
    if response.status_code == 200:
        prefs = response.json().get('preferences', {})
        print(json.dumps(prefs, indent=2))
        
        # Check if preset 2 is now set to the correct default
        if str(preset_id) not in prefs:
            print(f"✅ Success! Preset {preset_id} is reset to default.")
        else:
            print(f"❌ Error: Preset {preset_id} still has a custom value: {prefs[str(preset_id)]}")
    else:
        print(f"Failed to get preferences: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_reset_endpoint()