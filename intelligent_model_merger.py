#!/usr/bin/env python3
"""
Intelligent Model Merger

Intelligently merges LMSYS ELO data into OpenRouter model list using
advanced matching algorithms and contextual analysis.
"""

import csv
import json
import re
import logging
from difflib import SequenceMatcher
from collections import defaultdict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntelligentMatcher:
    def __init__(self):
        self.openrouter_models = []
        self.lmsys_models = []
        self.matches = []
        self.unmatched_or = []
        self.unmatched_lmsys = []
        
    def load_data(self):
        """Load both CSV files"""
        logger.info("Loading OpenRouter models...")
        with open('all_openrouter_models.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.openrouter_models = list(reader)
        
        logger.info("Loading LMSYS models...")
        with open('all_lmsys_models.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.lmsys_models = list(reader)
            
        logger.info(f"Loaded {len(self.openrouter_models)} OpenRouter models")
        logger.info(f"Loaded {len(self.lmsys_models)} LMSYS models")
    
    def normalize_model_name(self, name, preserve_variants=True):
        """Advanced normalization that preserves important distinctions"""
        if not name:
            return ""
        
        name = name.lower().strip()
        
        # Remove common prefixes/suffixes but preserve core identifiers
        name = re.sub(r'^(openai|anthropic|google|meta|microsoft|amazon|ai21|mistral)[\s:/\-]?', '', name)
        name = re.sub(r'\s*\(.*?\)\s*', '', name)  # Remove parenthetical info
        
        if preserve_variants:
            # Preserve important model variants and versions
            # Keep opus, sonnet, haiku, pro, mini, micro, lite
            # Keep version numbers like 3.5, 4.0, 1.5, 2.5
            # Keep size indicators like 70b, 8b, 7b
            # Keep dates like 20240620, 20241022
            pass
        else:
            # More aggressive normalization for fuzzy matching
            name = re.sub(r'[\s\-_\.:/]', '', name)
        
        # Standardize common variations
        replacements = {
            'chatgpt': 'gpt',
            'claude3': 'claude3',
            'claude35': 'claude35',
            'gemini': 'gemini',
            'llama3': 'llama3',
            'instruct': 'instruct',
        }
        
        for old, new in replacements.items():
            name = name.replace(old, new)
        
        return name
    
    def calculate_similarity(self, str1, str2):
        """Calculate similarity with weighted scoring"""
        return SequenceMatcher(None, str1, str2).ratio()
    
    def extract_key_features(self, model_name):
        """Extract key identifying features from model name"""
        features = {
            'provider': None,
            'model_family': None,
            'variant': None,
            'version': None,
            'size': None,
            'date': None,
            'type': None
        }
        
        name_lower = model_name.lower()
        
        # Provider detection
        providers = ['openai', 'anthropic', 'google', 'meta', 'amazon', 'microsoft', 'ai21', 'mistral', 'deepseek']
        for provider in providers:
            if provider in name_lower:
                features['provider'] = provider
                break
        
        # Model family detection
        families = ['gpt', 'claude', 'gemini', 'llama', 'nova', 'deepseek']
        for family in families:
            if family in name_lower:
                features['model_family'] = family
                break
        
        # Variant detection
        variants = ['opus', 'sonnet', 'haiku', 'pro', 'mini', 'micro', 'lite', 'flash', 'thinking']
        for variant in variants:
            if variant in name_lower:
                features['variant'] = variant
                break
        
        # Version detection (e.g., 3.5, 4.0, 1.5)
        version_match = re.search(r'(\d+\.?\d*)', name_lower)
        if version_match:
            features['version'] = version_match.group(1)
        
        # Size detection (e.g., 70b, 8b)
        size_match = re.search(r'(\d+\.?\d*[bmk])', name_lower)
        if size_match:
            features['size'] = size_match.group(1)
        
        # Date detection (e.g., 20240620)
        date_match = re.search(r'(20\d{6})', name_lower)
        if date_match:
            features['date'] = date_match.group(1)
        
        # Type detection
        types = ['instruct', 'chat', 'preview', 'turbo']
        for model_type in types:
            if model_type in name_lower:
                features['type'] = model_type
                break
        
        return features
    
    def feature_match_score(self, or_features, lmsys_features):
        """Calculate match score based on feature alignment"""
        score = 0
        weights = {
            'provider': 0.1,  # Less important since we normalize providers
            'model_family': 0.3,
            'variant': 0.3,
            'version': 0.2,
            'size': 0.2,
            'date': 0.1,
            'type': 0.1
        }
        
        for feature, weight in weights.items():
            or_val = or_features.get(feature)
            lmsys_val = lmsys_features.get(feature)
            
            if or_val and lmsys_val:
                if or_val == lmsys_val:
                    score += weight
                elif feature in ['version', 'size'] and or_val in lmsys_val or lmsys_val in or_val:
                    score += weight * 0.7  # Partial match
        
        return min(score, 1.0)
    
    def find_best_matches(self):
        """Find best matches using multiple algorithms"""
        logger.info("Finding intelligent matches...")
        
        # Track which LMSYS models have been matched
        lmsys_used = set()
        
        for or_model in self.openrouter_models:
            or_id = or_model['openrouter_id']
            or_name = or_model['display_name']
            
            best_match = None
            best_score = 0
            best_reasoning = ""
            
            # Extract features for this OpenRouter model
            or_features = self.extract_key_features(or_id + " " + or_name)
            
            for i, lmsys_model in enumerate(self.lmsys_models):
                if i in lmsys_used:
                    continue
                    
                lmsys_name = lmsys_model['lmsys_model_name']
                lmsys_features = self.extract_key_features(lmsys_name)
                
                # Multiple scoring approaches
                scores = {}
                
                # 1. Direct string similarity
                id_similarity = self.calculate_similarity(
                    self.normalize_model_name(or_id, preserve_variants=False),
                    self.normalize_model_name(lmsys_name, preserve_variants=False)
                )
                name_similarity = self.calculate_similarity(
                    self.normalize_model_name(or_name, preserve_variants=False),
                    self.normalize_model_name(lmsys_name, preserve_variants=False)
                )
                scores['string_sim'] = max(id_similarity, name_similarity)
                
                # 2. Feature-based matching
                scores['feature_match'] = self.feature_match_score(or_features, lmsys_features)
                
                # 3. Exact variant matching (high weight for exact matches)
                if (or_features.get('variant') == lmsys_features.get('variant') and
                    or_features.get('model_family') == lmsys_features.get('model_family')):
                    scores['exact_variant'] = 1.0
                else:
                    scores['exact_variant'] = 0
                
                # 4. Provider family bonus
                if (or_features.get('model_family') == lmsys_features.get('model_family')):
                    scores['family_bonus'] = 0.3
                else:
                    scores['family_bonus'] = 0
                
                # Weighted total score
                total_score = (
                    scores['string_sim'] * 0.4 +
                    scores['feature_match'] * 0.4 +
                    scores['exact_variant'] * 0.3 +
                    scores['family_bonus'] * 0.2
                )
                
                # Update best match if this is better
                if total_score > best_score and total_score >= 0.6:  # Minimum threshold
                    best_score = total_score
                    best_match = {
                        'lmsys_index': i,
                        'lmsys_model': lmsys_model,
                        'score': total_score,
                        'component_scores': scores
                    }
                    
                    # Generate reasoning
                    reasoning_parts = []
                    if scores['exact_variant'] > 0:
                        reasoning_parts.append("Exact variant match")
                    if scores['feature_match'] > 0.5:
                        reasoning_parts.append("Strong feature alignment")
                    if scores['string_sim'] > 0.8:
                        reasoning_parts.append("High string similarity")
                    if scores['family_bonus'] > 0:
                        reasoning_parts.append("Same model family")
                    
                    best_reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Moderate similarity"
            
            # Record the result
            if best_match and best_score >= 0.7:  # High confidence threshold
                self.matches.append({
                    'openrouter_model': or_model,
                    'lmsys_match': best_match['lmsys_model'],
                    'confidence_score': round(best_score * 100, 2),
                    'reasoning': best_reasoning,
                    'component_scores': best_match['component_scores']
                })
                lmsys_used.add(best_match['lmsys_index'])
            else:
                self.unmatched_or.append(or_model)
        
        # Track unmatched LMSYS models
        for i, lmsys_model in enumerate(self.lmsys_models):
            if i not in lmsys_used:
                self.unmatched_lmsys.append(lmsys_model)
        
        logger.info(f"Found {len(self.matches)} confident matches")
        logger.info(f"Unmatched OpenRouter models: {len(self.unmatched_or)}")
        logger.info(f"Unmatched LMSYS models: {len(self.unmatched_lmsys)}")
    
    def create_merged_csv(self):
        """Create the final merged CSV"""
        logger.info("Creating merged CSV...")
        
        # Create lookup for matches
        match_lookup = {}
        for match in self.matches:
            or_id = match['openrouter_model']['openrouter_id']
            match_lookup[or_id] = match
        
        # Generate merged data
        merged_data = []
        for or_model in self.openrouter_models:
            or_id = or_model['openrouter_id']
            
            # Start with OpenRouter data
            merged_row = or_model.copy()
            
            # Add matching information
            if or_id in match_lookup:
                match = match_lookup[or_id]
                lmsys_data = match['lmsys_match']
                
                merged_row.update({
                    'matched_lmsys_model': lmsys_data['lmsys_model_name'],
                    'matched_elo_score': lmsys_data['elo_score'],
                    'match_confidence': f"{match['confidence_score']}%",
                    'match_reasoning': match['reasoning'],
                    'lmsys_rank': lmsys_data.get('rank', ''),
                    'lmsys_organization': lmsys_data.get('organization', ''),
                    'has_elo_match': 'YES'
                })
            else:
                merged_row.update({
                    'matched_lmsys_model': '',
                    'matched_elo_score': '',
                    'match_confidence': '',
                    'match_reasoning': 'No confident match found',
                    'lmsys_rank': '',
                    'lmsys_organization': '',
                    'has_elo_match': 'NO'
                })
            
            merged_data.append(merged_row)
        
        # Write merged CSV
        filename = 'merged_openrouter_with_elo.csv'
        if merged_data:
            fieldnames = list(merged_data[0].keys())
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(merged_data)
        
        logger.info(f"Created merged file: {filename}")
        return filename
    
    def generate_summary(self):
        """Generate a summary of the matching process"""
        high_confidence = len([m for m in self.matches if m['confidence_score'] >= 85])
        medium_confidence = len([m for m in self.matches if 70 <= m['confidence_score'] < 85])
        
        logger.info("\n" + "="*60)
        logger.info("INTELLIGENT MATCHING SUMMARY")
        logger.info("="*60)
        logger.info(f"Total OpenRouter models: {len(self.openrouter_models)}")
        logger.info(f"Total LMSYS models: {len(self.lmsys_models)}")
        logger.info(f"Successful matches: {len(self.matches)}")
        logger.info(f"  - High confidence (≥85%): {high_confidence}")
        logger.info(f"  - Medium confidence (70-84%): {medium_confidence}")
        logger.info(f"Unmatched OpenRouter models: {len(self.unmatched_or)}")
        
        # Show some example matches
        logger.info("\nExample high-confidence matches:")
        high_conf_matches = [m for m in self.matches if m['confidence_score'] >= 85][:5]
        for match in high_conf_matches:
            or_name = match['openrouter_model']['openrouter_id']
            lmsys_name = match['lmsys_match']['lmsys_model_name']
            elo = match['lmsys_match']['elo_score']
            conf = match['confidence_score']
            logger.info(f"  {or_name} → {lmsys_name} (ELO: {elo}, {conf}%)")

def main():
    """Run the intelligent model merger"""
    logger.info("🧠 Starting Intelligent Model Merger")
    logger.info("="*50)
    
    try:
        matcher = IntelligentMatcher()
        matcher.load_data()
        matcher.find_best_matches()
        merged_file = matcher.create_merged_csv()
        matcher.generate_summary()
        
        logger.info(f"\n🎉 Intelligent merging completed!")
        logger.info(f"Output file: {merged_file}")
        logger.info("This file contains your OpenRouter models with matched ELO scores")
        logger.info("and confidence indicators for each match.")
        
        return True
        
    except Exception as e:
        logger.error(f"Merging failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)