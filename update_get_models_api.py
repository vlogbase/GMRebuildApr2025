"""
Script to verify that the get_models API includes the supports_pdf flag.
This won't run app.py but will directly check and modify it if needed.
"""
import os
import sys
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_get_models_api():
    """
    Verify and update the get_models API in app.py to include supports_pdf flag.
    """
    try:
        # Define the file path
        file_path = 'app.py'
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File {file_path} does not exist")
            return False
        
        # Read the file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Define the model_data dictionary pattern to match
        model_data_pattern = re.compile(r'model_data\s*=\s*{[^}]*?\'is_multimodal\':[^}]*?}')
        
        # Find all model_data dictionary instances
        model_data_matches = model_data_pattern.findall(content)
        
        if not model_data_matches:
            logger.error("Could not find model_data dictionary in app.py")
            return False
        
        # Check if any model_data dictionaries already include supports_pdf
        needs_update = True
        for match in model_data_matches:
            if 'supports_pdf' in match:
                logger.info("supports_pdf already exists in a model_data dictionary")
                needs_update = False
                break
        
        if needs_update:
            logger.info("Updating model_data dictionary to include supports_pdf")
            
            # Define pattern for the specific model_data dictionary in get_models
            target_model_data = re.compile(r'(model_data\s*=\s*{[^}]*?\'is_multimodal\':\s*db_model\.is_multimodal,)([^}]*?})')
            
            # Replace with updated dictionary including supports_pdf
            updated_content = target_model_data.sub(r'\1\n                    \'supports_pdf\': db_model.supports_pdf,  # Added supports_pdf flag\2', content)
            
            # Write the updated content back to the file
            with open(file_path, 'w') as f:
                f.write(updated_content)
            
            logger.info("Successfully updated get_models API to include supports_pdf flag")
        else:
            logger.info("No update needed, supports_pdf already exists in model_data dictionary")
        
        # Verify the update
        with open(file_path, 'r') as f:
            updated_content = f.read()
        
        # Look for the updated model_data dictionary
        model_data_with_supports_pdf = re.search(r'model_data\s*=\s*{[^}]*?\'supports_pdf\':[^}]*?}', updated_content)
        
        if model_data_with_supports_pdf:
            logger.info("Verification successful: model_data dictionary now includes supports_pdf")
            return True
        else:
            logger.warning("Verification failed: could not find supports_pdf in model_data dictionary")
            return False
            
    except Exception as e:
        logger.error(f"Error updating get_models API: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("Updating get_models API to include supports_pdf flag...")
    success = update_get_models_api()
    if success:
        logger.info("✅ Successfully updated get_models API!")
        sys.exit(0)
    else:
        logger.error("❌ Failed to update get_models API")
        sys.exit(1)