/**
 * Skimlinks Iframe Integration
 * 
 * This script creates a special "Affiliate View" for free model responses,
 * displaying them in a separate iframe that has its own Skimlinks instance.
 * This approach respects how Skimlinks is designed to work - as a page-level script.
 */

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    // Add button to toggle affiliate view mode
    addAffiliateViewToggle();
    
    // Setup message listener for free model messages
    setupFreeModelDetection();
    
    console.log('Skimlinks iframe integration initialized');
});

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
    toggleButton.style.display = 'none'; // Hidden by default, shown when free model content exists
    
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
 * Set up detection for free model messages
 */
function setupFreeModelDetection() {
    // Watch for model selection changes
    const modelPresetContainer = document.querySelector('.model-preset-buttons');
    if (modelPresetContainer) {
        // Create observer to watch for changes to the active preset
        const presetObserver = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes' && 
                    mutation.attributeName === 'class' && 
                    mutation.target.classList.contains('active')) {
                    
                    // A preset button became active
                    const presetId = mutation.target.getAttribute('data-preset-id');
                    const isFreePreset = presetId === '6';
                    
                    // Store this information for later use
                    window.currentlyUsingFreeModel = isFreePreset;
                    console.log('Model preset changed, using free model:', isFreePreset);
                }
            });
        });

        // Start observing preset buttons for changes
        const presetButtons = document.querySelectorAll('.model-preset-btn');
        presetButtons.forEach(button => {
            presetObserver.observe(button, {
                attributes: true,
                attributeFilter: ['class']
            });
            
            // Check initial state
            if (button.classList.contains('active')) {
                const presetId = button.getAttribute('data-preset-id');
                window.currentlyUsingFreeModel = presetId === '6';
                console.log('Initial model state, using free model:', window.currentlyUsingFreeModel);
            }
        });
    }
    
    // Watch for new messages
    const chatMessagesContainer = document.getElementById('chat-messages');
    if (chatMessagesContainer) {
        // Create a mutation observer to watch for new messages
        const messageObserver = new MutationObserver(function(mutations) {
            let hasFreeModelContent = false;
            
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    // Look for newly added AI message elements
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1 && node.classList.contains('message') && 
                            node.classList.contains('ai-message')) {
                            
                            // Check if this is from a free model (preset 6)
                            if (window.currentlyUsingFreeModel) {
                                node.dataset.modelType = 'free';
                                hasFreeModelContent = true;
                            } else {
                                node.dataset.modelType = 'paid';
                            }
                        }
                    });
                }
            });
            
            // If we have free model content, show the toggle button
            if (hasFreeModelContent) {
                const toggleButton = document.getElementById('affiliate-view-toggle');
                if (toggleButton) {
                    toggleButton.style.display = 'block';
                }
            }
        });
        
        // Start observing the chat container for new messages
        messageObserver.observe(chatMessagesContainer, {
            childList: true,
            subtree: false
        });
        
        // Also check for existing free model messages
        const existingFreeModelMessages = checkForExistingFreeModelContent();
        if (existingFreeModelMessages > 0) {
            const toggleButton = document.getElementById('affiliate-view-toggle');
            if (toggleButton) {
                toggleButton.style.display = 'block';
            }
        }
    }
}

/**
 * Check for existing free model content
 */
function checkForExistingFreeModelContent() {
    // Get active preset to determine if free model is selected
    const activeButton = document.querySelector('.model-preset-btn.active');
    if (!activeButton) return 0;
    
    const isFreeModel = activeButton.getAttribute('data-preset-id') === '6';
    
    // Check existing messages
    const messages = document.querySelectorAll('.message.ai-message');
    let freeModelCount = 0;
    
    messages.forEach(message => {
        if (!message.dataset.modelType) {
            // Mark messages based on current model (simplistic approach, but works for initial state)
            message.dataset.modelType = isFreeModel ? 'free' : 'paid';
            
            if (isFreeModel) {
                freeModelCount++;
            }
        } else if (message.dataset.modelType === 'free') {
            freeModelCount++;
        }
    });
    
    return freeModelCount;
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
                This view shows all free model responses. Product mentions should be automatically linked by Skimlinks.
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

/**
 * Debug tool to test affiliate view
 */
window.testAffiliateView = function() {
    // Create some test messages if none exist
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages && chatMessages.querySelectorAll('.message.ai-message[data-model-type="free"]').length === 0) {
        const testMessage = document.createElement('div');
        testMessage.className = 'message ai-message';
        testMessage.dataset.modelType = 'free';
        testMessage.innerHTML = `
            <div class="message-content">
                <p>Here are some popular products you could consider: iPhone for mobile photography, Samsung Galaxy for Android users, 
                MacBook Pro for professional work, a Dell XPS laptop for students, a 4K monitor for design work, 
                Bose noise-canceling headphones for focus, a Sony digital camera for travel, an iPad tablet for reading, and a Kindle for e-books.</p>
                <p>You might also like Nike running shoes for exercise, a Vitamix blender for healthy smoothies, 
                and an Instant Pot for convenient cooking.</p>
            </div>
        `;
        chatMessages.appendChild(testMessage);
    }
    
    // Show the toggle button
    const toggleButton = document.getElementById('affiliate-view-toggle');
    if (toggleButton) {
        toggleButton.style.display = 'block';
    }
    
    // Create affiliate view
    createAffiliateView();
    
    return 'Affiliate view created with test data. Click the "Close Affiliate View" button to dismiss.';
};