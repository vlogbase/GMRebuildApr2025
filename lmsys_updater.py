#!/usr/bin/env python3
"""
LMSYS ELO Data Fetcher and Cacher

This module fetches LMSYS Chatbot Arena ELO scores from Hugging Face
and caches them locally for integration with OpenRouter models.
"""

import os
import json
import csv
import io
import logging
import requests
from datetime import datetime
from typing import Dict, Optional

# Set up logging
logger = logging.getLogger(__name__)

# Cache file path
LMSYS_CACHE_FILE = 'lmsys_elo_cache.json'

def normalize_for_matching(model_id_or_name: str) -> str:
    """
    Normalize model identifiers for better matching between LMSYS and OpenRouter.
    
    Args:
        model_id_or_name: The model identifier or name to normalize
        
    Returns:
        Normalized string for comparison
    """
    if not model_id_or_name:
        return ""
    
    name = model_id_or_name.lower()
    
    # Remove common separators and symbols
    name = name.replace("-", "").replace("_", "").replace(" ", "")
    name = name.replace(".", "").replace(":", "").replace("/", "")
    name = name.replace("(", "").replace(")", "").replace("[", "").replace("]", "")
    
    # Normalize common variations
    name = name.replace("chatgpt", "gpt")
    name = name.replace("gpt4o", "gpt4o")
    name = name.replace("gpt4", "gpt4")
    name = name.replace("claude3", "claude3")
    name = name.replace("gemini2", "gemini2")
    
    return name

def fetch_and_cache_lmsys_elo_data() -> bool:
    """
    Fetch LMSYS Chatbot Arena ELO scores from Hugging Face and cache them locally.
    
    Returns:
        bool: True if successful, False otherwise
    """
    hf_token = os.environ.get('HF_TOKEN')
    if not hf_token:
        logger.error("HF_TOKEN environment variable not set. Cannot fetch LMSYS data.")
        return False
    
    try:
        logger.info("Fetching LMSYS Chatbot Arena ELO data from Hugging Face...")
        
        headers = {"Authorization": f"Bearer {hf_token}"}
        file_url = "https://huggingface.co/datasets/mathewhe/chatbot-arena-elo/resolve/main/elo.csv"
        
        response = requests.get(file_url, headers=headers, timeout=60)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch LMSYS data: HTTP {response.status_code}")
            return False
        
        # Parse CSV data
        csv_data = io.StringIO(response.text)
        reader = csv.DictReader(csv_data)
        entries = list(reader)
        
        logger.info(f"Successfully fetched {len(entries)} LMSYS models")
        
        # Build ELO mapping dictionary
        elo_mapping = {}
        successful_parses = 0
        
        for entry in entries:
            model_name = entry.get('Model')
            elo_score_str = entry.get('Arena Score')
            rank = entry.get('Rank* (UB)')
            organization = entry.get('Organization')
            
            if model_name and elo_score_str:
                try:
                    # Convert ELO score to integer
                    elo_score = int(float(elo_score_str.replace(',', '')))
                    normalized_name = normalize_for_matching(model_name)
                    
                    elo_mapping[normalized_name] = {
                        'elo_score': elo_score,
                        'original_lmsys_name': model_name,
                        'normalized_name': normalized_name,
                        'rank': rank,
                        'organization': organization
                    }
                    successful_parses += 1
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse ELO score for {model_name}: {elo_score_str} - {e}")
                    continue
        
        # Add metadata to the cache
        cache_data = {
            'last_updated': datetime.utcnow().isoformat(),
            'total_models': len(entries),
            'successful_parses': successful_parses,
            'data_source': 'mathewhe/chatbot-arena-elo',
            'elo_mapping': elo_mapping
        }
        
        # Save to cache file
        with open(LMSYS_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Successfully cached {successful_parses} LMSYS ELO scores to {LMSYS_CACHE_FILE}")
        return True
        
    except requests.RequestException as e:
        logger.error(f"Network error fetching LMSYS data: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error fetching LMSYS data: {e}")
        return False

def load_lmsys_elo_cache() -> Dict[str, Dict]:
    """
    Load LMSYS ELO data from local cache file.
    
    Returns:
        dict: Dictionary mapping normalized model names to ELO data
    """
    try:
        if not os.path.exists(LMSYS_CACHE_FILE):
            logger.warning(f"LMSYS cache file {LMSYS_CACHE_FILE} not found")
            return {}
        
        with open(LMSYS_CACHE_FILE, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        elo_mapping = cache_data.get('elo_mapping', {})
        last_updated = cache_data.get('last_updated', 'Unknown')
        
        logger.info(f"Loaded {len(elo_mapping)} ELO scores from cache (updated: {last_updated})")
        return elo_mapping
        
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Error loading LMSYS cache: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error loading LMSYS cache: {e}")
        return {}

def get_elo_score_for_model(model_id: str, elo_cache: Optional[Dict] = None) -> Optional[int]:
    """
    Get ELO score for a specific OpenRouter model ID.
    
    Args:
        model_id: OpenRouter model identifier (e.g., "google/gemini-pro")
        elo_cache: Optional pre-loaded ELO cache dictionary
        
    Returns:
        int: ELO score if found, None otherwise
    """
    if elo_cache is None:
        elo_cache = load_lmsys_elo_cache()
    
    if not elo_cache:
        return None
    
    # Normalize the OpenRouter model ID for matching
    normalized_model = normalize_for_matching(model_id)
    
    # Direct lookup
    if normalized_model in elo_cache:
        return elo_cache[normalized_model]['elo_score']
    
    # Try partial matching for common patterns
    for lmsys_norm, data in elo_cache.items():
        # Check for key model family matches
        if ('gemini' in normalized_model and 'gemini' in lmsys_norm) or \
           ('claude' in normalized_model and 'claude' in lmsys_norm) or \
           ('gpt4' in normalized_model and 'gpt4' in lmsys_norm) or \
           ('llama' in normalized_model and 'llama' in lmsys_norm):
            # Found a potential match, but this is basic - we'll improve this logic later
            logger.debug(f"Potential ELO match: {model_id} -> {data['original_lmsys_name']} (ELO: {data['elo_score']})")
            return data['elo_score']
    
    return None

# Manual mapping dictionary for cases where normalization doesn't catch matches
# This will be populated later based on the explore_lmsys_mapping.py output
MANUAL_OR_TO_LMSYS_NORM = {
    # Placeholder - will be populated with specific mappings
    # Example: "google/gemini-2.0-flash-exp": "gemini25flashpreview0520"
}

if __name__ == "__main__":
    # Test the functionality
    logging.basicConfig(level=logging.INFO)
    success = fetch_and_cache_lmsys_elo_data()
    if success:
        cache = load_lmsys_elo_cache()
        print(f"Successfully cached {len(cache)} ELO scores")
        
        # Test a few lookups
        test_models = ["google/gemini-pro", "anthropic/claude-3.5-sonnet", "openai/gpt-4o"]
        for model in test_models:
            elo = get_elo_score_for_model(model, cache)
            print(f"{model}: ELO {elo if elo else 'Not found'}")
    else:
        print("Failed to fetch LMSYS data")