"""
Add PDF upload and handling support to the app.py file.
This script will add a new upload_pdf route and modify the chat route to handle PDFs.
"""

import re
import sys

def read_file(filename):
    """Read the contents of a file."""
    with open(filename, 'r') as file:
        return file.read()

def write_file(filename, content):
    """Write content to a file."""
    with open(filename, 'w') as file:
        file.write(content)

def add_pdf_upload_route(content):
    """
    Add a new upload_pdf route to app.py, similar to the upload_image route
    but adapted for PDFs and using the gloriamundopdfs container.
    """
    # Find the end of the upload_image route
    upload_image_end = content.find('@app.route(\'/clear-conversations\', methods=[\'POST\'])')
    if upload_image_end == -1:
        print("Could not find the position to insert PDF upload route")
        return content
    
    # Create the PDF upload route
    pdf_upload_route = """
@app.route('/upload_pdf', methods=['POST'])
@login_required
def upload_pdf():
    """
    Route to handle PDF uploads for multimodal messages.
    Processes and stores PDFs in Azure Blob Storage.
    
    The returned PDF URL will be included in the multimodal message content
    following OpenRouter's standardized format for all models:
    
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "User's message text"},
            {"type": "file", "file": {"filename": "document.pdf", "file_data": "URL_RETURNED_FROM_THIS_ENDPOINT"}}
        ]
    }
    
    Examples:
        # Success case - uploading a valid PDF
        curl -X POST -F "file=@/path/to/document.pdf" http://localhost:5000/upload_pdf
        
        # Failure case - no file provided
        curl -X POST http://localhost:5000/upload_pdf
        
        # Failure case - unsupported file type
        curl -X POST -F "file=@/path/to/image.jpg" http://localhost:5000/upload_pdf
        
    Success Response:
        {
            "success": true,
            "pdf_url": "https://gloriamundopdfs.blob.core.windows.net/gloriamundopdfs/a1b2c3d4e5f6.pdf"
        }
        
    Error Response:
        {
            "error": "No file provided"
        }
        
        or
        
        {
            "error": "File type .jpg is not supported. Please upload a PDF file."
        }
    """
    try:
        # Verify a file was uploaded
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
            
        # Validate file type
        filename = file.filename
        extension = Path(filename).suffix.lower()
        allowed_extensions = {'.pdf'}
        
        if extension not in allowed_extensions:
            return jsonify({
                "error": f"File type {extension} is not supported. Please upload a PDF file."
            }), 400
            
        # Generate a unique filename to avoid collisions
        unique_filename = f"{uuid.uuid4().hex}{extension}"
        
        # Read the PDF into memory
        pdf_data = file.read()
        pdf_stream = io.BytesIO(pdf_data)
        
        # Storage path for Azure Blob Storage
        storage_path = unique_filename
        
        # PDF container name - use the dedicated PDFs container
        pdf_container_name = os.environ.get("AZURE_STORAGE_PDF_CONTAINER_NAME", "gloriamundopdfs")
        
        # Store the PDF in Azure Blob Storage or fallback to local storage
        if 'USE_AZURE_STORAGE' in globals() and USE_AZURE_STORAGE and 'blob_service_client' in globals() and blob_service_client:
            try:
                # Create a container client for the PDF container
                pdf_container_client = blob_service_client.get_container_client(pdf_container_name)
                
                # Check if container exists, if not create it
                try:
                    pdf_container_client.get_container_properties()
                    logger.info(f"Container {pdf_container_name} exists")
                except Exception as container_error:
                    logger.info(f"Container {pdf_container_name} does not exist, creating it...")
                    pdf_container_client = blob_service_client.create_container(pdf_container_name)
                    logger.info(f"Container {pdf_container_name} created successfully")
                
                # Get PDF data from the stream
                pdf_stream.seek(0)
                pdf_bytes = pdf_stream.read()
                
                # Create a blob client for the specific blob
                blob_client = pdf_container_client.get_blob_client(storage_path)
                
                # Set content settings (MIME type)
                content_settings = ContentSettings(content_type='application/pdf')
                
                # Upload the PDF data to Azure Blob Storage
                blob_client.upload_blob(
                    data=pdf_bytes,
                    content_settings=content_settings,
                    overwrite=True
                )
                
                # Check if a specific model is being used (from query params)
                target_model = request.args.get('model', None)
                
                # For PDFs, we need to encode as base64 for OpenRouter
                # First, get a URL to the PDF
                pdf_url = blob_client.url
                
                # For direct OpenRouter use, we need base64
                pdf_stream.seek(0)
                base64_pdf = base64.b64encode(pdf_stream.read()).decode('utf-8')
                pdf_data_url = f"data:application/pdf;base64,{base64_pdf}"
                
                logger.info(f"Uploaded PDF to Azure Blob Storage: {pdf_url[:50]}...")
                
                return jsonify({
                    "success": True,
                    "pdf_url": pdf_url,
                    "pdf_data_url": pdf_data_url,
                    "filename": filename
                })
            except Exception as e:
                logger.exception(f"Error uploading to Azure Blob Storage: {e}")
                # Fallback to local storage if Azure Blob Storage fails
                upload_dir = Path('static/uploads/pdfs')
                upload_dir.mkdir(parents=True, exist_ok=True)
                file_path = upload_dir / unique_filename
                
                with open(file_path, 'wb') as f:
                    pdf_stream.seek(0)
                    f.write(pdf_stream.read())
                
                pdf_url = url_for('static', filename=f'uploads/pdfs/{unique_filename}', _external=True)
                
                # For direct OpenRouter use, we need base64
                pdf_stream.seek(0)
                base64_pdf = base64.b64encode(pdf_stream.read()).decode('utf-8')
                pdf_data_url = f"data:application/pdf;base64,{base64_pdf}"
                
                logger.info(f"Fallback: Saved PDF to local filesystem: {file_path}")
                
                return jsonify({
                    "success": True,
                    "pdf_url": pdf_url,
                    "pdf_data_url": pdf_data_url,
                    "filename": filename
                })
        else:
            # Azure Blob Storage not available, use local filesystem
            upload_dir = Path('static/uploads/pdfs')
            upload_dir.mkdir(parents=True, exist_ok=True)
            file_path = upload_dir / unique_filename
            
            with open(file_path, 'wb') as f:
                pdf_stream.seek(0)
                f.write(pdf_stream.read())
            
            pdf_url = url_for('static', filename=f'uploads/pdfs/{unique_filename}', _external=True)
            
            # For direct OpenRouter use, we need base64
            pdf_stream.seek(0)
            base64_pdf = base64.b64encode(pdf_stream.read()).decode('utf-8')
            pdf_data_url = f"data:application/pdf;base64,{base64_pdf}"
            
            logger.info(f"Saved PDF to local filesystem: {file_path}")
            
            return jsonify({
                "success": True,
                "pdf_url": pdf_url,
                "pdf_data_url": pdf_data_url,
                "filename": filename
            })
    except Exception as e:
        logger.exception(f"Error handling PDF upload: {e}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

"""
    # Insert the PDF upload route before the clear-conversations route
    updated_content = content[:upload_image_end] + pdf_upload_route + content[upload_image_end:]
    return updated_content

