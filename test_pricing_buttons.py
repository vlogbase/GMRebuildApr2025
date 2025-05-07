"""
A simple test app to verify the OpenRouter model and pricing refresh functionality.
"""

import os
import logging
from flask import Flask, render_template, jsonify, redirect, url_for, request
import requests

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Define our test endpoint to hit the API refresh endpoint
@app.route('/test_refresh_prices', methods=['POST'])
def test_refresh_prices():
    """Test the refresh prices endpoint"""
    try:
        response = requests.post(
            'http://localhost:3000/api/refresh_model_prices',
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        # Log the response
        logger.info(f"Refresh prices response status: {response.status_code}")
        
        # Parse response JSON
        data = response.json()
        model_count = len(data.get('prices', {}))
        
        logger.info(f"Refresh returned {model_count} models")
        return jsonify({
            'success': True,
            'status_code': response.status_code,
            'model_count': model_count,
            'response': data
        })
    except Exception as e:
        logger.error(f"Error testing refresh prices: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Define our test endpoint to hit the model pricing endpoint
@app.route('/test_model_pricing', methods=['GET'])
def test_model_pricing():
    """Test the model pricing endpoint"""
    try:
        response = requests.get(
            'http://localhost:3000/api/model-pricing',
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        # Log the response
        logger.info(f"Model pricing response status: {response.status_code}")
        
        # Parse response JSON
        data = response.json()
        model_count = len(data.get('data', []))
        
        logger.info(f"Pricing data includes {model_count} models")
        
        # Truncate the data for display
        truncated_data = {
            'data': data.get('data', [])[:5],  # First 5 models
            'last_updated': data.get('last_updated')
        }
        
        return jsonify({
            'success': True,
            'status_code': response.status_code,
            'model_count': model_count,
            'truncated_response': truncated_data
        })
    except Exception as e:
        logger.error(f"Error testing model pricing: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Define our test endpoint to hit the models endpoint
@app.route('/test_models', methods=['GET'])
def test_models():
    """Test the models endpoint"""
    try:
        response = requests.get(
            'http://localhost:3000/models',
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        # Log the response
        logger.info(f"Models response status: {response.status_code}")
        
        # Parse response JSON
        data = response.json()
        
        # Extract information about models
        models = data.get('models', [])
        model_count = len(models)
        
        logger.info(f"Models data includes {model_count} models")
        
        # Truncate the data for display
        truncated_models = models[:5] if models else []
        
        return jsonify({
            'success': True,
            'status_code': response.status_code,
            'model_count': model_count,
            'truncated_models': truncated_models
        })
    except Exception as e:
        logger.error(f"Error testing models endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Define our test endpoint to hit the reset preferences endpoint
@app.route('/test_reset_preferences', methods=['POST'])
def test_reset_preferences():
    """Test the reset preferences endpoint"""
    try:
        # Reset all preferences
        response = requests.post(
            'http://localhost:3000/reset_preferences',
            json={},  # Empty JSON means reset all
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        # Log the response
        logger.info(f"Reset preferences response status: {response.status_code}")
        
        # Parse response JSON
        data = response.json()
        
        return jsonify({
            'success': True,
            'status_code': response.status_code,
            'response': data
        })
    except Exception as e:
        logger.error(f"Error testing reset preferences: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Main page with test buttons
@app.route('/')
def index():
    """Main test page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>OpenRouter API Test</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                line-height: 1.6;
            }
            h1 {
                color: #333;
            }
            .test-section {
                margin-bottom: 20px;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            button {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 10px 15px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 4px;
            }
            pre {
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;
            }
            .result {
                margin-top: 10px;
                min-height: 20px;
            }
        </style>
    </head>
    <body>
        <h1>OpenRouter API Test</h1>
        
        <div class="test-section">
            <h2>Test 1: Refresh Model Prices</h2>
            <p>This tests the "refresh prices" button functionality.</p>
            <button onclick="testRefreshPrices()">Test Refresh Prices</button>
            <div class="result" id="refresh-result"></div>
        </div>
        
        <div class="test-section">
            <h2>Test 2: Get Model Pricing</h2>
            <p>This tests if we can get all model pricing data.</p>
            <button onclick="testModelPricing()">Test Model Pricing</button>
            <div class="result" id="pricing-result"></div>
        </div>
        
        <div class="test-section">
            <h2>Test 3: Get Available Models</h2>
            <p>This tests if we can get all available models.</p>
            <button onclick="testModels()">Test Models</button>
            <div class="result" id="models-result"></div>
        </div>
        
        <div class="test-section">
            <h2>Test 4: Reset Preferences</h2>
            <p>This tests the "reset to defaults" button functionality.</p>
            <button onclick="testResetPreferences()">Test Reset Preferences</button>
            <div class="result" id="reset-result"></div>
        </div>
        
        <script>
            async function testRefreshPrices() {
                document.getElementById('refresh-result').innerHTML = 'Loading...';
                try {
                    const response = await fetch('/test_refresh_prices', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });
                    const data = await response.json();
                    
                    // Format the response for display
                    const resultHtml = `
                        <pre>Success: ${data.success}
Status Code: ${data.status_code}
Model Count: ${data.model_count}
Last Updated: ${data.response.last_updated}
Sample Models: ${Object.keys(data.response.prices).slice(0, 3).join(', ')}...</pre>
                    `;
                    
                    document.getElementById('refresh-result').innerHTML = resultHtml;
                } catch (error) {
                    document.getElementById('refresh-result').innerHTML = `<pre>Error: ${error.message}</pre>`;
                }
            }
            
            async function testModelPricing() {
                document.getElementById('pricing-result').innerHTML = 'Loading...';
                try {
                    const response = await fetch('/test_model_pricing');
                    const data = await response.json();
                    
                    // Format the response for display
                    const resultHtml = `
                        <pre>Success: ${data.success}
Status Code: ${data.status_code}
Model Count: ${data.model_count}
Last Updated: ${data.truncated_response.last_updated}
Sample Models: ${data.truncated_response.data.map(m => m.model_id).join(', ')}...</pre>
                    `;
                    
                    document.getElementById('pricing-result').innerHTML = resultHtml;
                } catch (error) {
                    document.getElementById('pricing-result').innerHTML = `<pre>Error: ${error.message}</pre>`;
                }
            }
            
            async function testModels() {
                document.getElementById('models-result').innerHTML = 'Loading...';
                try {
                    const response = await fetch('/test_models');
                    const data = await response.json();
                    
                    // Format the response for display
                    const resultHtml = `
                        <pre>Success: ${data.success}
Status Code: ${data.status_code}
Model Count: ${data.model_count}
Sample Models: ${data.truncated_models.map(m => m.id).join(', ')}...</pre>
                    `;
                    
                    document.getElementById('models-result').innerHTML = resultHtml;
                } catch (error) {
                    document.getElementById('models-result').innerHTML = `<pre>Error: ${error.message}</pre>`;
                }
            }
            
            async function testResetPreferences() {
                document.getElementById('reset-result').innerHTML = 'Loading...';
                try {
                    const response = await fetch('/test_reset_preferences', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });
                    const data = await response.json();
                    
                    // Format the response for display
                    const resultHtml = `
                        <pre>Success: ${data.success}
Status Code: ${data.status_code}
Response: ${JSON.stringify(data.response, null, 2)}</pre>
                    `;
                    
                    document.getElementById('reset-result').innerHTML = resultHtml;
                } catch (error) {
                    document.getElementById('reset-result').innerHTML = `<pre>Error: ${error.message}</pre>`;
                }
            }
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    # Run the app on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)