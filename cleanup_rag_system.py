"""
Script to clean up the old RAG system while preserving the PDF handling functionality.
This script will:
1. Remove RAG system imports and initialization
2. Remove or update the document upload route
3. Simplify RAG diagnostics route
4. Remove RAG-specific code from the chat function
5. Keep all memory system functionality intact
6. Keep all direct PDF handling functionality
"""

import re
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def read_file(filename):
    """Read the contents of a file."""
    with open(filename, 'r') as file:
        return file.read()

def write_file(filename, content):
    """Write content to a file."""
    with open(filename, 'w') as file:
        file.write(content)

def backup_file(filename):
    """Create a backup of the file before modifying it."""
    backup_filename = f"{filename}.bak"
    if os.path.exists(filename):
        content = read_file(filename)
        write_file(backup_filename, content)
        logger.info(f"Backup created: {backup_filename}")
        return True
    return False

def remove_document_processor_import(content):
    """Remove DocumentProcessor import and initialization."""
    
    # Remove import
    import_pattern = r'from document_processor import DocumentProcessor\s*'
    content = re.sub(import_pattern, '', content)
    logger.info("Removed DocumentProcessor import")
    
    # Remove global instance
    global_instance_pattern = r'# Initialize document processor for RAG.*?document_processor = None\s*'
    content = re.sub(global_instance_pattern, '', content, flags=re.DOTALL)
    logger.info("Removed global document processor instance")
    
    # Disable RAG flag
    enable_rag_pattern = r'(# Check if we should enable RAG features\s*ENABLE_RAG =) .*'
    content = re.sub(enable_rag_pattern, 
                    r'\1 False  # Disabled - using direct PDF handling with OpenRouter instead', 
                    content)
    logger.info("Set ENABLE_RAG to False")
    
    return content

def clean_chat_function(content):
    """Remove RAG-specific code from the chat function."""
    
    # Remove document retrieval logic
    rag_context_pattern = r'(# Check if we should add RAG context \(document retrieval\)\s*has_rag_documents = False\s*if ENABLE_RAG:).*?(# After all processing)'
    replacement = r'\1\n            # RAG system removed - using direct PDF handling with OpenRouter instead\n            pass\n        \2'
    content = re.sub(rag_context_pattern, replacement, content, flags=re.DOTALL)
    logger.info("Removed document retrieval logic from chat function")
    
    # Remove RAG context injection
    context_injection_pattern = r'(# Format document chunks as context\s*context_text = ".*?".*?for i, chunk in enumerate\(relevant_chunks\):).*?(# Add formatted chunk with source attribution\s*context_text \+= f".*?")'
    if re.search(context_injection_pattern, content, re.DOTALL):
        content = re.sub(context_injection_pattern, '', content, flags=re.DOTALL)
        logger.info("Removed context injection code")
    
    # Remove has_rag_documents checks
    rag_check_pattern = r'if has_rag_documents:.*?# Only use context if we actually retrieved documents'
    content = re.sub(rag_check_pattern, '', content, flags=re.DOTALL)
    logger.info("Removed has_rag_documents checks")
    
    return content

def update_upload_documents_route(content):
    """Update the /upload route to direct users to use the PDF upload functionality."""
    
    upload_route_pattern = r'@app\.route\(\'/upload\', methods=\[\'POST\'\]\)\s*@login_required\s*def upload_documents\(\):.*?return jsonify\(response\)'
    replacement = """@app.route('/upload', methods=['POST'])
@login_required
def upload_documents():
    \"\"\"
    Legacy document upload route - now redirects to the unified file upload endpoint.
    \"\"\"
    return redirect(url_for('upload_file'))"""
    
    content = re.sub(upload_route_pattern, replacement, content, flags=re.DOTALL)
    logger.info("Updated upload_documents route to redirect to unified upload_file endpoint")
    
    return content

def update_rag_diagnostics_route(content):
    """Update the RAG diagnostics route to return info about PDF handling."""
    
    diagnostics_pattern = r'@app\.route\(\'/api/rag/diagnostics\', methods=\[\'GET\'\]\)\s*def rag_diagnostics\(\):.*?return jsonify\(diagnostics\)'
    replacement = """@app.route('/api/rag/diagnostics', methods=['GET'])
def rag_diagnostics():
    \"\"\"
    Diagnostic endpoint to check the state of document processing.
    This endpoint now returns information about direct PDF handling capabilities.
    \"\"\"
    # Get models that support PDF handling
    pdf_capable_models = []
    
    try:
        models = _fetch_openrouter_models()
        for model_id, model_info in models.items():
            if model_info.get('pdf', False) or model_info.get('supports_pdf', False):
                pdf_capable_models.append(model_id)
    except Exception as e:
        logger.error(f"Error fetching PDF-capable models: {e}")
    
    return jsonify({
        "status": "transitioned",
        "message": "RAG system replaced with direct PDF handling through OpenRouter",
        "pdf_handling": {
            "enabled": True,
            "container": os.environ.get("AZURE_STORAGE_PDF_CONTAINER_NAME", "gloriamundopdfs"),
            "supported_models": pdf_capable_models
        }
    })"""
    
    content = re.sub(diagnostics_pattern, replacement, content, flags=re.DOTALL)
    logger.info("Updated RAG diagnostics route to report PDF handling capabilities")
    
    return content

def remove_obsolete_files():
    """Mark obsolete RAG files as deprecated."""
    obsolete_files = [
        'document_processor.py',
    ]
    
    for file in obsolete_files:
        if os.path.exists(file):
            # Rename the file to mark it as deprecated
            deprecated_name = f"{file}.deprecated"
            os.rename(file, deprecated_name)
            logger.info(f"Marked {file} as deprecated")
            
            # Create a placeholder file explaining the deprecation
            with open(file, 'w') as f:
                f.write(f"""\"\"\"
This file is deprecated. Its functionality has been replaced by direct PDF handling.
The original content has been moved to {deprecated_name}.
\"\"\"

# This file is deprecated and kept only for reference.
# Do not use or import any functions from this file.
""")
            logger.info(f"Created placeholder for {file}")

def main():
    """Execute the cleanup process."""
    logger.info("Starting RAG system cleanup...")
    
    # Backup app.py before making changes
    if backup_file('app.py'):
        # Read the content of app.py
        content = read_file('app.py')
        
        # Remove imports and initialization
        content = remove_document_processor_import(content)
        
        # Clean up the chat function
        content = clean_chat_function(content)
        
        # Update document upload route
        content = update_upload_documents_route(content)
        
        # Update RAG diagnostics route
        content = update_rag_diagnostics_route(content)
        
        # Write the cleaned content back to app.py
        write_file('app.py', content)
        logger.info("Updated app.py with RAG cleanup changes")
        
        # Mark obsolete files as deprecated
        remove_obsolete_files()
        
        logger.info("RAG system cleanup completed successfully!")
    else:
        logger.error("Failed to backup app.py. Cleanup aborted.")

if __name__ == "__main__":
    main()