def update_imports(content):
    """Add any necessary imports for PDF handling."""
    imports_to_add = "import base64\n"
    
    # Check if we need to add base64 import
    if "import base64" not in content:
        # Find a good spot to add imports - after the last import
        last_import_match = re.search(r'^import .*$|^from .* import .*$', content, re.MULTILINE)
        if last_import_match:
            last_import_pos = content.rfind("import", 0, 1000)  # Look within first 1000 chars
            if last_import_pos != -1:
                # Find the line end after this import
                line_end = content.find("\n", last_import_pos)
                if line_end != -1:
                    # Insert the new imports after the last import
                    return content[:line_end+1] + imports_to_add + content[line_end+1:]
    
    # If no suitable position found or imports already exist
    return content

def update_chat_route(content):
    """
    Update the chat route to handle PDF files similar to how it handles images.
    """
    # Let's identify patterns to modify in the chat route
    # This would depend on the existing code structure and might need adjustments
    # For now, we'll create a placeholder update
    
    # Find the parameter extraction section in the chat route
    param_extraction_pattern = r'(\s+# Extract data\n\s+user_message = data\.get\("message", ""\).*?\n\s+)(image_url = data\.get\("image_url", None\)\n\s+image_urls = data\.get\("image_urls", \[\]\))'
    
    # Add pdf_url and pdf_urls parameters
    replacement = r'\1image_url = data.get("image_url", None)\n        image_urls = data.get("image_urls", [])\n        pdf_url = data.get("pdf_url", None)\n        pdf_urls = data.get("pdf_urls", [])\n        pdf_filename = data.get("pdf_filename", "document.pdf")'
    
    content = re.sub(param_extraction_pattern, replacement, content, flags=re.DOTALL)
    
    # Find the multimodal content creation section
    multimodal_pattern = r'(\s+# Following OpenRouter\'s unified multimodal format.*?\n\s+# https://openrouter\.ai/docs#multimodal\n\s+if \(image_url or \(image_urls and len\(image_urls\) > 0\)\) and openrouter_model in MULTIMODAL_MODELS:)'
    
    # Update the condition to check for PDFs as well
    pdf_condition = r'\1 or (pdf_url or (pdf_urls and len(pdf_urls) > 0))'
    
    content = re.sub(multimodal_pattern, pdf_condition, content, flags=re.DOTALL)
    
    # Find the content creation part for multimodal messages
    content_creation_pattern = r'(\s+# Build the content array.*?\n.*?content_array = \[\]\n.*?content_array\.append\({"type": "text", "text": user_message}\))'
    
    # Add PDF handling to the content creation
    pdf_handling = r'''
        # Add PDFs to content array if provided
        if pdf_url:
            content_array.append({
                "type": "file",
                "file": {
                    "filename": pdf_filename,
                    "file_data": pdf_url
                }
            })
            logger.info(f"Added PDF to message: {pdf_filename}")
        
        # Add multiple PDFs if provided
        if pdf_urls and len(pdf_urls) > 0:
            for idx, pdf_item in enumerate(pdf_urls):
                pdf_data = pdf_item.get("url", "")
                pdf_name = pdf_item.get("filename", f"document_{idx+1}.pdf")
                if pdf_data:
                    content_array.append({
                        "type": "file",
                        "file": {
                            "filename": pdf_name,
                            "file_data": pdf_data
                        }
                    })
                    logger.info(f"Added PDF #{idx+1} to message: {pdf_name}")'''
    
    # Insert the PDF handling after adding text to the content array
    content = re.sub(content_creation_pattern, r'\1' + pdf_handling, content, flags=re.DOTALL)
    
    return content

