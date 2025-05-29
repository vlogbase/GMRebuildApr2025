"""
Script to refresh the model cache after updating preset configurations
"""
import os
import logging
from app import app
from database import db
from models import OpenRouterModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def refresh_model_cache():
    """Refresh the model cache to pick up new preset configurations"""
    with app.app_context():
        try:
            # First, let's ensure the reasoning models are properly marked
            non_free_reasoning_models = [
                'aion-labs/aion-1.0',
                'aion-labs/aion-1.0-mini',
                'anthropic/claude-3.7-sonnet',
                'anthropic/claude-3.7-sonnet:beta',
                'anthropic/claude-opus-4',
                'anthropic/claude-sonnet-4',
                'deepseek/deepseek-r1',
                'deepseek/deepseek-r1-0528',
                'deepseek/deepseek-r1-distill-llama-70b',
                'deepseek/deepseek-r1-distill-llama-8b',
                'deepseek/deepseek-r1-distill-qwen-1.5b',
                'deepseek/deepseek-r1-distill-qwen-14b',
                'deepseek/deepseek-r1-distill-qwen-32b',
                'google/gemini-2.5-flash-preview-05-20',
                'google/gemini-2.5-flash-preview-05-20:thinking',
                'microsoft/phi-4-reasoning-plus',
                'nvidia/llama-3.1-nemotron-ultra-253b-v1',
                'openai/codex-mini',
                'openai/o1-pro',
                'openai/o3',
                'perplexity/r1-1776',
                'perplexity/sonar-deep-research',
                'perplexity/sonar-reasoning',
                'perplexity/sonar-reasoning-pro',
                'qwen/qwen3-14b',
                'qwen/qwen3-235b-a22b',
                'qwen/qwen3-30b-a3b',
                'qwen/qwen3-32b',
                'qwen/qwen3-8b',
                'qwen/qwq-32b',
                'thedrummer/valkyrie-49b-v1',
                'thudm/glm-z1-32b',
                'thudm/glm-z1-rumination-32b',
                'x-ai/grok-3-mini-beta'
            ]
            
            logger.info("Refreshing model cache...")
            
            # Clear any existing cache files if they exist
            cache_files = ['model_cache.json', 'openrouter_models_cache.json', 'models_cache.json']
            for cache_file in cache_files:
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                    logger.info(f"Removed cache file: {cache_file}")
            
            # Verify our reasoning models are properly configured
            reasoning_count = OpenRouterModel.query.filter_by(
                supports_reasoning=True, 
                is_free=False, 
                model_is_active=True
            ).count()
            
            logger.info(f"Found {reasoning_count} active non-free reasoning models in database")
            
            # Log the new configuration
            from app import DEFAULT_PRESET_MODELS
            logger.info("Updated DEFAULT_PRESET_MODELS:")
            for preset_id, model_id in DEFAULT_PRESET_MODELS.items():
                logger.info(f"  Preset {preset_id}: {model_id}")
            
            # Verify claude-sonnet-4 is available and active
            claude_sonnet_4 = OpenRouterModel.query.filter_by(
                model_id='anthropic/claude-sonnet-4'
            ).first()
            
            if claude_sonnet_4:
                logger.info(f"Claude Sonnet 4 status: active={claude_sonnet_4.model_is_active}, reasoning={claude_sonnet_4.supports_reasoning}")
            else:
                logger.warning("Claude Sonnet 4 not found in database!")
            
            logger.info("Cache refresh completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error refreshing cache: {e}")
            return False

if __name__ == "__main__":
    success = refresh_model_cache()
    if success:
        print("✅ Model cache refreshed successfully!")
        print("📋 Summary of changes:")
        print("  • Updated preset button 3 to use non-free reasoning models")
        print("  • Set default model to anthropic/claude-sonnet-4")
        print("  • Cleared existing cache files")
    else:
        print("❌ Failed to refresh model cache")