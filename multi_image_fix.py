"""
Clean script to apply multi-image support to app.py without relying on complex regex patterns.
This script will locate key sections and apply targeted updates.
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

def update_chat_route_params(content):
    """Update the parameter extraction in the chat route."""
    pattern = r'(\s+# Extract data\n\s+user_message = data\.get\("message", ""\).*?\n\s+)image_url = data\.get\("image_url", None\)'
    replacement = r'\1image_url = data.get("image_url", None)\n        image_urls = data.get("image_urls", [])'
    return re.sub(pattern, replacement, content, flags=re.DOTALL)

def update_multimodal_condition(content):
    """Update the condition for multimodal content."""
    pattern = r'(\s+# Following OpenRouter\'s unified multimodal format.*?\n\s+# https://openrouter\.ai/docs#multimodal\n\s+)if image_url and openrouter_model in MULTIMODAL_MODELS:'
    replacement = r'\1if (image_url or (image_urls and len(image_urls) > 0)) and openrouter_model in MULTIMODAL_MODELS:'
    return re.sub(pattern, replacement, content, flags=re.DOTALL)

def update_multimodal_check(content):
    """Update the check for multimodal model support."""
    pattern = r'(\s+# Log if image was provided but model doesn\'t support it\n\s+)if image_url and openrouter_model not in MULTIMODAL_MODELS:'
    replacement = r'\1if (image_url or (image_urls and len(image_urls) > 0)) and openrouter_model not in MULTIMODAL_MODELS:'
    return re.sub(pattern, replacement, content, flags=re.DOTALL)

def update_multimodal_warning(content):
    """Update the warning for non-multimodal models."""
    pattern = r'(\s+# Log if image was provided but model doesn\'t support it\n\s+if .*?\n\s+)logger\.warning\(f"⚠️ Image URL provided but model {openrouter_model} doesn\'t support multimodal input\. Image ignored\."\)'
    replacement = r'\1logger.warning(f"⚠️ Image URL(s) provided but model {openrouter_model} doesn\'t support multimodal input. Images ignored.")'
    return re.sub(pattern, replacement, content, flags=re.DOTALL)

def replace_multimodal_block(content):
    """Replace the multimodal content creation block with multi-image support."""
    # First, find where the multimodal block starts
    start_pattern = r'# Following OpenRouter\'s unified multimodal format.*?\n\s+# https://openrouter\.ai/docs#multimodal\n\s+if \(image_url or \(image_urls and len\(image_urls\) > 0\)\) and openrouter_model in MULTIMODAL_MODELS:'
    start_match = re.search(start_pattern, content, re.DOTALL)
    
    if not start_match:
        print("❌ Could not find the start of the multimodal block")
        return content
    
    start_pos = start_match.start()
    
    # Now find the end of the multimodal block
    end_pattern = r'else:\n\s+# Standard text-only message\n\s+messages\.append\({\'role\': \'user\', \'content\': user_message}\)'
    end_match = re.search(end_pattern, content[start_pos:], re.DOTALL)
    
    if not end_match:
        print("❌ Could not find the end of the multimodal block")
        return content
    
    end_pos = start_pos + end_match.start()
    
    # Create the new multimodal block
    new_block = '''# Following OpenRouter's unified multimodal format that works across all models:
        # https://openrouter.ai/docs#multimodal
        if (image_url or (image_urls and len(image_urls) > 0)) and openrouter_model in MULTIMODAL_MODELS:
            # Create a multimodal content array with the text message
            multimodal_content = [
                {"type": "text", "text": user_message}
            ]
            
            # Process all images in the image_urls array
            urls_to_process = []
            if image_url:
                urls_to_process.append(image_url)
            if image_urls:
                urls_to_process.extend(image_urls)
                
            for url in urls_to_process:
                # Validate the image URL - ensure it's a publicly accessible URL
                if not url.startswith(('http://', 'https://')):
                    logger.error(f"❌ INVALID IMAGE URL: {url[:100]}...")
                    logger.error("Image URL must start with http:// or https://. Skipping this image.")
                    continue
                
                # Check if this is an Azure Blob Storage URL that needs to be optimized for the model
                is_azure_url = 'blob.core.windows.net' in url
                processed_url = url
                
                # If using Azure Storage and this is a Gemini model, we might need to regenerate
                # a "clean" URL without SAS tokens that Gemini can process better.
                if is_azure_url and "gemini" in openrouter_model.lower():
                    try:
                        # Extract the blob name from the URL
                        blob_name = url.split('?')[0].split('/')[-1]
                        logger.info(f"Extracted blob name: {blob_name}")
                        
                        # Regenerate a clean URL for Gemini
                        processed_url = get_object_storage_url(
                            blob_name, 
                            public=False, 
                            expires_in=3600, 
                            clean_url=True,
                            model_name="gemini"
                        )
                        logger.info(f"Regenerated clean URL for Gemini: {processed_url[:50]}...")
                    except Exception as url_error:
                        logger.error(f"Error regenerating clean URL: {url_error}")
                        # Continue with original URL if regeneration fails
                
                # Log detailed image information
                try:
                    # Parse URL components
                    parsed_url = urlparse(processed_url)
                    
                    # Check for query parameters that might indicate a SAS token
                    has_query_params = bool(parsed_url.query)
                    domain = parsed_url.netloc
                    path = parsed_url.path
                    extension = os.path.splitext(path)[1].lower()
                    
                    logger.info(f"📷 MULTIMODAL IMAGE {len(multimodal_content)} DETAILS:")
                    logger.info(f"  Domain: {domain}")
                    logger.info(f"  Path: {path}")
                    logger.info(f"  File Extension: {extension or 'none'}")
                    logger.info(f"  Has Query Parameters: {has_query_params}")
                    logger.info(f"  Model: {openrouter_model}")
                    
                    # Check for potential issues
                    if not extension:
                        logger.warning("⚠️ Image URL has no file extension - may cause issues with some models")
                    
                    if extension not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                        logger.warning(f"⚠️ Unusual file extension: {extension} - may not be supported by all models")
                    
                    if has_query_params:
                        logger.warning("⚠️ URL contains query parameters (possibly SAS token) - may cause issues with some models")
                    
                    if 'blob.core.windows.net' in domain and has_query_params and "gemini" in openrouter_model.lower():
                        logger.warning("⚠️ Gemini model with Azure Blob Storage URL + SAS token - high probability of failure")
                        logger.warning("⚠️ Consider setting your Azure Blob Storage container to allow public access")
                    
                    # Check if URL has unusual characters
                    if any(c in processed_url for c in ['&', '+', '%', ' ']):
                        logger.warning("⚠️ URL contains special characters - may cause issues with some models")
                except Exception as url_parse_error:
                    logger.error(f"Error analyzing image URL: {url_parse_error}")
                
                # Add this image to the multimodal content
                multimodal_content.append({
                    "type": "image_url", 
                    "image_url": {"url": processed_url}
                })
            
            # Add the multimodal content to messages if we have at least one valid image
            if len(multimodal_content) > 1:  # First item is text, so we need more than 1 item
                messages.append({'role': 'user', 'content': multimodal_content})
                logger.info(f"✅ Added multimodal message with {len(multimodal_content) - 1} images to {openrouter_model}")
                
                # Model-specific guidance for multiple images
                if "gemini" in openrouter_model.lower():
                    logger.info("ℹ️ Using Gemini model - ensure image URLs are simple and publicly accessible")
                    logger.info("ℹ️ Gemini often rejects complex URLs with tokens or special parameters")
                    logger.info("ℹ️ Gemini models can process up to 16 images, but work best with 1-4 images")
                    
                    # Additional check for WebP format with Gemini
                    if any(os.path.splitext(urlparse(url).path)[1].lower() == '.webp' for url in urls_to_process if url.startswith(('http://', 'https://'))):
                        logger.warning("⚠️ WebP format(s) with Gemini model - high probability of failure")
                        logger.warning("⚠️ Consider converting WebP images to JPEG or PNG for Gemini compatibility")
                
                elif "claude" in openrouter_model.lower():
                    logger.info("ℹ️ Using Claude model - handles most image formats but prefers standard URLs")
                    # Claude 3 Opus/Sonnet supports up to 5 images, but check the limits for your specific model
                    if len(multimodal_content) > 6:  # 1 text + 5 images
                        logger.warning("⚠️ Claude model - more than 5 images may not be fully processed")
                
                elif "gpt-4" in openrouter_model.lower():
                    logger.info("ℹ️ Using GPT-4 model - generally most flexible with image URLs")
                    # GPT-4 Vision (gpt-4-vision-preview) can handle up to 20 images
                    if len(multimodal_content) > 21:  # 1 text + 20 images
                        logger.warning("⚠️ GPT-4 Vision - more than 20 images may not be fully processed")
                
                # Log full payload for debugging multimodal messages
                try:
                    logger.debug(f"Multimodal message payload: {json.dumps(multimodal_content, indent=2)}")
                except Exception as e:
                    logger.debug(f"Could not serialize multimodal content for logging: {e}")
            else:
                # No valid images were found, fall back to text-only
                logger.warning("⚠️ No valid image URLs found. Falling back to text-only message.")
                messages.append({'role': 'user', 'content': user_message})'''
    
    # Combine the parts
    updated_content = content[:start_pos] + new_block + content[end_pos:]
    return updated_content

def apply_updates():
    """Apply all updates to app.py."""
    try:
        content = read_file('app.py')
        
        # Step 1: Add image_urls parameter
        content = update_chat_route_params(content)
        print("✅ Added image_urls parameter to chat route")
        
        # Step 2: Update multimodal condition
        content = update_multimodal_condition(content)
        print("✅ Updated multimodal condition")
        
        # Step 3: Update multimodal check
        content = update_multimodal_check(content)
        print("✅ Updated multimodal check condition")
        
        # Step 4: Update warning message
        content = update_multimodal_warning(content)
        print("✅ Updated warning message for non-multimodal models")
        
        # Step 5: Replace the multimodal block
        content = replace_multimodal_block(content)
        print("✅ Replaced multimodal content creation block with multi-image support")
        
        # Write the updated file
        write_file('app.py', content)
        print("\n✅ Successfully updated app.py with clean multi-image support!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    apply_updates()