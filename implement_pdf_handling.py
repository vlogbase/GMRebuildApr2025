"""
Script to implement PDF handling using OpenRouter's direct PDF processing capability.
This script will:
1. Add a PDF upload route similar to the image upload route
2. Update the app.py to handle PDFs in chat messages
3. Configure the necessary models and endpoints
"""

import os
import re
from pathlib import Path

def read_file(filename):
    """Read the contents of a file."""
    with open(filename, 'r') as file:
        return file.read()

def write_file(filename, content):
    """Write content to a file."""
    with open(filename, 'w') as file:
        file.write(content)

def add_pdf_upload_route():
    """Add a new PDF upload route to app.py."""
    app_content = read_file('app.py')
    
    # Look for the position after the image upload route
    upload_image_end = app_content.find('@app.route(\'/clear-conversations\'')
    
    if upload_image_end == -1:
        print("Could not locate position to insert PDF upload route")
        return False
    
    # PDF upload route implementation
    pdf_upload_route = """
@app.route('/upload_pdf', methods=['POST'])
@login_required
def upload_pdf():
    """
    Route to handle PDF uploads for multimodal messages.
    Processes and stores PDFs in Azure Blob Storage.
    
    The returned PDF URL will be included in the multimodal message content
    following OpenRouter's standardized format for all models.
    
    Example format:
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "User's message text"},
            {"type": "file", "file": {"filename": "document.pdf", "file_data": "DATA_URL_FROM_THIS_ENDPOINT"}}
        ]
    }
    """
    
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
            "pdf_url": "https://gloriamundopdfs.blob.core.windows.net/gloriamundopdfs/a1b2c3d4e5f6.pdf",
            "pdf_data_url": "data:application/pdf;base64,..."
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
                
                # For OpenRouter, we need to use base64 encoded data URL
                pdf_stream.seek(0)
                base64_pdf = base64.b64encode(pdf_stream.read()).decode('utf-8')
                pdf_data_url = f"data:application/pdf;base64,{base64_pdf}"
                
                logger.info(f"Uploaded PDF to Azure Blob Storage: {unique_filename}")
                
                return jsonify({
                    "success": True,
                    "pdf_url": blob_client.url,
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
                
                # For OpenRouter, we need to use base64 encoded data URL
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
            
            # For OpenRouter, we need to use base64 encoded data URL
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
    
    # Insert the PDF upload route
    updated_app_content = app_content[:upload_image_end] + pdf_upload_route + app_content[upload_image_end:]
    write_file('app.py', updated_app_content)
    print("✅ Added PDF upload route")
    return True

def add_document_models():
    """Add the DOCUMENT_MODELS set after MULTIMODAL_MODELS in app.py."""
    app_content = read_file('app.py')
    
    # Look for MULTIMODAL_MODELS
    multimodal_models_end = app_content.find('MULTIMODAL_MODELS =')
    if multimodal_models_end == -1:
        print("Could not locate MULTIMODAL_MODELS set")
        return False
    
    # Find the end of the MULTIMODAL_MODELS section
    models_end = app_content.find('}', multimodal_models_end)
    if models_end == -1:
        print("Could not locate end of MULTIMODAL_MODELS set")
        return False
    
    # If DOCUMENT_MODELS already exists, don't add it again
    if 'DOCUMENT_MODELS =' in app_content:
        print("DOCUMENT_MODELS already exists, skipping")
        return True
    
    # Add DOCUMENT_MODELS after MULTIMODAL_MODELS
    document_models_def = """

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
    
    updated_app_content = app_content[:models_end+1] + document_models_def + app_content[models_end+1:]
    write_file('app.py', updated_app_content)
    print("✅ Added DOCUMENT_MODELS definition")
    return True

