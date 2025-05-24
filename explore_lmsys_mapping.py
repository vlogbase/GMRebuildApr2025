#!/usr/bin/env python3
"""
Explore LMSYS Chatbot Arena ELO scores and map them to OpenRouter model identifiers.

This script loads the LMSYS dataset, fetches OpenRouter models, and attempts to match
them using normalized model identifiers to understand the mapping potential.
"""

import os
import sys
import json
from typing import Dict, List, Optional, Tuple

def normalize_for_matching(model_id_or_name: str) -> str:
    """
    Normalize model identifiers for better matching between LMSYS and OpenRouter.
    
    Args:
        model_id_or_name: The model identifier or name to normalize
        
    Returns:
        Normalized string for comparison
    """
    name = str(model_id_or_name).lower()
    
    # Remove common provider prefixes
    prefixes_to_remove = [
        "openai/", "anthropic/", "google/", "meta-llama/", 
        "mistralai/", "cohere/", "x-ai/", "perplexity/", "nousresearch/",
        "microsoft/", "meta/", "nvidia/", "salesforce/", "deepseek/",
        "qwen/", "alibaba/", "01-ai/", "cognitivecomputations/"
    ]
    for prefix in prefixes_to_remove:
        if name.startswith(prefix):
            name = name[len(prefix):]
    
    # Remove common suffixes and terms
    suffixes_and_terms_to_remove = [
        "-instruct", "-chat", "-hf", ":free", "-preview", "-latest",
        "-base", "-turbo", "-pro", "-ultra", "-mini", "-nano",
        "-it", "-ift", "-dpo", "-sft", "-rlhf"
    ]
    for term in suffixes_and_terms_to_remove:
        name = name.replace(term, "")
    
    # Make dense: remove hyphens, underscores, spaces, dots
    name = name.replace("-", "").replace("_", "").replace(" ", "").replace(".", "")
    
    # Specific common model name normalizations
    name = name.replace("gpt4", "gpt4")  # gpt-4o -> gpt4o
    name = name.replace("claude35", "claude35")  # claude-3.5-sonnet -> claude35sonnet
    name = name.replace("claude3", "claude3") 
    name = name.replace("llama3", "llama3")
    name = name.replace("gemini15", "gemini15")
    name = name.replace("gemini2", "gemini2")
    
    return name

def load_lmsys_data(hf_token: str) -> Dict[str, Dict]:
    """
    Load LMSYS Chatbot Arena dataset and parse ELO scores.
    
    Args:
        hf_token: Hugging Face access token
        
    Returns:
        Dictionary mapping normalized model names to ELO data
    """
    try:
        from datasets import load_dataset
        print("Loading LMSYS Chatbot Arena dataset...")
        
        # Load the dataset
        lmsys_ds = load_dataset("mathewhe/chatbot-arena-elo", token=hf_token)
        
        print("Dataset loaded successfully!")
        print(f"Dataset features: {lmsys_ds['train'].features}")
        print(f"Number of entries: {len(lmsys_ds['train'])}")
        
        # Parse the dataset into a usable format
        lmsys_models = {}
        
        for entry in lmsys_ds['train']:
            # Extract model identifier and ELO score based on actual dataset structure
            # We'll need to see the actual column names first
            print(f"Sample entry: {dict(entry)}")
            
            # Common possible column names for model identifier
            model_name = None
            for col in ['model', 'model_name', 'name', 'model_id', 'identifier']:
                if col in entry:
                    model_name = entry[col]
                    break
            
            # Common possible column names for ELO score
            elo_score = None
            for col in ['elo', 'elo_score', 'rating', 'score']:
                if col in entry:
                    elo_score = entry[col]
                    break
            
            if model_name and elo_score is not None:
                normalized_name = normalize_for_matching(model_name)
                lmsys_models[normalized_name] = {
                    'elo_score': elo_score,
                    'original_lmsys_name': model_name,
                    'normalized_name': normalized_name
                }
        
        print(f"Parsed {len(lmsys_models)} models from LMSYS dataset")
        return lmsys_models
        
    except ImportError:
        print("Error: 'datasets' library not installed. Please install it with: pip install datasets")
        return {}
    except Exception as e:
        print(f"Error loading LMSYS dataset: {e}")
        return {}

