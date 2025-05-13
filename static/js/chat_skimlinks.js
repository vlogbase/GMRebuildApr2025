/**
 * Chat-specific Skimlinks Integration
 * 
 * This approach is based on our testing which showed that Skimlinks can successfully 
 * convert brand names like Samsung, Dell, and Sony to affiliate links, even when
 * window.skimlinks and window._skimlinks objects aren't detected.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Log initialization
    console.log('Chat Skimlinks integration initialized');
    
    // Set up observer for new messages
    setupMessageObserver();
    
    // Add toggle button for affiliate mode
    addAffiliateViewToggle();
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
                            // Tag this message for affiliate content
                            node.dataset.modelType = 'free';
                            
                            // Force a repaint to ensure Skimlinks processes the content
                            setTimeout(() => {
                                forceRepaint(node);
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
 * Get the currently selected preset ID
 */
function getSelectedPresetId() {
    const activePreset = document.querySelector('.model-preset-btn.active');
    return activePreset ? activePreset.getAttribute('data-preset-id') : null;
}

/**
 * Force a repaint of an element to ensure Skimlinks processes it
 */
function forceRepaint(element) {
    // Add a class to indicate this has been processed
    element.classList.add('skimlinks-processed');
    
    // Force a repaint by triggering layout calculations
    const displayStyle = element.style.display;
    element.style.display = 'none';
    void element.offsetHeight; // Force a layout calculation
    element.style.display = displayStyle;
    
    console.log('Forced repaint for Skimlinks processing');
}

/**
 * Add a toggle button to switch to affiliate view mode
 */
function addAffiliateViewToggle() {
    // Create the toggle button 
    const toggleButton = document.createElement('button');
    toggleButton.id = 'affiliate-view-toggle';
    toggleButton.textContent = 'Show Affiliate View';
    toggleButton.style.position = 'fixed';
    toggleButton.style.bottom = '20px';
    toggleButton.style.right = '20px';
    toggleButton.style.zIndex = '9999';
    toggleButton.style.padding = '8px 12px';
    toggleButton.style.backgroundColor = '#0066cc';
    toggleButton.style.color = 'white';
    toggleButton.style.border = 'none';
    toggleButton.style.borderRadius = '4px';
    toggleButton.style.cursor = 'pointer';
    
    // Add click handler
    toggleButton.addEventListener('click', function() {
        if (document.getElementById('affiliate-view-iframe')) {
            // If iframe exists, remove it
            document.getElementById('affiliate-view-container').remove();
            toggleButton.textContent = 'Show Affiliate View';
        } else {
            // Create affiliate view
            createAffiliateView();
            toggleButton.textContent = 'Close Affiliate View';
        }
    });
    
    document.body.appendChild(toggleButton);
}

/**
 * Create the affiliate view iframe
 */
