/**
 * Targeted Skimlinks Integration
 * 
 * This approach addresses the core issue with integrating Skimlinks into a chat interface:
 * - Skimlinks is designed to process an entire page at once on initial load
 * - Chat content is added dynamically, so it typically doesn't get processed
 * 
 * Solution: This script detects when free model messages are added and creates a special
 * container elsewhere in the document specifically for Skimlinks to process. Then it
 * applies the processed content back to the original message.
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Late Skimlinks integration initialized');
    
    // Set up observer for new content
    setupContentObserver();
    
    // Process any existing messages
    setTimeout(processExistingFreeMessages, 1000);
});

/**
 * Observe the chat container for new message elements with the needs-skimlinks class
 */
function setupContentObserver() {
    const chatContainer = document.getElementById('chat-messages');
    if (!chatContainer) return;
    
    // Create a shadow container for Skimlinks processing
    createShadowContainer();
    
    // Create an observer to watch for new chat messages
    const messageObserver = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                // Check each new node
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1 && node.classList.contains('needs-skimlinks')) {
                        // Process this new message after a slight delay to ensure it's fully rendered
                        setTimeout(() => {
                            processSkimlinksContent(node);
                        }, 500);
                    }
                });
            }
        });
    });
    
    // Start observing the chat container for new messages
    messageObserver.observe(chatContainer, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['class']
    });
    
    console.log('Content observer set up for Skimlinks processing');
}

/**
 * Create a hidden container for Skimlinks to process content
 */
function createShadowContainer() {
    // Remove existing container if present
    const existing = document.getElementById('skimlinks-shadow-container');
    if (existing) {
        existing.remove();
    }
    
    // Create the shadow container
    const container = document.createElement('div');
    container.id = 'skimlinks-shadow-container';
    container.style.position = 'absolute';
    container.style.top = '-9999px';
    container.style.left = '-9999px';
    container.style.width = '500px'; // Set a width so content flows naturally
    container.style.height = '0';
    container.style.overflow = 'hidden';
    container.style.visibility = 'hidden';
    
    // Add to the document body
    document.body.appendChild(container);
    
    console.log('Created Skimlinks shadow container');
}

/**
 * Process any existing free messages that need Skimlinks processing
 */
function processExistingFreeMessages() {
    const freeMessages = document.querySelectorAll('.message.needs-skimlinks');
    if (freeMessages.length > 0) {
        console.log(`Found ${freeMessages.length} existing messages to process with Skimlinks`);
        
        freeMessages.forEach((message, index) => {
            // Process each message with a slight delay between them
            setTimeout(() => {
                processSkimlinksContent(message);
            }, index * 300); // 300ms delay between each message
        });
    }
}

/**
 * Process a message with Skimlinks
 */
function processSkimlinksContent(messageElement) {
    // Skip if already processed
    if (messageElement.hasAttribute('data-skimlinks-processed')) {
        return;
    }
    
    // Find the message content
    const contentElement = messageElement.querySelector('.message-content');
    if (!contentElement) return;
    
    // Mark as being processed
    messageElement.setAttribute('data-skimlinks-processed', 'true');
    
    // Get the original content
    const originalHTML = contentElement.innerHTML;
    
    // Get the shadow container
    const shadowContainer = document.getElementById('skimlinks-shadow-container');
    if (!shadowContainer) {
        console.error('Skimlinks shadow container not found');
        return;
    }
    
    // Clear the container and add the content
    shadowContainer.innerHTML = '';
    shadowContainer.innerHTML = originalHTML;
    
    // Give Skimlinks time to process the content
    setTimeout(() => {
        // Get the processed content
        const processedHTML = shadowContainer.innerHTML;
        
        // Check if the content was changed
        if (processedHTML !== originalHTML) {
            // Update the message content
            contentElement.innerHTML = processedHTML;
            console.log('Updated message with Skimlinks processed content');
            
            // Force a repaint to ensure changes are visible
            forceRepaint(contentElement);
            
            // Mark as successfully processed
            messageElement.classList.add('skimlinks-processed');
            messageElement.classList.remove('needs-skimlinks');
        } else {
            console.log('No changes made by Skimlinks to this message');
        }
        
        // Clear the shadow container
        shadowContainer.innerHTML = '';
    }, 1000);
}

