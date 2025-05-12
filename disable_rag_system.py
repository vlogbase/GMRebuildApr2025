"""
Disable the old RAG system in app.py while keeping the memory system.
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

def disable_rag_system():
    """Disable the RAG system in app.py"""
    content = read_file('app.py')
    
    # 1. Set ENABLE_RAG to False
    enable_rag_pattern = r'(# Check if we should enable RAG features\nENABLE_RAG =) os\.environ\.get\(\'ENABLE_RAG\', \'true\'\)\.lower\(\) == \'true\''
    
    if re.search(enable_rag_pattern, content):
        content = re.sub(
            enable_rag_pattern,
            r'\1 False  # Disabled - using direct PDF handling with OpenRouter instead',
            content
        )
        print("✅ Set ENABLE_RAG to False")
    else:
        print("Could not find ENABLE_RAG configuration")
    
    # 2. Replace the document processor initialization
    document_processor_pattern = r'# Initialize document processor for RAG if enabled\nif ENABLE_RAG:.*?ENABLE_RAG = False'
    
    if re.search(document_processor_pattern, content, re.DOTALL):
        replacement = """# RAG system removed - using direct PDF handling with OpenRouter instead
# ENABLE_RAG is permanently set to False"""
        
        content = re.sub(
            document_processor_pattern,
            replacement,
            content,
            flags=re.DOTALL
        )
        print("✅ Removed document processor initialization")
    else:
        print("Could not find document processor initialization")
    
    # 3. Simplify RAG context retrieval in chat function
    rag_context_pattern = r'(# Check if we should add RAG context \(document retrieval\)\n\s+has_rag_documents = False\n\s+if ENABLE_RAG:).*?(# After all processing, add the final user message)'
    
    if re.search(rag_context_pattern, content, re.DOTALL):
        replacement = r'\1\n            # RAG system disabled - using direct PDF handling with OpenRouter instead\n            pass\n            \n            \2'
        
        content = re.sub(
            rag_context_pattern,
            replacement,
            content,
            flags=re.DOTALL
        )
        print("✅ Simplified RAG context retrieval in chat function")
    else:
        print("Could not find RAG context retrieval in chat function")
    
    # 4. Update the document upload route
    upload_route_pattern = r'@app\.route\(\'/upload\', methods=\[\'POST\'\]\)\ndef upload_documents\(\):.*?return jsonify\(response\)'
    
    if re.search(upload_route_pattern, content, re.DOTALL):
        replacement = """@app.route('/upload', methods=['POST'])
def upload_documents():
    """
    Document upload route - now disabled in favor of direct PDF handling.
    """
    return jsonify({
        "error": "The document upload feature has been replaced with direct PDF handling",
        "message": "Please use the PDF upload feature instead"
    }), 400"""
        
        content = re.sub(
            upload_route_pattern,
            replacement,
            content,
            flags=re.DOTALL
        )
        print("✅ Updated document upload route")
    else:
        print("Could not find document upload route")
    
    # 5. Update the RAG diagnostics route
    diagnostics_route_pattern = r'@app\.route\(\'/api/rag/diagnostics\', methods=\[\'GET\'\]\)\ndef rag_diagnostics\(\):.*?return jsonify\(diagnostics\)'
    
    if re.search(diagnostics_route_pattern, content, re.DOTALL):
        replacement = """@app.route('/api/rag/diagnostics', methods=['GET'])
def rag_diagnostics():
    """
    Diagnostic endpoint for RAG functionality - now disabled.
    Returns information about the new direct PDF handling capability.
    """
    return jsonify({
        "status": "disabled",
        "message": "RAG system has been replaced with direct PDF handling through OpenRouter",
        "pdf_handling": {
            "enabled": True,
            "container": os.environ.get("AZURE_STORAGE_PDF_CONTAINER_NAME", "gloriamundopdfs"),
            "supported_models": list(DOCUMENT_MODELS) if "DOCUMENT_MODELS" in globals() else []
        }
    })"""
        
        content = re.sub(
            diagnostics_route_pattern,
            replacement,
            content,
            flags=re.DOTALL
        )
        print("✅ Updated RAG diagnostics route")
    else:
        print("Could not find RAG diagnostics route")
    
    # Write the updated content back to app.py
    write_file('app.py', content)
    print("✅ RAG system disabled in app.py")
    return True

if __name__ == "__main__":
    disable_rag_system()