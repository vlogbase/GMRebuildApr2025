/**
 * Affiliate Frame Integration
 * 
 * This script creates an invisible iframe for each free model message,
 * loads a clean page with Skimlinks in the iframe, and uses that to
 * process the message content.
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Affiliate Frame integration initialized');
    
    // Set up observer for new messages
    setupMessageObserver();
    
    // Process existing messages
    processExistingMessages();
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
                            // Process with a delay to ensure the message is fully rendered
                            setTimeout(() => {
                                processMessageWithFrame(node);
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
    
    console.log('Message observer set up for affiliate frames');
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
        
        // Process each message with a slight delay between them
        aiMessages.forEach((message, index) => {
            setTimeout(() => {
                processMessageWithFrame(message);
            }, index * 300); // 300ms delay between each message
        });
        
        console.log(`Processing ${aiMessages.length} existing messages with affiliate frames`);
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
 * Process a message using an iframe with a clean Skimlinks environment
 */
function processMessageWithFrame(message) {
    // Skip if already processed
    if (message.hasAttribute('data-affiliate-processed')) {
        return;
    }
    
    // Find the message content
    const contentElement = message.querySelector('.message-content');
    if (!contentElement) return;
    
    // Mark as being processed
    message.setAttribute('data-affiliate-processed', 'true');
    
    // Get the original content
    const originalHTML = contentElement.innerHTML;
    
    // Create iframe
    const iframe = document.createElement('iframe');
    iframe.style.width = '0';
    iframe.style.height = '0';
    iframe.style.border = 'none';
    iframe.style.position = 'absolute';
    iframe.style.top = '-9999px';
    iframe.style.left = '-9999px';
    iframe.className = 'affiliate-frame';
    
    // Add to document
    document.body.appendChild(iframe);
    
    // Write content to iframe
    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
    iframeDoc.open();
    iframeDoc.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                .content { margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <div class="content" id="affiliate-content">${originalHTML}</div>
            
            <script>
                // When the page loads, send the processed content back to the parent
                window.addEventListener('load', function() {
                    // Give Skimlinks time to process the links
                    setTimeout(function() {
                        const processedContent = document.getElementById('affiliate-content').innerHTML;
                        window.parent.postMessage({
                            type: 'affiliate-processed',
                            content: processedContent,
                            messageId: "${message.getAttribute('data-message-id')}"
                        }, '*');
                    }, 1000);
                });
            </script>
            
            <!-- Skimlinks script placed at the end of body -->
            <script type="text/javascript" src="https://s.skimresources.com/js/44501X1766367.skimlinks.js"></script>
        </body>
        </html>
    `);
    iframeDoc.close();
    
    console.log(`Created affiliate frame for message ${message.getAttribute('data-message-id')}`);
}

// Listen for messages from iframes
window.addEventListener('message', function(event) {
    if (event.data && event.data.type === 'affiliate-processed') {
        // Find the message
        const message = document.querySelector(`.message[data-message-id="${event.data.messageId}"]`);
        if (message) {
            // Update the content
            const contentElement = message.querySelector('.message-content');
            if (contentElement) {
                const originalContent = contentElement.innerHTML;
                const newContent = event.data.content;
                
                // Only update if content actually changed
                if (originalContent !== newContent) {
                    contentElement.innerHTML = newContent;
                    console.log(`Updated content for message ${event.data.messageId} with affiliate links`);
                } else {
                    console.log(`No changes needed for message ${event.data.messageId}`);
                }
            }
        }
    }
});

/**
 * Add a test function for Skimlinks
 */
window.testSkimlinks = function() {
    // Open the test page in a new window/tab
    window.open('/skimlinks-test', '_blank');
    return 'Opening Skimlinks test page...';
};