/**
 * Force a repaint of an element to ensure changes are visible
 */
function forceRepaint(element) {
    if (!element) {
        console.warn('forceRepaint called with null/undefined element');
        return;
    }
    
    // Read layout property to force layout calculation
    const currentHeight = element.offsetHeight;
    // Force a style recalculation with a substantial change
    element.style.transform = 'translateZ(0)';
    // Use requestAnimationFrame to ensure it processes in the next paint cycle
    requestAnimationFrame(() => {
        element.style.transform = '';
    });
    
    // Log debug info
    console.debug(`forceRepaint applied to element: ${element.className || 'unnamed'}`);
}

/**
 * Test function to manually trigger Skimlinks processing
 */
window.testSkimlinks = function() {
    // Create a test popup
    const testContainer = document.createElement('div');
    testContainer.id = 'skimlinks-test-container';
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
        <p>This is a test of Skimlinks integration directly in the chat interface.</p>
        
        <div style="margin: 15px 0;">
            <button id="process-free-messages" style="background: #4CAF50; color: white; border: none; padding: 8px 15px; margin-right: 10px; border-radius: 4px; cursor: pointer;">
                Process All Free Messages
            </button>
            
            <button id="process-test-content" style="background: #2196F3; color: white; border: none; padding: 8px 15px; margin-right: 10px; border-radius: 4px; cursor: pointer;">
                Process Test Content
            </button>
            
            <button id="close-test-popup" style="background: #f44336; color: white; border: none; padding: 8px 15px; border-radius: 4px; cursor: pointer;">
                Close Test
            </button>
        </div>
        
        <div id="test-content" style="background: #f9f9f9; padding: 15px; border-radius: 5px; margin: 10px 0;">
            <p>Popular brands include Samsung, Dell, Sony, Apple, and Microsoft. 
            You might want to consider a MacBook Pro for professional work or a Kindle for reading.</p>
            <p>Here's the official <a href="http://test.skimlinks.com">Skimlinks test link</a> that should always be converted.</p>
        </div>
        
        <div id="test-result" style="margin-top: 15px; padding: 10px; background: #f0f8ff; border-left: 3px solid #0066cc;">
            Results will appear here after processing.
        </div>
    `;
    
    // Add to body
    document.body.appendChild(testContainer);
    
    // Set up button event handlers
    document.getElementById('process-free-messages').addEventListener('click', function() {
        processExistingFreeMessages();
        document.getElementById('test-result').innerHTML = 'Processing all free messages...';
    });
    
    document.getElementById('process-test-content').addEventListener('click', function() {
        const testContent = document.getElementById('test-content');
        const originalHTML = testContent.innerHTML;
        
        // Use the shadow container for processing
        const shadowContainer = document.getElementById('skimlinks-shadow-container');
        shadowContainer.innerHTML = originalHTML;
        
        // Process and show results
        setTimeout(() => {
            const processedHTML = shadowContainer.innerHTML;
            
            // Update test content
            testContent.innerHTML = processedHTML;
            
            // Show results
            const resultElement = document.getElementById('test-result');
            if (processedHTML !== originalHTML) {
                resultElement.innerHTML = '<strong>Success!</strong> Skimlinks modified the content with affiliate links.';
                resultElement.style.borderColor = '#4CAF50';
            } else {
                resultElement.innerHTML = '<strong>No changes detected.</strong> Skimlinks did not modify the content.';
                resultElement.style.borderColor = '#f44336';
            }
        }, 1000);
    });
    
    document.getElementById('close-test-popup').addEventListener('click', function() {
        document.body.removeChild(testContainer);
    });
    
    return 'Opened Skimlinks test interface. Use the buttons to test different aspects of the integration.';
};