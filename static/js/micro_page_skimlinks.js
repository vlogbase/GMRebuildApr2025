/**
 * Micro Page Skimlinks Integration
 * 
 * This approach treats each free model message as its own "micro page" with body tags
 * to allow Skimlinks to process it as a separate document.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Log initialization
    console.log('Micro Page Skimlinks integration initialized');
    
    // Set up observer for new messages
    setupMessageObserver();
    
    // Check existing messages
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
                            // This is a free model message, convert it to a micro page
                            convertToMicroPage(node);
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
    
    console.log('Message observer set up for Skimlinks micro pages');
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
        aiMessages.forEach(message => {
            convertToMicroPage(message);
        });
        
        console.log(`Processed ${aiMessages.length} existing messages as micro pages`);
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
 * Convert a message into a "micro page" with its own body tags
 * to allow Skimlinks to process it separately
 */
function convertToMicroPage(message) {
    // Skip if already processed
    if (message.classList.contains('skimlinks-micro-page')) {
        return;
    }
    
    // Find the message content
    const contentElement = message.querySelector('.message-content');
    if (!contentElement) return;
    
    // Get the original HTML
    const originalHTML = contentElement.innerHTML;
    
    // Mark message as being processed
    message.classList.add('skimlinks-micro-page');
    message.dataset.originalContent = originalHTML;
    
    // Create iframe for the micro page
    const iframe = document.createElement('iframe');
    iframe.className = 'skimlinks-micro-iframe';
    iframe.style.border = 'none';
    iframe.style.width = '100%';
    iframe.style.height = '0';
    iframe.style.overflow = 'hidden';
    iframe.style.display = 'block';
    
    // Add the iframe to the message
    message.appendChild(iframe);
    
    // Set up the micro page content in the iframe
    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
    iframeDoc.open();
    iframeDoc.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    color: #333;
                    line-height: 1.6;
                }
                
                .message-content {
                    padding: 0;
                }
                
                /* Match styling from parent page */
                p {
                    margin-bottom: 0.8em;
                }
                
                a {
                    color: #0066cc;
                    text-decoration: underline;
                }
            </style>
        </head>
        <body>
            <div class="message-content" id="micro-content">
                ${originalHTML}
            </div>
            
            <!-- Skimlinks script -->
            <script type="text/javascript" src="https://s.skimresources.com/js/44501X1766367.skimlinks.js"></script>
            
            <!-- Listen for changes to inject back into parent -->
            <script>
                window.addEventListener('load', function() {
                    // Give Skimlinks a moment to process the content
                    setTimeout(function() {
                        // Get the processed content
                        const processedContent = document.getElementById('micro-content').innerHTML;
                        
                        // Send message to parent window
                        window.parent.postMessage({
                            type: 'skimlinks-content',
                            content: processedContent
                        }, '*');
                        
                        // Check if any links were modified
                        const links = document.querySelectorAll('a');
                        const modifiedLinks = Array.from(links).filter(link => 
                            link.href.includes('go.skimresources.com') || 
                            link.hasAttribute('data-skimlinks') || 
                            link.hasAttribute('data-skimwords')
                        );
                        
                        console.log('Micro page processed with ' + modifiedLinks.length + ' affiliate links');
                    }, 1000);
                });
            </script>
        </body>
        </html>
    `);
    iframeDoc.close();
    
    // Adjust iframe height based on content
    setTimeout(() => {
        try {
            const height = iframe.contentWindow.document.body.scrollHeight;
            iframe.style.height = height + 'px';
        } catch (e) {
            console.error('Error resizing iframe:', e);
        }
    }, 100);
    
    // Listen for messages from the iframe
    window.addEventListener('message', function(event) {
        // Verify message is from our iframe
        if (event.data && event.data.type === 'skimlinks-content') {
            // Find all iframes in messages
            const messageIframes = document.querySelectorAll('.message.ai-message .skimlinks-micro-iframe');
            
            // Find the corresponding message for this iframe
            for (let i = 0; i < messageIframes.length; i++) {
                try {
                    if (messageIframes[i].contentWindow === event.source) {
                        const parentMessage = messageIframes[i].closest('.message.ai-message');
                        const contentElement = parentMessage.querySelector('.message-content');
                        
                        // Update the visible content with processed content
                        contentElement.innerHTML = event.data.content;
                        
                        // Hide the iframe as it's no longer needed
                        messageIframes[i].style.display = 'none';
                        
                        console.log('Updated message content with Skimlinks processed content');
                        break;
                    }
                } catch (e) {
                    console.error('Error processing message from iframe:', e);
                }
            }
        }
    });
}