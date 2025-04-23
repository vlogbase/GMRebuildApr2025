"""
Test script for model filtering logic.
"""
import json

# Simulated model data from OpenRouter
test_models = [
    {
        "id": "model1",
        "pricing": {
            "prompt": 0.001,
            "completion": 0.002
        }
    },
    {
        "id": "model2",
        "pricing": {
            "prompt": "FREE",
            "completion": "—"
        }
    },
    {
        "id": "model3",
        "pricing": {
            "prompt": "$0.05",
            "completion": "$0.1"
        }
    },
    {
        "id": "model4",
        "is_free": True,
        "pricing": {
            "prompt": None,
            "completion": None
        }
    },
    {
        "id": "model5",
        "pricing": {
            "prompt": "rate-limited",
            "completion": "unknown"
        }
    },
    "just_a_string_model",  # Malformed model entry
    {
        "id": "model6",
        "pricing": "string_pricing"  # Malformed pricing
    },
    {
        "id": "model7"
        # No pricing info
    },
    {
        "id": "model8",
        "is_free": False,  # explicitly not free
        "pricing": {
            "prompt": 0.5,  # High cost
            "completion": 0.8  # High cost
        }
    }
]

def process_model_filtering(models, max_input_cost=1500.0, max_output_cost=1500.0):
    """
    Test function to process model filtering based on our updated logic
    """
    hidden_count = 0
    filtered_models = []
    total_count = 0
    
    # Process models
    for model in models:
        total_count += 1
        
        # Skip string entries (malformed data)
        if not isinstance(model, dict):
            # Count as hidden since we can't process it
            hidden_count += 1
            print(f"Non-dictionary model entry: {str(model)[:30]}... (will be hidden)")
            continue
        
        model_id = model.get('id', 'unknown')
        
        # Free models are always shown
        if model.get('is_free', False):  # Default to false if not specified
            print(f"Model {model_id} is free - adding to filtered list")
            filtered_models.append(model)
            continue
            
        # Models without pricing info are always shown
        if not model.get('pricing'):
            print(f"Model {model_id} has no pricing info - adding to filtered list")
            filtered_models.append(model)
            continue
            
        # Get pricing info
        pricing = model.get('pricing', {})
        if not isinstance(pricing, dict):
            # Non-dictionary pricing data - show model
            print(f"Model {model_id} has non-dictionary pricing - adding to filtered list")
            filtered_models.append(model)
            continue
            
        try:
            # Process prompt cost
            prompt_cost = None
            try:
                # Get prompt cost value
                prompt_cost_raw = pricing.get('prompt')
                
                # Handle string values
                if isinstance(prompt_cost_raw, str):
                    prompt_cost_raw = prompt_cost_raw.strip().lower()
                    if prompt_cost_raw in ['free', '--', '—', '-']:
                        prompt_cost = 0
                    else:
                        # Try to extract numeric part from strings like "$0.0123"
                        try:
                            prompt_cost = float(prompt_cost_raw.replace('$', '').strip())
                        except (ValueError, TypeError):
                            # Treat as exceeding limit
                            prompt_cost = max_input_cost + 1
                else:
                    # Handle numeric values
                    if isinstance(prompt_cost_raw, (int, float)):
                        prompt_cost = float(prompt_cost_raw)
                    else:
                        # Unknown format, treat as exceeding limit
                        prompt_cost = max_input_cost + 1
            except Exception as e:
                print(f"Error processing prompt cost for {model_id}: {e}")
                # Treat as exceeding limit
                prompt_cost = max_input_cost + 1
                
            # Process completion cost
            completion_cost = None
            try:
                # Get completion cost value
                completion_cost_raw = pricing.get('completion')
                
                # Handle string values
                if isinstance(completion_cost_raw, str):
                    completion_cost_raw = completion_cost_raw.strip().lower()
                    if completion_cost_raw in ['free', '--', '—', '-']:
                        completion_cost = 0
                    else:
                        # Try to extract numeric part from strings like "$0.0123"
                        try:
                            completion_cost = float(completion_cost_raw.replace('$', '').strip())
                        except (ValueError, TypeError):
                            # Treat as exceeding limit
                            completion_cost = max_output_cost + 1
                else:
                    # Handle numeric values
                    if isinstance(completion_cost_raw, (int, float)):
                        completion_cost = float(completion_cost_raw)
                    else:
                        # Unknown format, treat as exceeding limit
                        completion_cost = max_output_cost + 1
            except Exception as e:
                print(f"Error processing completion cost for {model_id}: {e}")
                # Treat as exceeding limit
                completion_cost = max_output_cost + 1
                
            # Calculate per-million costs
            input_cost = prompt_cost * 1000 if prompt_cost is not None else max_input_cost + 1
            output_cost = completion_cost * 1000 if completion_cost is not None else max_output_cost + 1
            
            # Compare costs
            if input_cost > max_input_cost or output_cost > max_output_cost:
                hidden_count += 1
                print(f"Model {model_id} filtered out (input: ${input_cost:.2f} > ${max_input_cost:.2f} or output: ${output_cost:.2f} > ${max_output_cost:.2f})")
            else:
                filtered_models.append(model)
                print(f"Model {model_id} included in filtered list (input: ${input_cost:.2f} <= ${max_input_cost:.2f} and output: ${output_cost:.2f} <= ${max_output_cost:.2f})")
        except Exception as e:
            print(f"Error processing model pricing for {model_id}: {e}")
            # Models with processing errors are excluded (fail closed approach)
            hidden_count += 1
            continue
    
    return {
        "success": True,
        "models": filtered_models,
        "hidden_count": hidden_count,
        "total_count": total_count,
        "filter_settings": {
            "max_input_cost": max_input_cost,
            "max_output_cost": max_output_cost
        }
    }

def main():
    # Test with default max costs (1500)
    print("Testing with default max costs (1500):")
    result1 = process_model_filtering(test_models)
    print(f"\nSummary: {result1['hidden_count']} of {result1['total_count']} models hidden")
    print(f"Filtered models: {[m['id'] for m in result1['models'] if isinstance(m, dict) and 'id' in m]}")
    
    print("\n" + "="*80 + "\n")
    
    # Test with low max costs (50)
    print("Testing with low max costs (50):")
    result2 = process_model_filtering(test_models, max_input_cost=50.0, max_output_cost=50.0)
    print(f"\nSummary: {result2['hidden_count']} of {result2['total_count']} models hidden")
    print(f"Filtered models: {[m['id'] for m in result2['models'] if isinstance(m, dict) and 'id' in m]}")

if __name__ == "__main__":
    main()