function createAffiliateView() {
    // Check if iframe already exists
    if (document.getElementById('affiliate-view-iframe')) {
        return;
    }
    
    // Create container
    const container = document.createElement('div');
    container.id = 'affiliate-view-container';
    container.style.position = 'fixed';
    container.style.top = '0';
    container.style.left = '0';
    container.style.width = '100%';
    container.style.height = '100%';
    container.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
    container.style.zIndex = '9998';
    container.style.display = 'flex';
    container.style.justifyContent = 'center';
    container.style.alignItems = 'center';
    
    // Create iframe container
    const iframeContainer = document.createElement('div');
    iframeContainer.style.width = '90%';
    iframeContainer.style.height = '90%';
    iframeContainer.style.backgroundColor = 'white';
    iframeContainer.style.borderRadius = '8px';
    iframeContainer.style.boxShadow = '0 4px 20px rgba(0,0,0,0.5)';
    iframeContainer.style.position = 'relative';
    iframeContainer.style.display = 'flex';
    iframeContainer.style.flexDirection = 'column';
    
    // Create header
    const header = document.createElement('div');
    header.style.padding = '15px';
    header.style.borderBottom = '1px solid #e0e0e0';
    header.style.display = 'flex';
    header.style.justifyContent = 'space-between';
    header.style.alignItems = 'center';
    
    // Header title
    const title = document.createElement('h2');
    title.textContent = 'Affiliate Product View';
    title.style.margin = '0';
    title.style.color = '#333';
    
    // Close button
    const closeButton = document.createElement('button');
    closeButton.textContent = '✕';
    closeButton.style.background = 'none';
    closeButton.style.border = 'none';
    closeButton.style.fontSize = '20px';
    closeButton.style.cursor = 'pointer';
    closeButton.style.color = '#666';
    
    closeButton.addEventListener('click', function() {
        container.remove();
        document.getElementById('affiliate-view-toggle').textContent = 'Show Affiliate View';
    });
    
    header.appendChild(title);
    header.appendChild(closeButton);
    
    // Create iframe
    const iframe = document.createElement('iframe');
    iframe.id = 'affiliate-view-iframe';
    iframe.style.flex = '1';
    iframe.style.width = '100%';
    iframe.style.border = 'none';
    
    // Assemble the UI
    iframeContainer.appendChild(header);
    iframeContainer.appendChild(iframe);
    container.appendChild(iframeContainer);
    document.body.appendChild(container);
    
    // Now populate the iframe with content
    populateAffiliateView(iframe);
}

/**
 * Populate the affiliate view iframe with content and Skimlinks
 */
function populateAffiliateView(iframe) {
    // Get all free model messages
    const freeMessages = document.querySelectorAll('.message.ai-message[data-model-type="free"]');
    
    // Create HTML content for iframe
    let content = `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Affiliate Product View</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    padding: 20px;
                    margin: 0;
                }
                
                .message {
                    background-color: #f9f9f9;
                    border-radius: 10px;
                    padding: 15px;
                    margin-bottom: 20px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }
                
                .message-content {
                    font-size: 16px;
                }
                
                h1 {
                    font-size: 24px;
                    color: #0066cc;
                    margin-top: 0;
                    border-bottom: 1px solid #e0e0e0;
                    padding-bottom: 10px;
                }
                
                p {
                    margin: 0 0 15px;
                }
                
                .test-link {
                    display: inline-block;
                    margin: 10px 0;
                    color: #0066cc;
                    text-decoration: underline;
                }
                
                .no-content {
                    text-align: center;
                    padding: 50px;
                    color: #666;
                }
                
                .info-box {
                    background-color: #e9f7ff;
                    border: 1px solid #0066cc;
                    border-radius: 5px;
                    padding: 15px;
                    margin: 20px 0;
                }
            </style>
        </head>
        <body>
            <h1>AI-Generated Content with Product Links</h1>
            
            <div class="info-box">
                This view shows all free model responses. Brand names like Samsung, Dell, and Sony should be automatically linked.
                <br><br>
                Test link: <a href="http://test.skimlinks.com" class="test-link">Skimlinks Test</a> (click to verify Skimlinks is working)
            </div>
    `;
    
    // Add free model messages to content
    if (freeMessages.length > 0) {
        freeMessages.forEach((message, index) => {
            const messageContent = message.querySelector('.message-content');
            if (messageContent) {
                content += `
                    <div class="message">
                        <div class="message-content">
                            ${messageContent.innerHTML}
                        </div>
                    </div>
                `;
            }
        });
    } else {
        content += `
            <div class="no-content">
                <p>No free model content found. Try sending a message with the free model (preset 6).</p>
            </div>
        `;
    }
    
    // Add Skimlinks script at the end
    content += `
            <script type="text/javascript" src="https://s.skimresources.com/js/44501X1766367.skimlinks.js"></script>
        </body>
        </html>
    `;
    
    // Set content to iframe
    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
    iframeDoc.open();
    iframeDoc.write(content);
    iframeDoc.close();
}