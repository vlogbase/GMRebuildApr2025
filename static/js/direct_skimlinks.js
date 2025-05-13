/**
 * Direct Skimlinks Integration
 * 
 * This approach directly manipulates the message content to allow Skimlinks to process it naturally.
 * It works by taking the content from AI messages, moving it into the document body temporarily,
 * letting Skimlinks process it, then moving it back.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Log initialization
    console.log('Direct Skimlinks integration initialized');
    
    // Set up observer for new messages
    setupMessageObserver();
    
    // Mark existing messages for processing after Skimlinks is fully loaded
    window.addEventListener('load', function() {
        console.log('Window loaded, waiting for Skimlinks initialization...');
        // Wait a moment for Skimlinks to be ready
        setTimeout(processExistingMessages, 1500);
    });
});

/**
 * Set up mutation observer to watch for new chat messages
 */
function setupMessageObserver() {
    const chatContainer = document.getElementById('chat-messages');
    if (!chatContainer) return;
    
    // Create an observer to watch for new chat messages
    const messageObserver = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                // Process each added node
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1 && node.classList.contains('message') && 
                        node.classList.contains('ai-message')) {
                        
                        // Check if this is from a free model (preset 6)
                        const presetId = getSelectedPresetId();
                        if (presetId === '6') {
                            // Process after a slight delay to ensure the message is fully rendered
                            setTimeout(() => {
                                processMessageContent(node);
                            }, 500);
                        }
                    }
                });
            }
        });
    });
    
    // Start observing the chat container
    messageObserver.observe(chatContainer, {
        childList: true,
        subtree: false
    });
    
    console.log('Message observer set up for Skimlinks integration');
}

/**
 * Process existing messages in the chat
 */
function processExistingMessages() {
    // Get the current preset ID
    const presetId = getSelectedPresetId();
    
    // Only process if we're using the free model
    if (presetId === '6') {
        // Find all AI messages
        const aiMessages = document.querySelectorAll('.message.ai-message');
        if (aiMessages.length > 0) {
            console.log(`Found ${aiMessages.length} existing AI messages to process`);
            
            // Process each message with a slight delay between them
            aiMessages.forEach((message, index) => {
                setTimeout(() => {
                    processMessageContent(message);
                }, index * 300); // 300ms delay between each message
            });
        } else {
            console.log('No existing AI messages found');
        }
    } else {
        console.log('Not using free model, skipping existing message processing');
    }
}

/**
 * Get the currently selected preset ID
 */
function getSelectedPresetId() {
    const activePreset = document.querySelector('.model-preset-btn.active');
    return activePreset ? activePreset.getAttribute('data-preset-id') : null;
}

/**
 * Process a message to allow Skimlinks to parse it
 */
function processMessageContent(message) {
    // Skip if already processed
    if (message.hasAttribute('data-skimlinks-processed')) {
        return;
    }
    
    // Find the message content
    const contentElement = message.querySelector('.message-content');
    if (!contentElement) return;
    
    // Mark as being processed
    message.setAttribute('data-skimlinks-processed', 'true');
    
    // Get the original content
    const originalHTML = contentElement.innerHTML;
    
    // Create a temporary container in the body
    const tempContainer = document.createElement('div');
    tempContainer.id = 'skimlinks-temp-container';
    tempContainer.style.position = 'absolute';
    tempContainer.style.top = '-9999px';
    tempContainer.style.left = '-9999px';
    tempContainer.style.width = '500px'; // Give it some width so content flows naturally
    tempContainer.innerHTML = originalHTML;
    
    // Append to body (where Skimlinks will process it)
    document.body.appendChild(tempContainer);
    
    // Give Skimlinks time to process the content
    setTimeout(() => {
        // Get the processed content
        const processedHTML = tempContainer.innerHTML;
        
        // Update the message content if it's different
        if (processedHTML !== originalHTML) {
            contentElement.innerHTML = processedHTML;
            console.log('Updated message with Skimlinks processed content');
            
            // Force a repaint to ensure changes are visible
            forceRepaint(contentElement);
            
            // Add a class to indicate it's been processed
            message.classList.add('skimlinks-processed');
        } else {
            console.log('No changes made by Skimlinks to this message');
        }
        
        // Remove the temporary container
        document.body.removeChild(tempContainer);
    }, 1000);
}

