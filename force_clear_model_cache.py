"""
Force clear all model-related caches to ensure frontend gets updated reasoning data
"""
import os
from app import app

def clear_all_model_caches():
    """Clear all model-related caches"""
    with app.app_context():
        try:
            # Import Redis client
            from api_cache import get_redis_client
            redis_client = get_redis_client()
            
            if redis_client:
                # Clear all model-related cache keys
                cache_patterns = [
                    'cache:models:*',
                    'cache:pricing_table_data',
                    'model_cache*',
                    'openrouter_models*',
                    'models_cache*'
                ]
                
                cleared_count = 0
                for pattern in cache_patterns:
                    keys = redis_client.keys(pattern)
                    if keys:
                        redis_client.delete(*keys)
                        cleared_count += len(keys)
                        print(f"✅ Cleared {len(keys)} keys matching '{pattern}'")
                
                print(f"🧹 Total cache keys cleared: {cleared_count}")
            else:
                print("⚠️ Redis client not available")
                
            # Remove local cache files if they exist
            local_cache_files = [
                'model_cache.json',
                'openrouter_models_cache.json', 
                'models_cache.json',
                'available_models.json'
            ]
            
            removed_files = 0
            for cache_file in local_cache_files:
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                    removed_files += 1
                    print(f"🗑️ Removed local cache file: {cache_file}")
            
            if removed_files == 0:
                print("📁 No local cache files found to remove")
                
            print("\n🔄 Cache clearing complete! The next request should fetch fresh model data.")
            return True
            
        except Exception as e:
            print(f"❌ Error clearing caches: {e}")
            return False

if __name__ == "__main__":
    success = clear_all_model_caches()
    if success:
        print("\n✅ All model caches cleared successfully!")
        print("🔍 Next step: Refresh your browser page to get updated model data")
    else:
        print("\n❌ Cache clearing failed")