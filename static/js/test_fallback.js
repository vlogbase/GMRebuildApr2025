/**
 * Test script for model fallback confirmation feature
 * 
 * This adds test buttons to the UI to simulate different model fallback scenarios
 * so we can verify the fallback confirmation dialog works correctly.
 */
document.addEventListener('DOMContentLoaded', function() {
    // Create a test panel to add to the UI
    const testPanel = document.createElement('div');
    testPanel.className = 'fallback-test-panel';
    testPanel.style.cssText = 'position: fixed; top: 10px; right: 10px; background: #333; padding: 15px; border-radius: 8px; z-index: 1000; max-width: 300px;';
    
    // Add title to the panel
    const testTitle = document.createElement('h3');
    testTitle.textContent = 'Model Fallback Test Panel';
    testTitle.style.cssText = 'margin-top: 0; color: #fff; font-size: 16px;';
    testPanel.appendChild(testTitle);
    
    // Add description
    const testDescription = document.createElement('p');
    testDescription.textContent = 'Click a button to test different model fallback scenarios:';
    testDescription.style.cssText = 'margin-bottom: 10px; color: #ccc; font-size: 13px;';
    testPanel.appendChild(testDescription);
    
    // Add test buttons
    const testScenarios = [
        {
            name: 'Model Unavailable',
            action: () => simulateFallback('claude-3-haiku', 'gpt-4o')
        },
        {
            name: 'Accept Fallback',
            action: () => {
                simulateFallback('claude-3-haiku', 'gpt-4o');
                setTimeout(() => {
                    document.getElementById('use-fallback').click();
                }, 500);
            }
        },
        {
            name: 'Reject Fallback',
            action: () => {
                simulateFallback('claude-3-haiku', 'gpt-4o');
                setTimeout(() => {
                    document.getElementById('cancel-fallback').click();
                }, 500);
            }
        },
        {
            name: 'Auto-fallback On',
            action: () => {
                const checkbox = document.getElementById('auto-fallback-checkbox');
                if (checkbox) {
                    checkbox.checked = true;
                    simulateFallback('claude-3-haiku', 'gpt-4o');
                    setTimeout(() => {
                        document.getElementById('use-fallback').click();
                    }, 500);
                }
            }
        }
    ];
    
    // Create buttons for each test scenario
    testScenarios.forEach(scenario => {
        const button = document.createElement('button');
        button.textContent = scenario.name;
        button.className = 'btn btn-sm btn-primary';
        button.style.cssText = 'margin: 5px; width: 100%;';
        button.addEventListener('click', scenario.action);
        testPanel.appendChild(button);
    });
    
    // Add a close button
    const closeButton = document.createElement('button');
    closeButton.textContent = 'Close Test Panel';
    closeButton.className = 'btn btn-sm btn-danger';
    closeButton.style.cssText = 'margin: 5px; width: 100%; margin-top: 15px;';
    closeButton.addEventListener('click', () => testPanel.remove());
    testPanel.appendChild(closeButton);
    
    // Add the panel to the document
    document.body.appendChild(testPanel);
    
    // Function to simulate a fallback
    function simulateFallback(requestedModel, fallbackModel) {
        // Only proceed if showFallbackModal is available
        if (typeof window.showFallbackModal !== 'function') {
            alert('Fallback modal function not available. Make sure model_fallback.js is loaded.');
            return;
        }
        
        // Simulate a message being typed
        const userInput = document.getElementById('user-input');
        if (userInput) {
            userInput.value = 'This is a test message to trigger model fallback';
        }
        
        // Create the fallback data
        const fallbackData = {
            requested_model: requestedModel,
            fallback_model: fallbackModel
        };
        
        // Create the message data
        const messageData = {
            message: userInput ? userInput.value : 'Test message',
            model: requestedModel
        };
        
        // Show the fallback modal
        window.showFallbackModal(fallbackData, messageData);
    }
});