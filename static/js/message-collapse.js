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
        // Skip typing messages - don't collapse them
        if (messageElement.querySelector('.typing-indicator')) {
            return;
        }
        
        // Find the message content element
        const contentElement = messageElement.querySelector('.message-content');
        if (!contentElement) return;

        // Get the message wrapper (parent of message-content)
        const wrapperElement = contentElement.closest('.message-wrapper');
        if (!wrapperElement) return;

        // Don't process messages already being processed
        if (contentElement.dataset.processingCollapsible === 'true') return;
        contentElement.dataset.processingCollapsible = 'true';

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
        
        // If the message is long enough to need truncation (with buffer)
        if (scrollHeight > MAX_COLLAPSED_HEIGHT + 20) {
            // Add collapsible classes if not already present
            if (!contentElement.classList.contains('collapsible')) {
                contentElement.classList.add('collapsible', 'collapsed');
            }

            // Check if toggle button already exists
            let toggleButton = wrapperElement.querySelector('.message-truncate-toggle');
            if (!toggleButton) {
                // Create toggle button
                toggleButton = document.createElement('button');
                toggleButton.className = 'message-truncate-toggle';
                toggleButton.setAttribute('aria-label', 'Toggle message visibility');
                toggleButton.innerHTML = '<i class="fa-solid fa-chevron-down"></i>';
                
                // Insert button after content element
                contentElement.insertAdjacentElement('afterend', toggleButton);

                // Add click handler
                toggleButton.addEventListener('click', function(e) {
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
                });
            }
            // Ensure button is visible
            toggleButton.style.display = 'flex';
        } else {
            // If message is not long enough, remove classes and hide button
            contentElement.classList.remove('collapsible', 'collapsed', 'expanded');
            
            let toggleButton = wrapperElement.querySelector('.message-truncate-toggle');
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
        document.querySelectorAll('.message').forEach(initializeTruncation);
    }

    // Process all messages on page load
    // Use small timeout to ensure DOM is fully ready and any dynamically added messages are present
    setTimeout(processAllMessages, 500);

    // Also handle when new content is added to existing messages (streaming)
    // Handle dynamically added messages using MutationObserver
    const chatMessagesContainer = document.getElementById('chat-messages');
    if (chatMessagesContainer) {
        const observer = new MutationObserver(function(mutationsList) {
            for (const mutation of mutationsList) {
                // For node additions (new messages)
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === 1) { // Element node
                            if (node.classList.contains('message')) {
                                // Wait a tiny bit for content to settle
                                setTimeout(() => initializeTruncation(node), 100);
                            } else if (node.querySelector) {
                                // Look for messages inside the added node
                                const messagesInside = node.querySelectorAll('.message');
                                messagesInside.forEach(msg => {
                                    setTimeout(() => initializeTruncation(msg), 100);
                                });
                            }
                        }
                    });
                }
                // For content changes in existing nodes
                else if (mutation.type === 'characterData' || mutation.type === 'attributes') {
                    // Find the nearest message container
                    let messageElement = mutation.target;
                    while (messageElement && !messageElement.classList?.contains('message')) {
                        messageElement = messageElement.parentElement;
                    }
                    
                    if (messageElement) {
                        // Delay slightly to allow content to settle
                        setTimeout(() => initializeTruncation(messageElement), 100);
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

    // Also process messages again when the window is resized,
    // as this can change the height requirements
    window.addEventListener('resize', function() {
        // Debounce the resize event
        if (this.resizeTimeout) clearTimeout(this.resizeTimeout);
        this.resizeTimeout = setTimeout(processAllMessages, 300);
    });

    // Expose for manual calls from other scripts
    window.reinitializeMessageTruncation = processAllMessages;
});