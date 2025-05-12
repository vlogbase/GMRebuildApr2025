"""
Script to implement a unified file upload handler that supports both images and PDFs.
This script will:
1. Add a unified upload_file route that handles both images and PDFs
2. Update the frontend code to use this unified handler
3. Modify the chat function to handle both types seamlessly
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

def add_unified_upload_route():
    """Add a unified upload_file route to app.py."""
    # Read current content of app.py
    content = read_file('app.py')
    
    # Check if the route already exists
    if 'def upload_file()' in content:
        logger.info("Unified upload_file route already exists, skipping")
        return content
    
    # Find the position to insert the new route (after upload_image route)
    upload_image_end = content.find('@app.route(\'/upload_pdf\'')
    
    if upload_image_end == -1:
        # Try another anchor
        upload_image_end = content.find('@app.route(\'/clear-conversations\'')
    
    if upload_image_end == -1:
        logger.error("Could not find position to insert unified upload route")
        return content
    
    # Create the unified upload route
    unified_upload_route = """
@app.route('/upload_file', methods=['POST'])
@login_required
def upload_file():
    \"\"\"
    Unified file upload route that handles both images and PDFs based on file type.
    This allows a single upload button in the UI to handle different file types.
    
    For images:
        - Processes and stores in Azure 'gloriamundoblobs' container
        - Returns image_url suitable for multimodal models
        
    For PDFs:
        - Stores PDFs in 'gloriamundopdfs' Azure Blob Storage container
        - Returns pdf_data_url as base64 data URL for OpenRouter document handling
        
    Query Parameters:
        conversation_id (str, optional): The ID of the current conversation for metadata tracking
        model (str, optional): The ID of the model being used (affects URL generation)
        
    Returns:
        JSON with appropriate URLs based on file type
    \"\"\"
    try:
        # Get query parameters
        conversation_id = request.args.get('conversation_id')
        model_id = request.args.get('model')
        
        # Verify a file was uploaded
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        # Verify the file has a name
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Check file type
        filename = file.filename.lower()
        
        # For PDFs
        if filename.endswith('.pdf'):
            # Check if the selected model supports PDFs
            if model_id:
                model_supports_pdf = False
                try:
                    models = _fetch_openrouter_models()
                    model_info = models.get(model_id, {})
                    model_supports_pdf = model_info.get('pdf', False) or model_info.get('supports_pdf', False)
                except Exception as e:
                    logger.error(f"Error checking PDF support for model {model_id}: {e}")
                
                if not model_supports_pdf:
                    return jsonify({
                        "error": f"The selected model '{model_id}' does not support PDFs. Please select a compatible model or upload an image instead."
                    }), 400
            
            # Process as PDF
            # Generate a unique filename
            pdf_filename = f"{generate_share_id()}.pdf"
            
            # Initialize Azure Blob Storage client for PDFs
            blob_service_client = BlobServiceClient.from_connection_string(os.environ.get("AZURE_STORAGE_CONNECTION_STRING"))
            pdf_container_name = os.environ.get("AZURE_STORAGE_PDF_CONTAINER_NAME", "gloriamundopdfs")
            
            # Check if the container exists, create it if it doesn't
            try:
                container_client = blob_service_client.get_container_client(pdf_container_name)
                container_client.get_container_properties()  # Will raise if container doesn't exist
                logger.info(f"Container {pdf_container_name} exists")
            except Exception:
                container_client = blob_service_client.create_container_client(pdf_container_name)
                container_client.create_container(public_access=PublicAccess.BLOB)
                logger.info(f"Container {pdf_container_name} created")
            
            # Upload to Azure Blob Storage
            blob_client = container_client.get_blob_client(pdf_filename)
            blob_client.upload_blob(file.read(), overwrite=True)
            
            # Get the PDF URL
            pdf_url = f"https://{os.environ.get('AZURE_STORAGE_ACCOUNT_NAME')}.blob.core.windows.net/{pdf_container_name}/{pdf_filename}"
            
            # Return a response
            response = {
                "success": True,
                "message": "PDF uploaded successfully",
                "file_type": "pdf",
                "pdf_url": pdf_url,
                "pdf_filename": os.path.basename(file.filename),
                "conversation_id": conversation_id
            }
            
            # Get the file as base64 data URL if requested
            file.seek(0)  # Reset file pointer to start
            file_content = file.read()
            
            # Create base64 data URL for OpenRouter's document handling
            import base64
            pdf_data_url = f"data:application/pdf;base64,{base64.b64encode(file_content).decode('utf-8')}"
            response["pdf_data_url"] = pdf_data_url
            
            # If this is part of a conversation, update the conversation record
            if conversation_id and current_user.is_authenticated:
                try:
                    with app.app_context():
                        conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first()
                        if conversation:
                            # Update conversation metadata to indicate it contains PDF content
                            if not conversation.metadata:
                                conversation.metadata = {}
                            
                            if 'files' not in conversation.metadata:
                                conversation.metadata['files'] = []
                            
                            # Add file info to metadata
                            conversation.metadata['files'].append({
                                'type': 'pdf',
                                'filename': os.path.basename(file.filename),
                                'url': pdf_url,
                                'timestamp': datetime.utcnow().isoformat()
                            })
                            
                            db.session.commit()
                            logger.info(f"Updated conversation {conversation_id} with PDF file metadata")
                except Exception as e:
                    logger.error(f"Error updating conversation metadata: {e}")
            
            return jsonify(response)
            
        # For images
        elif any(filename.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
            # Process as image
            # Generate a unique filename
            image_extension = os.path.splitext(file.filename)[1].lower()
            image_filename = f"{generate_share_id()}{image_extension}"
            
            # Check if the Blob Storage client is initialized
            if 'blob_service_client' not in locals():
                blob_service_client = BlobServiceClient.from_connection_string(os.environ.get("AZURE_STORAGE_CONNECTION_STRING"))
            
            image_container_name = "gloriamundoblobs"
            
            # Check if the container exists, create it if it doesn't
            try:
                container_client = blob_service_client.get_container_client(image_container_name)
                container_client.get_container_properties()  # Will raise if container doesn't exist
                logger.info(f"Container {image_container_name} exists")
            except Exception:
                container_client = blob_service_client.create_container_client(image_container_name)
                container_client.create_container(public_access=PublicAccess.BLOB)
                logger.info(f"Container {image_container_name} created")
            
            # Process the image with PIL to ensure it's valid and optimize if needed
            from PIL import Image
            import io
            
            # Open and verify the image
            try:
                img = Image.open(file.stream)
                
                # If the image is very large, resize it to a reasonable size
                # Max dimensions as used by most AI models
                MAX_WIDTH = 2048
                MAX_HEIGHT = 2048
                
                if img.width > MAX_WIDTH or img.height > MAX_HEIGHT:
                    # Calculate the new dimensions while maintaining aspect ratio
                    ratio = min(MAX_WIDTH / img.width, MAX_HEIGHT / img.height)
                    new_width = int(img.width * ratio)
                    new_height = int(img.height * ratio)
                    
                    # Resize with high quality
                    img = img.resize((new_width, new_height), Image.LANCZOS)
                    logger.info(f"Resized image from {img.width}x{img.height} to {new_width}x{new_height}")
                
                # Convert to the most appropriate format based on original format
                output_format = img.format if img.format in ['JPEG', 'PNG', 'GIF', 'WEBP'] else 'JPEG'
                
                # Save to BytesIO object with optimized settings
                img_byte_arr = io.BytesIO()
                
                # Determine quality based on format
                quality_setting = 85  # Default quality setting
                
                if output_format == 'JPEG':
                    img.save(img_byte_arr, format=output_format, quality=quality_setting, optimize=True)
                elif output_format == 'PNG':
                    img.save(img_byte_arr, format=output_format, optimize=True)
                elif output_format == 'WEBP':
                    img.save(img_byte_arr, format=output_format, quality=quality_setting)
                else:  # GIF or other formats
                    img.save(img_byte_arr, format=output_format)
                
                img_byte_arr.seek(0)  # Reset to start of BytesIO object
                
                # Upload to Azure Blob Storage
                blob_client = container_client.get_blob_client(image_filename)
                blob_client.upload_blob(img_byte_arr.getvalue(), overwrite=True, content_settings=ContentSettings(
                    content_type=f"image/{output_format.lower()}"
                ))
                
                # Get the image URL
                image_url = get_object_storage_url(image_filename, model_name=model_id)
                
                # Return a response
                response = {
                    "success": True,
                    "message": "Image uploaded successfully",
                    "file_type": "image",
                    "image_url": image_url,
                    "image_filename": os.path.basename(file.filename),
                    "conversation_id": conversation_id
                }
                
                # If this is part of a conversation, update the conversation record
                if conversation_id and current_user.is_authenticated:
                    try:
                        with app.app_context():
                            conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first()
                            if conversation:
                                # Update conversation metadata to indicate it contains image content
                                if not conversation.metadata:
                                    conversation.metadata = {}
                                
                                if 'files' not in conversation.metadata:
                                    conversation.metadata['files'] = []
                                
                                # Add file info to metadata
                                conversation.metadata['files'].append({
                                    'type': 'image',
                                    'filename': os.path.basename(file.filename),
                                    'url': image_url,
                                    'timestamp': datetime.utcnow().isoformat()
                                })
                                
                                db.session.commit()
                                logger.info(f"Updated conversation {conversation_id} with image file metadata")
                    except Exception as e:
                        logger.error(f"Error updating conversation metadata: {e}")
                
                return jsonify(response)
                
            except Exception as img_error:
                logger.error(f"Error processing image: {img_error}")
                return jsonify({"error": f"Invalid image file: {str(img_error)}"}), 400
        
        # For unsupported file types
        else:
            supported_extensions = ".jpg, .jpeg, .png, .gif, .webp, .pdf"
            return jsonify({
                "error": f"File type {os.path.splitext(filename)[1]} is not supported. Please upload a file in {supported_extensions} format."
            }), 400
            
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/upload', methods=['POST'])
@login_required
def redirect_to_upload_file():
    \"\"\"
    Route handler that redirects to the main upload_file function
    to maintain compatibility with any existing code using the /upload endpoint.
    \"\"\"
    return redirect(url_for('upload_file', **request.args))
"""
    
    # Insert the unified upload route
    updated_content = content[:upload_image_end] + unified_upload_route + content[upload_image_end:]
    logger.info("Added unified upload_file route")
    
    return updated_content

def update_frontend_javascript():
    """Update script.js to use the unified upload handler."""
    js_file = 'static/js/script.js'
    
    if not os.path.exists(js_file):
        logger.error(f"JavaScript file not found: {js_file}")
        return False
    
    # Read the content of script.js
    content = read_file(js_file)
    
    # Update the file upload function to use the unified endpoint
    upload_handler_pattern = r'(function uploadFile\(file, conversationId\) \{.*?)(const formData = new FormData\(\);.*?)(let url = \'\/upload_image\';)'
    if re.search(upload_handler_pattern, content, re.DOTALL):
        updated_content = re.sub(
            upload_handler_pattern,
            r'\1\2    let url = \'/upload_file\';',
            content,
            flags=re.DOTALL
        )
        
        # Write the updated content back to script.js
        write_file(js_file, updated_content)
        logger.info("Updated JavaScript to use unified upload endpoint")
        return True
    else:
        logger.warning("Could not find upload handler function in script.js")
        return False

def update_html_template():
    """Update index.html to handle both file types with a single button."""
    html_file = 'templates/index.html'
    
    if not os.path.exists(html_file):
        logger.error(f"HTML template not found: {html_file}")
        return False
    
    # Read the content of index.html
    content = read_file(html_file)
    
    # Update file input accept attribute to include PDFs conditionally
    file_input_pattern = r'(<input type="file" id="file-upload" .*?accept=")([^"]*?)(".*?>)'
    if re.search(file_input_pattern, content):
        updated_content = re.sub(
            file_input_pattern,
            r'\1.jpg,.jpeg,.png,.gif,.webp,.pdf\3',
            content
        )
        
        # Update the file upload button label
        button_label_pattern = r'(<button id="file-upload-button".*?>)([^<]*?)(</button>)'
        if re.search(button_label_pattern, updated_content):
            updated_content = re.sub(
                button_label_pattern,
                r'\1Upload File\3',
                updated_content
            )
            
            # Write the updated content back to index.html
            write_file(html_file, updated_content)
            logger.info("Updated HTML template to handle both file types")
            return True
        else:
            logger.warning("Could not find file upload button in index.html")
            return False
    else:
        logger.warning("Could not find file input element in index.html")
        return False

def update_javascript_model_capability_check():
    """Update JavaScript to check model capabilities for file types."""
    js_file = 'static/js/script.js'
    
    if not os.path.exists(js_file):
        logger.error(f"JavaScript file not found: {js_file}")
        return False
    
    # Read the content of script.js
    content = read_file(js_file)
    
    # Find the checkModelCapabilities function
    capability_function_pattern = r'function checkModelCapabilities\(\) \{(.*?)\}'
    capability_function = re.search(capability_function_pattern, content, re.DOTALL)
    
    if capability_function:
        # Current implementation
        current_function_body = capability_function.group(1)
        
        # Check if it already handles PDFs
        if 'pdf' in current_function_body or 'supports_pdf' in current_function_body:
            logger.info("Model capability check already handles PDFs, skipping")
            return True
        
        # Update to handle PDFs
        updated_function_body = current_function_body.replace(
            '// Enable or disable image upload based on model capabilities',
            """// Enable or disable file upload based on model capabilities
    const selectedModel = document.getElementById('model-selector').value;
    const modelInfo = modelData.find(m => m.id === selectedModel);
    
    // Check if model supports images
    const supportsImages = modelInfo && modelInfo.multimodal === true;
    
    // Check if model supports PDFs 
    const supportsPdfs = modelInfo && (modelInfo.pdf === true || modelInfo.supports_pdf === true);
    
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    
    // Update button state and file input accept attribute
    if (fileUploadButton && fileUpload) {
        if (supportsImages && supportsPdfs) {
            // Model supports both images and PDFs
            fileUploadButton.disabled = false;
            fileUploadButton.title = 'Upload images or PDFs';
            fileUpload.accept = '.jpg,.jpeg,.png,.gif,.webp,.pdf';
        } else if (supportsImages) {
            // Model supports only images
            fileUploadButton.disabled = false;
            fileUploadButton.title = 'This model supports images but not PDFs';
            fileUpload.accept = '.jpg,.jpeg,.png,.gif,.webp';
        } else if (supportsPdfs) {
            // Model supports only PDFs
            fileUploadButton.disabled = false;
            fileUploadButton.title = 'This model supports PDFs but not images';
            fileUpload.accept = '.pdf';
        } else {
            // Model doesn't support any files
            fileUploadButton.disabled = true;
            fileUploadButton.title = 'This model does not support file uploads';
        }
    }
    
    console.debug(`Model ${selectedModel} capabilities: images=${supportsImages}, pdfs=${supportsPdfs}`);"""
        )
        
        # Replace the function body
        updated_content = content.replace(current_function_body, updated_function_body)
        
        # Write the updated content back to script.js
        write_file(js_file, updated_content)
        logger.info("Updated JavaScript model capability check to handle PDFs")
        return True
    else:
        logger.warning("Could not find checkModelCapabilities function in script.js")
        return False

def update_javascript_file_handler():
    """Update JavaScript to handle both file types properly."""
    js_file = 'static/js/script.js'
    
    if not os.path.exists(js_file):
        logger.error(f"JavaScript file not found: {js_file}")
        return False
    
    # Read the content of script.js
    content = read_file(js_file)
    
    # Find the uploadFile function
    upload_function_pattern = r'function uploadFile\(file, conversationId\) \{(.*?return.*?)\}'
    upload_function = re.search(upload_function_pattern, content, re.DOTALL)
    
    if upload_function:
        # Current implementation
        current_function_body = upload_function.group(1)
        
        # Update to handle response based on file type
        updated_function_body = current_function_body.replace(
            'return response.json();',
            """const jsonResponse = await response.json();
            
            // Add file type information for the UI
            if (jsonResponse.file_type === 'pdf') {
                jsonResponse.isPdf = true;
            } else if (jsonResponse.file_type === 'image') {
                jsonResponse.isImage = true;
            }
            
            return jsonResponse;"""
        )
        
        # Replace the function body
        updated_content = content.replace(current_function_body, updated_function_body)
        
        # Find the handleUploadedFile function to update for PDF handling
        file_handler_pattern = r'function handleUploadedFile\(fileData\) \{(.*?)\}'
        file_handler = re.search(file_handler_pattern, updated_content, re.DOTALL)
        
        if file_handler:
            # Current implementation
            current_handler_body = file_handler.group(1)
            
            # Update to handle different file types
            updated_handler_body = """
    const currentMessage = document.getElementById('user-input').value;
    
    // Check what type of file was uploaded
    if (fileData.isPdf || fileData.pdf_url) {
        console.debug('PDF file uploaded:', fileData);
        
        // Handle PDF file
        const pdfUrl = fileData.pdf_url;
        const pdfDataUrl = fileData.pdf_data_url;
        const pdfFilename = fileData.pdf_filename || 'document.pdf';
        
        // Add PDF info to the message input as hidden fields
        const pdfInfoContainer = document.createElement('div');
        pdfInfoContainer.id = 'pdf-info-container';
        pdfInfoContainer.style.display = 'flex';
        pdfInfoContainer.style.alignItems = 'center';
        pdfInfoContainer.style.marginBottom = '10px';
        pdfInfoContainer.style.backgroundColor = '#f0f7ff';
        pdfInfoContainer.style.padding = '8px';
        pdfInfoContainer.style.borderRadius = '4px';
        
        // Add PDF icon
        const pdfIcon = document.createElement('span');
        pdfIcon.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><path d="M9 15h6"></path><path d="M9 11h6"></path></svg>';
        pdfIcon.style.marginRight = '8px';
        pdfInfoContainer.appendChild(pdfIcon);
        
        // Add filename
        const fileInfo = document.createElement('span');
        fileInfo.textContent = pdfFilename;
        fileInfo.style.marginRight = 'auto';
        pdfInfoContainer.appendChild(fileInfo);
        
        // Add remove button
        const removeButton = document.createElement('button');
        removeButton.innerHTML = '&times;';
        removeButton.title = 'Remove PDF';
        removeButton.className = 'remove-file-button';
        removeButton.onclick = function() {
            pdfInfoContainer.remove();
            // Clear the PDF data from the form
            document.getElementById('pdf-url').value = '';
            document.getElementById('pdf-data-url').value = '';
            document.getElementById('pdf-filename').value = '';
        };
        pdfInfoContainer.appendChild(removeButton);
        
        // Insert the PDF info container before the message input
        const messageForm = document.getElementById('message-form');
        const userInput = document.getElementById('user-input');
        messageForm.insertBefore(pdfInfoContainer, userInput);
        
        // Add hidden fields for the PDF data if they don't exist
        if (!document.getElementById('pdf-url')) {
            const pdfUrlInput = document.createElement('input');
            pdfUrlInput.type = 'hidden';
            pdfUrlInput.id = 'pdf-url';
            pdfUrlInput.name = 'pdf_url';
            messageForm.appendChild(pdfUrlInput);
        }
        
        if (!document.getElementById('pdf-data-url')) {
            const pdfDataUrlInput = document.createElement('input');
            pdfDataUrlInput.type = 'hidden';
            pdfDataUrlInput.id = 'pdf-data-url';
            pdfDataUrlInput.name = 'pdf_data_url';
            messageForm.appendChild(pdfDataUrlInput);
        }
        
        if (!document.getElementById('pdf-filename')) {
            const pdfFilenameInput = document.createElement('input');
            pdfFilenameInput.type = 'hidden';
            pdfFilenameInput.id = 'pdf-filename';
            pdfFilenameInput.name = 'pdf_filename';
            messageForm.appendChild(pdfFilenameInput);
        }
        
        // Set the PDF data
        document.getElementById('pdf-url').value = pdfUrl || '';
        document.getElementById('pdf-data-url').value = pdfDataUrl || '';
        document.getElementById('pdf-filename').value = pdfFilename || '';
        
        // Add some context to the message if it's empty
        if (!currentMessage.trim()) {
            document.getElementById('user-input').value = `Here's a PDF document. Please analyze it for me.`;
        }
        
    } else if (fileData.isImage || fileData.image_url) {
        console.debug('Image file uploaded:', fileData);
        
        // Handle image file - existing logic
        const imageUrl = fileData.image_url;
        
        // Create an image preview element
        const imagePreviewContainer = document.createElement('div');
        imagePreviewContainer.id = 'image-preview-container';
        imagePreviewContainer.style.display = 'flex';
        imagePreviewContainer.style.alignItems = 'center';
        imagePreviewContainer.style.marginBottom = '10px';
        imagePreviewContainer.style.backgroundColor = '#f0f7ff';
        imagePreviewContainer.style.padding = '8px';
        imagePreviewContainer.style.borderRadius = '4px';
        
        // Add image thumbnail
        const imageThumbnail = document.createElement('img');
        imageThumbnail.src = imageUrl;
        imageThumbnail.style.width = '36px';
        imageThumbnail.style.height = '36px';
        imageThumbnail.style.objectFit = 'cover';
        imageThumbnail.style.borderRadius = '4px';
        imageThumbnail.style.marginRight = '8px';
        imagePreviewContainer.appendChild(imageThumbnail);
        
        // Add filename or placeholder
        const fileInfo = document.createElement('span');
        fileInfo.textContent = fileData.image_filename || 'Uploaded image';
        fileInfo.style.marginRight = 'auto';
        imagePreviewContainer.appendChild(fileInfo);
        
        // Add remove button
        const removeButton = document.createElement('button');
        removeButton.innerHTML = '&times;';
        removeButton.title = 'Remove image';
        removeButton.className = 'remove-file-button';
        removeButton.onclick = function() {
            imagePreviewContainer.remove();
            // Clear the image data from the form
            document.getElementById('image-url').value = '';
        };
        imagePreviewContainer.appendChild(removeButton);
        
        // Insert the image preview container before the message input
        const messageForm = document.getElementById('message-form');
        const userInput = document.getElementById('user-input');
        messageForm.insertBefore(imagePreviewContainer, userInput);
        
        // Add hidden field for the image URL if it doesn't exist
        if (!document.getElementById('image-url')) {
            const imageUrlInput = document.createElement('input');
            imageUrlInput.type = 'hidden';
            imageUrlInput.id = 'image-url';
            imageUrlInput.name = 'image_url';
            messageForm.appendChild(imageUrlInput);
        }
        
        // Set the image URL
        document.getElementById('image-url').value = imageUrl;
        
        // Add some context to the message if it's empty
        if (!currentMessage.trim()) {
            document.getElementById('user-input').value = `What's in this image?`;
        }
    }
    
    // Enable the send button if it was disabled
    const sendButton = document.getElementById('send-button');
    if (sendButton && sendButton.disabled) {
        sendButton.disabled = false;
    }
"""
            
            # Replace the function body
            updated_content = updated_content.replace(current_handler_body, updated_handler_body)
            
            # Write the updated content back to script.js
            write_file(js_file, updated_content)
            logger.info("Updated JavaScript file handler to handle both file types")
            return True
        else:
            logger.warning("Could not find handleUploadedFile function in script.js")
            return False
    else:
        logger.warning("Could not find uploadFile function in script.js")
        return False

def update_javascript_form_submit():
    """Update the form submission handler to include PDF data."""
    js_file = 'static/js/script.js'
    
    if not os.path.exists(js_file):
        logger.error(f"JavaScript file not found: {js_file}")
        return False
    
    # Read the content of script.js
    content = read_file(js_file)
    
    # Find the form submit handler
    form_handler_pattern = r'document\.getElementById\(\'message-form\'\)\.addEventListener\(\'submit\', async function\(event\) \{(.*?)\}\);'
    form_handler = re.search(form_handler_pattern, content, re.DOTALL)
    
    if form_handler:
        # Current implementation
        current_handler_body = form_handler.group(1)
        
        # Check if it's already updated for PDFs
        if 'pdf_url' in current_handler_body or 'pdf-url' in current_handler_body:
            logger.info("Form submit handler already includes PDF data, skipping")
            return True
        
        # Find the message data construction
        message_data_pattern = r'(const messageData = \{[^}]*?\};)'
        message_data_match = re.search(message_data_pattern, current_handler_body)
        
        if message_data_match:
            current_message_data = message_data_match.group(1)
            
            # Updated message data including PDF info
            updated_message_data = current_message_data.replace(
                '};',
                """
        
        // Check if we have PDF data
        const pdfUrl = document.getElementById('pdf-url')?.value;
        const pdfDataUrl = document.getElementById('pdf-data-url')?.value;
        const pdfFilename = document.getElementById('pdf-filename')?.value;
        
        if (pdfUrl && pdfDataUrl) {
            messageData.pdf_url = pdfUrl;
            messageData.pdf_data_url = pdfDataUrl;
            messageData.pdf_filename = pdfFilename || 'document.pdf';
            
            // Clean up UI elements
            const pdfInfoContainer = document.getElementById('pdf-info-container');
            if (pdfInfoContainer) {
                pdfInfoContainer.remove();
            }
            
            // Clear hidden inputs
            if (document.getElementById('pdf-url')) document.getElementById('pdf-url').value = '';
            if (document.getElementById('pdf-data-url')) document.getElementById('pdf-data-url').value = '';
            if (document.getElementById('pdf-filename')) document.getElementById('pdf-filename').value = '';
        }
    };"""
            )
            
            # Replace the message data construction
            updated_handler_body = current_handler_body.replace(current_message_data, updated_message_data)
            
            # Replace the form handler body
            updated_content = content.replace(current_handler_body, updated_handler_body)
            
            # Write the updated content back to script.js
            write_file(js_file, updated_content)
            logger.info("Updated form submit handler to include PDF data")
            return True
        else:
            logger.warning("Could not find message data construction in form handler")
            return False
    else:
        logger.warning("Could not find form submit handler in script.js")
        return False

def update_chat_function():
    """Update the chat function to handle PDF files."""
    # Read current content of app.py
    content = read_file('app.py')
    
    # Find the data extraction in the chat function
    data_extraction_pattern = r'(# Extract data\s*user_message = data\.get\("message", ""\)\s*image_url = data\.get\("image_url", None\)\s*image_urls = data\.get\("image_urls", \[\]\))'
    
    if re.search(data_extraction_pattern, content):
        # Add PDF data extraction
        pdf_extraction = """
        # Extract PDF data
        pdf_url = data.get("pdf_url", None)
        pdf_data_url = data.get("pdf_data_url", None)
        pdf_urls = data.get("pdf_urls", [])
        pdf_filename = data.get("pdf_filename", "document.pdf")"""
        
        updated_content = re.sub(
            data_extraction_pattern,
            r'\1' + pdf_extraction,
            content
        )
        logger.info("Added PDF data extraction to chat function")
        
        # Find the message content creation part
        if 'multimodal_message_content' in updated_content:
            # Update the multimodal content creation to include PDFs
            multimodal_content_pattern = r'(# Create message content array for multimodal models.*?multimodal_message_content = \[\]).*?(# Add text content)'
            
            multimodal_handler = """
            
            # Add text content first
            if user_message.strip():
                multimodal_message_content.append({
                    "type": "text",
                    "text": user_message
                })
            
            # Add image content if available
            if image_url:
                multimodal_message_content.append({
                    "type": "image_url",
                    "image_url": {"url": image_url}
                })
            
            # Add multiple images if available
            if image_urls and len(image_urls) > 0:
                for img_url in image_urls:
                    multimodal_message_content.append({
                        "type": "image_url",
                        "image_url": {"url": img_url}
                    })
            
            # Add PDF content if available and the model supports it
            if (pdf_url or pdf_data_url) and openrouter_model in DOCUMENT_MODELS:
                # Use the data URL if available, otherwise use the regular URL
                pdf_content = pdf_data_url or pdf_url
                
                if pdf_content:
                    multimodal_message_content.append({
                        "type": "file",
                        "file": {
                            "filename": pdf_filename,
                            "file_data": pdf_content
                        }
                    })
                    logger.info(f"Added PDF to message content: {pdf_filename}")
            
            # If we don't have any content, use an empty text message
            if not multimodal_message_content:
                multimodal_message_content.append({
                    "type": "text",
                    "text": user_message or ""
                })
            """
            
            updated_content = re.sub(
                multimodal_content_pattern,
                r'\1' + multimodal_handler + r'\2',
                updated_content,
                flags=re.DOTALL
            )
            logger.info("Updated multimodal content creation to include PDFs")
            
            # Add handling for plugins (needed for PDF native parsing in OpenRouter)
            payload_creation_pattern = r'(# Create the request payload.*?payload = \{[^}]*?\})'
            
            if 'plugins' not in updated_content:
                # Add plugin support
                plugin_support = """
                
                # Add PDF processing plugin if needed
                plugins = []
                has_pdf_content = pdf_url or pdf_data_url or (pdf_urls and len(pdf_urls) > 0)
                
                if has_pdf_content and openrouter_model in DOCUMENT_MODELS:
                    # Add the file-parser plugin with default engine (PDFText)
                    plugins.append({
                        "id": "file-parser",
                        "pdf": {
                            "engine": "native"  # Use the native PDF engine for best results
                        }
                    })
                    logger.info("Added PDF processing plugin with native engine")
                
                # Add plugins to payload if any are defined
                if plugins:
                    payload["plugins"] = plugins"""
                
                updated_content = re.sub(
                    payload_creation_pattern,
                    r'\1' + plugin_support,
                    updated_content
                )
                logger.info("Added PDF plugin support to payload creation")
        
        # Write the updated content back to app.py
        write_file('app.py', updated_content)
        logger.info("Updated chat function to handle PDFs")
        return True
    else:
        logger.warning("Could not find data extraction section in chat function")
        return False

def main():
    """Execute the implementation."""
    logger.info("Starting unified file upload implementation...")
    
    # Backup relevant files before modifying them
    files_to_backup = ['app.py', 'static/js/script.js', 'templates/index.html']
    for file in files_to_backup:
        if os.path.exists(file):
            backup_file(file)
    
    # Add the unified upload route
    app_content = add_unified_upload_route()
    write_file('app.py', app_content)
    
    # Update the chat function to handle PDFs
    update_chat_function()
    
    # Update the frontend JavaScript
    update_frontend_javascript()
    update_javascript_model_capability_check()
    update_javascript_file_handler()
    update_javascript_form_submit()
    
    # Update the HTML template
    update_html_template()
    
    logger.info("Unified file upload implementation completed!")

if __name__ == "__main__":
    main()