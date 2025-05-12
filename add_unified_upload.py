"""
Script to add a unified file upload handler to app.py
This will create a single endpoint that handles both image and PDF uploads
"""
import os
import re
import logging

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
    """Add a unified upload route to app.py"""
    # Backup the file first
    if backup_file('app.py'):
        content = read_file('app.py')
        
        # Check if the route already exists
        if 'def upload_file()' in content:
            logger.info("Unified upload_file route already exists, skipping")
            return True
            
        # Find the position to insert the new route
        upload_pdf_pos = content.find('@app.route(\'/upload_pdf\'')
        if upload_pdf_pos == -1:
            # Try another anchor
            upload_pdf_pos = content.find('@app.route(\'/clear-conversations\'')
            
        if upload_pdf_pos == -1:
            logger.error("Could not find position to insert unified upload route")
            return False
            
        # Create the unified upload route
        unified_route = '''
@app.route('/upload_file', methods=['POST'])
@login_required
def upload_file():
    """
    Unified file upload route that handles both images and PDFs based on file type.
    
    For images:
        - Processes and stores in Azure 'gloriamundoblobs' container
        - Returns image_url suitable for multimodal models
        
    For PDFs:
        - Stores PDFs in 'gloriamundopdfs' Azure Blob Storage container
        - Returns pdf_data_url as base64 data URL for OpenRouter document handling
    """
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
            
            # Process as PDF - similar to upload_pdf route
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
                container_client.create_container(public_access="blob")
                logger.info(f"Container {pdf_container_name} created")
            
            # Upload to Azure Blob Storage
            blob_client = container_client.get_blob_client(pdf_filename)
            blob_client.upload_blob(file.read(), overwrite=True)
            
            # Get the PDF URL
            pdf_url = f"https://{os.environ.get('AZURE_STORAGE_ACCOUNT_NAME')}.blob.core.windows.net/{pdf_container_name}/{pdf_filename}"
            
            # Create a response
            response = {
                "success": True,
                "message": "PDF uploaded successfully",
                "file_type": "pdf",
                "pdf_url": pdf_url,
                "pdf_filename": os.path.basename(file.filename),
                "conversation_id": conversation_id
            }
            
            # Get the file as base64 data URL
            file.seek(0)  # Reset file pointer to start
            file_content = file.read()
            
            # Create base64 data URL for OpenRouter's document handling
            import base64
            pdf_data_url = f"data:application/pdf;base64,{base64.b64encode(file_content).decode('utf-8')}"
            response["pdf_data_url"] = pdf_data_url
            
            # If this is part of a conversation, update the conversation record
            if conversation_id and current_user.is_authenticated:
                try:
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
            # Process as image - similar to upload_image route
            # Generate a unique filename
            image_extension = os.path.splitext(file.filename)[1].lower()
            image_filename = f"{generate_share_id()}{image_extension}"
            
            # Check if the Blob Storage client is initialized 
            blob_service_client = BlobServiceClient.from_connection_string(os.environ.get("AZURE_STORAGE_CONNECTION_STRING"))
            image_container_name = "gloriamundoblobs"
            
            # Check if the container exists, create it if it doesn't
            try:
                container_client = blob_service_client.get_container_client(image_container_name)
                container_client.get_container_properties()  # Will raise if container doesn't exist
                logger.info(f"Container {image_container_name} exists")
            except Exception:
                container_client = blob_service_client.create_container_client(image_container_name)
                container_client.create_container(public_access="blob")
                logger.info(f"Container {image_container_name} created")
            
            # Process the image with PIL
            from PIL import Image
            import io
            
            # Open and verify the image
            try:
                img = Image.open(file.stream)
                
                # If the image is very large, resize it
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
                
                # Convert to appropriate format
                output_format = img.format if img.format in ['JPEG', 'PNG', 'GIF', 'WEBP'] else 'JPEG'
                
                # Save to BytesIO object
                img_byte_arr = io.BytesIO()
                
                # Set quality
                quality_setting = 85
                
                if output_format == 'JPEG':
                    img.save(img_byte_arr, format=output_format, quality=quality_setting, optimize=True)
                elif output_format == 'PNG':
                    img.save(img_byte_arr, format=output_format, optimize=True)
                elif output_format == 'WEBP':
                    img.save(img_byte_arr, format=output_format, quality=quality_setting)
                else:  # GIF or other formats
                    img.save(img_byte_arr, format=output_format)
                
                img_byte_arr.seek(0)  # Reset to start
                
                # Upload to Azure Blob Storage
                blob_client = container_client.get_blob_client(image_filename)
                blob_client.upload_blob(img_byte_arr.getvalue(), overwrite=True, content_settings=ContentSettings(
                    content_type=f"image/{output_format.lower()}"
                ))
                
                # Get the image URL
                image_url = get_object_storage_url(image_filename, model_name=model_id)
                
                # Create a response
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
                        conversation = Conversation.query.filter_by(id=conversation_id, user_id=current_user.id).first()
                        if conversation:
                            # Update conversation metadata to indicate it contains image
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
    """
    Route handler that redirects to the main upload_file function
    to maintain compatibility with any existing code using the /upload endpoint.
    """
    return redirect(url_for('upload_file', **request.args))
'''
        
        # Insert the unified route
        updated_content = content[:upload_pdf_pos] + unified_route + content[upload_pdf_pos:]
        
        # Write the updated content back to the file
        write_file('app.py', updated_content)
        logger.info("Added unified upload_file route to app.py")
        return True
    else:
        logger.error("Failed to backup app.py, operation aborted")
        return False