def update_chat_function():
    """Update the chat function to handle PDFs."""
    app_content = read_file('app.py')
    
    # First, let's add PDF parameters to the data extraction part
    data_extraction_pattern = r'(\s+# Extract data\n\s+user_message = data\.get\("message", ""\).*?\n\s+image_url = data\.get\("image_url", None\)\n\s+image_urls = data\.get\("image_urls", \[\]\))'
    
    if re.search(data_extraction_pattern, app_content):
        pdf_params = "\n        pdf_url = data.get(\"pdf_url\", None)\n        pdf_urls = data.get(\"pdf_urls\", [])\n        pdf_filename = data.get(\"pdf_filename\", \"document.pdf\")"
        
        updated_app_content = re.sub(
            data_extraction_pattern,
            r'\1' + pdf_params,
            app_content
        )
        
        print("✅ Added PDF parameters to data extraction")
    else:
        print("❌ Could not locate data extraction section")
        updated_app_content = app_content
    
    # Now, modify the multimodal condition to check for PDFs too
    multimodal_condition_pattern = r'(if \(image_url or \(image_urls and len\(image_urls\) > 0\)\)) and openrouter_model in MULTIMODAL_MODELS:'
    
    if re.search(multimodal_condition_pattern, updated_app_content):
        pdf_condition = r'\1 or (pdf_url or (pdf_urls and len(pdf_urls) > 0)):\n            # Check if model supports multimodal content\n            supports_multimodal = openrouter_model in MULTIMODAL_MODELS\n            \n            # Check if model supports PDF documents\n            supports_documents = openrouter_model in DOCUMENT_MODELS\n            \n            if supports_multimodal or supports_documents'
        
        updated_app_content = re.sub(
            multimodal_condition_pattern,
            pdf_condition,
            updated_app_content
        )
        
        print("✅ Modified multimodal condition to check for PDFs and model capabilities")
    else:
        print("❌ Could not locate multimodal condition section")
    
    # Finally, add PDF handling to the content array creation
    content_array_pattern = r'(\s+# Add multiple images if provided.*?\n\s+for idx, img_url in enumerate\(image_urls\):.*?\n\s+logger\.info\(f"Added image #{idx\+1} to message"\))'
    
    if re.search(content_array_pattern, updated_app_content):
        pdf_handling = """
                
                # Add PDF to content array if provided
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
                            logger.info(f"Added PDF #{idx+1} to message: {pdf_name}")"""
        
        updated_app_content = re.sub(
            content_array_pattern,
            r'\1' + pdf_handling,
            updated_app_content
        )
        
        print("✅ Added PDF handling to content array creation")
    else:
        print("❌ Could not locate content array creation section")
    
    write_file('app.py', updated_app_content)
    return True

def add_pdf_plugin_support():
    """Add PDF plugin support for advanced processing."""
    app_content = read_file('app.py')
    
    # Find the payload creation before the OpenRouter API call
    payload_pattern = r'(\s+# Prepare the payload for OpenRouter API\n\s+payload = \{\n\s+"model": openrouter_model,\n\s+"messages": messages,\n\s+"stream": True,)'
    
    if re.search(payload_pattern, app_content):
        plugin_support = """
            
            # Add PDF processing plugin if needed
            plugins = []
            has_pdf_content = pdf_url or (pdf_urls and len(pdf_urls) > 0)
            
            if has_pdf_content:
                # Add the file-parser plugin with default engine (PDFText)
                plugins.append({
                    "id": "file-parser",
                    "pdf": {
                        "engine": "pdf-text"  # Free engine for text-based PDFs
                    }
                })
                logger.info("Added PDF processing plugin with pdf-text engine")
                
            # Add plugins to payload if any are defined
            if plugins:
                payload["plugins"] = plugins"""
        
        updated_app_content = re.sub(
            payload_pattern,
            r'\1' + plugin_support,
            app_content
        )
        
        print("✅ Added PDF plugin support")
        write_file('app.py', updated_app_content)
        return True
    else:
        print("❌ Could not locate payload creation section")
        return False

def main():
    """Run all PDF implementation steps."""
    print("Starting PDF handling implementation...")
    
    # Add DOCUMENT_MODELS set
    add_document_models()
    
    # Update chat function to handle PDFs
    update_chat_function()
    
    # Add PDF plugin support
    add_pdf_plugin_support()
    
    # Add PDF upload route
    add_pdf_upload_route()
    
    print("✅ PDF handling implementation complete!")

if __name__ == "__main__":
    main()