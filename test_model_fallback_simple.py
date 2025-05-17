"""
Simple standalone test for model fallback confirmation feature.
This test doesn't require database access or the full app.py.
"""
import os
import logging
from flask import Flask, render_template, jsonify, request, session

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_app():
    """Create a minimal Flask app for testing"""
    app = Flask(__name__)
    app.secret_key = 'test_secret_key'
    
    @app.route('/')
    def index():
        """Home page - shows the test interface"""
        return render_template('test_fallback.html')
    
    @app.route('/api/test-fallback', methods=['POST'])
    def test_fallback_api():
        """Simulate a model fallback situation for testing"""
        try:
            data = request.json
            requested_model = data.get('model', 'anthropic/claude-3-haiku')
            requested_name = requested_model.split('/')[-1].replace('-', ' ').title()
            
            # Simulate fallback to Gemini Flash
            fallback_model_id = 'google/gemini-flash:free'
            fallback_model_name = 'Gemini Flash'
            
            # Return a fallback notification
            return jsonify({
                'type': 'model_fallback',
                'requested_model': requested_name,
                'fallback_model': fallback_model_name,
                'original_model_id': requested_model,
                'fallback_model_id': fallback_model_id,
                'reason': 'Model unavailable for testing purposes'
            })
        except Exception as e:
            logger.error(f"Error in test_fallback_api: {e}")
            return jsonify({
                'error': str(e)
            }), 500
    
    return app

def run():
    """Run the standalone test server"""
    app = create_app()
    logger.info("=" * 80)
    logger.info("MODEL FALLBACK CONFIRMATION TEST")
    logger.info("=" * 80)
    logger.info("Test the model fallback confirmation feature by:")
    logger.info("1. Navigate to http://localhost:5000")
    logger.info("2. Click the 'Test Fallback Dialog' button to simulate a model fallback")
    logger.info("=" * 80)
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    run()