def update_frontend_js():
    """Update the JavaScript to use the unified upload endpoint"""
    js_file = 'static/js/script.js'
    
    if not os.path.exists(js_file):
        logger.error(f"JavaScript file not found: {js_file}")
        return False
        
    # Backup the file first
    if backup_file(js_file):
        content = read_file(js_file)
        
        # Update the upload function to use our unified endpoint
        upload_func_pattern = r'(function uploadFile\(file, conversationId\) \{.*?)(let url = \'\/upload_image\';)'
        if re.search(upload_func_pattern, content, re.DOTALL):
            updated_content = re.sub(
                upload_func_pattern,
                r'\1let url = \'/upload_file\';',
                content,
                flags=re.DOTALL
            )
            
            # Check if we need to update file handling code
            if 'isPdf' not in content:
                # Add PDF handling to the response handling
                handle_func_pattern = r'(function handleUploadedFile\(fileData\) \{.*?)(\s+const currentMessage = document\.getElementById\(\'user-input\'\)\.value;)'
                if re.search(handle_func_pattern, updated_content, re.DOTALL):
                    pdf_handler = '''
    // Check what type of file was uploaded
    if (fileData.file_type === 'pdf' || fileData.pdf_url) {
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
    } else if (fileData.file_type === 'image' || fileData.image_url) {
        // Handle image - the existing code will work here since we check image_url
        console.debug('Image file uploaded:', fileData);
'''
                    updated_content = re.sub(
                        handle_func_pattern,
                        r'\1' + pdf_handler + r'\2',
                        updated_content,
                        flags=re.DOTALL
                    )
                
                # Update the form submission handler to include PDF data
                form_handler_pattern = r'(document\.getElementById\(\'message-form\'\)\.addEventListener\(\'submit\', async function\(event\) \{.*?const messageData = \{[^}]*?\};)'
                if re.search(form_handler_pattern, updated_content, re.DOTALL):
                    pdf_data_handler = '''
        
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
        }'''
                    
                    updated_content = re.sub(
                        form_handler_pattern,
                        r'\1' + pdf_data_handler,
                        updated_content,
                        flags=re.DOTALL
                    )
            
            # Write the updated content back to the file
            write_file(js_file, updated_content)
            logger.info("Updated JavaScript to use unified upload endpoint")
            return True
        else:
            logger.warning("Could not find upload function in JavaScript")
            return False
    else:
        logger.error("Failed to backup script.js, operation aborted")
        return False

def update_model_capability_check():
    """Update the model capability check function to check for PDF support"""
    js_file = 'static/js/script.js'
    
    if not os.path.exists(js_file):
        logger.error(f"JavaScript file not found: {js_file}")
        return False
        
    # The file was already backed up in the previous function
    content = read_file(js_file)
    
    # Find the checkModelCapabilities function
    capability_pattern = r'(function checkModelCapabilities\(\) \{.*?})'
    capability_match = re.search(capability_pattern, content, re.DOTALL)
    
    if capability_match:
        old_function = capability_match.group(1)
        
        # Check if it already handles PDFs
        if 'supportsPdfs' in old_function:
            logger.info("Model capability check already handles PDFs, skipping")
            return True
            
        # Create updated function with PDF support check
        new_function = '''function checkModelCapabilities() {
    // Get the selected model information
    const selectedModel = document.getElementById('model-selector').value;
    const modelInfo = modelData.find(m => m.id === selectedModel);
    
    // Check if model supports images
    const supportsImages = modelInfo && modelInfo.multimodal === true;
    
    // Check if model supports PDFs
    const supportsPdfs = modelInfo && (modelInfo.pdf === true || modelInfo.supports_pdf === true);
    
    // Update the file upload button state
    const fileUploadButton = document.getElementById('file-upload-button');
    const fileUpload = document.getElementById('file-upload');
    
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
    
    console.debug(`Model ${selectedModel} capabilities: images=${supportsImages}, pdfs=${supportsPdfs}`);
}'''
        
        # Replace the function
        updated_content = content.replace(old_function, new_function)
        
        # Write the updated content back to the file
        write_file(js_file, updated_content)
        logger.info("Updated model capability check to handle PDFs")
        return True
    else:
        logger.warning("Could not find checkModelCapabilities function")
        return False

