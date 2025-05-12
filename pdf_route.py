"""
PDF upload endpoint for OpenRouter direct PDF processing.
This file implements a route for uploading PDFs to Azure Blob Storage
and preparing them for OpenRouter's PDF processing.
"""

import os
import io
import uuid
import base64
import logging
from pathlib import Path
from flask import request, jsonify, url_for
from azure.storage.blob import ContentSettings
from app import app, USE_AZURE_STORAGE, blob_service_client

logger = logging.getLogger(__name__)

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    """
    Handle PDF uploads for OpenRouter direct PDF processing.
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