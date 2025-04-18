"""
Script to update the app.py file to handle multiple images in chat messages.
This will patch the chat function to process image_urls array instead of just a single image_url.
"""

import re
import sys

def update_chat_function():
    # Open the app.py file
    with open('app.py', 'r') as file:
        content = file.read()
    
    # Find the section where we handle multimodal content
    pattern = r'(# Following OpenRouter\'s unified multimodal format[^\n]*\n\s+# https://openrouter\.ai/docs#multimodal\n\s+if image_url and openrouter_model in MULTIMODAL_MODELS:)(.*?)(else:\n\s+# Standard text-only message\n\s+messages\.append\({\'role\': \'user\', \'content\': user_message}\)\n\s+\n\s+# Log if image was provided but model doesn\'t support it\n\s+if image_url and openrouter_model not in MULTIMODAL_MODELS:)'
    
    # Define the new code to replace the old section
    new_code = r'''\1
            # Create a multimodal content array with the text message
            multimodal_content = [
                {"type": "text", "text": user_message}
            ]
            
            # Process all images in the image_urls array
            for url in image_urls:
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
                    if any(os.path.splitext(urlparse(url).path)[1].lower() == '.webp' for url in image_urls if url.startswith(('http://', 'https://'))):
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
                messages.append({'role': 'user', 'content': user_message})\3
        # Standard text-only message
        messages.append({'role': 'user', 'content': user_message})
        
        # Log if image was provided but model doesn't support it
        if (image_url or (image_urls and len(image_urls) > 0)) and openrouter_model not in MULTIMODAL_MODELS:'''
    
    # Also update the condition in the if statement
    updated_code = re.sub(pattern, new_code, content, flags=re.DOTALL)
    
    # Update the if condition from "if image_url" to "if (image_url or (image_urls and len(image_urls) > 0))"
    updated_code = updated_code.replace(
        "if image_url and openrouter_model in MULTIMODAL_MODELS:", 
        "if (image_url or (image_urls and len(image_urls) > 0)) and openrouter_model in MULTIMODAL_MODELS:"
    )
    
    # Write the updated content back to app.py
    with open('app.py', 'w') as file:
        file.write(updated_code)
    
    print("✅ Successfully updated app.py with multi-image support!")
    print("The chat function can now handle multiple images in a single message.")

if __name__ == "__main__":
    try:
        update_chat_function()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)