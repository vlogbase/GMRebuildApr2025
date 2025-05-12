"""
Script to remove the old RAG system while preserving the memory system.
This script will:
1. Disable RAG globally in app.py
2. Remove the document upload route
3. Remove RAG diagnostics route
4. Keep all memory system functionality intact
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

def disable_rag_globally():
    """
    Disable RAG globally by setting ENABLE_RAG to 'false'.
    """
    app_content = read_file('app.py')
    
    # Find the ENABLE_RAG line
    enable_rag_pattern = r'(# Check if we should enable RAG features\nENABLE_RAG =) os\.environ\.get\(\'ENABLE_RAG\', \'true\'\)\.lower\(\) == \'true\''
    
    if re.search(enable_rag_pattern, app_content):
        # Replace with disabled version
        updated_app_content = re.sub(
            enable_rag_pattern,
            r'\1 False # Disabled - using direct PDF handling with OpenRouter instead',
            app_content
        )
        
        write_file('app.py', updated_app_content)
        print("✅ Disabled RAG globally")
        return True
    else:
        print("❌ Could not locate ENABLE_RAG configuration")
        return False

def remove_document_upload_route():
    """
    Remove the document upload route from app.py.
    """
    app_content = read_file('app.py')
    
    # Find the document upload route
    upload_route_pattern = r'@app\.route\(\'/upload\', methods=\[\'POST\'\]\)\ndef upload_documents\(\):[^@]*?return jsonify\(response\)'
    
    if re.search(upload_route_pattern, app_content, re.DOTALL):
        # Replace the route with a comment
        updated_app_content = re.sub(
            upload_route_pattern,
            '# Document upload route removed - using direct PDF handling with OpenRouter instead',
            app_content,
            flags=re.DOTALL
        )
        
        write_file('app.py', updated_app_content)
        print("✅ Removed document upload route")
        return True
    else:
        print("❌ Could not locate document upload route")
        return False

def remove_rag_diagnostics_route():
    """
    Remove the RAG diagnostics route from app.py.
    """
    app_content = read_file('app.py')
    
    # Find the RAG diagnostics route
    diagnostics_route_pattern = r'@app\.route\(\'/api/rag/diagnostics\'[^@]*?return jsonify\(diagnostics\)'
    
    if re.search(diagnostics_route_pattern, app_content, re.DOTALL):
        # Replace the route with a comment and a simple disabled response
        replacement = """@app.route('/api/rag/diagnostics', methods=['GET'])
def rag_diagnostics():
    """
    Diagnostic endpoint for RAG functionality - now disabled.
    """
    return jsonify({
        "status": "disabled",
        "message": "RAG system has been replaced with direct PDF handling through OpenRouter"
    })"""
        
        updated_app_content = re.sub(
            diagnostics_route_pattern,
            replacement,
            app_content,
            flags=re.DOTALL
        )
        
        write_file('app.py', updated_app_content)
        print("✅ Updated RAG diagnostics route to return disabled status")
        return True
    else:
        print("❌ Could not locate RAG diagnostics route")
        return False

def remove_rag_from_chat_route():
    """
    Remove RAG logic from the chat route while keeping everything else.
    """
    app_content = read_file('app.py')
    
    # Find the RAG retrieval section in the chat function
    rag_retrieval_pattern = r'(# Check if we should add RAG context \(document retrieval\)\n\s+has_rag_documents = False\n\s+if ENABLE_RAG:).*?(# After all processing, add the final user message)'
    
    if re.search(rag_retrieval_pattern, app_content, re.DOTALL):
        # Replace with simplified version that does nothing
        replacement = r'\1\n            # RAG system has been disabled - using direct PDF handling with OpenRouter instead\n            pass\n            \n            \2'
        
        updated_app_content = re.sub(
            rag_retrieval_pattern,
            replacement,
            app_content,
            flags=re.DOTALL
        )
        
        write_file('app.py', updated_app_content)
        print("✅ Removed RAG logic from chat route")
        return True
    else:
        print("❌ Could not locate RAG retrieval section in chat route")
        return False

def remove_document_processor_import():
    """
    Remove the document_processor import and initialization if it exists.
    """
    app_content = read_file('app.py')
    
    # Find the document_processor import section
    import_pattern = r'# Initialize document processor for RAG if enabled\nif ENABLE_RAG:.*?ENABLE_RAG = False'
    
    if re.search(import_pattern, app_content, re.DOTALL):
        # Replace with a comment
        replacement = """# RAG system has been removed - using direct PDF handling with OpenRouter instead
# ENABLE_RAG is permanently set to False"""
        
        updated_app_content = re.sub(
            import_pattern,
            replacement,
            app_content,
            flags=re.DOTALL
        )
        
        write_file('app.py', updated_app_content)
        print("✅ Removed document_processor import and initialization")
        return True
    else:
        print("❌ Could not locate document_processor import section")
        return False

def main():
    """Execute all RAG removal steps."""
    print("Starting RAG system removal...")
    
    # 1. Remove document_processor import and initialization
    remove_document_processor_import()
    
    # 2. Disable RAG globally
    disable_rag_globally()
    
    # 3. Remove RAG logic from chat route
    remove_rag_from_chat_route()
    
    # 4. Remove document upload route
    remove_document_upload_route()
    
    # 5. Update RAG diagnostics route
    remove_rag_diagnostics_route()
    
    print("RAG system removal complete!")

if __name__ == "__main__":
    main()