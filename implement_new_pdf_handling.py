"""
Master script to implement new PDF handling and remove the old RAG system.
This script will:
1. Add document models to app.py
2. Update the chat function to handle PDFs
3. Disable the old RAG system
4. Add the PDF upload route
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Run all implementation steps"""
    try:
        # Step 1: Add PDF document models
        logger.info("Step 1: Adding PDF document models...")
        from add_document_models import add_document_models
        if not add_document_models():
            logger.error("Failed to add PDF document models")
            return False
        
        # Step 2: Update chat function to handle PDFs
        logger.info("Step 2: Updating chat function to handle PDFs...")
        from update_chat_for_pdfs import update_chat_function
        if not update_chat_function():
            logger.error("Failed to update chat function")
            return False
        
        # Step 3: Disable old RAG system
        logger.info("Step 3: Disabling old RAG system...")
        from disable_rag_system import disable_rag_system
        if not disable_rag_system():
            logger.error("Failed to disable old RAG system")
            return False
        
        # Step 4: Import PDF route
        logger.info("Step 4: Adding PDF route...")
        with open('app.py', 'r') as f:
            content = f.read()
        
        # Check if the route is already imported
        if "from pdf_route import upload_pdf" not in content:
            # Find a good place to add the import, ideally at the end of imports
            import_pos = content.find("# Initialize Azure Blob Storage for image uploads")
            
            if import_pos != -1:
                # Add import before Azure Blob Storage initialization
                new_content = content[:import_pos] + "# Import PDF route\nfrom pdf_route import upload_pdf\n\n" + content[import_pos:]
                
                with open('app.py', 'w') as f:
                    f.write(new_content)
                
                logger.info("✅ Added PDF route import to app.py")
            else:
                logger.error("Could not find a suitable position to add PDF route import")
                return False
        else:
            logger.info("PDF route already imported in app.py, skipping")
        
        logger.info("✅ PDF handling implementation complete!")
        logger.info("The system now uses direct PDF handling through OpenRouter instead of the old RAG system.")
        return True
    
    except Exception as e:
        logger.exception(f"Implementation failed: {e}")
        return False

if __name__ == "__main__":
    main()