def load_openrouter_models() -> List[Dict]:
    """
    Load OpenRouter models from the database or API endpoint.
    
    Returns:
        List of OpenRouter model dictionaries
    """
    openrouter_models = []
    
    # Method 1: Try direct database access
    try:
        # Import Flask app and database
        sys.path.append('.')
        from app import app, db
        from models import OpenRouterModel
        
        print("Loading OpenRouter models from database...")
        
        with app.app_context():
            db_models = OpenRouterModel.query.filter(OpenRouterModel.model_is_active == True).all()
            
            for db_model in db_models:
                openrouter_models.append({
                    'model_id': db_model.model_id,
                    'name': db_model.name or db_model.model_id,
                    'elo_score': None  # Will be populated from LMSYS data
                })
        
        print(f"Loaded {len(openrouter_models)} active OpenRouter models from database")
        return openrouter_models
        
    except Exception as e:
        print(f"Database access failed: {e}")
        print("Falling back to API endpoint...")
    
    # Method 2: Try API endpoint
    try:
        import requests
        
        print("Loading OpenRouter models from API endpoint...")
        response = requests.get('http://localhost:5000/api/get_model_prices', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'prices' in data:
                for model_id, model_data in data['prices'].items():
                    openrouter_models.append({
                        'model_id': model_id,
                        'name': model_data.get('model_name', model_id),
                        'elo_score': None
                    })
                
                print(f"Loaded {len(openrouter_models)} OpenRouter models from API")
                return openrouter_models
            else:
                print("No 'prices' key found in API response")
        else:
            print(f"API request failed with status code: {response.status_code}")
            
    except Exception as e:
        print(f"API request failed: {e}")
    
    print("Warning: Could not load OpenRouter models from either database or API")
    return []

def match_models(openrouter_models: List[Dict], lmsys_models: Dict[str, Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Attempt to match OpenRouter models with LMSYS ELO scores.
    
    Args:
        openrouter_models: List of OpenRouter model dictionaries
        lmsys_models: Dictionary of LMSYS models with normalized names as keys
        
    Returns:
        Tuple of (matched_models, unmatched_openrouter, sample_unmatched_lmsys)
    """
    matched_models = []
    unmatched_openrouter = []
    
    print("\nAttempting to match models...")
    
    for or_model in openrouter_models:
        model_id = or_model['model_id']
        model_name = or_model['name']
        
        # Normalize both the ID and name for matching
        normalized_id = normalize_for_matching(model_id)
        normalized_name = normalize_for_matching(model_name)
        
        # Try to find a match in LMSYS data
        match_found = False
        lmsys_match = None
        
        # Priority 1: Match by normalized OpenRouter ID
        if normalized_id in lmsys_models:
            lmsys_match = lmsys_models[normalized_id]
            match_found = True
        # Priority 2: Match by normalized OpenRouter name
        elif normalized_name in lmsys_models:
            lmsys_match = lmsys_models[normalized_name]
            match_found = True
        
        if match_found:
            matched_model = {
                'openrouter_id': model_id,
                'openrouter_name': model_name,
                'lmsys_original_name': lmsys_match['original_lmsys_name'],
                'elo_score': lmsys_match['elo_score'],
                'normalized_match': lmsys_match['normalized_name']
            }
            matched_models.append(matched_model)
        else:
            unmatched_model = {
                'openrouter_id': model_id,
                'openrouter_name': model_name,
                'normalized_id': normalized_id,
                'normalized_name': normalized_name
            }
            unmatched_openrouter.append(unmatched_model)
    
    # Get sample of unmatched LMSYS models
    matched_lmsys_names = {m['normalized_match'] for m in matched_models}
    unmatched_lmsys = []
    
    for normalized_name, lmsys_data in lmsys_models.items():
        if normalized_name not in matched_lmsys_names:
            unmatched_lmsys.append({
                'lmsys_original_name': lmsys_data['original_lmsys_name'],
                'normalized_name': normalized_name,
                'elo_score': lmsys_data['elo_score']
            })
    
    # Sort and take sample of unmatched LMSYS models
    unmatched_lmsys.sort(key=lambda x: x['elo_score'], reverse=True)
    sample_unmatched_lmsys = unmatched_lmsys[:15]  # Top 15 by ELO score
    
    return matched_models, unmatched_openrouter, sample_unmatched_lmsys

def print_results(matched_models: List[Dict], unmatched_openrouter: List[Dict], 
                 sample_unmatched_lmsys: List[Dict], total_lmsys: int, total_openrouter: int):
    """
    Print detailed results of the matching process.
    """
    print("\n" + "="*80)
    print("LMSYS TO OPENROUTER MAPPING ANALYSIS RESULTS")
    print("="*80)
    
    print(f"\nDATASET SUMMARY:")
    print(f"  • Total LMSYS models loaded: {total_lmsys}")
    print(f"  • Total active OpenRouter models: {total_openrouter}")
    print(f"  • Successfully matched models: {len(matched_models)}")
    print(f"  • Match rate: {len(matched_models)/total_openrouter*100:.1f}% of OpenRouter models")
    
    # Sort matched models by ELO score (highest first)
    matched_models.sort(key=lambda x: x['elo_score'], reverse=True)
    
    print(f"\n{'='*80}")
    print("SUCCESSFULLY MATCHED MODELS (sorted by ELO score)")
    print("="*80)
    if matched_models:
        for model in matched_models:
            print(f"{model['openrouter_id']:50} | {model['openrouter_name']:40} | {model['lmsys_original_name']:40} | ELO: {model['elo_score']}")
    else:
        print("No models were successfully matched.")
    
    print(f"\n{'='*80}")
    print("OPENROUTER MODELS NOT MATCHED TO LMSYS")
    print("="*80)
    if unmatched_openrouter:
        for model in unmatched_openrouter:
            print(f"{model['openrouter_id']:50} | {model['openrouter_name']:40} | Norm ID: {model['normalized_id']:30} | Norm Name: {model['normalized_name']:30}")
    else:
        print("All OpenRouter models were successfully matched!")
    
    print(f"\n{'='*80}")
    print("SAMPLE: HIGH-ELO LMSYS MODELS NOT MATCHED TO OPENROUTER")
    print("="*80)
    if sample_unmatched_lmsys:
        for model in sample_unmatched_lmsys:
            print(f"{model['lmsys_original_name']:60} | Norm: {model['normalized_name']:40} | ELO: {model['elo_score']}")
    else:
        print("All high-ELO LMSYS models were matched to OpenRouter models!")

def main():
    """
    Main execution function.
    """
    print("LMSYS Chatbot Arena ELO Mapping Exploration")
    print("="*50)
    
    # 1. Get Hugging Face token
    hf_token = os.environ.get('HF_TOKEN')
    if not hf_token:
        print("Error: HF_TOKEN not found in environment variables.")
        print("Please add your Hugging Face User Access Token to Replit Secrets under the key 'HF_TOKEN'.")
        sys.exit(1)
    
    print(f"Using Hugging Face token: {hf_token[:8]}..." if len(hf_token) > 8 else "Short token found")
    
    # 2. Load LMSYS data
    lmsys_models = load_lmsys_data(hf_token)
    if not lmsys_models:
        print("Failed to load LMSYS data. Exiting.")
        sys.exit(1)
    
    # 3. Load OpenRouter models
    openrouter_models = load_openrouter_models()
    if not openrouter_models:
        print("Failed to load OpenRouter models. Exiting.")
        sys.exit(1)
    
    # 4. Attempt matching
    matched_models, unmatched_openrouter, sample_unmatched_lmsys = match_models(
        openrouter_models, lmsys_models
    )
    
    # 5. Print results
    print_results(
        matched_models, unmatched_openrouter, sample_unmatched_lmsys,
        len(lmsys_models), len(openrouter_models)
    )
    
    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print("="*80)
    print("Next steps:")
    print("1. Review the matched models to validate accuracy")
    print("2. Analyze unmatched models to improve normalization function")
    print("3. Consider manual mappings for high-value models")
    print("4. Integrate successful mappings into price_updater.py")

if __name__ == "__main__":
    main()