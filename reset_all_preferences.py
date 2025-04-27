"""
Script to reset all user preferences to force reload of the default models.
This will delete all UserPreference entries from the database.
"""
from app import app, db
from models import UserPreference

def reset_all_preferences():
    """Delete all UserPreference entries"""
    with app.app_context():
        # Count all preferences before deletion
        count = UserPreference.query.count()
        
        # Delete all preferences
        UserPreference.query.delete()
        
        # Commit changes
        db.session.commit()
        
        print(f"Successfully deleted {count} user preferences.")
        print("All users will now use the default preset models:")
        
        # Show the default models that will be used
        from app import DEFAULT_PRESET_MODELS
        for preset_id, model_id in DEFAULT_PRESET_MODELS.items():
            print(f"  Preset {preset_id}: {model_id}")

if __name__ == "__main__":
    reset_all_preferences()