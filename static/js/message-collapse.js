/**
 * Message Collapsing Functionality
 * 
 * This script adds collapsible messages to the chat interface,
 * with an arrow toggle to expand and collapse long messages.
 */

document.addEventListener('DOMContentLoaded', function() {
    const MAX_COLLAPSED_HEIGHT = 200; // Must match CSS max-height for .message-content.collapsible.collapsed
    let observer; // Store observer reference so we can disconnect/reconnect
    
    // Set to track which messages have already been processed
    const processedMessages = new Set();

    /**
     * Initialize truncation for a message element
     * @param {HTMLElement} messageElement - The message container element
     */
    function initializeTruncation(messageElement) {
        // Skip typing messages
        if (messageElement.querySelector('.typing-indicator')) {
            return;
        }
        
        // Skip already processed messages to prevent infinite loops
        const messageId = messageElement.dataset.messageId || messageElement.id || null;
        if (messageId && processedMessages.has(messageId)) {
            return;
        }
        
        // Find the message content element
        const contentElement = messageElement.querySelector('.message-content');
        if (!contentElement) {
            return;
        }

        // Don't process messages already being processed
        if (contentElement.dataset.processingCollapsible === 'true') {
            return;
        }
        
        // Mark as being processed
        contentElement.dataset.processingCollapsible = 'true';
        
        try {
            // Get the parent container for the toggle button
            // Use a consistent approach: prefer immediate parent of content element
            const buttonContainer = contentElement.parentNode;
            
            // Temporarily disconnect observer to prevent feedback loop
            if (observer) {
                observer.disconnect();
            }
            
            // Temporarily remove collapsed state to measure full height
            const wasCollapsed = contentElement.classList.contains('collapsed');
            contentElement.classList.remove('collapsed');
            
            // Save current max-height and temporarily remove it for accurate measurement
            const currentMaxHeight = contentElement.style.maxHeight;
            contentElement.style.maxHeight = 'none';
    
            // Get the full content height
            const scrollHeight = contentElement.scrollHeight;
            
            // Restore previous state and styles
            if (wasCollapsed) {
                contentElement.classList.add('collapsed');
            }
            contentElement.style.maxHeight = currentMaxHeight;
            
            // Only process if message is long enough - prevents unnecessary DOM changes
            if (scrollHeight > MAX_COLLAPSED_HEIGHT + 20) {
                // Check if toggle button already exists
                let toggleButton = messageElement.querySelector('.message-truncate-toggle');
                
                // Add collapsible class if needed
                if (!contentElement.classList.contains('collapsible')) {
                    contentElement.classList.add('collapsible', 'collapsed');
                }
                
                if (!toggleButton) {
                    // Create toggle button
                    toggleButton = document.createElement('button');
                    toggleButton.className = 'message-truncate-toggle';
                    toggleButton.setAttribute('aria-label', 'Toggle message visibility');
                    toggleButton.setAttribute('type', 'button');
                    toggleButton.innerHTML = '<i class="fa-solid fa-chevron-down"></i>';
                    
                    // Insert the button immediately after content
                    contentElement.insertAdjacentElement('afterend', toggleButton);
    
                    // Add click handler - only do this once
                    toggleButton.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        
                        // Disconnect observer temporarily to prevent feedback loop
                        if (observer) observer.disconnect();
                        
                        // Toggle classes for content
                        contentElement.classList.toggle('expanded');
                        contentElement.classList.toggle('collapsed');
                        
                        // Toggle classes for button
                        this.classList.toggle('expanded');
    
                        // Update icon
                        const icon = this.querySelector('i');
                        if (contentElement.classList.contains('expanded')) {
                            icon.classList.remove('fa-chevron-down');
                            icon.classList.add('fa-chevron-up');
                        } else {
                            icon.classList.remove('fa-chevron-up');
                            icon.classList.add('fa-chevron-down');
                        }
                        
                        // Reconnect observer after changes
                        reconnectObserver();
                    });
                }
                
                // Ensure button is visible
                toggleButton.style.display = 'flex';
                
                // Add to processed messages set if we have an ID
                if (messageId) {
                    processedMessages.add(messageId);
                }
            } else {
                // Message is not long enough, remove classes
                contentElement.classList.remove('collapsible', 'collapsed', 'expanded');
                
                // Hide toggle button if it exists
                const toggleButton = messageElement.querySelector('.message-truncate-toggle');
                if (toggleButton) {
                    toggleButton.style.display = 'none';
                }
            }
        } catch (error) {
            console.error('Error in initializeTruncation:', error);
        } finally {
            // Always clear processing flag and reconnect observer
            contentElement.dataset.processingCollapsible = 'false';
            reconnectObserver();
        }
    }
    
    /**
     * Safely reconnect the mutation observer
     */
    function reconnectObserver() {
        // Reconnect using requestAnimationFrame to ensure DOM is settled
        requestAnimationFrame(() => {
            const chatMessagesContainer = document.getElementById('chat-messages');
            if (chatMessagesContainer && observer) {
                observer.observe(chatMessagesContainer, { 
                    childList: true,
                    subtree: true,
                    characterData: false, // Reduce sensitivity - we don't need this
                    attributes: false     // Reduce sensitivity - we don't need this
                });
            }
        });
    }

    /**
     * Process all existing messages
     */
    function processAllMessages() {
        const messages = document.querySelectorAll('.message');
        // Temporarily disconnect observer during bulk processing
        if (observer) observer.disconnect();
        
        messages.forEach(message => {
            // Stagger processing slightly to allow DOM to update
            setTimeout(() => initializeTruncation(message), 10);
        });
        
        // Reconnect observer after all messages processed
        setTimeout(reconnectObserver, 100);
    }

    // Disable older truncation system from script.js if it exists
    if (window.shouldTruncateMessage) {
        // Store the original function
        const originalShouldTruncate = window.shouldTruncateMessage;
        // Replace with a function that always returns false
        window.shouldTruncateMessage = function() {
            return false;
        };
    }

    // Process all messages after DOM is loaded
    setTimeout(processAllMessages, 500);

    // Setup mutation observer with reduced sensitivity
    const chatMessagesContainer = document.getElementById('chat-messages');
    if (chatMessagesContainer) {
        observer = new MutationObserver(function(mutationsList) {
            // Process in batches to avoid rapid re-processing
            let messagesToProcess = new Set();
            
            for (const mutation of mutationsList) {
                // Only handle new nodes - ignore attribute changes
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === 1) { // Element node
                            if (node.classList && node.classList.contains('message')) {
                                messagesToProcess.add(node);
                            } else if (node.querySelector) {
                                // Add any messages inside this node
                                node.querySelectorAll('.message').forEach(msg => {
                                    messagesToProcess.add(msg);
                                });
                            }
                        }
                    });
                }
            }
            
            // Disconnect during batch processing
            observer.disconnect();
            
            // Process discovered messages
            messagesToProcess.forEach(msg => {
                initializeTruncation(msg);
            });
            
            // Reconnect observer
            reconnectObserver();
        });

        // Initial observation - only watch for new nodes, not attribute changes
        observer.observe(chatMessagesContainer, { 
            childList: true,
            subtree: true,
            characterData: false, // Don't observe text content changes
            attributes: false     // Don't observe attribute changes
        });
    }

    // Process messages again when window is resized
    let resizeTimeout;
    window.addEventListener('resize', function() {
        // Debounce the resize event
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(processAllMessages, 300);
    });

    // Run again after full page load
    window.addEventListener('load', function() {
        setTimeout(processAllMessages, 800);
    });

    // Expose for manual calls from other scripts
    window.reinitializeMessageTruncation = processAllMessages;
});