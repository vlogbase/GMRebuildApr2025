#!/usr/bin/env python3
"""
Quick LMSYS sample analysis to show mapping potential
"""
import os
import requests
import csv
import io
from typing import Dict, List

def normalize_for_matching(model_id_or_name: str) -> str:
    """Normalize model identifiers for better matching"""
    if not model_id_or_name:
        return ""
    
    name = model_id_or_name.lower()
    name = name.replace("-", "").replace("_", "").replace(" ", "")
    name = name.replace(".", "")
    name = name.replace(":", "")
    name = name.replace("/", "")
    
    return name

def get_lmsys_sample():
    """Get a sample of LMSYS models with ELO scores"""
    hf_token = os.environ.get('HF_TOKEN')
    if not hf_token:
        print("Error: HF_TOKEN environment variable not set")
        return []
    
    try:
        headers = {"Authorization": f"Bearer {hf_token}"}
        file_url = "https://huggingface.co/datasets/mathewhe/chatbot-arena-elo/resolve/main/elo.csv"
        response = requests.get(file_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            csv_data = io.StringIO(response.text)
            reader = csv.DictReader(csv_data)
            entries = list(reader)
            
            # Parse top models
            lmsys_models = []
            for entry in entries[:20]:  # Just top 20 for quick analysis
                model_name = entry.get('Model')
                elo_score_str = entry.get('Arena Score')
                rank = entry.get('Rank* (UB)')
                organization = entry.get('Organization')
                
                if model_name and elo_score_str:
                    try:
                        elo_score = float(elo_score_str.replace(',', ''))
                        lmsys_models.append({
                            'rank': rank,
                            'model_name': model_name,
                            'elo_score': elo_score,
                            'organization': organization,
                            'normalized': normalize_for_matching(model_name)
                        })
                    except ValueError:
                        continue
            
            return lmsys_models
        else:
            print(f"Failed to download LMSYS data: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"Error: {e}")
        return []

def get_openrouter_sample():
    """Get a sample of OpenRouter model names for comparison"""
    # Common OpenRouter model patterns we expect to find
    sample_models = [
        "google/gemini-2.0-flash-exp",
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4o",
        "meta-llama/llama-3.2-90b-vision-instruct",
        "google/gemini-pro-1.5",
        "anthropic/claude-3-haiku",
        "openai/gpt-4o-mini",
        "mistralai/mistral-large-2407",
        "qwen/qwen-2.5-72b-instruct"
    ]
    
    return [{'id': model, 'normalized': normalize_for_matching(model)} for model in sample_models]

def main():
    print("LMSYS ELO Score Mapping Analysis")
    print("=" * 40)
    
    # Get LMSYS top models
    print("Loading top LMSYS models...")
    lmsys_models = get_lmsys_sample()
    
    if not lmsys_models:
        print("Failed to load LMSYS data")
        return
    
    print(f"Loaded {len(lmsys_models)} top LMSYS models")
    print("\nTop LMSYS Models with ELO Scores:")
    print("-" * 60)
    for model in lmsys_models[:10]:
        print(f"#{model['rank']:>2} | {model['elo_score']:>4.0f} | {model['model_name']} ({model['organization']})")
    
    # Get OpenRouter sample
    print(f"\nOpenRouter Sample Models:")
    print("-" * 40)
    openrouter_models = get_openrouter_sample()
    
    # Simple matching attempt
    print(f"\nPotential Matches:")
    print("-" * 60)
    matches_found = 0
    
    for or_model in openrouter_models:
        for lmsys_model in lmsys_models:
            # Simple matching heuristics
            or_norm = or_model['normalized']
            lmsys_norm = lmsys_model['normalized']
            
            # Check if OpenRouter model contains key parts of LMSYS model
            if ('gemini' in or_norm and 'gemini' in lmsys_norm) or \
               ('claude' in or_norm and 'claude' in lmsys_norm) or \
               ('gpt4' in or_norm and 'gpt4' in lmsys_norm) or \
               ('llama' in or_norm and 'llama' in lmsys_norm):
                print(f"Potential: {or_model['id']} ↔ {lmsys_model['model_name']} (ELO: {lmsys_model['elo_score']})")
                matches_found += 1
                break
    
    print(f"\nSummary:")
    print(f"- LMSYS models loaded: {len(lmsys_models)}")
    print(f"- OpenRouter models tested: {len(openrouter_models)}")
    print(f"- Potential matches found: {matches_found}")
    print(f"- Mapping success rate: {matches_found/len(openrouter_models)*100:.1f}%")
    
    print(f"\nNext Steps:")
    print("- Implement more sophisticated matching logic")
    print("- Load full OpenRouter model database")
    print("- Create ELO-based ranking system")
    print("- Integrate rankings into model selection interface")

if __name__ == "__main__":
    main()