/**
 * Force a repaint of an element to ensure changes are visible
 */
function forceRepaint(element) {
    // Force a repaint by triggering layout calculations
    const displayStyle = element.style.display;
    element.style.display = 'none';
    void element.offsetHeight; // Force a layout calculation
    element.style.display = displayStyle;
}

/**
 * Add testable functionality
 */
window.testSkimlinks = function() {
    console.log('Testing Skimlinks on all free model messages');
    
    // Add a sample message for testing if none exist
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
        // Create a test container
        const testContainer = document.createElement('div');
        testContainer.style.position = 'fixed';
        testContainer.style.top = '50%';
        testContainer.style.left = '50%';
        testContainer.style.transform = 'translate(-50%, -50%)';
        testContainer.style.width = '80%';
        testContainer.style.maxWidth = '600px';
        testContainer.style.backgroundColor = 'white';
        testContainer.style.padding = '20px';
        testContainer.style.boxShadow = '0 4px 20px rgba(0,0,0,0.3)';
        testContainer.style.zIndex = '9999';
        testContainer.style.borderRadius = '8px';
        
        // Add test content
        testContainer.innerHTML = `
            <h3 style="margin-top: 0; color: #333;">Skimlinks Test</h3>
            <p>This is a test of Skimlinks integration. Here are some product mentions that should be converted to affiliate links:</p>
            <div id="test-content" style="background: #f9f9f9; padding: 15px; border-radius: 5px; margin: 10px 0;">
                <p>Popular brands include Samsung, Dell, Sony, Apple, and Microsoft. 
                You might want to consider a MacBook Pro for professional work or a Kindle for reading.</p>
            </div>
            <p><a href="http://test.skimlinks.com" style="color: #0066cc;">Official Skimlinks Test Link</a></p>
            <div id="test-result" style="margin-top: 15px; padding: 10px; background: #f0f8ff; border-left: 3px solid #0066cc;"></div>
            <button id="close-test" style="background: #333; color: white; border: none; padding: 8px 15px; border-radius: 4px; margin-top: 15px; cursor: pointer;">Close Test</button>
        `;
        
        // Add to body
        document.body.appendChild(testContainer);
        
        // Add close functionality
        document.getElementById('close-test').addEventListener('click', function() {
            document.body.removeChild(testContainer);
        });
        
        // Process the test content
        const testContent = document.getElementById('test-content');
        const originalHTML = testContent.innerHTML;
        
        // Create a container for processing
        const processContainer = document.createElement('div');
        processContainer.style.position = 'absolute';
        processContainer.style.top = '-9999px';
        processContainer.style.left = '-9999px';
        processContainer.innerHTML = originalHTML;
        document.body.appendChild(processContainer);
        
        // Give Skimlinks time to process
        setTimeout(() => {
            // Get processed content
            const processedHTML = processContainer.innerHTML;
            
            // Update test content
            testContent.innerHTML = processedHTML;
            
            // Show results
            const testResult = document.getElementById('test-result');
            if (processedHTML !== originalHTML) {
                testResult.innerHTML = '<strong>Success!</strong> Skimlinks modified the content with affiliate links.';
                testResult.style.color = 'green';
            } else {
                testResult.innerHTML = '<strong>No changes detected.</strong> Skimlinks did not modify the content.';
                testResult.style.color = 'red';
            }
            
            // Clean up
            document.body.removeChild(processContainer);
        }, 1000);
    }
    
    return 'Testing Skimlinks integration...';
};