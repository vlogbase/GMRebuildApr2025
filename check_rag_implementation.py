"""
Script to verify and test RAG (Retrieval Augmented Generation) implementation.
This validates that:
1. The 'supports_pdf' flag is correctly set in the database
2. The UI correctly displays RAG capabilities
3. Document processing functions work as expected
"""

import logging
import os
import sys
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('rag_implementation_check.log')
    ]
)
logger = logging.getLogger('rag_check')

def check_database_models_pdf_support():
    """
    Check if the models in the database have the 'supports_pdf' flag set correctly.
    """
    try:
        # Import Flask app and models
        from app import app, db
        from models import OpenRouterModel
        
        with app.app_context():
            # Query all active models
            models = OpenRouterModel.query.filter_by(model_is_active=True).all()
            
            if not models:
                logger.error("No active models found in the database!")
                return False
                
            logger.info(f"Found {len(models)} active models in the database")
            
            # Check which models support PDF
            pdf_capable_models = [model for model in models if model.supports_pdf]
            multimodal_models = [model for model in models if model.is_multimodal]
            
            logger.info(f"PDF-capable models: {len(pdf_capable_models)}/{len(models)}")
            logger.info(f"Multimodal models: {len(multimodal_models)}/{len(models)}")
            
            # Log the details of PDF-capable models
            logger.info("PDF-capable models:")
            for model in pdf_capable_models:
                logger.info(f"  - {model.model_id} ({model.name})")
                
            # Check if key models like GPT-4o and Gemini have the correct flags
            gpt4o = OpenRouterModel.query.filter(OpenRouterModel.model_id.like('%gpt-4o%')).first()
            gemini = OpenRouterModel.query.filter(OpenRouterModel.model_id.like('%gemini%')).first()
            
            if gpt4o:
                logger.info(f"GPT-4o model: {gpt4o.model_id}, supports_pdf={gpt4o.supports_pdf}, multimodal={gpt4o.is_multimodal}")
            else:
                logger.warning("No GPT-4o model found in the database")
                
            if gemini:
                logger.info(f"Gemini model: {gemini.model_id}, supports_pdf={gemini.supports_pdf}, multimodal={gemini.is_multimodal}")
            else:
                logger.warning("No Gemini model found in the database")
                
            return len(pdf_capable_models) > 0
            
    except Exception as e:
        logger.error(f"Error checking database models: {e}")
        return False

def check_api_endpoints():
    """
    Check if the API endpoints correctly include the 'supports_pdf' flag.
    """
    try:
        import requests
        
        # Make a request to the get_models endpoint
        response = requests.get('http://localhost:5000/api/get_models')
        if response.status_code != 200:
            logger.error(f"Error fetching models: {response.status_code}")
            return False
            
        data = response.json()
        if not data.get('models'):
            logger.error("No models returned from the API")
            return False
            
        # Check if any models have the supports_pdf flag
        models_with_pdf = [model for model in data['models'] if model.get('supports_pdf')]
        logger.info(f"API returned {len(models_with_pdf)}/{len(data['models'])} models with supports_pdf=True")
        
        # Check the model_prices endpoint
        prices_response = requests.get('http://localhost:5000/api/get_model_prices')
        if prices_response.status_code != 200:
            logger.error(f"Error fetching model prices: {prices_response.status_code}")
            return False
            
        prices_data = prices_response.json()
        if not prices_data.get('prices'):
            logger.error("No prices returned from the API")
            return False
            
        # Check if price data includes the supports_pdf flag
        prices_with_pdf = sum(1 for model_id, price_data in prices_data['prices'].items() 
                             if price_data.get('supports_pdf'))
        logger.info(f"API returned {prices_with_pdf}/{len(prices_data['prices'])} price entries with supports_pdf=True")
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking API endpoints: {e}")
        return False

def test_document_upload():
    """
    Test uploading a document through the RAG endpoint.
    """
    try:
        import requests
        import os
        from pathlib import Path
        
        # Check if we have a test PDF
        test_files_dir = Path('test_files')
        if not test_files_dir.exists():
            test_files_dir.mkdir(exist_ok=True)
            
        test_pdf = test_files_dir / 'test_document.pdf'
        
        # If no test PDF exists, create a simple one
        if not test_pdf.exists():
            logger.info("No test PDF found, this test requires a PDF file at test_files/test_document.pdf")
            return False
            
        logger.info(f"Using test PDF: {test_pdf}")
        
        # Create a session to maintain cookies
        with requests.Session() as session:
            # Upload the test file
            with open(test_pdf, 'rb') as f:
                files = {'file': (test_pdf.name, f, 'application/pdf')}
                response = session.post(
                    'http://localhost:5000/attach_file_for_rag',
                    files=files,
                    data={'model_id': 'openai/gpt-4o'}  # Assuming GPT-4o supports PDFs
                )
                
            if response.status_code != 200:
                logger.error(f"Error uploading document: {response.status_code}")
                logger.error(f"Response content: {response.text}")
                return False
                
            data = response.json()
            if 'error' in data:
                logger.error(f"Error from server: {data['error']}")
                return False
                
            logger.info(f"Document upload response: {data}")
            
            # Check if we have a success result
            if 'results' in data and data['results']:
                result = data['results'][0]
                if result.get('status') == 'success':
                    logger.info(f"Document uploaded successfully: {result.get('filename')}")
                    logger.info(f"Document URL: {result.get('url')}")
                    logger.info(f"Document ID in DB: {result.get('id_in_db')}")
                    return True
                else:
                    logger.error(f"Upload failed: {result.get('message')}")
                    return False
            else:
                logger.error("No results returned from the server")
                return False
                
    except Exception as e:
        logger.error(f"Error testing document upload: {e}")
        return False

def main():
    """
    Run all verification checks.
    """
    logger.info("=== Starting RAG Implementation Check ===")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    
    db_check = check_database_models_pdf_support()
    logger.info(f"Database models check: {'PASSED' if db_check else 'FAILED'}")
    
    # Only run API checks if database check passed
    if db_check:
        api_check = check_api_endpoints()
        logger.info(f"API endpoints check: {'PASSED' if api_check else 'FAILED'}")
    else:
        logger.warning("Skipping API check due to database check failure")
        api_check = False
    
    # Only attempt document upload if database and API checks passed
    if db_check and api_check:
        upload_check = test_document_upload()
        logger.info(f"Document upload test: {'PASSED' if upload_check else 'FAILED'}")
    else:
        logger.warning("Skipping document upload test due to previous check failures")
        upload_check = False
    
    logger.info("=== RAG Implementation Check Complete ===")
    logger.info(f"Overall status: {'PASSED' if (db_check and api_check and upload_check) else 'FAILED'}")
    
    return 0 if (db_check and api_check and upload_check) else 1

if __name__ == "__main__":
    sys.exit(main())