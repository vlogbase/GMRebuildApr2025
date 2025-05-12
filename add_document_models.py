"""
Add PDF document model support to app.py
"""

import re

def read_file(filename):
    """Read the contents of a file."""
    with open(filename, 'r') as file:
        return file.read()

def write_file(filename, content):
    """Write content to a file."""
    with open(filename, 'w') as file:
        file.write(content)

def add_document_models():
    """Add DOCUMENT_MODELS after MULTIMODAL_MODELS in app.py"""
    content = read_file('app.py')
    
    # Find the MULTIMODAL_MODELS definition
    multimodal_models_pattern = r'(# Models that support images \(multimodal\)\nMULTIMODAL_MODELS = \{[^\}]+\})'
    
    if re.search(multimodal_models_pattern, content):
        document_models = """

# Models that support PDF documents (document processing)
DOCUMENT_MODELS = {
    "google/gemini-pro-vision", 
    "google/gemini-1.5-pro-latest",
    "google/gemini-2.0-pro",
    "google/gemini-2.5-pro-preview",
    "anthropic/claude-3-opus-20240229",
    "anthropic/claude-3-sonnet-20240229", 
    "anthropic/claude-3-haiku-20240307",
    "anthropic/claude-3.5-sonnet-20240620",
    "anthropic/claude-3.7-sonnet-20240910",
    "openai/gpt-4-turbo",
    "openai/gpt-4-vision-preview",
    "openai/gpt-4o-2024-05-13",
    "openai/gpt-4o-2024-08-06",
    "openai/o1-mini-2024-09-12",
    "perplexity/sonar-pro"
}"""
        
        # Check if DOCUMENT_MODELS already exists
        if "DOCUMENT_MODELS =" not in content:
            # Add DOCUMENT_MODELS after MULTIMODAL_MODELS
            updated_content = re.sub(
                multimodal_models_pattern,
                r'\1' + document_models,
                content
            )
            
            write_file('app.py', updated_content)
            print("✅ Added DOCUMENT_MODELS to app.py")
            return True
        else:
            print("DOCUMENT_MODELS already exists, skipping")
            return True
    else:
        print("Could not find MULTIMODAL_MODELS definition in app.py")
        return False

if __name__ == "__main__":
    add_document_models()