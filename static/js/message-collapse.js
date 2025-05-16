/**
 * Message Collapsing Functionality
 * 
 * This script adds collapsible messages to the chat interface,
 * with an arrow toggle to expand and collapse long messages.
 */

document.addEventListener('DOMContentLoaded', function() {
    const MAX_COLLAPSED_HEIGHT = 200; // Must match CSS max-height for .message-content.collapsible.collapsed

    /**
     * Initialize truncation for a message element
     * @param {HTMLElement} messageElement - The message container element
     */
    function initializeTruncation(messageElement) {
        // Skip typing messages and messages that are being processed
        if (messageElement.querySelector('.typing-indicator')) {
            return;
        }
        
        // Find the message content element
        const contentElement = messageElement.querySelector('.message-content');
        if (!contentElement) {
            console.log('Message content element not found', messageElement);
            return;
        }

        // Don't process messages already being processed
        if (contentElement.dataset.processingCollapsible === 'true') return;
        contentElement.dataset.processingCollapsible = 'true';
        
        // Get the parent container for the toggle button
        // Try to find message-wrapper, fall back to message element or content's parent
        let buttonContainer = messageElement.querySelector('.message-wrapper') || 
                             contentElement.parentNode || 
                             messageElement;

        // Temporarily remove collapsed state to measure full height
        const wasCollapsed = contentElement.classList.contains('collapsed');
        contentElement.classList.remove('collapsed');
        
        // Save current max-height and temporarily remove it for accurate measurement
        const currentMaxHeight = contentElement.style.maxHeight;
        contentElement.style.maxHeight = 'none';

        // Get the full content height
        const scrollHeight = contentElement.scrollHeight;
        console.log('Message height:', scrollHeight, 'threshold:', MAX_COLLAPSED_HEIGHT);
        
        // Restore previous state and styles
        if (wasCollapsed) {
            contentElement.classList.add('collapsed');
        }
        contentElement.style.maxHeight = currentMaxHeight;
        
        // If the message is long enough to need truncation (with buffer)
        if (scrollHeight > MAX_COLLAPSED_HEIGHT + 20) {
            console.log('Message needs truncation');
            // Add collapsible classes if not already present
            if (!contentElement.classList.contains('collapsible')) {
                contentElement.classList.add('collapsible', 'collapsed');
            }

            // Check if toggle button already exists in any parent container
            let toggleButton = messageElement.querySelector('.message-truncate-toggle');
            if (!toggleButton) {
                // Create toggle button
                toggleButton = document.createElement('button');
                toggleButton.className = 'message-truncate-toggle';
                toggleButton.setAttribute('aria-label', 'Toggle message visibility');
                toggleButton.setAttribute('type', 'button'); // Ensure it's a button type
                toggleButton.innerHTML = '<i class="fa-solid fa-chevron-down"></i>';
                
                // Insert button after content element or at the end of the message
                if (buttonContainer === contentElement.parentNode) {
                    contentElement.insertAdjacentElement('afterend', toggleButton);
                } else {
                    buttonContainer.appendChild(toggleButton);
                }

                // Add click handler
                toggleButton.addEventListener('click', function(e) {
                    console.log('Toggle button clicked');
                    e.preventDefault(); // Prevent default button behavior
                    e.stopPropagation(); // Prevent event bubbling
                    
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
                    
                    // Log current state for debugging
                    console.log('Message expanded state:', contentElement.classList.contains('expanded'));
                });
            }
            // Ensure button is visible and properly styled
            toggleButton.style.display = 'flex';
            toggleButton.style.visibility = 'visible';
            toggleButton.style.opacity = '1';
        } else {
            // If message is not long enough, remove classes and hide button
            contentElement.classList.remove('collapsible', 'collapsed', 'expanded');
            
            let toggleButton = messageElement.querySelector('.message-truncate-toggle');
            if (toggleButton) {
                toggleButton.style.display = 'none';
            }
        }
        
        // Clear processing flag
        contentElement.dataset.processingCollapsible = 'false';
    }

    /**
     * Process all existing messages
     */
    function processAllMessages() {
        console.log('Processing all messages for collapsible state');
        const messages = document.querySelectorAll('.message');
        console.log(`Found ${messages.length} messages to process`);
        messages.forEach(initializeTruncation);
    }

    // Disable older truncation system from script.js if it exists
    if (window.shouldTruncateMessage) {
        console.log('Disabling older truncation system');
        // Store the original function
        const originalShouldTruncate = window.shouldTruncateMessage;
        // Replace with a function that always returns false
        window.shouldTruncateMessage = function() {
            return false;
        };
    }

    // Process all messages after a short delay to ensure DOM is fully loaded
    setTimeout(processAllMessages, 800);

    // Handle dynamically added messages using MutationObserver
    const chatMessagesContainer = document.getElementById('chat-messages');
    if (chatMessagesContainer) {
        console.log('Setting up mutation observer for chat messages');
        const observer = new MutationObserver(function(mutationsList) {
            for (const mutation of mutationsList) {
                // For node additions (new messages)
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === 1) { // Element node
                            if (node.classList && node.classList.contains('message')) {
                                // Wait a bit for content to settle
                                setTimeout(() => initializeTruncation(node), 300);
                            } else if (node.querySelector) {
                                // Look for messages inside the added node
                                const messagesInside = node.querySelectorAll('.message');
                                messagesInside.forEach(msg => {
                                    setTimeout(() => initializeTruncation(msg), 300);
                                });
                            }
                        }
                    });
                }
                // For content changes in existing nodes
                else if (mutation.type === 'characterData' || mutation.type === 'attributes') {
                    // Find the nearest message container
                    let messageElement = mutation.target;
                    while (messageElement && (!messageElement.classList || !messageElement.classList.contains('message'))) {
                        messageElement = messageElement.parentElement;
                    }
                    
                    if (messageElement) {
                        // Delay to allow content to settle
                        setTimeout(() => initializeTruncation(messageElement), 300);
                    }
                }
            }
        });

        // Observe both child additions/removals and content changes
        observer.observe(chatMessagesContainer, { 
            childList: true,
            subtree: true,
            characterData: true,
            attributes: true
        });
    }

    // Process messages again when the window is resized
    window.addEventListener('resize', function() {
        // Debounce the resize event
        if (this.resizeTimeout) clearTimeout(this.resizeTimeout);
        this.resizeTimeout = setTimeout(processAllMessages, 300);
    });

    // Run again after the page has fully loaded to catch any missing messages
    window.addEventListener('load', function() {
        setTimeout(processAllMessages, 1000);
    });

    // Expose for manual calls from other scripts
    window.reinitializeMessageTruncation = processAllMessages;
});