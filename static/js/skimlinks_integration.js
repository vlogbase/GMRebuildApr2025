/**
 * Skimlinks Integration
 * 
 * This script handles integration with Skimlinks for affiliate linking,
 * specifically targeting free model responses (preset 6) to monetize them.
 */

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    // Check if Skimlinks script is loaded
    const skimlinksLoaded = typeof window.skimlinks !== 'undefined';
    console.warn('SKIMLINKS INTEGRATION: Initialized, script loaded:', skimlinksLoaded);
    
    // Log more details about what's available from Skimlinks
    console.warn('SKIMLINKS DEBUG: window.skimlinks exists:', typeof window.skimlinks !== 'undefined');
    console.warn('SKIMLINKS DEBUG: window._skimlinks exists:', typeof window._skimlinks !== 'undefined');
    console.warn('SKIMLINKS DEBUG: window.skimlinksAPI exists:', typeof window.skimlinksAPI !== 'undefined');

    // Global variables
    let processingQueue = [];
    let processingInProgress = false;
    let skimlinksObserver = null;
    let messageObserver = null;

    /**
     * Initialize Skimlinks observers and handlers
     */
    function initSkimlinks() {
        // Track initialization to prevent multiple runs
        if (document.skimlinksInitialized) {
            console.warn('SKIMLINKS DEBUG: Already initialized, skipping');
            return;
        }
        document.skimlinksInitialized = true;
        
        console.warn('SKIMLINKS DEBUG: Initializing Skimlinks integration');
        
        // Check if Skimlinks is available at initialization time
        const skimlinksAvailable = typeof window.skimlinks !== 'undefined';
        const skimlinksAPIAvailable = typeof window.skimlinksAPI !== 'undefined';
        const _skimlinksAvailable = typeof window._skimlinks !== 'undefined';
        
        console.warn('SKIMLINKS DEBUG: API availability check:', {
            'window.skimlinks': skimlinksAvailable,
            'window.skimlinksAPI': skimlinksAPIAvailable,
            'window._skimlinks': _skimlinksAvailable
        });
        
        // Store API availability globally for other functions to check
        document.skimlinksApiAvailable = skimlinksAvailable || skimlinksAPIAvailable || _skimlinksAvailable;
        
        // Create an observer to watch for new AI messages in the chat
        initMessageObserver();

        // Find any existing free model messages and process them
        processExistingFreeMessages();

        // Hook into the sendMessage function to mark messages from free models
        hookIntoMessageHandling();

        console.warn('SKIMLINKS DEBUG: Integration setup complete');
    }

    /**
     * Initialize the observer that watches for new messages
     */
    function initMessageObserver() {
        // Get the chat messages container
        const chatMessagesContainer = document.getElementById('chat-messages');
        if (!chatMessagesContainer) {
            console.log('Chat messages container not found, observer not initialized');
            return;
        }

        // Create a mutation observer to watch for new messages
        messageObserver = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    // Look for newly added AI message elements
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1 && node.classList.contains('message') && 
                            node.classList.contains('ai-message')) {
                            
                            // Check if this is from a free model
                            checkAndProcessMessage(node);
                        }
                    });
                }
            });
        });

        // Start observing the chat container for new messages
        messageObserver.observe(chatMessagesContainer, {
            childList: true,
            subtree: false
        });

        console.log('Message observer initialized');
    }

    /**
     * Process any existing free model messages that are already in the DOM
     */
    function processExistingFreeMessages() {
        // Get the currently selected model
        const activePresetButton = document.querySelector('.model-preset-btn.active');
        if (!activePresetButton) return;

        const presetId = activePresetButton.getAttribute('data-preset-id');
        const isFreePreset = presetId === '6';

        // If current preset is not free, no need to process existing messages
        if (!isFreePreset) return;

        // Find all AI messages in the chat
        const aiMessages = document.querySelectorAll('.message.ai-message');
        if (aiMessages.length === 0) return;

        console.log(`Found ${aiMessages.length} existing AI messages to check for Skimlinks processing`);
        
        // Process each message
        aiMessages.forEach(message => {
            // Mark as from free model and queue for processing
            message.dataset.modelType = 'free';
            queueMessageForProcessing(message);
        });
    }

    /**
     * Hook into the message handling functions to mark messages from free models
     */
    function hookIntoMessageHandling() {
        // We'll use a mutation observer to look for changes to the preset buttons
        // This way we can determine if the active model is a free model
        const modelPresetContainer = document.querySelector('.model-preset-buttons');
        if (!modelPresetContainer) return;

        // Create observer to watch for changes to the active preset
        const presetObserver = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes' && 
                    mutation.attributeName === 'class' && 
                    mutation.target.classList.contains('active')) {
                    
                    // A preset button became active
                    const presetId = mutation.target.getAttribute('data-preset-id');
                    const isFreePreset = presetId === '6';
                    
                    // Store this information for later use when processing messages
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

    /**
     * Check if a message is from a free model and process it if needed
     */
    function checkAndProcessMessage(messageElement) {
        console.warn("SKIMLINKS DEBUG: Checking message element:", messageElement);
        
        // First, check if the message already has a model type
        if (messageElement.dataset.modelType) {
            console.warn("SKIMLINKS DEBUG: Message has model type:", messageElement.dataset.modelType);
            
            // If already processed or marked as non-free, skip
            if (messageElement.dataset.skimlinksProcessed === 'true' || 
                messageElement.dataset.modelType !== 'free') {
                console.warn("SKIMLINKS DEBUG: Message already processed or not free, skipping");
                return;
            }
        } else {
            // If no model type yet, determine based on current model
            const isFreeModel = window.currentlyUsingFreeModel === true;
            console.warn("SKIMLINKS DEBUG: Setting model type based on currentlyUsingFreeModel:", isFreeModel);
            
            messageElement.dataset.modelType = isFreeModel ? 'free' : 'paid';
            
            // If not a free model message, no need to process
            if (!isFreeModel) {
                console.warn("SKIMLINKS DEBUG: Not a free model message, skipping");
                return;
            }
        }

        console.warn("SKIMLINKS DEBUG: Message is from free model, queueing for processing");
        // Queue this message for processing
        queueMessageForProcessing(messageElement);
    }

    /**
     * Queue a message for Skimlinks processing
     */
    function queueMessageForProcessing(messageElement) {
        // Find the message content element
        const messageContent = messageElement.querySelector('.message-content');
        if (!messageContent) return;

        // Only process if it has actual content and hasn't been processed
        if (messageContent.innerHTML.trim() && 
            !messageElement.dataset.skimlinksProcessed) {
            
            // Add to processing queue
            processingQueue.push(messageElement);
            console.log('Queued message for Skimlinks processing');
            
            // Start processing queue if not already in progress
            if (!processingInProgress) {
                processNextInQueue();
            }
        }
    }

    /**
     * Process the next message in the queue
     */
    function processNextInQueue() {
        if (processingQueue.length === 0) {
            processingInProgress = false;
            return;
        }

        processingInProgress = true;
        const messageElement = processingQueue.shift();
        
        // Skip if already processed
        if (messageElement.dataset.skimlinksProcessed === 'true') {
            processNextInQueue();
            return;
        }

        console.log('Processing message with Skimlinks');
        processMessageWithSkimlinks(messageElement);
    }

    /**
     * Process a message element with Skimlinks and handle completion
     */
    function processMessageWithSkimlinks(messageElement) {
        // Mark as being processed
        messageElement.dataset.skimlinksProcessing = 'true';
        
        // Find the message content
        const messageContent = messageElement.querySelector('.message-content');
        if (!messageContent) {
            messageElement.dataset.skimlinksProcessed = 'true';
            processNextInQueue();
            return;
        }

        // Try adding our own affiliate links as a fallback method
        const contentHTML = messageContent.innerHTML;
        
        // List of common product keywords and their affiliate links
        const affiliateLinks = {
            'iphone': 'https://www.amazon.com/s?k=iphone&linkCode=ll2&tag=skimlinks_replacement&linkId=123456',
            'samsung': 'https://www.amazon.com/s?k=samsung&linkCode=ll2&tag=skimlinks_replacement&linkId=123456',
            'macbook': 'https://www.amazon.com/s?k=macbook&linkCode=ll2&tag=skimlinks_replacement&linkId=123456',
            'laptop': 'https://www.amazon.com/s?k=laptop&linkCode=ll2&tag=skimlinks_replacement&linkId=123456',
            'monitor': 'https://www.amazon.com/s?k=monitor&linkCode=ll2&tag=skimlinks_replacement&linkId=123456',
            'headphones': 'https://www.amazon.com/s?k=headphones&linkCode=ll2&tag=skimlinks_replacement&linkId=123456',
            'camera': 'https://www.amazon.com/s?k=camera&linkCode=ll2&tag=skimlinks_replacement&linkId=123456',
            'tablet': 'https://www.amazon.com/s?k=tablet&linkCode=ll2&tag=skimlinks_replacement&linkId=123456',
            'kindle': 'https://www.amazon.com/s?k=kindle&linkCode=ll2&tag=skimlinks_replacement&linkId=123456'
        };
        
        // Simple direct linking approach - replace product keywords with links
        let processedHTML = contentHTML;
        let madeChanges = false;
        
        Object.keys(affiliateLinks).forEach(keyword => {
            const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
            if (regex.test(processedHTML)) {
                processedHTML = processedHTML.replace(regex, `<a href="${affiliateLinks[keyword]}" target="_blank" rel="nofollow noopener" data-manual-affiliate="true">$&</a>`);
                madeChanges = true;
                console.warn(`SKIMLINKS DEBUG: Added manual affiliate link for "${keyword}"`);
            }
        });
        
        if (madeChanges) {
            messageContent.innerHTML = processedHTML;
            console.warn('SKIMLINKS DEBUG: Applied manual affiliate links, forcing repaint');
            forceRepaint(messageContent);
            repaintApplied = true;
            
            // Mark as processed
            messageElement.dataset.skimlinksProcessed = 'true';
            messageElement.dataset.skimlinksProcessing = 'false';
            
            // Move to next in queue
            setTimeout(processNextInQueue, 100);
            return;
        }
        
        // Continue with normal Skimlinks integration if manual linking didn't make changes
        // Set a flag to track if we've done a repaint
        let repaintApplied = false;
        
        // Set up mutation observer to watch for Skimlinks link additions
        if (!skimlinksObserver) {
            skimlinksObserver = new MutationObserver(function(mutations) {
                if (repaintApplied) return;
                
                // Check for Skimlinks link additions
                for (const mutation of mutations) {
                    // Check for direct link additions in this mutation
                    if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                        const hasSkimlinksNode = Array.from(mutation.addedNodes).some(node => {
                            if (node.nodeName === 'A') {
                                return node.href && (
                                    node.href.includes('go.skimresources.com') || 
                                    node.hasAttribute('data-skimlinks') ||
                                    node.hasAttribute('data-skimwords')
                                );
                            } else if (node.nodeType === 1) {
                                // Check for Skimlinks inside added nodes
                                return node.querySelector && node.querySelector(
                                    'a[href*="go.skimresources.com"], a[data-skimlinks], a[data-skimwords]'
                                );
                            }
                            return false;
                        });
                        
                        if (hasSkimlinksNode) {
                            console.log('Skimlinks link detected (added node), applying repaint');
                            forceRepaint(messageContent);
                            repaintApplied = true;
                            
                            // Mark as processed
                            messageElement.dataset.skimlinksProcessed = 'true';
                            messageElement.dataset.skimlinksProcessing = 'false';
                            
                            // Move to next in queue
                            setTimeout(processNextInQueue, 100);
                            break;
                        }
                    }
                    
                    // Check for attribute changes that indicate Skimlinks processing
                    if (mutation.type === 'attributes' && 
                        mutation.target.nodeName === 'A' && 
                        (mutation.attributeName === 'href' || 
                         mutation.attributeName === 'data-skimlinks' ||
                         mutation.attributeName === 'data-skimwords')) {
                        
                        const link = mutation.target;
                        if (link.href && link.href.includes('go.skimresources.com') || 
                            link.hasAttribute('data-skimlinks') || 
                            link.hasAttribute('data-skimwords')) {
                            
                            console.log('Skimlinks link detected (attribute change), applying repaint');
                            forceRepaint(messageContent);
                            repaintApplied = true;
                            
                            // Mark as processed
                            messageElement.dataset.skimlinksProcessed = 'true';
                            messageElement.dataset.skimlinksProcessing = 'false';
                            
                            // Move to next in queue
                            setTimeout(processNextInQueue, 100);
                            break;
                        }
                    }
                }
            });
        }
        
        // Start observing this message for Skimlinks modifications
        skimlinksObserver.observe(messageContent, { 
            childList: true, 
            subtree: true,
            attributes: true,
            attributeFilter: ['href', 'data-skimlinks']
        });
        
        // Trigger Skimlinks processing if the API is available
        if (typeof window.skimlinks !== 'undefined') {
            console.warn('SKIMLINKS DEBUG: Using Skimlinks API to process content');
            
            // Try different methods to activate Skimlinks on this content
            try {
                // First try the publisher.linkizeContent method if available
                if (window.skimlinks.publisher && typeof window.skimlinks.publisher.linkizeContent === 'function') {
                    console.warn('SKIMLINKS DEBUG: Using publisher.linkizeContent()');
                    window.skimlinks.publisher.linkizeContent();
                } 
                // Then try to trigger skimlinks by assigning to the global variable
                else if (typeof window._skimlinks === 'function') {
                    console.warn('SKIMLINKS DEBUG: Using _skimlinks() function with specific element');
                    window._skimlinks(messageContent);
                }
                // Try the skimlinksAPI if it exists
                else if (window.skimlinksAPI) {
                    if (typeof window.skimlinksAPI.scanAndLinkify === 'function') {
                        console.warn('SKIMLINKS DEBUG: Using skimlinksAPI.scanAndLinkify()');
                        window.skimlinksAPI.scanAndLinkify();
                    } else if (typeof window.skimlinksAPI.link === 'function') {
                        console.warn('SKIMLINKS DEBUG: Using skimlinksAPI.link()');
                        window.skimlinksAPI.link();
                    }
                }
                // Try a direct approach by cloning and replacing - sometimes this triggers Skimlinks
                else {
                    console.warn('SKIMLINKS DEBUG: No API methods found, trying direct DOM manipulation');
                    const originalContent = messageContent.innerHTML;
                    
                    // Add a marker class for Skimlinks to recognize
                    messageContent.classList.add('skimlinks-target');
                    
                    // First try: Insert sample affiliate text to see if Skimlinks activates at all
                    const sampleText = "Check out these products: iPhone, Samsung Galaxy, Amazon Echo, Nike shoes";
                    const testElem = document.createElement('div');
                    testElem.style.display = 'none';
                    testElem.classList.add('skimlinks-test-target');
                    testElem.innerHTML = sampleText;
                    document.body.appendChild(testElem);
                    
                    // Clone and replace technique often triggers Skimlinks
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = originalContent;
                    
                    // Force a content replacement that might trigger Skimlinks
                    messageContent.innerHTML = '';
                    setTimeout(() => {
                        // Re-add the content
                        messageContent.innerHTML = tempDiv.innerHTML;
                        
                        // Force another round of DOM modification to try to trigger Skimlinks
                        setTimeout(() => {
                            // If by this point the message doesn't have Skimlinks links,
                            // let's add a class that might trigger a Skimlinks rescan
                            if (!messageContent.querySelector('a[href*="go.skimresources.com"]')) {
                                console.warn('SKIMLINKS DEBUG: Still no links, adding skimlinks-unprocessed class');
                                messageContent.classList.add('skimlinks-unprocessed');
                                
                                // Create a fake user interaction event to trigger Skimlinks
                                messageContent.dispatchEvent(new Event('mouseover', { bubbles: true }));
                                messageContent.dispatchEvent(new Event('mouseenter', { bubbles: true }));
                            }
                        }, 200);
                    }, 100);
                }
                
                console.warn('SKIMLINKS DEBUG: Skimlinks processing triggered');
            } catch (e) {
                console.error('Error using Skimlinks API:', e);
            }
        } else {
            console.warn('SKIMLINKS DEBUG: Skimlinks API not available');
        }
        
        // Fallback timeout in case observer doesn't trigger
        setTimeout(() => {
            if (!repaintApplied) {
                console.log('Applying fallback repaint after Skimlinks timeout');
                forceRepaint(messageContent);
                
                // Mark as processed
                messageElement.dataset.skimlinksProcessed = 'true';
                messageElement.dataset.skimlinksProcessing = 'false';
                
                // Move to next in queue
                processNextInQueue();
            }
        }, 3000); // 3 second fallback
    }

    /**
     * Force a browser repaint on an element
     * This is a copy of the function from script.js
     */
    function forceRepaint(element) {
        if (!element) {
            console.warn('forceRepaint called with null/undefined element');
            return;
        }
        
        // Read layout property to force layout calculation
        const currentHeight = element.offsetHeight;
        // Force a style recalculation with a more substantial change
        element.style.transform = 'translateZ(0)';
        // Use requestAnimationFrame to ensure it processes in the next paint cycle
        requestAnimationFrame(() => {
            element.style.transform = '';
        });
        
        console.debug(`Skimlinks: forceRepaint applied to element: ${element.className || 'unnamed'}`);
    }

    // Add a global debug function to trigger Skimlinks processing and test manual linking
    window.forceSkimlinksProcessing = function() {
        console.warn('SKIMLINKS DEBUG: Manually forcing Skimlinks processing on all free model messages');
        
        // Find all free model messages
        const freeMessages = document.querySelectorAll('.message.ai-message[data-model-type="free"]');
        console.warn(`SKIMLINKS DEBUG: Found ${freeMessages.length} free model messages to process`);
        
        freeMessages.forEach(message => {
            // Reset processing state to force reprocessing
            message.dataset.skimlinksProcessed = 'false';
            message.dataset.skimlinksProcessing = 'false';
            
            // Queue for processing
            queueMessageForProcessing(message);
        });
        
        // Create a test for manual affiliate linking
        console.warn('SKIMLINKS DEBUG: Testing manual affiliate linking system');
        
        // Create a temporary message with test content containing product keywords
        const testManualMessage = document.createElement('div');
        testManualMessage.className = 'message ai-message';
        testManualMessage.dataset.modelType = 'free';
        testManualMessage.innerHTML = `
            <div class="message-content">
                <p>Here are some popular products you could consider: iPhone for mobile photography, Samsung for Android users, 
                MacBook for professional work, a good laptop for students, a high-resolution monitor for design work, 
                noise-canceling headphones for focus, a digital camera for travel, a tablet for reading, and a Kindle for e-books.</p>
            </div>
        `;
        document.body.appendChild(testManualMessage);
        
        // Apply manual processing to the test message
        const messageContent = testManualMessage.querySelector('.message-content');
        if (messageContent) {
            const contentHTML = messageContent.innerHTML;
            
            // List of common product keywords and their affiliate links - copied from message processor
            const affiliateLinks = {
                'iphone': 'https://www.amazon.com/s?k=iphone&linkCode=ll2&tag=skimlinks_replacement&linkId=123456',
                'samsung': 'https://www.amazon.com/s?k=samsung&linkCode=ll2&tag=skimlinks_replacement&linkId=123456',
                'macbook': 'https://www.amazon.com/s?k=macbook&linkCode=ll2&tag=skimlinks_replacement&linkId=123456',
                'laptop': 'https://www.amazon.com/s?k=laptop&linkCode=ll2&tag=skimlinks_replacement&linkId=123456',
                'monitor': 'https://www.amazon.com/s?k=monitor&linkCode=ll2&tag=skimlinks_replacement&linkId=123456',
                'headphones': 'https://www.amazon.com/s?k=headphones&linkCode=ll2&tag=skimlinks_replacement&linkId=123456',
                'camera': 'https://www.amazon.com/s?k=camera&linkCode=ll2&tag=skimlinks_replacement&linkId=123456',
                'tablet': 'https://www.amazon.com/s?k=tablet&linkCode=ll2&tag=skimlinks_replacement&linkId=123456',
                'kindle': 'https://www.amazon.com/s?k=kindle&linkCode=ll2&tag=skimlinks_replacement&linkId=123456'
            };
            
            // Simple direct linking approach - replace product keywords with links
            let processedHTML = contentHTML;
            let linkCount = 0;
            
            Object.keys(affiliateLinks).forEach(keyword => {
                const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
                if (regex.test(processedHTML)) {
                    processedHTML = processedHTML.replace(regex, `<a href="${affiliateLinks[keyword]}" target="_blank" rel="nofollow noopener" data-manual-affiliate="true" style="color: #0066cc; text-decoration: underline;">$&</a>`);
                    linkCount++;
                    console.warn(`SKIMLINKS DEBUG: Added manual affiliate link for "${keyword}"`);
                }
            });
            
            if (linkCount > 0) {
                messageContent.innerHTML = processedHTML;
                console.warn(`SKIMLINKS DEBUG: Applied ${linkCount} manual affiliate links to test message`);
                forceRepaint(messageContent);
                
                // Add visual indication that this is a test
                const testLabel = document.createElement('div');
                testLabel.style.background = '#f8f9fa';
                testLabel.style.color = '#666';
                testLabel.style.padding = '4px 8px';
                testLabel.style.marginTop = '8px';
                testLabel.style.borderRadius = '4px';
                testLabel.style.fontSize = '12px';
                testLabel.innerHTML = 'TEST MESSAGE: Manual affiliate links applied';
                messageContent.appendChild(testLabel);
            } else {
                console.warn('SKIMLINKS DEBUG: No keywords found in test message');
            }
        }
        
        // Also try standard Skimlinks processing on a separate test message
        console.warn('SKIMLINKS DEBUG: Adding test messages with product keywords for Skimlinks API test');
        
        // Create a temporary message with product keywords
        const testSkimlinksMessage = document.createElement('div');
        testSkimlinksMessage.className = 'skimlinks-test-message';
        testSkimlinksMessage.innerHTML = `
            <div class="message-content">
                <p>Here are some popular products: iPhone 15 Pro, Samsung Galaxy S23, Sony PlayStation 5, 
                Nike Air Max, Amazon Echo, Apple MacBook Pro, Nintendo Switch, Dyson Vacuum.</p>
            </div>
        `;
        document.body.appendChild(testSkimlinksMessage);
        
        // Try to apply Skimlinks to this test element
        if (window.skimlinks && window.skimlinks.publisher) {
            console.warn('SKIMLINKS DEBUG: Using publisher API on test message');
            window.skimlinks.publisher.linkizeContent();
        } else if (window._skimlinks) {
            console.warn('SKIMLINKS DEBUG: Using _skimlinks function on test message');
            window._skimlinks(testSkimlinksMessage);
        }
        
        // Check if any links were created by Skimlinks
        setTimeout(() => {
            const createdLinks = testSkimlinksMessage.querySelectorAll('a[href*="go.skimresources.com"]');
            console.warn(`SKIMLINKS DEBUG: Test message generated ${createdLinks.length} Skimlinks links`);
            
            // Clean up test messages after 10 seconds
            setTimeout(() => {
                if (testSkimlinksMessage.parentNode) {
                    testSkimlinksMessage.parentNode.removeChild(testSkimlinksMessage);
                }
                if (testManualMessage.parentNode) {
                    testManualMessage.parentNode.removeChild(testManualMessage);
                }
            }, 10000);
        }, 1000);
        
        return 'Skimlinks and manual linking tests started - check your page for test messages and console for results';
    };
    
    // Wait for Skimlinks to load before initializing
    // First attempt after a short delay
    setTimeout(() => {
        const skimlinksLoaded = typeof window.skimlinks !== 'undefined';
        console.warn('SKIMLINKS DEBUG: First load check, script loaded:', skimlinksLoaded);
        
        if (skimlinksLoaded) {
            initSkimlinks();
        } else {
            // If not loaded yet, try again after a longer delay
            console.warn('SKIMLINKS DEBUG: Script not loaded yet, will try again in 2 seconds');
            setTimeout(() => {
                const retryLoaded = typeof window.skimlinks !== 'undefined';
                console.warn('SKIMLINKS DEBUG: Second load check, script loaded:', retryLoaded);
                initSkimlinks();
            }, 2000);
        }
    }, 500);
    
    // Force initialization after a maximum wait time, regardless of script load state
    setTimeout(() => {
        const finalCheck = typeof window.skimlinks !== 'undefined';
        console.warn('SKIMLINKS DEBUG: Final load check, script loaded:', finalCheck);
        
        if (!document.skimlinksInitialized) {
            console.warn('SKIMLINKS DEBUG: Forcing initialization after timeout');
            initSkimlinks();
        }
        
        // Add another attempt to trigger Skimlinks on all content after full page load
        setTimeout(() => {
            console.warn('SKIMLINKS DEBUG: Trying final attempt to process all page content with Skimlinks');
            if (window.skimlinks && window.skimlinks.publisher) {
                window.skimlinks.publisher.linkizeContent();
            }
        }, 2000);
    }, 5000);
});