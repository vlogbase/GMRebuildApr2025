/**
 * Message Collapsing Functionality - Improved Version
 * 
 * This script adds collapsible messages to the chat interface,
 * with an arrow toggle to expand and collapse long messages.
 * 
 * Features:
 * - Handles dynamic content
 * - Prevents infinite mutation observer loops
 * - Works on both desktop and mobile devices
 * - Has failsafes to prevent UI breakage
 */

(function() {
    // Enforce running only once
    if (window.messageCollapseInitialized) return;
    window.messageCollapseInitialized = true;
    
    // Configuration
    const MAX_COLLAPSED_HEIGHT = 200; // Must match CSS max-height for .message-content.collapsible.collapsed
    const DEBOUNCE_TIME = 250; // Debounce time for events in ms
    
    // State
    let observer = null; // Store observer reference so we can disconnect/reconnect
    let observerActive = false; // Track if observer is active
    let observerPaused = false; // Track if observer is intentionally paused
    let processingContentId = null; // Store ID of content being processed
    
    // Set to track processed messages to prevent duplicate processing 
    const processedMessages = new Set();
    const collapsibleMessages = new Set(); // Track actually collapsible messages
    
    /**
     * Safe wrapper for DOM operations to avoid cascading errors
     */
    function safeDOM(fn, fallback) {
        try {
            return fn();
        } catch (error) {
            console.error('[Message Collapse] DOM operation failed:', error);
            return fallback;
        }
    }
    
    /**
     * Safely disconnect the observer to prevent feedback loops
     */
    function safeDisconnect() {
        if (observer && observerActive) {
            observer.disconnect();
            observerActive = false;
        }
    }
    
    /**
     * Safely reconnect the observer when it's safe to do so
     */
    function safeReconnect() {
        if (observerPaused || !observer) return;
        
        // Use RAF to ensure DOM is settled before reconnecting
        requestAnimationFrame(() => {
            const chatMessagesContainer = document.getElementById('chat-messages');
            if (chatMessagesContainer && observer && !observerActive) {
                observer.observe(chatMessagesContainer, { 
                    childList: true,    // Watch for new messages
                    subtree: true,      // Look inside added nodes
                    characterData: false, // Don't watch for text changes (reduces events)
                    attributes: false     // Don't watch for attribute changes (reduces events)
                });
                observerActive = true;
            }
        });
    }
    
    /**
     * Process a single message for collapsibility
     * @param {HTMLElement} messageElement - The message container element
     * @returns {boolean} - Whether the message was processed
     */
    function processMessage(messageElement) {
        // Skip invalid elements and typing indicators
        if (!messageElement || 
            !messageElement.classList || 
            messageElement.querySelector('.typing-indicator')) {
            return false;
        }
        
        // Skip already processed messages to prevent loops
        const messageId = messageElement.dataset.messageId || messageElement.id || 
                          `msg-${Date.now()}-${Math.floor(Math.random() * 10000)}`;
                          
        if (processedMessages.has(messageId)) {
            return false;
        }
        
        // Find the message content element
        const contentElement = messageElement.querySelector('.message-content');
        if (!contentElement) {
            return false;
        }
        
        // Skip if already being processed (prevent race conditions)
        if (contentElement.dataset.processingCollapsible === 'true' || 
            processingContentId === messageId) {
            return false;
        }
        
        // Mark as being processed
        contentElement.dataset.processingCollapsible = 'true';
        processingContentId = messageId;
        
        try {
            // Measure content height when fully expanded
            let scrollHeight = 0;
            
            // Temporarily remove any collapsed/expanded states
            const wasCollapsed = contentElement.classList.contains('collapsed');
            safeDOM(() => {
                // Store current max-height
                const currentMaxHeight = contentElement.style.maxHeight;
                
                // Remove collapse/expand state temporarily
                contentElement.classList.remove('collapsed', 'expanded');
                contentElement.style.maxHeight = 'none';
                
                // Measure full content height
                scrollHeight = contentElement.scrollHeight;
                
                // Restore previous state
                if (wasCollapsed) {
                    contentElement.classList.add('collapsed');
                }
                contentElement.style.maxHeight = currentMaxHeight;
            });
            
            // Store this message as processed
            processedMessages.add(messageId);
            
            // Only continue if message is long enough to need truncation
            if (scrollHeight <= MAX_COLLAPSED_HEIGHT) {
                // Message too short, ensure it has no collapsible classes
                safeDOM(() => {
                    contentElement.classList.remove('collapsible', 'collapsed', 'expanded');
                    
                    // Hide any existing toggle button
                    const toggleButton = messageElement.querySelector('.message-truncate-toggle');
                    if (toggleButton) {
                        toggleButton.style.display = 'none';
                    }
                });
                return true;
            }
            
            // Message is collapsible
            collapsibleMessages.add(messageId);
            
            // Get or create the toggle button
            let toggleButton = messageElement.querySelector('.message-truncate-toggle');
            
            safeDOM(() => {
                // Add collapsible classes 
                if (!contentElement.classList.contains('collapsible')) {
                    contentElement.classList.add('collapsible', 'collapsed');
                }
                
                // Create toggle button if it doesn't exist
                if (!toggleButton) {
                    toggleButton = document.createElement('button');
                    toggleButton.className = 'message-truncate-toggle';
                    toggleButton.setAttribute('aria-label', 'Show more');
                    toggleButton.setAttribute('type', 'button');
                    toggleButton.innerHTML = '<i class="fa-solid fa-chevron-down"></i>';
                    
                    // Insert button after content
                    contentElement.insertAdjacentElement('afterend', toggleButton);
                    
                    // Add click handler
                    toggleButton.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        
                        // Pause observer during toggle
                        observerPaused = true;
                        safeDisconnect();
                        
                        safeDOM(() => {
                            // Toggle classes
                            contentElement.classList.toggle('expanded');
                            contentElement.classList.toggle('collapsed');
                            toggleButton.classList.toggle('expanded');
                            
                            // Update button appearance
                            const icon = toggleButton.querySelector('i');
                            const isExpanded = contentElement.classList.contains('expanded');
                            
                            if (isExpanded) {
                                icon.classList.remove('fa-chevron-down');
                                icon.classList.add('fa-chevron-up');
                                toggleButton.setAttribute('aria-label', 'Show less');
                                
                                // Add top collapse button
                                let topCollapseButton = messageElement.querySelector('.message-truncate-toggle-top');
                                
                                if (!topCollapseButton) {
                                    topCollapseButton = document.createElement('button');
                                    topCollapseButton.className = 'message-truncate-toggle message-truncate-toggle-top expanded';
                                    topCollapseButton.setAttribute('aria-label', 'Show less');
                                    topCollapseButton.setAttribute('type', 'button');
                                    topCollapseButton.innerHTML = '<i class="fa-solid fa-chevron-up"></i>';
                                    
                                    // Insert at the top of the content element
                                    contentElement.insertAdjacentElement('beforebegin', topCollapseButton);
                                    
                                    // Add click handler that triggers the bottom button's click event
                                    topCollapseButton.addEventListener('click', function(e) {
                                        e.preventDefault();
                                        e.stopPropagation();
                                        
                                        // Trigger the original toggle button's click event
                                        toggleButton.click();
                                    });
                                }
                                
                                // Make sure top button is visible
                                topCollapseButton.style.display = 'flex';
                                topCollapseButton.style.visibility = 'visible';
                                topCollapseButton.style.opacity = '1';
                            } else {
                                icon.classList.remove('fa-chevron-up');
                                icon.classList.add('fa-chevron-down');
                                toggleButton.setAttribute('aria-label', 'Show more');
                                
                                // Remove top collapse button when collapsed
                                const topCollapseButton = messageElement.querySelector('.message-truncate-toggle-top');
                                if (topCollapseButton) {
                                    topCollapseButton.remove();
                                }
                            }
                        });
                        
                        // Resume observer after a delay
                        setTimeout(() => {
                            observerPaused = false;
                            safeReconnect();
                        }, 100);
                    });
                }
                
                // Ensure button is visible
                toggleButton.style.display = 'flex';
                toggleButton.style.visibility = 'visible';
                toggleButton.style.opacity = '1';
            });
            
            return true;
        } catch (error) {
            console.error('[Message Collapse] Error processing message:', error);
            return false;
        } finally {
            // Always clear processing flags
            contentElement.dataset.processingCollapsible = 'false';
            if (processingContentId === messageId) {
                processingContentId = null;
            }
        }
    }
    
    /**
     * Process all existing messages in the DOM
     */
    function processAllMessages() {
        // Don't process if observer is paused
        if (observerPaused) return;
        
        // Pause the observer during bulk processing
        observerPaused = true;
        safeDisconnect();
        
        const messages = document.querySelectorAll('.message');
        let processed = 0;
        
        // Process messages in small batches to avoid blocking the main thread
        const processBatch = (index, batchSize = 5) => {
            const endIndex = Math.min(index + batchSize, messages.length);
            
            for (let i = index; i < endIndex; i++) {
                if (processMessage(messages[i])) {
                    processed++;
                }
            }
            
            if (endIndex < messages.length) {
                // Process next batch
                setTimeout(() => processBatch(endIndex, batchSize), 0);
            } else {
                // All done, reconnect observer
                setTimeout(() => {
                    observerPaused = false;
                    safeReconnect();
                }, 50);
            }
        };
        
        // Start processing in batches
        processBatch(0);
    }
    
    // Setup mutation observer to watch for new messages
    function setupObserver() {
        if (!observer) {
            const chatMessagesContainer = document.getElementById('chat-messages');
            if (!chatMessagesContainer) return;
            
            observer = new MutationObserver((mutations) => {
                // If observer is paused, do nothing
                if (observerPaused) return;
                
                // Pause observer while processing
                observerPaused = true;
                safeDisconnect();
                
                // Find new messages to process
                const newMessages = new Set();
                
                mutations.forEach(mutation => {
                    // Only look at childList mutations (new nodes added)
                    if (mutation.type === 'childList') {
                        mutation.addedNodes.forEach(node => {
                            if (node.nodeType !== 1) return; // Skip non-elements
                            
                            // If node is a message, add it
                            if (node.classList && node.classList.contains('message')) {
                                newMessages.add(node);
                            } else if (node.querySelectorAll) {
                                // Otherwise, find messages inside the node
                                node.querySelectorAll('.message').forEach(msg => {
                                    newMessages.add(msg);
                                });
                            }
                        });
                    }
                });
                
                // Process any new messages found
                if (newMessages.size > 0) {
                    newMessages.forEach(msg => processMessage(msg));
                }
                
                // Reconnect observer after processing
                setTimeout(() => {
                    observerPaused = false;
                    safeReconnect();
                }, 50);
            });
            
            // Start observing
            observer.observe(chatMessagesContainer, {
                childList: true,
                subtree: true,
                characterData: false, // Don't observe text changes
                attributes: false     // Don't observe attribute changes
            });
            
            observerActive = true;
        }
    }
    
    // Initialize when DOM is ready
    function initialize() {
        // Disable old truncation system
        if (window.shouldTruncateMessage) {
            window.shouldTruncateMessage = function() { return false; };
        }
        
        // Process existing messages
        setTimeout(processAllMessages, 300);
        
        // Set up observer for new messages
        setupObserver();
        
        // Process messages on window resize (debounced)
        let resizeTimeout;
        window.addEventListener('resize', () => {
            if (resizeTimeout) clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                // Reprocess collapsible messages on resize
                if (collapsibleMessages.size > 0) {
                    observerPaused = true;
                    safeDisconnect();
                    
                    // Only reprocess messages that are known to be collapsible
                    collapsibleMessages.forEach(id => {
                        let element = null;
                        // Find by messageId data attribute
                        const messages = document.querySelectorAll('.message');
                        for (let i = 0; i < messages.length; i++) {
                            if (messages[i].dataset.messageId === id || messages[i].id === id) {
                                element = messages[i];
                                break;
                            }
                        }
                        
                        if (element) processMessage(element);
                    });
                    
                    setTimeout(() => {
                        observerPaused = false;
                        safeReconnect();
                    }, 50);
                }
            }, DEBOUNCE_TIME);
        });
        
        // Also process after fonts and images load (can affect heights)
        window.addEventListener('load', () => setTimeout(processAllMessages, 500));
        
        // Expose the reinitialization function globally
        window.reinitializeMessageTruncation = function() {
            observerPaused = true;
            safeDisconnect();
            setTimeout(() => {
                processAllMessages();
                setTimeout(() => {
                    observerPaused = false;
                    safeReconnect();
                }, 100);
            }, 50);
        };
    }
    
    // Start initialization when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        // DOM already loaded, initialize immediately
        initialize();
    }
})();