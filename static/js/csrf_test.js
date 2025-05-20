/**
 * CSRF Test Script
 * 
 * This script tests our AJAX endpoints to verify that CSRF protection is working properly.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Only run these tests when a specific URL parameter is present
    // This prevents running tests automatically on every page load
    const urlParams = new URLSearchParams(window.location.search);
    if (!urlParams.has('test_csrf')) return;
    
    // Create a test div to display results
    const testResultsDiv = document.createElement('div');
    testResultsDiv.id = 'csrf-test-results';
    testResultsDiv.style.position = 'fixed';
    testResultsDiv.style.top = '20px';
    testResultsDiv.style.right = '20px';
    testResultsDiv.style.width = '400px';
    testResultsDiv.style.maxHeight = '80vh';
    testResultsDiv.style.overflowY = 'auto';
    testResultsDiv.style.backgroundColor = 'rgba(240, 240, 240, 0.9)';
    testResultsDiv.style.padding = '15px';
    testResultsDiv.style.border = '1px solid #ccc';
    testResultsDiv.style.borderRadius = '5px';
    testResultsDiv.style.zIndex = '9999';
    testResultsDiv.style.boxShadow = '0 0 10px rgba(0,0,0,0.1)';
    
    // Add a heading
    testResultsDiv.innerHTML = '<h3>CSRF Test Results</h3><div id="test-log"></div>';
    document.body.appendChild(testResultsDiv);
    
    const logDiv = document.getElementById('test-log');
    
    // Helper function to log test results
    function logResult(message, success = true) {
        const entry = document.createElement('div');
        entry.style.marginBottom = '10px';
        entry.style.padding = '5px';
        entry.style.borderLeft = `4px solid ${success ? 'green' : 'red'}`;
        entry.style.backgroundColor = `rgba(${success ? '200, 255, 200' : '255, 200, 200'}, 0.3)`;
        entry.style.fontSize = '14px';
        entry.innerHTML = message;
        logDiv.appendChild(entry);
        console.log(message);
    }
    
    // Test endpoints
    const endpoints = [
        {
            name: 'Save Preference',
            url: '/save_preference',
            method: 'POST',
            body: { preset_id: '1', model_id: 'test-model' }
        },
        {
            name: 'Cleanup Empty Conversations',
            url: '/api/cleanup-empty-conversations',
            method: 'POST',
            body: {}
        },
        {
            name: 'Create Conversation',
            url: '/api/create-conversation',
            method: 'POST',
            body: {}
        }
    ];
    
    // Run tests sequentially
    async function runTests() {
        logResult('Starting CSRF token tests...', true);
        
        // First, log the CSRF meta tag
        const metaToken = document.querySelector('meta[name="csrf-token"]')?.content;
        if (metaToken) {
            logResult(`CSRF Meta Tag present with token: ${metaToken.substring(0, 10)}...`, true);
        } else {
            logResult('CSRF Meta Tag is missing!', false);
            return; // Stop tests if token is missing
        }
        
        // Test each endpoint
        for (const endpoint of endpoints) {
            try {
                logResult(`Testing ${endpoint.name} (${endpoint.url})...`, true);
                
                const response = await fetch(endpoint.url, {
                    method: endpoint.method,
                    headers: {
                        'Content-Type': 'application/json'
                        // Don't add CSRF token manually - let the helper scripts do it
                    },
                    body: JSON.stringify(endpoint.body)
                });
                
                // Check if response is JSON
                let isJson = false;
                let responseData = null;
                
                try {
                    responseData = await response.json();
                    isJson = true;
                } catch (e) {
                    // Not JSON - likely HTML error page
                    const text = await response.clone().text();
                    responseData = text.substring(0, 100) + '...'; // Just show beginning
                }
                
                if (response.ok) {
                    logResult(`✓ ${endpoint.name}: Success (${response.status})`, true);
                    if (isJson) {
                        logResult(`Response: ${JSON.stringify(responseData).substring(0, 100)}...`, true);
                    }
                } else {
                    logResult(`✗ ${endpoint.name}: Failed with status ${response.status}`, false);
                    logResult(`Response: ${isJson ? JSON.stringify(responseData) : responseData}`, false);
                }
            } catch (error) {
                logResult(`✗ ${endpoint.name}: Error - ${error.message}`, false);
            }
        }
        
        logResult('All tests completed.', true);
    }
    
    // Add a button to start tests
    const testButton = document.createElement('button');
    testButton.textContent = 'Run CSRF Tests';
    testButton.style.marginTop = '10px';
    testButton.style.padding = '8px 15px';
    testButton.style.backgroundColor = '#0066cc';
    testButton.style.color = 'white';
    testButton.style.border = 'none';
    testButton.style.borderRadius = '4px';
    testButton.style.cursor = 'pointer';
    
    testButton.addEventListener('click', runTests);
    testResultsDiv.appendChild(testButton);
    
    // Log that the test script is ready
    logResult('CSRF Test script loaded. Click the button to start tests.', true);
});