def update_html_button():
    """Update the HTML to show a generic 'Upload File' button"""
    html_file = 'templates/index.html'
    
    if not os.path.exists(html_file):
        logger.error(f"HTML file not found: {html_file}")
        return False
        
    # Backup the file first
    if backup_file(html_file):
        content = read_file(html_file)
        
        # Update the file input label
        label_pattern = r'(<label for="file-upload".*?>)(.*?)(</label>)'
        if re.search(label_pattern, content):
            updated_content = re.sub(
                label_pattern,
                r'\1Upload File\3',
                content
            )
            
            # Update the button text
            button_pattern = r'(<button id="file-upload-button".*?>)(.*?)(</button>)'
            if re.search(button_pattern, updated_content):
                updated_content = re.sub(
                    button_pattern,
                    r'\1Upload File\3',
                    updated_content
                )
                
                # Update the input accept attribute
                input_pattern = r'(<input type="file" id="file-upload".*?accept=")[^"]*(".*?>)'
                if re.search(input_pattern, updated_content):
                    updated_content = re.sub(
                        input_pattern,
                        r'\1.jpg,.jpeg,.png,.gif,.webp,.pdf\2',
                        updated_content
                    )
                    
                    # Write the updated content back to the file
                    write_file(html_file, updated_content)
                    logger.info("Updated HTML for unified file upload")
                    return True
                else:
                    logger.warning("Could not find file input in HTML")
                    return False
            else:
                logger.warning("Could not find upload button in HTML")
                return False
        else:
            logger.warning("Could not find file input label in HTML")
            return False
    else:
        logger.error("Failed to backup index.html, operation aborted")
        return False

def update_chat_function():
    """Update the chat function to handle PDFs"""
    # The app.py file was already backed up in the first function
    content = read_file('app.py')
    
    # Find the data extraction part of the chat function
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
        
        # Find the multimodal message content creation
        multimodal_pattern = r'(# Create message content array for multimodal models.*?multimodal_message_content = \[\]\s*)(# Add text content.*?}\))'
        
        if re.search(multimodal_pattern, updated_content, re.DOTALL):
            # Add PDF content handling
            pdf_content_handler = """
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
                multimodal_pattern,
                r'\1' + pdf_content_handler,
                updated_content,
                flags=re.DOTALL
            )
            
            # Add PDF plugin support
            payload_pattern = r'(# Create the request payload.*?payload = \{[^}]*?\})'
            
            if re.search(payload_pattern, updated_content):
                plugin_support = """
                
                # Add PDF processing plugin if needed
                plugins = []
                has_pdf_content = pdf_url or pdf_data_url or (pdf_urls and len(pdf_urls) > 0)
                
                if has_pdf_content and openrouter_model in DOCUMENT_MODELS:
                    # Add the file-parser plugin with native engine
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
                    payload_pattern,
                    r'\1' + plugin_support,
                    updated_content
                )
            
            # Write the updated content back to the file
            write_file('app.py', updated_content)
            logger.info("Updated chat function to handle PDFs")
            return True
        else:
            logger.warning("Could not find multimodal message content creation")
            return False
    else:
        logger.warning("Could not find data extraction in chat function")
        return False

def add_document_models_set():
    """Add DOCUMENT_MODELS set if it doesn't exist"""
    content = read_file('app.py')
    
    # Check if DOCUMENT_MODELS already exists
    if "DOCUMENT_MODELS = " in content:
        logger.info("DOCUMENT_MODELS set already exists, skipping")
        return True
        
    # Find the MULTIMODAL_MODELS definition
    models_pattern = r'(# Set of models that support multimodal inputs \(images\)\nMULTIMODAL_MODELS = \{[^}]*\})'
    
    if re.search(models_pattern, content):
        # Add DOCUMENT_MODELS after MULTIMODAL_MODELS
        document_models = """

# Set of models that support document/PDF inputs
DOCUMENT_MODELS = {
    "anthropic/claude-3-opus-20240229",
    "anthropic/claude-3-sonnet-20240229",
    "anthropic/claude-3-haiku-20240307",
    "google/gemini-1.5-pro-latest",
    "google/gemini-1.5-flash-latest"
}
"""
        updated_content = re.sub(
            models_pattern,
            r'\1' + document_models,
            content
        )
        
        # Write the updated content back to the file
        write_file('app.py', updated_content)
        logger.info("Added DOCUMENT_MODELS set")
        return True
    else:
        logger.warning("Could not find MULTIMODAL_MODELS definition")
        return False

def main():
    """Run all the functions"""
    logger.info("Starting unified upload implementation...")
    
    # Add DOCUMENT_MODELS set if needed
    add_document_models_set()
    
    # Add the unified upload route
    add_unified_upload_route()
    
    # Update the chat function
    update_chat_function()
    
    # Update the frontend
    update_frontend_js()
    update_model_capability_check()
    update_html_button()
    
    logger.info("Unified upload implementation complete!")

if __name__ == '__main__':
    main()