def update_document_models(content):
    """
    Update the models list to include PDF capable models.
    """
    # Find the MULTIMODAL_MODELS section
    multimodal_pattern = r'(# Models that support images \(multimodal\)\nMULTIMODAL_MODELS = \{[^\}]+\})'
    
    # Define DOCUMENT_MODELS section
    document_models = '''
# Models that support PDFs (document processing)
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
}'''
    
    # Add DOCUMENT_MODELS after MULTIMODAL_MODELS
    if "DOCUMENT_MODELS =" not in content:
        content = re.sub(multimodal_pattern, r'\1\n' + document_models, content, flags=re.DOTALL)
    
    return content

def update_multimodal_condition(content):
    """
    Update the multimodal checking condition to include PDF-capable models.
    """
    # Find where we check if a model is multimodal in the chat route
    model_check_pattern = r'(if \(image_url or \(image_urls and len\(image_urls\) > 0\)\)) and openrouter_model in MULTIMODAL_MODELS:'
    
    # Update to include DOCUMENT_MODELS if they exist
    new_condition = r'\1:\n            # Check if the model supports multimodal content\n            is_multimodal = openrouter_model in MULTIMODAL_MODELS\n            \n            # Check if the model supports PDF documents\n            is_document_capable = openrouter_model in DOCUMENT_MODELS\n            \n            if is_multimodal or is_document_capable'
    
    content = re.sub(model_check_pattern, new_condition, content)
    
    return content

def apply_updates():
    """Apply all updates to app.py."""
    try:
        content = read_file('app.py')
        
        # Step 1: Add necessary imports
        content = update_imports(content)
        print("✅ Added necessary imports")
        
        # Step 2: Update models list to include document-capable models
        content = update_document_models(content)
        print("✅ Added DOCUMENT_MODELS to identify PDF-capable models")
        
        # Step 3: Update multimodal condition check
        content = update_multimodal_condition(content)
        print("✅ Updated model capability checks")
        
        # Step 4: Update chat route to handle PDFs
        content = update_chat_route(content)
        print("✅ Updated chat route to handle PDFs")
        
        # Step 5: Add PDF upload route
        content = add_pdf_upload_route(content)
        print("✅ Added PDF upload route")
        
        # Write the updated file
        write_file('app.py', content)
        print("\n✅ Successfully updated app.py with PDF handling support!")
        
    except Exception as e:
        print(f"❌ Error updating app.py: {e}")

if __name__ == "__main__":
    apply_updates()