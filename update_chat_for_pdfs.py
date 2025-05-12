"""
Update the chat function to handle PDFs in app.py
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

def update_chat_function():
    """Update the chat function to handle PDFs"""
    content = read_file('app.py')
    
    # Find the data extraction section
    data_extraction_pattern = r'(\s+# Extract data\n\s+user_message = data\.get\("message", ""\)\n\s+image_url = data\.get\("image_url", None\)\n\s+image_urls = data\.get\("image_urls", \[\]\))'
    
    if re.search(data_extraction_pattern, content):
        pdf_data_extraction = """
        # Extract PDF data
        pdf_url = data.get("pdf_url", None)
        pdf_urls = data.get("pdf_urls", [])
        pdf_filename = data.get("pdf_filename", "document.pdf")"""
        
        # Add PDF data extraction
        content = re.sub(
            data_extraction_pattern,
            r'\1' + pdf_data_extraction,
            content
        )
        
        print("✅ Added PDF data extraction to chat function")
    else:
        print("Could not find data extraction section in chat function")
        return False
    
    # Find the multimodal condition
    multimodal_condition_pattern = r'(if \(image_url or \(image_urls and len\(image_urls\) > 0\)\)) and openrouter_model in MULTIMODAL_MODELS:'
    
    if re.search(multimodal_condition_pattern, content):
        # Update multimodal condition to include PDFs
        pdf_condition = r'\1 or (pdf_url or (pdf_urls and len(pdf_urls) > 0)):\n            # Check if model supports multimodal content\n            supports_multimodal = openrouter_model in MULTIMODAL_MODELS\n            \n            # Check if model supports PDF documents\n            supports_documents = openrouter_model in DOCUMENT_MODELS\n            \n            if supports_multimodal or supports_documents'
        
        content = re.sub(
            multimodal_condition_pattern,
            pdf_condition,
            content
        )
        
        print("✅ Updated multimodal condition to include PDFs")
    else:
        print("Could not find multimodal condition in chat function")
        return False
    
    # Find the content creation section
    content_creation_pattern = r'(\s+# Add multiple images if provided.*?\n\s+for idx, img_url in enumerate\(image_urls\):.*?\n\s+logger\.info\(f"Added image #{idx\+1} to message"\))'
    
    if re.search(content_creation_pattern, content, re.DOTALL):
        # Add PDF handling to content array
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
        
        content = re.sub(
            content_creation_pattern,
            r'\1' + pdf_handling,
            content,
            flags=re.DOTALL
        )
        
        print("✅ Added PDF handling to content creation")
    else:
        print("Could not find content creation section in chat function")
        return False
    
    # Find the payload creation section
    payload_creation_pattern = r'(\s+# Prepare the payload for OpenRouter API\n\s+payload = \{\n\s+"model": openrouter_model,\n\s+"messages": messages,\n\s+"stream": True,)'
    
    if re.search(payload_creation_pattern, content):
        # Add PDF plugin support
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
        
        content = re.sub(
            payload_creation_pattern,
            r'\1' + plugin_support,
            content
        )
        
        print("✅ Added PDF plugin support to payload creation")
    else:
        print("Could not find payload creation section in chat function")
        return False
    
    # Write the updated content back to app.py
    write_file('app.py', content)
    print("✅ Chat function updated to handle PDFs")
    return True

if __name__ == "__main__":
    update_chat_function()